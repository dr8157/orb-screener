"""
ORB Institutional Screener - Live Stream Engine
File: live_stream_engine.py
Real-time tick processing and candle aggregation via Kite WebSocket
"""

import logging
import asyncio
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional, Callable, Any
from zoneinfo import ZoneInfo
from collections import defaultdict
import threading

from kiteconnect import KiteTicker

from models import CandleData, SymbolState, SymbolStateEnum

logger = logging.getLogger(__name__)

# Indian timezone
IST = ZoneInfo("Asia/Kolkata")

# Market timing constants
MARKET_OPEN = dt_time(9, 15)
MARKET_CLOSE = dt_time(15, 30)
ORB_END = dt_time(9, 20)  # First 5-minute candle ends


class LiveStreamEngine:
    """
    Manages real-time tick processing from Kite WebSocket.
    Aggregates ticks into 1-minute and 5-minute candles.
    """
    
    def __init__(self, api_key: str, access_token: str):
        """
        Initialize the live stream engine.
        
        Args:
            api_key: Kite API key
            access_token: Kite access token
        """
        self.api_key = api_key
        self.access_token = access_token
        self.kws: Optional[KiteTicker] = None
        
        # Symbol state tracking
        self.symbol_states: Dict[str, SymbolState] = {}
        
        # Candle building
        self._current_1m_candles: Dict[str, CandleData] = {}
        self._current_5m_candles: Dict[str, CandleData] = {}
        self._completed_1m_candles: Dict[str, List[CandleData]] = defaultdict(list)
        self._completed_5m_candles: Dict[str, List[CandleData]] = defaultdict(list)
        
        # Volume tracking for candle-specific volume calculation
        self._cumulative_vol_at_5m_start: Dict[str, int] = {}
        
        # Tick data
        self._latest_ticks: Dict[str, Dict[str, Any]] = {}
        self._last_tick_time: Optional[datetime] = None
        
        # Instrument mapping
        self._token_to_symbol: Dict[int, str] = {}
        self._symbol_to_token: Dict[str, int] = {}
        
        # Callbacks
        self._on_candle_complete: Optional[Callable] = None
        self._on_orb_complete: Optional[Callable] = None
        self._on_tick: Optional[Callable] = None
        
        # Connection state
        self._is_connected = False
        self._is_running = False
        self._ws_thread: Optional[threading.Thread] = None
    
    def set_instrument_mapping(self, symbol_to_token: Dict[str, int]):
        """Set symbol to instrument token mapping"""
        self._symbol_to_token = symbol_to_token
        self._token_to_symbol = {v: k for k, v in symbol_to_token.items()}
    
    def set_callbacks(
        self,
        on_tick: Optional[Callable] = None,
        on_candle_complete: Optional[Callable] = None,
        on_orb_complete: Optional[Callable] = None
    ):
        """Set event callbacks"""
        self._on_tick = on_tick
        self._on_candle_complete = on_candle_complete
        self._on_orb_complete = on_orb_complete
    
    def get_symbol_state(self, symbol: str) -> Optional[SymbolState]:
        """Get current state for a symbol"""
        return self.symbol_states.get(symbol)
    
    def get_all_states(self) -> Dict[str, SymbolState]:
        """Get all symbol states"""
        return self.symbol_states
    
    def get_latest_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest tick data for a symbol"""
        return self._latest_ticks.get(symbol)
    
    def get_current_5m_candle(self, symbol: str) -> Optional[CandleData]:
        """Get current in-progress 5m candle"""
        return self._current_5m_candles.get(symbol)
    
    def get_orb_candle(self, symbol: str) -> Optional[CandleData]:
        """Get the ORB (first 5m) candle for a symbol"""
        completed = self._completed_5m_candles.get(symbol, [])
        if completed:
            # First 5m candle of the day
            for candle in completed:
                if candle.timestamp.time() >= MARKET_OPEN:
                    return candle
        return None
    
    def get_sparkline_data(self, symbol: str, count: int = 20) -> List[float]:
        """Get last N close prices for sparkline"""
        state = self.symbol_states.get(symbol)
        if state and state.sparkline:
            return state.sparkline[-count:]
        return []
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self._is_connected
    
    @property
    def last_tick_time(self) -> Optional[datetime]:
        """Get timestamp of last received tick"""
        return self._last_tick_time
    
    def _get_current_minute(self, ts: Optional[datetime] = None) -> datetime:
        """Get current minute timestamp (floored)"""
        now = ts or datetime.now(IST)
        if now.time() >= MARKET_CLOSE:
            return now.replace(hour=15, minute=29, second=0, microsecond=0)
        return now.replace(second=0, microsecond=0)
    
    def _get_5m_bucket(self, ts: datetime) -> datetime:
        """Get 5-minute bucket start time"""
        if ts.time() >= MARKET_CLOSE:
            return ts.replace(hour=15, minute=25, second=0, microsecond=0)
        minute = ts.minute - (ts.minute % 5)
        return ts.replace(minute=minute, second=0, microsecond=0)
    
    def _is_market_hours(self) -> bool:
        """Check if within market hours"""
        now = datetime.now(IST).time()
        return MARKET_OPEN <= now <= MARKET_CLOSE
    
    def _is_orb_period(self) -> bool:
        """Check if within ORB formation period (9:15-9:20)"""
        now = datetime.now(IST).time()
        return MARKET_OPEN <= now < ORB_END
    
    def _initialize_symbol_state(self, symbol: str) -> SymbolState:
        """Initialize or get symbol state"""
        if symbol not in self.symbol_states:
            self.symbol_states[symbol] = SymbolState(symbol=symbol)
        return self.symbol_states[symbol]
    
    def _process_tick(self, tick: Dict[str, Any]):
        """
        Process a single tick and update candles/state.
        
        Args:
            tick: Tick data from Kite WebSocket
        """
        token = tick.get('instrument_token')
        symbol = self._token_to_symbol.get(token)
        
        if not symbol:
            return
        
        ltp = tick.get('last_price', 0)
        volume = tick.get('volume_traded', 0)
        timestamp = tick.get('exchange_timestamp') or datetime.now(IST)
        
        # Ensure timestamp is timezone-aware
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=IST)
        
        # Store latest tick
        self._latest_ticks[symbol] = tick
        self._last_tick_time = timestamp
        
        # Initialize state
        state = self._initialize_symbol_state(symbol)
        state.current_price = ltp
        state.last_tick_time = timestamp
        
        # Capture Kite's change % (dividend-adjusted)
        ohlc = tick.get('ohlc', {})
        prev_close = ohlc.get('close', 0)
        if prev_close > 0:
            state.prev_close = prev_close
            state.change_percent = ((ltp - prev_close) / prev_close) * 100
        
        # Capture cumulative day volume (volume_traded is cumulative for the day)
        state.day_volume = volume
        
        # Update sparkline
        if len(state.sparkline) == 0 or state.sparkline[-1] != ltp:
            state.sparkline.append(ltp)
            if len(state.sparkline) > 100:
                state.sparkline = state.sparkline[-100:]
        
        # Build candles
        self._update_candles(symbol, ltp, volume, timestamp, tick)
        
        # Update state machine
        self._update_state_machine(symbol)
        
        # Fire tick callback
        if self._on_tick:
            try:
                self._on_tick(symbol, tick, state)
            except Exception as e:
                logger.error(f"Tick callback error: {e}")
    
    def _update_candles(
        self, 
        symbol: str, 
        ltp: float, 
        volume: int, 
        timestamp: datetime,
        tick: Dict[str, Any]
    ):
        """Update 1m and 5m candles with tick data"""
        
        # Get bucket times
        bucket_1m = self._get_current_minute(timestamp)
        bucket_5m = self._get_5m_bucket(timestamp)
        
        # --- 1-minute candle ---
        if symbol not in self._current_1m_candles:
            self._current_1m_candles[symbol] = CandleData(
                symbol=symbol,
                timestamp=bucket_1m,
                open=ltp,
                high=ltp,
                low=ltp,
                close=ltp,
                volume=0
            )
        
        candle_1m = self._current_1m_candles[symbol]
        
        # Check if new minute
        if candle_1m.timestamp != bucket_1m:
            # Complete previous candle
            self._completed_1m_candles[symbol].append(candle_1m)
            
            # Keep only last 60 candles
            if len(self._completed_1m_candles[symbol]) > 60:
                self._completed_1m_candles[symbol] = self._completed_1m_candles[symbol][-60:]
            
            # Start new candle
            self._current_1m_candles[symbol] = CandleData(
                symbol=symbol,
                timestamp=bucket_1m,
                open=ltp,
                high=ltp,
                low=ltp,
                close=ltp,
                volume=0
            )
            candle_1m = self._current_1m_candles[symbol]
        
        # Update candle
        candle_1m.high = max(candle_1m.high, ltp)
        candle_1m.low = min(candle_1m.low, ltp)
        candle_1m.close = ltp
        
        # Estimate volume for this candle from cumulative
        # (Kite provides cumulative day volume)
        ohlc = tick.get('ohlc', {})
        candle_1m.volume = volume  # Using cumulative for now
        
        # --- 5-minute candle ---
        if symbol not in self._current_5m_candles:
            self._current_5m_candles[symbol] = CandleData(
                symbol=symbol,
                timestamp=bucket_5m,
                open=ltp,
                high=ltp,
                low=ltp,
                close=ltp,
                volume=0
            )
            # Track cumulative volume at candle start
            self._cumulative_vol_at_5m_start[symbol] = volume
        
        candle_5m = self._current_5m_candles[symbol]
        
        # Check if new 5-minute bucket
        if candle_5m.timestamp != bucket_5m:
            # Calculate actual candle volume before saving
            start_vol = self._cumulative_vol_at_5m_start.get(symbol, 0)
            candle_5m.volume = volume - start_vol if volume > start_vol else candle_5m.volume
            
            # Complete previous candle
            self._completed_5m_candles[symbol].append(candle_5m)
            
            # Fire ORB complete callback if this was the 9:15-9:20 candle
            prev_time = candle_5m.timestamp.time()
            if prev_time == MARKET_OPEN and self._on_orb_complete:
                try:
                    self._on_orb_complete(symbol, candle_5m)
                except Exception as e:
                    logger.error(f"ORB complete callback error: {e}")
            
            # Fire candle complete callback
            if self._on_candle_complete:
                try:
                    self._on_candle_complete(symbol, candle_5m, "5m")
                except Exception as e:
                    logger.error(f"Candle complete callback error: {e}")
            
            # Update state with previous candle volume for deceleration
            state = self.symbol_states.get(symbol)
            if state:
                state.prev_candle_volume = candle_5m.volume
            
            # Keep only last 20 5m candles
            if len(self._completed_5m_candles[symbol]) > 20:
                self._completed_5m_candles[symbol] = self._completed_5m_candles[symbol][-20:]
            
            # Start new candle and track new start volume
            self._current_5m_candles[symbol] = CandleData(
                symbol=symbol,
                timestamp=bucket_5m,
                open=ltp,
                high=ltp,
                low=ltp,
                close=ltp,
                volume=0
            )
            self._cumulative_vol_at_5m_start[symbol] = volume
            candle_5m = self._current_5m_candles[symbol]
        
        # Update candle
        candle_5m.high = max(candle_5m.high, ltp)
        candle_5m.low = min(candle_5m.low, ltp)
        candle_5m.close = ltp
        
        # Calculate current candle volume (cumulative now - cumulative at candle start)
        start_vol = self._cumulative_vol_at_5m_start.get(symbol, 0)
        candle_5m.volume = volume - start_vol if volume > start_vol else 0
        
        # Update current candle volume for deceleration
        state = self.symbol_states.get(symbol)
        if state:
            state.curr_candle_volume = candle_5m.volume
    
    def _update_state_machine(self, symbol: str):
        """Update symbol state machine based on current data"""
        state = self.symbol_states.get(symbol)
        if not state:
            return
        
        now = datetime.now(IST)
        current_time = now.time()
        
        # Get ORB candle (first 5m candle of the day)
        orb_candle = self.get_orb_candle(symbol)
        
        # State transitions
        if state.state == SymbolStateEnum.IDLE:
            # Check for ignition (high volume in first 5m)
            if self._is_orb_period():
                candle = self._current_5m_candles.get(symbol)
                if candle and candle.volume > 0:
                    state.state = SymbolStateEnum.IGNITION
                    state.orb_open = candle.open
                    state.orb_high = candle.high
                    state.orb_low = candle.low
                    state.orb_close = candle.close
                    state.orb_volume = candle.volume
                    state.orb_timestamp = candle.timestamp
        
        elif state.state == SymbolStateEnum.IGNITION:
            # Update ORB values during formation
            candle = self._current_5m_candles.get(symbol)
            if candle:
                state.orb_high = max(state.orb_high, candle.high)
                state.orb_low = min(state.orb_low, candle.low) if state.orb_low > 0 else candle.low
                state.orb_close = candle.close
                state.orb_volume = candle.volume
            
            # Transition to ORB_FORMED after 9:20
            if current_time >= ORB_END:
                if orb_candle:
                    state.orb_high = orb_candle.high
                    state.orb_low = orb_candle.low
                    state.orb_open = orb_candle.open
                    state.orb_close = orb_candle.close
                    state.orb_volume = orb_candle.volume
                state.state = SymbolStateEnum.ORB_FORMED
        
        elif state.state == SymbolStateEnum.ORB_FORMED:
            ltp = state.current_price
            
            # Track lowest price for pre-breakout pullback measurement
            if state.pre_breakout_low == 0 or ltp < state.pre_breakout_low:
                state.pre_breakout_low = ltp
            
            # Check for ORB break
            if ltp > state.orb_high:
                state.state = SymbolStateEnum.ORB_BROKEN
                state.breakout_price = ltp
                state.breakout_time = now
                
                # Calculate pre-breakout pullback
                if state.orb_high > 0 and state.pre_breakout_low > 0:
                    state.pullback_percent = ((state.orb_high - state.pre_breakout_low) / state.orb_high) * 100
                
                # Calculate speed (minutes since ORB formed at 9:20)
                orb_end_time = now.replace(hour=9, minute=20, second=0, microsecond=0)
                if now >= orb_end_time:
                    speed_delta = now - orb_end_time
                    state.speed_minutes = int(speed_delta.total_seconds() / 60)
            
            elif ltp < state.orb_low:
                state.state = SymbolStateEnum.FAILED
            
            # Check for testing (within 0.5% of high)
            elif state.orb_high > 0:
                distance_pct = ((state.orb_high - ltp) / state.orb_high) * 100
                if distance_pct <= 0.5:
                    state.state = SymbolStateEnum.ORB_TESTING
        
        elif state.state == SymbolStateEnum.ORB_TESTING:
            ltp = state.current_price
            
            # Continue tracking lowest price for pre-breakout pullback
            if ltp < state.pre_breakout_low:
                state.pre_breakout_low = ltp
            
            # Check for breakout
            if ltp > state.orb_high:
                state.state = SymbolStateEnum.ORB_BROKEN
                state.breakout_price = ltp
                state.breakout_time = now
                
                # Calculate pre-breakout pullback
                if state.orb_high > 0 and state.pre_breakout_low > 0:
                    state.pullback_percent = ((state.orb_high - state.pre_breakout_low) / state.orb_high) * 100
                
                # Calculate speed
                orb_end_time = now.replace(hour=9, minute=20, second=0, microsecond=0)
                if now >= orb_end_time:
                    speed_delta = now - orb_end_time
                    state.speed_minutes = int(speed_delta.total_seconds() / 60)
            
            elif ltp < state.orb_low:
                state.state = SymbolStateEnum.FAILED
            
            # Return to ORB_FORMED if price retreats
            elif state.orb_high > 0:
                distance_pct = ((state.orb_high - ltp) / state.orb_high) * 100
                if distance_pct > 0.5:
                    state.state = SymbolStateEnum.ORB_FORMED
        
        elif state.state == SymbolStateEnum.ORB_BROKEN:
            ltp = state.current_price
            
            # Calculate deceleration
            if state.prev_candle_volume > 0 and state.curr_candle_volume > 0:
                state.decel_ok = state.curr_candle_volume < state.prev_candle_volume
    
    def _on_ws_connect(self, ws, response):
        """WebSocket connected callback"""
        logger.info("✅ Kite WebSocket connected")
        self._is_connected = True
        
        # Subscribe to all instruments
        tokens = list(self._token_to_symbol.keys())
        if tokens:
            # Subscribe in batches (max 3000 per call)
            batch_size = 3000
            for i in range(0, len(tokens), batch_size):
                batch = tokens[i:i+batch_size]
                ws.subscribe(batch)
                ws.set_mode(ws.MODE_FULL, batch)
            logger.info(f"Subscribed to {len(tokens)} instruments")
    
    def _on_ws_close(self, ws, code, reason):
        """WebSocket closed callback"""
        logger.warning(f"WebSocket closed: {code} - {reason}")
        self._is_connected = False
    
    def _on_ws_error(self, ws, code, reason):
        """WebSocket error callback"""
        logger.error(f"WebSocket error: {code} - {reason}")
    
    def _on_ws_ticks(self, ws, ticks: List[Dict]):
        """WebSocket ticks callback"""
        for tick in ticks:
            try:
                self._process_tick(tick)
            except Exception as e:
                logger.error(f"Error processing tick: {e}")
    
    def _on_ws_reconnect(self, ws, attempts_count):
        """WebSocket reconnecting callback"""
        logger.info(f"WebSocket reconnecting... attempt {attempts_count}")
    
    def _on_ws_noreconnect(self, ws):
        """WebSocket no more reconnects callback"""
        logger.error("WebSocket: Max reconnect attempts reached")
        self._is_connected = False
    
    def start(self):
        """Start the WebSocket connection"""
        if self._is_running:
            logger.warning("Stream already running")
            return
        
        logger.info("Starting Kite WebSocket stream...")
        
        self.kws = KiteTicker(self.api_key, self.access_token)
        
        # Set callbacks
        self.kws.on_connect = self._on_ws_connect
        self.kws.on_close = self._on_ws_close
        self.kws.on_error = self._on_ws_error
        self.kws.on_ticks = self._on_ws_ticks
        self.kws.on_reconnect = self._on_ws_reconnect
        self.kws.on_noreconnect = self._on_ws_noreconnect
        
        self._is_running = True
        
        # Start in background thread
        def run_ws():
            try:
                self.kws.connect(threaded=False)
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                self._is_connected = False
                self._is_running = False
        
        self._ws_thread = threading.Thread(target=run_ws, daemon=True)
        self._ws_thread.start()
    
    def stop(self):
        """Stop the WebSocket connection"""
        logger.info("Stopping Kite WebSocket stream...")
        self._is_running = False
        
        if self.kws:
            try:
                self.kws.close()
            except Exception:
                pass
        
        self._is_connected = False
    
    def reset_day(self):
        """Reset all state for new trading day"""
        logger.info("Resetting state for new trading day")
        
        self.symbol_states.clear()
        self._current_1m_candles.clear()
        self._current_5m_candles.clear()
        self._completed_1m_candles.clear()
        self._completed_5m_candles.clear()
        self._cumulative_vol_at_5m_start.clear()
        self._latest_ticks.clear()
