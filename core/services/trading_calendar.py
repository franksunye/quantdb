#!/usr/bin/env python3
"""
Trading calendar service for QuantDB core - provides accurate trading day determination
Supports multiple markets: China A-shares and Hong Kong stocks
"""

import logging
import os
import pickle
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional, Set, Union
from enum import Enum

import akshare as ak
import pandas as pd
import pandas_market_calendars as mcal

from ..utils.logger import logger


class Market(Enum):
    """Supported markets"""
    CHINA_A = "china_a"  # China A-shares (Shanghai + Shenzhen)
    HONG_KONG = "hong_kong"  # Hong Kong Stock Exchange

    @classmethod
    def from_symbol(cls, symbol: str) -> 'Market':
        """Determine market from stock symbol"""
        # Clean up symbol
        symbol = symbol.upper().strip()

        # Check Hong Kong stocks first (5-digit codes)
        if len(symbol) == 5 and symbol.isdigit():  # 5-digit Hong Kong code
            return cls.HONG_KONG
        elif symbol.startswith(('HK.', 'HK')):  # Hong Kong with HK prefix
            return cls.HONG_KONG
        elif symbol.startswith(('0', '3')):  # Shenzhen A-shares
            return cls.CHINA_A
        elif symbol.startswith(('6')):  # Shanghai A-shares
            return cls.CHINA_A
        else:
            # Default to China A-shares for backward compatibility
            return cls.CHINA_A


class TradingCalendar:
    """Multi-market trading calendar service using pandas_market_calendars"""

    def __init__(self, cache_file: str = "data/trading_calendar_cache.pkl"):
        """
        Initialize multi-market trading calendar service

        Args:
            cache_file: Cache file path
        """
        self.cache_file = cache_file
        self._market_calendars: Dict[Market, any] = {}
        self._trading_dates: Dict[Market, Set[str]] = {}
        self._last_update: Dict[Market, datetime] = {}

        # Market calendar mappings
        self._calendar_codes = {
            Market.CHINA_A: 'XSHG',  # Use Shanghai as primary for A-shares
            Market.HONG_KONG: 'XHKG'  # Hong Kong Stock Exchange
        }

        self._initialize_calendars()

    def _initialize_calendars(self):
        """Initialize all market calendars"""
        # Try to load from cache first
        if self._load_from_cache():
            logger.info("Successfully loaded multi-market trading calendars from cache")
            return

        # Initialize pandas_market_calendars for each market
        logger.info("Initializing pandas_market_calendars for all markets...")
        self._fetch_all_calendars()

    def _load_from_cache(self) -> bool:
        """Load multi-market trading calendars from cache file"""
        try:
            if not os.path.exists(self.cache_file):
                return False

            # Check if cache file is expired (older than 7 days)
            cache_age = datetime.now() - datetime.fromtimestamp(
                os.path.getmtime(self.cache_file)
            )
            if cache_age > timedelta(days=7):
                logger.info("Multi-market trading calendar cache has expired, need to refresh")
                return False

            with open(self.cache_file, "rb") as f:
                cache_data = pickle.load(f)

                # Check if this is the old cache format (single market)
                if "version" not in cache_data:
                    logger.info("Found old cache format, will refresh with new multi-market format")
                    return False

                # Load new multi-market format
                trading_dates_data = cache_data.get("trading_dates", {})
                last_update_data = cache_data.get("last_update", {})

                # Convert string keys back to Market enum if needed
                self._trading_dates = {}
                self._last_update = {}

                for market_key, dates in trading_dates_data.items():
                    if isinstance(market_key, str):
                        # Convert string back to Market enum
                        for market in Market:
                            if market.value == market_key:
                                self._trading_dates[market] = dates
                                break
                    else:
                        # Already Market enum
                        self._trading_dates[market_key] = dates

                for market_key, update_time in last_update_data.items():
                    if isinstance(market_key, str):
                        # Convert string back to Market enum
                        for market in Market:
                            if market.value == market_key:
                                self._last_update[market] = update_time
                                break
                    else:
                        # Already Market enum
                        self._last_update[market_key] = update_time

            total_days = sum(len(dates) for dates in self._trading_dates.values())
            logger.info(f"Loaded {total_days} trading days across {len(self._trading_dates)} markets from cache")
            return len(self._trading_dates) > 0

        except Exception as e:
            logger.warning(f"Failed to load multi-market trading calendar cache: {e}")
            return False

    def _fetch_all_calendars(self):
        """Fetch trading calendars for all supported markets"""
        for market in Market:
            try:
                self._fetch_market_calendar(market)
            except Exception as e:
                logger.error(f"Failed to fetch {market.value} calendar: {e}")
                self._use_fallback_calendar(market)

        # Save to cache after fetching all markets
        self._save_to_cache()

    def _fetch_market_calendar(self, market: Market):
        """Fetch trading calendar for a specific market using pandas_market_calendars"""
        try:
            calendar_code = self._calendar_codes[market]
            cal = mcal.get_calendar(calendar_code)

            # Get trading days for the past 5 years and next 2 years
            start_date = datetime.now() - timedelta(days=5*365)
            end_date = datetime.now() + timedelta(days=2*365)

            schedule = cal.schedule(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )

            # Convert to date set in YYYYMMDD format
            trading_dates = set(schedule.index.strftime('%Y%m%d'))

            self._trading_dates[market] = trading_dates
            self._last_update[market] = datetime.now()

            logger.info(f"Fetched {len(trading_dates)} trading days for {market.value} from pandas_market_calendars")

        except Exception as e:
            logger.error(f"Failed to fetch {market.value} calendar from pandas_market_calendars: {e}")
            # Fallback to AKShare for China A-shares
            if market == Market.CHINA_A:
                self._fetch_china_a_from_akshare()
            else:
                raise e

    def _fetch_china_a_from_akshare(self):
        """Fallback: Fetch China A-shares calendar from AKShare"""
        try:
            logger.info("Falling back to AKShare for China A-shares calendar...")
            trade_cal = ak.tool_trade_date_hist_sina()

            # Convert to date set
            trade_cal["trade_date"] = pd.to_datetime(trade_cal["trade_date"])
            trading_dates = set(trade_cal["trade_date"].dt.strftime("%Y%m%d"))

            self._trading_dates[Market.CHINA_A] = trading_dates
            self._last_update[Market.CHINA_A] = datetime.now()

            logger.info(f"Fetched {len(trading_dates)} China A-shares trading days from AKShare")

        except Exception as e:
            logger.error(f"Failed to fetch China A-shares calendar from AKShare: {e}")
            self._use_fallback_calendar(Market.CHINA_A)

    def _save_to_cache(self):
        """Save multi-market trading calendars to cache file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

            # Convert Market enum keys to strings for serialization
            trading_dates_serializable = {
                market.value: dates for market, dates in self._trading_dates.items()
            }
            last_update_serializable = {
                market.value: update_time for market, update_time in self._last_update.items()
            }

            cache_data = {
                "trading_dates": trading_dates_serializable,
                "last_update": last_update_serializable,
                "version": "2.0_multi_market"  # Version marker for cache format
            }

            with open(self.cache_file, "wb") as f:
                pickle.dump(cache_data, f)

            total_days = sum(len(dates) for dates in self._trading_dates.values())
            logger.info(f"Multi-market trading calendars saved to cache: {self.cache_file} ({total_days} total days)")

        except Exception as e:
            logger.warning(f"Failed to save multi-market trading calendar cache: {e}")

    def _use_fallback_calendar(self, market: Market):
        """Use fallback simplified trading calendar for a specific market (exclude weekends only)"""
        logger.warning(
            f"Using fallback trading calendar for {market.value}: exclude weekends only, not considering holidays"
        )
        # Empty set indicates fallback mode for this market
        self._trading_dates[market] = set()
        self._last_update[market] = datetime.now()

    def is_trading_day(self, date: str, market: Optional[Market] = None, symbol: Optional[str] = None) -> bool:
        """
        Determine if the specified date is a trading day for the given market

        Args:
            date: Date string in format YYYYMMDD
            market: Market to check (optional, will be inferred from symbol if not provided)
            symbol: Stock symbol to infer market from (optional)

        Returns:
            True if it's a trading day, False otherwise
        """
        # Determine market if not provided
        if market is None:
            if symbol:
                market = Market.from_symbol(symbol)
            else:
                # Default to China A-shares for backward compatibility
                market = Market.CHINA_A

        # If we have complete trading calendar for this market, query directly
        if market in self._trading_dates and self._trading_dates[market]:
            return date in self._trading_dates[market]

        # Fallback: exclude weekends only
        try:
            date_dt = datetime.strptime(date, "%Y%m%d")
            return date_dt.weekday() < 5  # Monday to Friday
        except ValueError:
            logger.error(f"Invalid date format: {date}")
            return False

    def get_trading_days(self, start_date: str, end_date: str,
                        market: Optional[Market] = None, symbol: Optional[str] = None) -> List[str]:
        """
        Get all trading days within the specified date range for the given market

        Args:
            start_date: Start date in format YYYYMMDD
            end_date: End date in format YYYYMMDD
            market: Market to check (optional, will be inferred from symbol if not provided)
            symbol: Stock symbol to infer market from (optional)

        Returns:
            List of trading days
        """
        # Determine market if not provided
        if market is None:
            if symbol:
                market = Market.from_symbol(symbol)
            else:
                # Default to China A-shares for backward compatibility
                market = Market.CHINA_A

        try:
            start_dt = datetime.strptime(start_date, "%Y%m%d")
            end_dt = datetime.strptime(end_date, "%Y%m%d")
        except ValueError as e:
            logger.error(f"Invalid date format: {e}")
            return []

        trading_days = []
        current_dt = start_dt

        while current_dt <= end_dt:
            date_str = current_dt.strftime("%Y%m%d")
            if self.is_trading_day(date_str, market=market):
                trading_days.append(date_str)
            current_dt += timedelta(days=1)

        return trading_days

    def refresh_calendar(self, market: Optional[Market] = None):
        """Force refresh trading calendar for specific market or all markets"""
        if market:
            logger.info(f"Force refreshing {market.value} trading calendar...")
            self._fetch_market_calendar(market)
        else:
            logger.info("Force refreshing all trading calendars...")
            self._fetch_all_calendars()

    def get_calendar_info(self, market: Optional[Market] = None) -> dict:
        """Get trading calendar information for specific market or all markets"""
        if market:
            trading_dates = self._trading_dates.get(market, set())
            last_update = self._last_update.get(market)
            return {
                "market": market.value,
                "total_trading_days": len(trading_dates),
                "last_update": last_update,
                "cache_file": self.cache_file,
                "is_fallback_mode": len(trading_dates) == 0,
            }
        else:
            # Return info for all markets
            total_days = sum(len(dates) for dates in self._trading_dates.values())
            return {
                "markets": list(self._trading_dates.keys()),
                "total_trading_days": total_days,
                "last_update": dict(self._last_update),
                "cache_file": self.cache_file,
                "market_details": {
                    market.value: {
                        "trading_days": len(dates),
                        "is_fallback_mode": len(dates) == 0
                    }
                    for market, dates in self._trading_dates.items()
                }
            }

    def get_supported_markets(self) -> List[Market]:
        """Get list of supported markets"""
        return list(Market)

    def is_market_supported(self, market: Market) -> bool:
        """Check if a market is supported"""
        return market in self._calendar_codes


# Global instance
_trading_calendar = None


def get_trading_calendar() -> TradingCalendar:
    """Get trading calendar instance (singleton pattern)"""
    global _trading_calendar
    if _trading_calendar is None:
        _trading_calendar = TradingCalendar()
    return _trading_calendar


# Convenience functions for backward compatibility
def is_trading_day(date: str, market: Optional[Market] = None, symbol: Optional[str] = None) -> bool:
    """
    Convenience function to determine if it's a trading day

    Args:
        date: Date string in format YYYYMMDD
        market: Market to check (optional, defaults to China A-shares for backward compatibility)
        symbol: Stock symbol to infer market from (optional)

    Returns:
        True if it's a trading day, False otherwise
    """
    return get_trading_calendar().is_trading_day(date, market=market, symbol=symbol)


def get_trading_days(start_date: str, end_date: str,
                    market: Optional[Market] = None, symbol: Optional[str] = None) -> List[str]:
    """
    Convenience function to get trading days list

    Args:
        start_date: Start date in format YYYYMMDD
        end_date: End date in format YYYYMMDD
        market: Market to check (optional, defaults to China A-shares for backward compatibility)
        symbol: Stock symbol to infer market from (optional)

    Returns:
        List of trading days
    """
    return get_trading_calendar().get_trading_days(start_date, end_date, market=market, symbol=symbol)


# New convenience functions for multi-market support
def is_hk_trading_day(date: str) -> bool:
    """Convenience function to check if it's a Hong Kong trading day"""
    return is_trading_day(date, market=Market.HONG_KONG)


def get_hk_trading_days(start_date: str, end_date: str) -> List[str]:
    """Convenience function to get Hong Kong trading days list"""
    return get_trading_days(start_date, end_date, market=Market.HONG_KONG)


def is_china_a_trading_day(date: str) -> bool:
    """Convenience function to check if it's a China A-shares trading day"""
    return is_trading_day(date, market=Market.CHINA_A)


def get_china_a_trading_days(start_date: str, end_date: str) -> List[str]:
    """Convenience function to get China A-shares trading days list"""
    return get_trading_days(start_date, end_date, market=Market.CHINA_A)
