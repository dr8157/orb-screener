"""
ORB Institutional Screener - Scoring Engine
File: scoring_engine.py
Calculates composite scores for all signal metrics
"""

import logging
import math
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from models import (
    SignalData, 
    SymbolState, 
    SymbolStateEnum, 
    BaselineMetrics, 
    ScreenerConfig,
    CandleData
)

logger = logging.getLogger(__name__)

# Indian timezone
IST = ZoneInfo("Asia/Kolkata")

# Market timing
ORB_END = dt_time(9, 20)


class ScoringEngine:
    """
    Calculates signal scores based on PRD specifications.
    
    Scoring Weights:
    - Volume Heat: 25%
    - Value Heat: 25%
    - Body Heat: 20%
    - Speed: 15%
    - Pullback: 10%
    - Deceleration: 5%
    """
    
    def __init__(self, config: Optional[ScreenerConfig] = None):
        """Initialize with configuration"""
        self.config = config or ScreenerConfig()
        self._signals_cache: Dict[str, SignalData] = {}
    
    def update_config(self, config: ScreenerConfig):
        """Update configuration"""
        self.config = config
    
    def _format_volume(self, volume: int) -> str:
        """Format volume for display (Lakhs/Crores)"""
        if volume >= 1e7:
            return f"{volume / 1e7:.2f}Cr"
        elif volume >= 1e5:
            return f"{volume / 1e5:.2f}L"
        elif volume >= 1e3:
            return f"{volume / 1e3:.2f}K"
        return str(volume)
    
    def _calculate_heat_percent(
        self, 
        current: float, 
        baseline: float
    ) -> float:
        """
        Calculate heat percentage.
        
        Formula: ((current / baseline) - 1) * 100
        """
        if baseline <= 0:
            return 0.0
        
        heat = ((current / baseline) - 1) * 100
        return heat
    
    def _normalize_heat(self, heat: float) -> float:
        """
        Normalize heat to 0-1 range for scoring.
        Caps at heat_max from config.
        """
        if heat <= 0:
            return 0.0
        
        # Cap at heat_max
        capped = min(heat, self.config.heat_max)
        
        # Normalize to 0-1
        return capped / self.config.heat_max
    
    def _calculate_speed_factor(self, speed_minutes: int) -> float:
        """
        Calculate speed score factor.
        
        Formula: exp(-speed_minutes / k)
        Faster breakout = higher score
        """
        if speed_minutes <= 0:
            return 1.0  # Instant breakout
        
        k = self.config.speed_decay_k  # Default 30 minutes
        factor = math.exp(-speed_minutes / k)
        
        return factor
    
    def _calculate_pullback_factor(self, pullback_percent: float) -> float:
        """
        Calculate pullback score factor.
        
        Formula: 1 - (pullback% / pb_max)
        Smaller pullback = higher score
        """
        if pullback_percent <= 0:
            return 1.0  # No pullback = perfect
        
        pb_max = self.config.pb_max  # Default 5%
        normalized = min(pullback_percent, pb_max) / pb_max
        
        return 1.0 - normalized
    
    def _calculate_decel_factor(self, decel_ok: bool) -> float:
        """
        Calculate deceleration factor.
        
        Returns 1.0 if volume is decelerating (good sign)
        Returns 0.0 if volume is accelerating (distribution)
        """
        return 1.0 if decel_ok else 0.0
    
    def calculate_signal(
        self,
        symbol: str,
        state: SymbolState,
        baseline: Optional[BaselineMetrics],
        current_candle: Optional[CandleData],
        orb_candle: Optional[CandleData]
    ) -> SignalData:
        """
        Calculate complete signal for a symbol.
        
        Args:
            symbol: Stock symbol
            state: Current symbol state
            baseline: Baseline metrics for comparison
            current_candle: Current 5m candle in progress
            orb_candle: First 5m candle (9:15-9:20)
            
        Returns:
            SignalData with all calculated metrics
        """
        now = datetime.now(IST)
        
        # Initialize signal
        signal = SignalData(
            symbol=symbol,
            state=state.state.value if state else "IDLE",
            last_updated=now.isoformat()
        )
        
        if not state:
            return signal
        
        # Basic price info
        signal.price = state.current_price
        signal.orb_high = state.orb_high
        signal.orb_low = state.orb_low
        
        # Calculate change percent - prefer Kite's dividend-adjusted value
        if state.change_percent != 0:
            # Use Kite's change % (dividend-adjusted, most accurate)
            signal.change_percent = round(state.change_percent, 2)
            signal.yesterday_close = state.prev_close
        elif baseline and baseline.yesterday_close > 0:
            # Fallback to baseline calculation
            change_pct = ((state.current_price - baseline.yesterday_close) / baseline.yesterday_close) * 100
            signal.change_percent = round(change_pct, 2)
            signal.yesterday_close = baseline.yesterday_close
        
        # Direction
        if state.current_price > state.orb_high:
            signal.dir = "LONG"
        elif state.current_price < state.orb_low:
            signal.dir = "SHORT"
        else:
            signal.dir = "LONG"  # Default
        
        # Time (breakout time or ORB formation time)
        if state.breakout_time:
            signal.time = state.breakout_time.strftime("%H:%M")
        elif state.orb_timestamp:
            # Use 9:20 as the signal time (ORB complete)
            signal.time = "09:20"
        
        # ORB validity
        signal.orb_valid = state.state in [
            SymbolStateEnum.ORB_BROKEN,
            SymbolStateEnum.ORB_TESTING
        ]
        
        # Determine which candle to use for Volume/Value/Body metrics
        # After ORB period (9:20 AM), use current candle for real-time updates
        # During ORB period or when current candle unavailable, use ORB candle
        current_time = now.time()
        is_after_orb = current_time >= ORB_END
        
        # For real-time metrics (Volume, Value, Body), prefer current candle after ORB
        if is_after_orb and current_candle and current_candle.volume > 0:
            metrics_candle = current_candle
        else:
            metrics_candle = orb_candle or current_candle
        
        if metrics_candle:
            # Volume metrics - use current 5m candle after ORB period
            signal.volume_raw = metrics_candle.volume
            signal.volume = self._format_volume(metrics_candle.volume)
            
            if baseline and baseline.avg_vol_5m > 0:
                signal.volume_heat_percent = round(
                    self._calculate_heat_percent(metrics_candle.volume, baseline.avg_vol_5m), 
                    1
                )
            
            # Value metrics - use current 5m candle after ORB period
            signal.value = round(metrics_candle.value, 2)
            
            if baseline and baseline.avg_value_5m > 0:
                signal.value_heat_percent = round(
                    self._calculate_heat_percent(metrics_candle.value, baseline.avg_value_5m),
                    1
                )
            
            # Body metrics - use current 5m candle after ORB period
            signal.body = round(metrics_candle.body, 2)
            
            if baseline and baseline.avg_body_5m > 0:
                signal.body_heat_percent = round(
                    self._calculate_heat_percent(metrics_candle.body, baseline.avg_body_5m),
                    1
                )
        
        # Real-time day volume (cumulative from live ticks)
        if state and state.day_volume > 0:
            signal.day_volume_raw = state.day_volume
            signal.day_volume = self._format_volume(state.day_volume)
        
        # Speed (already calculated in state machine)
        signal.speed_minutes = state.speed_minutes
        
        # Pullback
        signal.pullback_percent = round(state.pullback_percent, 2)
        
        # Deceleration - cap at reasonable range to avoid absurd values
        signal.decel_ok = state.decel_ok
        if state.prev_candle_volume > 100:  # Minimum volume to avoid tiny denominators
            decel_pct = ((state.curr_candle_volume - state.prev_candle_volume) / state.prev_candle_volume) * 100
            # Cap at ±999% to keep values readable
            decel_pct = max(-999, min(999, decel_pct))
            signal.decel_percent = round(decel_pct, 1)
        
        # Sparkline
        signal.sparkline = state.sparkline[-20:] if state.sparkline else []
        
        # Calculate composite score
        score, ignition, continuation, quality = self._calculate_composite_score(signal)
        
        signal.score = score
        signal.ignition_score = round(ignition, 1)
        signal.continuation_score = round(continuation, 1)
        signal.quality_score = round(quality, 1)
        
        return signal
    
    def _calculate_composite_score(
        self, 
        signal: SignalData
    ) -> Tuple[int, float, float, float]:
        """
        Calculate composite score from individual metrics.
        
        Returns: (total_score, ignition_score, continuation_score, quality_score)
        """
        # Normalize heat percentages
        vol_norm = self._normalize_heat(signal.volume_heat_percent)
        val_norm = self._normalize_heat(signal.value_heat_percent)
        body_norm = self._normalize_heat(signal.body_heat_percent)
        
        # Calculate factors
        speed_factor = self._calculate_speed_factor(signal.speed_minutes)
        pb_factor = self._calculate_pullback_factor(signal.pullback_percent)
        decel_factor = self._calculate_decel_factor(signal.decel_ok)
        
        # Ignition score (Volume + Value + Body) - 45 points max
        ignition = (
            vol_norm * self.config.weight_volume +
            val_norm * self.config.weight_value +
            body_norm * self.config.weight_body
        )
        ignition_points = ignition * 45 / (
            self.config.weight_volume + 
            self.config.weight_value + 
            self.config.weight_body
        )
        
        # Continuation score (Speed + Pullback + Decel) - 40 points max
        continuation = (
            speed_factor * self.config.weight_speed +
            pb_factor * self.config.weight_pullback +
            decel_factor * self.config.weight_decel
        )
        continuation_points = continuation * 40 / (
            self.config.weight_speed + 
            self.config.weight_pullback + 
            self.config.weight_decel
        )
        
        # Quality score (ORB validity, above PDH, etc.) - 15 points max
        quality = 0.0
        if signal.orb_valid:
            quality += 0.6  # 60% of quality for valid ORB break
        if signal.change_percent > 0:
            quality += 0.2  # 20% for positive change
        if signal.dir == "LONG":
            quality += 0.2  # 20% for long direction (bullish)
        quality_points = quality * 15
        
        # Total score (0-100)
        total = ignition_points + continuation_points + quality_points
        total_score = int(min(100, max(0, total)))
        
        return total_score, ignition_points, continuation_points, quality_points
    
    def get_top_signals(
        self,
        signals: Dict[str, SignalData],
        n: int = 10,
        min_score: int = 0
    ) -> List[SignalData]:
        """
        Get top N signals sorted by score.
        
        Args:
            signals: Dictionary of symbol -> SignalData
            n: Number of top signals to return
            min_score: Minimum score threshold
            
        Returns:
            List of top signals, ranked
        """
        # Apply all admin filters from config
        value_threshold = self.config.value_threshold
        volume_multiplier = self.config.volume_multiplier  # Volume heat must be >= (multiplier-1)*100%
        body_threshold = self.config.body_threshold  # Body heat must be >= (threshold-1)*100%
        
        # Convert multipliers to heat percentage thresholds
        # e.g., 5x multiplier means heat% must be >= 400% (5x baseline - 1 = 4 = 400%)
        min_volume_heat = (volume_multiplier - 1) * 100
        min_body_heat = (body_threshold - 1) * 100
        
        valid_signals = []
        for s in signals.values():
            # Basic filters always apply
            if s.score < min_score:
                continue
            if s.value < value_threshold:
                continue
            if s.state not in ["ORB_BROKEN", "ORB_TESTING", "ORB_FORMED", "IGNITION"]:
                continue
            
            # Heat filters only apply if baselines are loaded (heat > 0)
            # This ensures signals show while baselines are loading
            if s.volume_heat_percent > 0 and s.volume_heat_percent < min_volume_heat:
                continue
            if s.body_heat_percent > 0 and s.body_heat_percent < min_body_heat:
                continue
            
            valid_signals.append(s)
        
        # Sort by score descending, with volume_heat_percent and change_percent as tiebreakers
        # This ensures stocks with significant moves rank higher even with same score
        sorted_signals = sorted(
            valid_signals,
            key=lambda x: (x.score, x.volume_heat_percent, abs(x.change_percent)),
            reverse=True
        )
        
        # Take top N and assign ranks
        top_signals = sorted_signals[:n]
        for idx, signal in enumerate(top_signals):
            signal.rank = idx + 1
        
        return top_signals
    
    def recalculate_all(
        self,
        states: Dict[str, SymbolState],
        baselines: Dict[str, BaselineMetrics],
        current_candles: Dict[str, CandleData],
        orb_candles: Dict[str, CandleData]
    ) -> Dict[str, SignalData]:
        """
        Recalculate signals for all symbols.
        
        Args:
            states: All symbol states
            baselines: All baseline metrics
            current_candles: Current 5m candles
            orb_candles: ORB candles
            
        Returns:
            Dictionary of symbol -> SignalData
        """
        signals = {}
        
        for symbol, state in states.items():
            baseline = baselines.get(symbol)
            current_candle = current_candles.get(symbol)
            orb_candle = orb_candles.get(symbol)
            
            signal = self.calculate_signal(
                symbol=symbol,
                state=state,
                baseline=baseline,
                current_candle=current_candle,
                orb_candle=orb_candle
            )
            
            signals[symbol] = signal
        
        self._signals_cache = signals
        return signals
    
    @property
    def cached_signals(self) -> Dict[str, SignalData]:
        """Get cached signals"""
        return self._signals_cache
