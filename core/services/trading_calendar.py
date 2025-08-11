#!/usr/bin/env python3
"""
Trading calendar service for QuantDB core - provides accurate trading day determination
"""

import logging
import os
import pickle
from datetime import datetime, timedelta
from functools import lru_cache
from typing import List, Set

import akshare as ak
import pandas as pd

from ..utils.logger import logger


class TradingCalendar:
    """Trading calendar service that provides accurate trading day determination"""

    def __init__(self, cache_file: str = "data/trading_calendar_cache.pkl"):
        """
        Initialize trading calendar service

        Args:
            cache_file: Cache file path
        """
        self.cache_file = cache_file
        self._trading_dates: Set[str] = set()
        self._last_update = None
        self._load_or_fetch_calendar()

    def _load_or_fetch_calendar(self):
        """Load or fetch trading calendar"""
        # Try to load from cache
        if self._load_from_cache():
            logger.info("Successfully loaded trading calendar from cache")
            return

        # Cache doesn't exist or expired, fetch from AKShare
        logger.info("Fetching trading calendar from AKShare...")
        self._fetch_from_akshare()

    def _load_from_cache(self) -> bool:
        """Load trading calendar from cache file"""
        try:
            if not os.path.exists(self.cache_file):
                return False

            # Check if cache file is expired (older than 7 days)
            cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(self.cache_file))
            if cache_age > timedelta(days=7):
                logger.info("Trading calendar cache has expired, need to refresh")
                return False

            with open(self.cache_file, "rb") as f:
                cache_data = pickle.load(f)
                self._trading_dates = cache_data["trading_dates"]
                self._last_update = cache_data["last_update"]

            logger.info(f"Loaded {len(self._trading_dates)} trading days from cache")
            return True

        except Exception as e:
            logger.warning(f"Failed to load trading calendar cache: {e}")
            return False

    def _fetch_from_akshare(self):
        """Fetch trading calendar from AKShare"""
        try:
            # Get trading calendar
            trade_cal = ak.tool_trade_date_hist_sina()

            # Convert to date set
            trade_cal["trade_date"] = pd.to_datetime(trade_cal["trade_date"])
            self._trading_dates = set(trade_cal["trade_date"].dt.strftime("%Y%m%d"))
            self._last_update = datetime.now()

            logger.info(f"Fetched {len(self._trading_dates)} trading days from AKShare")

            # Save to cache
            self._save_to_cache()

        except Exception as e:
            logger.error(f"Failed to fetch trading calendar from AKShare: {e}")
            # If fetch fails, use simplified weekend judgment as fallback
            logger.warning("Using simplified weekend judgment as fallback")
            self._use_fallback_calendar()

    def _save_to_cache(self):
        """Save trading calendar to cache file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

            cache_data = {"trading_dates": self._trading_dates, "last_update": self._last_update}

            with open(self.cache_file, "wb") as f:
                pickle.dump(cache_data, f)

            logger.info(f"Trading calendar saved to cache: {self.cache_file}")

        except Exception as e:
            logger.warning(f"Failed to save trading calendar cache: {e}")

    def _use_fallback_calendar(self):
        """Use fallback simplified trading calendar (exclude weekends only)"""
        logger.warning(
            "Using fallback trading calendar: exclude weekends only, not considering holidays"
        )
        # We don't pre-generate dates here, but judge dynamically in is_trading_day
        self._trading_dates = set()  # Empty set indicates fallback mode

    def is_trading_day(self, date: str) -> bool:
        """
        Determine if the specified date is a trading day

        Args:
            date: Date string in format YYYYMMDD

        Returns:
            True if it's a trading day, False otherwise
        """
        # If we have complete trading calendar, query directly
        if self._trading_dates:
            return date in self._trading_dates

        # Fallback: exclude weekends only
        try:
            date_dt = datetime.strptime(date, "%Y%m%d")
            return date_dt.weekday() < 5  # Monday to Friday
        except ValueError:
            logger.error(f"Invalid date format: {date}")
            return False

    def get_trading_days(self, start_date: str, end_date: str) -> List[str]:
        """
        Get all trading days within the specified date range

        Args:
            start_date: Start date in format YYYYMMDD
            end_date: End date in format YYYYMMDD

        Returns:
            List of trading days
        """
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
            if self.is_trading_day(date_str):
                trading_days.append(date_str)
            current_dt += timedelta(days=1)

        return trading_days

    def refresh_calendar(self):
        """Force refresh trading calendar"""
        logger.info("Force refreshing trading calendar...")
        self._fetch_from_akshare()

    def get_calendar_info(self) -> dict:
        """Get trading calendar information"""
        return {
            "total_trading_days": len(self._trading_dates),
            "last_update": self._last_update,
            "cache_file": self.cache_file,
            "is_fallback_mode": len(self._trading_dates) == 0,
        }


# Global instance
_trading_calendar = None


def get_trading_calendar() -> TradingCalendar:
    """Get trading calendar instance (singleton pattern)"""
    global _trading_calendar
    if _trading_calendar is None:
        _trading_calendar = TradingCalendar()
    return _trading_calendar


# Convenience functions
def is_trading_day(date: str) -> bool:
    """Convenience function to determine if it's a trading day"""
    return get_trading_calendar().is_trading_day(date)


def get_trading_days(start_date: str, end_date: str) -> List[str]:
    """Convenience function to get trading days list"""
    return get_trading_calendar().get_trading_days(start_date, end_date)
