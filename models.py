"""
ORB Institutional Screener - Data Models
File: models.py
Pydantic models for type-safe data handling
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SymbolStateEnum(str, Enum):
    """State machine for ORB tracking"""
    IDLE = "IDLE"
    IGNITION = "IGNITION"
    ORB_FORMED = "ORB_FORMED"
    ORB_TESTING = "ORB_TESTING"
    ORB_BROKEN = "ORB_BROKEN"
    FAILED = "FAILED"


class DirectionEnum(str, Enum):
    """Breakout direction"""
    LONG = "LONG"
    SHORT = "SHORT"


class ScreenerConfig(BaseModel):
    """Configuration for the screener"""
    # Baseline Settings
    baseline_days: int = Field(default=20, ge=1, le=100, description="Days for baseline calculation")
    
    # Threshold Settings
    volume_multiplier: float = Field(default=1.5, ge=1.0, description="Volume spike threshold (Nx)")
    value_threshold: float = Field(default=0.5, ge=0.0, description="Value threshold in Crores")
    body_threshold: float = Field(default=1.2, ge=0.0, description="Body expansion threshold")
    score_threshold: int = Field(default=0, ge=0, le=100, description="Minimum score to display")
    top_n_display: int = Field(default=10, ge=1, le=50, description="Number of top signals to show")
    
    # Score Weights (must sum to 1.0)
    weight_volume: float = Field(default=0.25, ge=0.0, le=1.0)
    weight_value: float = Field(default=0.25, ge=0.0, le=1.0)
    weight_body: float = Field(default=0.20, ge=0.0, le=1.0)
    weight_speed: float = Field(default=0.15, ge=0.0, le=1.0)
    weight_pullback: float = Field(default=0.10, ge=0.0, le=1.0)
    weight_decel: float = Field(default=0.05, ge=0.0, le=1.0)
    
    # Scoring Formula Constants
    heat_max: float = Field(default=1000.0, description="Cap heat% for normalization")
    speed_decay_k: float = Field(default=30.0, description="Speed decay constant")
    pb_max: float = Field(default=5.0, description="Max pullback% for normalization")
    
    # Watchlist (empty = all NSE stocks)
    watchlist: List[str] = Field(default_factory=list)


class CandleData(BaseModel):
    """OHLCV candle structure"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    @property
    def body(self) -> float:
        """Candle body size (absolute)"""
        return abs(self.close - self.open)
    
    @property
    def range(self) -> float:
        """Total candle range"""
        return self.high - self.low
    
    @property
    def body_ratio(self) -> float:
        """Body to range ratio (0-1)"""
        if self.range == 0:
            return 0.0
        return self.body / self.range
    
    @property
    def value(self) -> float:
        """Turnover in Crores"""
        return (self.volume * self.close) / 1e7


class BaselineMetrics(BaseModel):
    """Pre-computed baseline metrics per symbol"""
    symbol: str
    avg_vol_5m: float = 0.0  # Average 5m volume
    std_vol_5m: float = 0.0  # Std dev 5m volume
    avg_value_5m: float = 0.0  # Average 5m value in Cr
    avg_body_5m: float = 0.0  # Average 5m body size
    yesterday_close: float = 0.0  # Previous day close
    last_updated: datetime = Field(default_factory=datetime.now)


class SymbolState(BaseModel):
    """State tracking for a symbol"""
    symbol: str
    state: SymbolStateEnum = SymbolStateEnum.IDLE
    
    # ORB Reference (9:15-9:20 candle)
    orb_high: float = 0.0
    orb_low: float = 0.0
    orb_open: float = 0.0
    orb_close: float = 0.0
    orb_volume: int = 0
    orb_timestamp: Optional[datetime] = None
    
    # Current tracking
    current_price: float = 0.0
    breakout_price: float = 0.0
    breakout_time: Optional[datetime] = None
    
    # Pre-breakout pullback tracking (retracement from ORB high before breakout)
    pre_breakout_low: float = 0.0  # Lowest price between ORB formation and breakout
    pullback_percent: float = 0.0
    
    # Deceleration tracking
    prev_candle_volume: int = 0
    curr_candle_volume: int = 0
    decel_ok: bool = False
    
    # Speed tracking
    speed_minutes: int = 0
    
    # Change tracking (from Kite tick data - dividend adjusted)
    change_percent: float = 0.0
    prev_close: float = 0.0
    
    # Sparkline data (last N close prices)
    sparkline: List[float] = Field(default_factory=list)
    
    # Last tick
    last_tick_time: Optional[datetime] = None
    
    # Cumulative day volume from live ticks
    day_volume: int = 0


class SignalData(BaseModel):
    """Output signal matching frontend contract"""
    rank: int = 0
    symbol: str
    time: str = "--:--"  # HH:MM format
    dir: str = "LONG"
    price: float = 0.0
    change_percent: float = 0.0
    
    # Volume metrics (ORB candle volume)
    volume: str = "0L"  # Formatted string
    volume_raw: int = 0
    volume_heat_percent: float = 0.0
    
    # Real-time day volume (cumulative)
    day_volume: str = "0L"  # Formatted string
    day_volume_raw: int = 0
    
    # Value metrics
    value: float = 0.0  # In Crores
    value_heat_percent: float = 0.0
    
    # Body metrics
    body: float = 0.0
    body_heat_percent: float = 0.0
    
    # ORB metrics
    orb_valid: bool = False
    orb_high: float = 0.0
    orb_low: float = 0.0
    
    # Continuation metrics
    speed_minutes: int = 0
    pullback_percent: float = 0.0
    decel_ok: bool = False
    decel_percent: float = 0.0
    
    # Scores
    ignition_score: float = 0.0
    continuation_score: float = 0.0
    quality_score: float = 0.0
    score: int = 0
    
    # State
    state: str = "IDLE"
    sparkline: List[float] = Field(default_factory=list)
    yesterday_close: float = 0.0
    last_updated: str = ""
    
    class Config:
        from_attributes = True


class TopSignalsResponse(BaseModel):
    """API response for top signals"""
    signals: List[SignalData]
    timestamp: str
    count: int


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str = "update"
    signals: List[SignalData] = Field(default_factory=list)
    timestamp: str = ""


class ConfigUpdateRequest(BaseModel):
    """Request for config update"""
    config: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    kite_connected: bool = False
    market_status: str = "closed"
    symbols_loaded: int = 0
    baselines_loaded: int = 0
    last_tick: Optional[str] = None
