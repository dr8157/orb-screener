"""
ORB Institutional Screener - FastAPI Backend
File: main.py
Main application with REST API and WebSocket endpoints
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, time as dt_time
from typing import Dict, List, Set, Optional, Any
from zoneinfo import ZoneInfo

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Admin password for config changes
ADMIN_PASSWORD = "orb@deepak2026"

from models import (
    ScreenerConfig,
    SignalData,
    TopSignalsResponse,
    WebSocketMessage,
    HealthResponse,
    CandleData
)
from baseline_engine import BaselineEngine
from live_stream_engine import LiveStreamEngine
from scoring_engine import ScoringEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Indian timezone
IST = ZoneInfo("Asia/Kolkata")

# Market timing
MARKET_OPEN = dt_time(9, 15)
MARKET_CLOSE = dt_time(15, 30)

# Global state
config = ScreenerConfig()
baseline_engine: Optional[BaselineEngine] = None
live_stream_engine: Optional[LiveStreamEngine] = None
scoring_engine: Optional[ScoringEngine] = None

# WebSocket connections
ws_connections: Set[WebSocket] = set()

# Cached signals
signals_cache: Dict[str, SignalData] = {}
last_broadcast: Optional[datetime] = None


def is_market_hours() -> bool:
    """Check if within market hours"""
    now = datetime.now(IST).time()
    return MARKET_OPEN <= now <= MARKET_CLOSE


def get_market_status() -> str:
    """Get current market status string"""
    now = datetime.now(IST).time()
    
    if now < MARKET_OPEN:
        return "pre-market"
    elif now > MARKET_CLOSE:
        return "closed"
    else:
        return "open"


async def broadcast_signals():
    """Broadcast signals to all connected WebSocket clients"""
    global last_broadcast
    
    if not ws_connections:
        return
    
    # Get top signals
    top_signals = scoring_engine.get_top_signals(
        signals_cache,
        n=config.top_n_display,
        min_score=config.score_threshold  # Use admin threshold
    )
    
    # Create message
    message = WebSocketMessage(
        type="update",
        signals=[s.model_dump() for s in top_signals],
        timestamp=datetime.now(IST).isoformat()
    )
    
    # Broadcast to all clients
    message_json = message.model_dump_json()
    disconnected = set()
    
    for ws in ws_connections:
        try:
            await ws.send_text(message_json)
        except Exception:
            disconnected.add(ws)
    
    # Remove disconnected clients
    for ws in disconnected:
        ws_connections.discard(ws)
    
    last_broadcast = datetime.now(IST)


async def signal_update_loop():
    """Background loop to update signals and broadcast"""
    global signals_cache
    
    logger.info("Starting signal update loop...")
    
    while True:
        try:
            # Recalculate signals if we have data
            if live_stream_engine and scoring_engine:
                states = live_stream_engine.get_all_states()
                baselines = baseline_engine.get_all_baselines() if baseline_engine else {}
                
                # Get current and ORB candles
                current_candles = {}
                orb_candles = {}
                
                for symbol in states.keys():
                    current = live_stream_engine.get_current_5m_candle(symbol)
                    orb = live_stream_engine.get_orb_candle(symbol)
                    
                    if current:
                        current_candles[symbol] = current
                    if orb:
                        orb_candles[symbol] = orb
                
                # Recalculate
                signals_cache = scoring_engine.recalculate_all(
                    states=states,
                    baselines=baselines,
                    current_candles=current_candles,
                    orb_candles=orb_candles
                )
                
                # Broadcast to WebSocket clients
                await broadcast_signals()
            
            # Wait 1 second before next update
            await asyncio.sleep(1)
            
        except asyncio.CancelledError:
            logger.info("Signal update loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in signal update loop: {e}")
            await asyncio.sleep(1)


async def load_todays_orb_candles(kite, symbols: List[str], token_mapping: Dict[str, int]):
    """
    Load today's 9:15-9:20 candles from historical data.
    This allows the screener to work even when starting mid-day.
    """
    global live_stream_engine
    
    logger.info("Loading today's ORB candles from historical data...")
    
    now = datetime.now(IST)
    today = now.date()
    
    # Only load if we're past 9:20 AM
    if now.time() < dt_time(9, 20):
        logger.info("Before 9:20 AM - ORB candles will form naturally")
        return
    
    loaded_count = 0
    broken_count = 0
    from models import SymbolState, SymbolStateEnum, CandleData
    
    # Fetch historical data for today in batches
    from_date = datetime.combine(today, dt_time(9, 15)).replace(tzinfo=IST)
    to_date = datetime.combine(today, dt_time(15, 30)).replace(tzinfo=IST)
    orb_end = dt_time(9, 20)
    
    import time as time_module
    batch_size = 50
    
    for i, symbol in enumerate(symbols):  # Load ALL symbols
        try:
            instrument_token = token_mapping.get(symbol)
            if not instrument_token:
                continue
            
            # Fetch today's 5-minute data
            data = kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval="5minute"
            )
            
            if not data:
                continue
            
            # Find the 9:15 candle (first candle = ORB)
            orb_candle_data = None
            for candle in data:
                candle_time = candle['date']
                if hasattr(candle_time, 'time'):
                    if candle_time.time() == dt_time(9, 15):
                        orb_candle_data = candle
                        break
                else:
                    # Parse if string
                    from dateutil import parser
                    parsed = parser.parse(str(candle_time))
                    if parsed.time() == dt_time(9, 15):
                        orb_candle_data = candle
                        break
            
            if not orb_candle_data:
                continue
            
            # Create ORB candle
            orb_candle = CandleData(
                symbol=symbol,
                timestamp=from_date,
                open=orb_candle_data['open'],
                high=orb_candle_data['high'],
                low=orb_candle_data['low'],
                close=orb_candle_data['close'],
                volume=orb_candle_data['volume']
            )
            
            orb_high = orb_candle.high
            orb_low = orb_candle.low
            
            # Initialize symbol state with ORB values
            state = SymbolState(
                symbol=symbol,
                state=SymbolStateEnum.ORB_FORMED,
                orb_high=orb_high,
                orb_low=orb_low,
                orb_open=orb_candle.open,
                orb_close=orb_candle.close,
                orb_volume=orb_candle.volume,
                orb_timestamp=from_date
            )
            
            # Scan through subsequent candles to find breakout
            breakout_found = False
            pre_breakout_low = orb_low  # Start tracking from ORB low
            for candle in data:
                candle_time = candle['date']
                if hasattr(candle_time, 'time'):
                    ct = candle_time.time()
                else:
                    from dateutil import parser
                    ct = parser.parse(str(candle_time)).time()
                
                # Skip candles before ORB end
                if ct < orb_end:
                    continue
                
                # Track lowest price before breakout
                pre_breakout_low = min(pre_breakout_low, candle['low'])
                
                # Check for breakout (high breaks above ORB high)
                if candle['high'] > orb_high:
                    state.state = SymbolStateEnum.ORB_BROKEN
                    state.breakout_price = orb_high
                    
                    # Calculate pre-breakout pullback
                    state.pre_breakout_low = pre_breakout_low
                    if orb_high > 0:
                        state.pullback_percent = ((orb_high - pre_breakout_low) / orb_high) * 100
                    
                    # Get candle start time
                    if hasattr(candle_time, 'time'):
                        candle_start_dt = candle_time
                    else:
                        candle_start_dt = parser.parse(str(candle_time))
                    
                    if candle_start_dt.tzinfo is None:
                        candle_start_dt = candle_start_dt.replace(tzinfo=IST)
                    
                    # Breakout time = candle END time (confirmed when candle closes)
                    from datetime import timedelta
                    breakout_dt = candle_start_dt + timedelta(minutes=5)
                    state.breakout_time = breakout_dt
                    
                    # Speed = minutes from 9:20 to breakout candle END
                    orb_end_dt = datetime.combine(today, orb_end).replace(tzinfo=IST)
                    speed_delta = breakout_dt - orb_end_dt
                    state.speed_minutes = max(0, int(speed_delta.total_seconds() / 60))
                    
                    breakout_found = True
                    broken_count += 1
                    break
                
                elif candle['low'] < orb_low:
                    state.state = SymbolStateEnum.FAILED
                    break
            
            # Get current price from latest candle and calculate day volume
            if data:
                latest = data[-1]
                state.current_price = latest['close']
                
                # Calculate cumulative day volume (sum of all candles)
                state.day_volume = sum(candle['volume'] for candle in data)
                
                # Calculate change percent from previous day close (if available from ORB candle)
                # This helps with proper ranking
                if orb_candle.open > 0:
                    state.prev_close = orb_candle.open  # Approximate prev close
                    state.change_percent = ((latest['close'] - orb_candle.open) / orb_candle.open) * 100
                
                # Pre-breakout pullback is already calculated at breakout time
                # No post-breakout tracking needed
                
                # Store deceleration tracking from last two candles
                if len(data) >= 2:
                    state.prev_candle_volume = data[-2]['volume']
                    state.curr_candle_volume = data[-1]['volume']
                    state.decel_ok = state.curr_candle_volume < state.prev_candle_volume
            
            # Store in live stream engine
            if live_stream_engine:
                live_stream_engine.symbol_states[symbol] = state
                live_stream_engine._completed_5m_candles[symbol].append(orb_candle)
                
                # Also store the current/latest candle for real-time metric updates
                if data and len(data) > 0:
                    latest_candle_data = data[-1]
                    latest_time = latest_candle_data['date']
                    if hasattr(latest_time, 'tzinfo') and latest_time.tzinfo is None:
                        latest_time = latest_time.replace(tzinfo=IST)
                    elif not hasattr(latest_time, 'tzinfo'):
                        from dateutil import parser
                        latest_time = parser.parse(str(latest_time)).replace(tzinfo=IST)
                    
                    current_candle = CandleData(
                        symbol=symbol,
                        timestamp=latest_time,
                        open=latest_candle_data['open'],
                        high=latest_candle_data['high'],
                        low=latest_candle_data['low'],
                        close=latest_candle_data['close'],
                        volume=latest_candle_data['volume']
                    )
                    live_stream_engine._current_5m_candles[symbol] = current_candle
            
            loaded_count += 1
            
            # Rate limiting: pause after every batch to avoid API throttling
            if (i + 1) % batch_size == 0:
                logger.info(f"Loaded {loaded_count} ORB candles so far...")
                time_module.sleep(0.5)  # 500ms pause between batches
            
        except Exception as e:
            logger.debug(f"Failed to load ORB for {symbol}: {e}")
            continue
    
    logger.info(f"Loaded {loaded_count} ORB candles, {broken_count} breakouts detected")


async def initialize_engines():
    """Initialize all engines on startup"""
    global baseline_engine, live_stream_engine, scoring_engine
    
    logger.info("Initializing ORB Screener engines...")
    
    try:
        # Import Kite credentials
        from kite_credentials import (
            get_kite_instance,
            API_KEY,
            load_instruments_cache,
            get_nse_equity_symbols,
            get_instruments_batch
        )
        
        # Get authenticated Kite instance
        kite = get_kite_instance()
        access_token = kite.access_token
        
        # Load instrument cache
        logger.info("Loading NSE instruments...")
        load_instruments_cache()
        
        # Get equity symbols (limit for performance)
        symbols = get_nse_equity_symbols(limit=500)
        logger.info(f"Monitoring {len(symbols)} NSE equity symbols")
        
        # Get instrument tokens
        token_mapping = get_instruments_batch(symbols)
        logger.info(f"Mapped {len(token_mapping)} instrument tokens")
        
        # Initialize Baseline Engine
        logger.info("Initializing Baseline Engine...")
        baseline_engine = BaselineEngine(kite)
        baseline_engine.set_instrument_tokens(token_mapping)
        baseline_engine.update_config(config)
        
        # Refresh baselines (takes time, do in background for startup)
        if is_market_hours() or baseline_engine.is_stale():
            logger.info("Refreshing baselines in background for ALL symbols...")
            # Load baselines for ALL symbols to ensure heat percentages work
            asyncio.create_task(
                asyncio.to_thread(
                    baseline_engine.refresh_baselines, 
                    symbols  # Load ALL symbols, not just subset
                )
            )
        
        # Initialize Scoring Engine
        logger.info("Initializing Scoring Engine...")
        scoring_engine = ScoringEngine(config)
        
        # Initialize Live Stream Engine
        logger.info("Initializing Live Stream Engine...")
        live_stream_engine = LiveStreamEngine(API_KEY, access_token)
        live_stream_engine.set_instrument_mapping(token_mapping)
        
        # Set callbacks
        def on_tick(symbol, tick, state):
            # Tick received - signals will be updated in the loop
            pass
        
        def on_orb_complete(symbol, candle):
            logger.info(f"ORB formed for {symbol}: H={candle.high} L={candle.low}")
        
        live_stream_engine.set_callbacks(
            on_tick=on_tick,
            on_orb_complete=on_orb_complete
        )
        
        # Load today's ORB candles (for mid-day start OR after-hours demo)
        now = datetime.now(IST)
        today_9am = now.replace(hour=9, minute=15, second=0, microsecond=0)
        
        # If today had a market session (we're after 9:15 AM today), load the data
        if now >= today_9am:
            logger.info("Loading today's historical ORB data...")
            await load_todays_orb_candles(kite, symbols, token_mapping)
        
        # Start WebSocket stream only during market hours
        if is_market_hours():
            logger.info("Market is open - starting live stream...")
            live_stream_engine.start()
        else:
            logger.info("Market is closed - showing today's historical signals for demo")
        
        logger.info("All engines initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize engines: {e}")
        raise
        raise


async def shutdown_engines():
    """Cleanup on shutdown"""
    logger.info("Shutting down engines...")
    
    if live_stream_engine:
        live_stream_engine.stop()
    
    logger.info("Engines shut down")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    await initialize_engines()
    
    # Start background task
    update_task = asyncio.create_task(signal_update_loop())
    
    yield
    
    # Shutdown
    update_task.cancel()
    try:
        await update_task
    except asyncio.CancelledError:
        pass
    
    await shutdown_engines()


# Create FastAPI app
app = FastAPI(
    title="ORB Institutional Screener",
    description="Real-time NSE stock breakout detection",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        kite_connected=live_stream_engine.is_connected if live_stream_engine else False,
        market_status=get_market_status(),
        symbols_loaded=len(live_stream_engine._symbol_to_token) if live_stream_engine else 0,
        baselines_loaded=baseline_engine.loaded_count if baseline_engine else 0,
        last_tick=live_stream_engine.last_tick_time.isoformat() if live_stream_engine and live_stream_engine.last_tick_time else None
    )


@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    return config.model_dump()


@app.post("/api/config")
async def update_config(new_config: Dict[str, Any], x_admin_password: Optional[str] = Header(None)):
    """Update configuration - requires admin password"""
    global config

    # Check admin password
    if x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Unauthorized: Invalid admin password")

    try:
        # Update only provided fields
        current = config.model_dump()
        current.update(new_config)
        config = ScreenerConfig(**current)

        # Update engines
        if baseline_engine:
            baseline_engine.update_config(config)
        if scoring_engine:
            scoring_engine.update_config(config)

        logger.info(f"Configuration updated: {new_config}")
        return {"status": "success", "config": config.model_dump()}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/top-signals", response_model=TopSignalsResponse)
async def get_top_signals():
    """Get top ranked signals"""
    top_signals = scoring_engine.get_top_signals(
        signals_cache,
        n=config.top_n_display,
        min_score=config.score_threshold  # Use admin threshold
    ) if scoring_engine else []
    
    return TopSignalsResponse(
        signals=top_signals,
        timestamp=datetime.now(IST).isoformat(),
        count=len(top_signals)
    )


@app.post("/api/baseline/refresh")
async def refresh_baselines():
    """Trigger baseline recalculation"""
    if not baseline_engine:
        raise HTTPException(status_code=503, detail="Baseline engine not initialized")
    
    try:
        # Get symbols from live stream engine
        symbols = list(live_stream_engine._symbol_to_token.keys()) if live_stream_engine else []
        
        if not symbols:
            raise HTTPException(status_code=400, detail="No symbols loaded")
        
        # Refresh in background (limit to 100 for API call)
        asyncio.create_task(
            asyncio.to_thread(
                baseline_engine.refresh_baselines,
                symbols[:100]
            )
        )
        
        return {
            "status": "started",
            "message": f"Refreshing baselines for {min(len(symbols), 100)} symbols"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/debug")
async def debug_info():
    """Debug information endpoint with state distribution"""
    # Count states
    state_counts = {}
    recent_breakouts = []
    orb_formed_count = 0
    
    if live_stream_engine:
        for symbol, state in live_stream_engine.get_all_states().items():
            state_name = state.state.value if hasattr(state.state, 'value') else str(state.state)
            state_counts[state_name] = state_counts.get(state_name, 0) + 1
            
            # Track recent breakouts (last 30 min)
            if state.breakout_time:
                now = datetime.now(IST)
                if hasattr(state.breakout_time, 'tzinfo') and state.breakout_time.tzinfo is None:
                    bt = state.breakout_time.replace(tzinfo=IST)
                else:
                    bt = state.breakout_time
                
                # Breakouts after 2:00 PM (late breakouts)
                if bt.hour >= 14:
                    recent_breakouts.append({
                        "symbol": symbol,
                        "breakout_time": bt.strftime("%H:%M"),
                        "price": state.current_price,
                        "speed_minutes": state.speed_minutes
                    })
    
    return {
        "market_status": get_market_status(),
        "is_market_hours": is_market_hours(),
        "current_time_ist": datetime.now(IST).isoformat(),
        "ws_connected": live_stream_engine.is_connected if live_stream_engine else False,
        "ws_clients": len(ws_connections),
        "symbols_tracked": len(live_stream_engine.get_all_states()) if live_stream_engine else 0,
        "baselines_loaded": baseline_engine.loaded_count if baseline_engine else 0,
        "signals_cached": len(signals_cache),
        "state_distribution": state_counts,
        "late_breakouts": recent_breakouts[:10],
        "last_broadcast": last_broadcast.isoformat() if last_broadcast else None,
        "config": config.model_dump()
    }


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time signal streaming"""
    await websocket.accept()
    ws_connections.add(websocket)
    
    # Only log when we have multiple clients (reduces noise)
    client_count = len(ws_connections)
    if client_count == 1:
        logger.info("✅ WebSocket client connected")
    
    try:
        # Send initial data immediately
        top_signals = scoring_engine.get_top_signals(
            signals_cache,
            n=config.top_n_display,
            min_score=config.score_threshold  # Use admin threshold
        ) if scoring_engine else []
        
        initial_message = WebSocketMessage(
            type="update",
            signals=[s.model_dump() for s in top_signals],
            timestamp=datetime.now(IST).isoformat()
        )
        
        await websocket.send_text(initial_message.model_dump_json())
        
        # Keep connection alive with shorter timeout for responsiveness
        while True:
            try:
                # Wait for client messages (ping/pong)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # Reduced from 60s
                )
                
                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_text('{"type":"ping"}')
                except Exception:
                    break  # Connection lost
                    
    except WebSocketDisconnect:
        pass  # Normal disconnect, no need to log
    except Exception:
        pass  # Suppress connection errors on page refresh
    finally:
        ws_connections.discard(websocket)
        # Only log when all clients disconnected
        if len(ws_connections) == 0:
            logger.debug("All WebSocket clients disconnected")


# Direct run
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
