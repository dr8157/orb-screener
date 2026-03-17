"""
ORB Institutional Screener - Baseline Engine
File: baseline_engine.py
Fetches and caches historical baseline data for 20-day comparisons
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from zoneinfo import ZoneInfo

from models import BaselineMetrics, ScreenerConfig

logger = logging.getLogger(__name__)

# Indian timezone
IST = ZoneInfo("Asia/Kolkata")


class BaselineEngine:
    """
    Manages historical baseline calculations for all symbols.
    Fetches 20-day 5-minute OHLCV data and computes averages.
    """
    
    def __init__(self, kite_instance):
        """
        Initialize with authenticated Kite instance.
        
        Args:
            kite_instance: Authenticated KiteConnect instance
        """
        self.kite = kite_instance
        self.baselines: Dict[str, BaselineMetrics] = {}
        self.config = ScreenerConfig()
        self._last_refresh: Optional[datetime] = None
        self._instrument_tokens: Dict[str, int] = {}
    
    def set_instrument_tokens(self, tokens: Dict[str, int]):
        """Set instrument token mapping for historical data fetch"""
        self._instrument_tokens = tokens
    
    def update_config(self, config: ScreenerConfig):
        """Update configuration"""
        self.config = config
    
    def get_baseline(self, symbol: str) -> Optional[BaselineMetrics]:
        """Get baseline metrics for a symbol"""
        return self.baselines.get(symbol)
    
    def get_all_baselines(self) -> Dict[str, BaselineMetrics]:
        """Get all baseline metrics"""
        return self.baselines
    
    def _get_trading_days(self, num_days: int) -> List[datetime]:
        """
        Get list of past trading days (excluding weekends).
        
        Args:
            num_days: Number of trading days to fetch
            
        Returns:
            List of datetime objects for trading days
        """
        trading_days = []
        current = datetime.now(IST).date()
        
        while len(trading_days) < num_days:
            current -= timedelta(days=1)
            # Skip weekends (Saturday=5, Sunday=6)
            if current.weekday() < 5:
                trading_days.append(current)
        
        return trading_days
    
    def _fetch_historical_candles(
        self, 
        symbol: str, 
        instrument_token: int,
        from_date: datetime,
        to_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical 5-minute candles for a symbol.
        
        Args:
            symbol: Stock symbol
            instrument_token: Kite instrument token
            from_date: Start date
            to_date: End date
            
        Returns:
            DataFrame with OHLCV data or None on error
        """
        try:
            data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval="5minute"
            )
            
            if not data:
                return None
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            
            # Make datetime timezone-aware if not already
            if df['date'].dt.tz is None:
                df['date'] = df['date'].dt.tz_localize(IST)
            
            return df
            
        except Exception as e:
            logger.warning(f"Failed to fetch historical data for {symbol}: {e}")
            return None
    
    def _extract_first_5m_candle(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """
        Extract the first 5-minute candle (9:15-9:20) from each day.
        
        Args:
            df: DataFrame with historical data
            
        Returns:
            Series with aggregated first 5m candle metrics
        """
        if df is None or df.empty:
            return None
        
        # Filter for 9:15 candles (first 5-minute candle of the day)
        df['time'] = df['date'].dt.time
        first_candle_time = pd.Timestamp("09:15:00").time()
        
        first_candles = df[df['time'] == first_candle_time]
        
        if first_candles.empty:
            return None
        
        return first_candles
    
    def calculate_baseline(self, symbol: str) -> Optional[BaselineMetrics]:
        """
        Calculate baseline metrics for a single symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            BaselineMetrics object or None on error
        """
        instrument_token = self._instrument_tokens.get(symbol)
        if not instrument_token:
            logger.warning(f"No instrument token for {symbol}")
            return None
        
        # Get date range for historical data
        num_days = self.config.baseline_days
        to_date = datetime.now(IST)
        from_date = to_date - timedelta(days=num_days + 10)  # Extra days for weekends
        
        # Fetch historical data
        df = self._fetch_historical_candles(symbol, instrument_token, from_date, to_date)
        
        if df is None or df.empty:
            return None
        
        # Use ALL 5-minute candles during market hours for baseline
        today = datetime.now(IST).date()
        market_open_time = pd.Timestamp("09:15:00").time()
        market_close_time = pd.Timestamp("15:30:00").time()
        
        df['time'] = df['date'].dt.time
        # Filter: market hours only, exclude today
        all_candles = df[
            (df['time'] >= market_open_time) & 
            (df['time'] <= market_close_time) &
            (df['date'].dt.date < today)
        ]
        
        if all_candles.empty:
            return None
        
        # Limit to last N trading days
        all_candles = all_candles.copy()
        all_candles['trading_date'] = all_candles['date'].dt.date
        unique_days = sorted(all_candles['trading_date'].unique())
        last_n_days = unique_days[-num_days:] if len(unique_days) > num_days else unique_days
        all_candles = all_candles[all_candles['trading_date'].isin(last_n_days)]
        
        # Calculate metrics across ALL 5-minute candles
        avg_vol = all_candles['volume'].mean()
        std_vol = all_candles['volume'].std() if len(all_candles) > 1 else 0
        
        # Calculate body size for each candle
        all_candles['body'] = abs(all_candles['close'] - all_candles['open'])
        avg_body = all_candles['body'].mean()
        
        # Calculate value (turnover) for each candle
        all_candles['value'] = (all_candles['volume'] * all_candles['close']) / 1e7
        avg_value = all_candles['value'].mean()
        
        # Get yesterday's close (3:25-3:30 PM candle close)
        yesterday_close = 0.0
        try:
            # Get the previous trading day's data
            today = datetime.now(IST).date()
            prev_day_data = df[df['date'].dt.date < today]
            
            if not prev_day_data.empty:
                # Get the last trading day
                last_trading_day = prev_day_data['date'].dt.date.max()
                last_day_candles = prev_day_data[prev_day_data['date'].dt.date == last_trading_day]
                
                if not last_day_candles.empty:
                    # Get the last candle of the day (around 3:25-3:30 PM)
                    yesterday_close = last_day_candles.iloc[-1]['close']
        except Exception as e:
            logger.debug(f"Error getting yesterday close for {symbol}: {e}")
        
        baseline = BaselineMetrics(
            symbol=symbol,
            avg_vol_5m=float(avg_vol) if pd.notna(avg_vol) else 0.0,
            std_vol_5m=float(std_vol) if pd.notna(std_vol) else 0.0,
            avg_value_5m=float(avg_value) if pd.notna(avg_value) else 0.0,
            avg_body_5m=float(avg_body) if pd.notna(avg_body) else 0.0,
            yesterday_close=float(yesterday_close),
            last_updated=datetime.now(IST)
        )
        
        return baseline
    
    def refresh_baselines(
        self, 
        symbols: List[str],
        progress_callback=None
    ) -> Dict[str, BaselineMetrics]:
        """
        Refresh baselines for all symbols.
        
        Args:
            symbols: List of symbols to process
            progress_callback: Optional callback(current, total, symbol)
            
        Returns:
            Dictionary of symbol -> BaselineMetrics
        """
        logger.info(f"Refreshing baselines for {len(symbols)} symbols...")
        
        total = len(symbols)
        success_count = 0
        
        for idx, symbol in enumerate(symbols):
            try:
                baseline = self.calculate_baseline(symbol)
                
                if baseline:
                    self.baselines[symbol] = baseline
                    success_count += 1
                
                if progress_callback:
                    progress_callback(idx + 1, total, symbol)
                    
            except Exception as e:
                logger.warning(f"Failed to calculate baseline for {symbol}: {e}")
                continue
        
        self._last_refresh = datetime.now(IST)
        logger.info(f"Baselines refreshed: {success_count}/{total} successful")
        
        return self.baselines
    
    def get_yesterday_close(self, symbol: str) -> float:
        """Get yesterday's close for a symbol"""
        baseline = self.baselines.get(symbol)
        if baseline:
            return baseline.yesterday_close
        return 0.0
    
    def is_stale(self, max_age_hours: int = 12) -> bool:
        """Check if baselines need refresh"""
        if self._last_refresh is None:
            return True
        
        age = datetime.now(IST) - self._last_refresh
        return age.total_seconds() > (max_age_hours * 3600)
    
    @property
    def last_refresh(self) -> Optional[datetime]:
        """Get last refresh timestamp"""
        return self._last_refresh
    
    @property
    def loaded_count(self) -> int:
        """Number of symbols with baselines loaded"""
        return len(self.baselines)
