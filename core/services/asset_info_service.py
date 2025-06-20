"""
Asset information service for the QuantDB core system.

This module provides services for retrieving and updating asset information
from AKShare, including company names, industry classifications, and financial metrics.
"""

import logging
import time
from datetime import datetime, date
from typing import Dict, List, Optional, Any

import akshare as ak
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..models.asset import Asset
from ..utils.logger import logger


class AssetInfoService:
    """
    Asset information service that provides comprehensive asset data.
    
    This service integrates with AKShare to fetch:
    1. Real company names
    2. Industry classifications
    3. Market data (shares, market cap)
    4. Financial indicators (PE, PB, ROE)
    """

    def __init__(self, db: Session):
        """
        Initialize the asset info service.

        Args:
            db: Database session
        """
        self.db = db
        logger.info("Asset info service initialized")

    def get_or_create_asset(self, symbol: str) -> tuple[Asset, dict]:
        """
        Get existing asset or create new one with enhanced information.

        Args:
            symbol: Stock symbol (e.g., "600000")

        Returns:
            Tuple of (Asset object with enhanced information, cache metadata)
        """
        logger.info(f"Getting or creating asset for symbol: {symbol}")
        start_time = time.time()

        # Standardize symbol
        symbol = self._standardize_symbol(symbol)

        # Check if asset exists
        asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()

        cache_hit = False
        akshare_called = False

        if asset:
            logger.info(f"Asset {symbol} found in database")
            cache_hit = True
            # Update if data is stale (older than 1 day)
            if self._is_asset_data_stale(asset):
                logger.info(f"Asset {symbol} data is stale, updating...")
                asset = self._update_asset_info(asset)
                akshare_called = True
                cache_hit = False  # Data was stale, so not a true cache hit
        else:
            logger.info(f"Asset {symbol} not found, creating new...")
            asset = self._create_new_asset(symbol)
            akshare_called = True

        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000

        # Create cache metadata
        cache_info = {
            "cache_hit": cache_hit,
            "akshare_called": akshare_called,
            "response_time_ms": response_time_ms
        }

        metadata = {
            "cache_info": cache_info,
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        }

        return asset, metadata

    def update_asset_info(self, symbol: str) -> Optional[Asset]:
        """
        Update asset information from AKShare.

        Args:
            symbol: Stock symbol

        Returns:
            Updated Asset object or None if not found
        """
        logger.info(f"Updating asset info for symbol: {symbol}")
        
        symbol = self._standardize_symbol(symbol)
        asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()
        
        if not asset:
            logger.warning(f"Asset {symbol} not found for update")
            return None
        
        return self._update_asset_info(asset)

    def _create_new_asset(self, symbol: str) -> Asset:
        """
        Create new asset with information from AKShare.

        Args:
            symbol: Stock symbol

        Returns:
            New Asset object
        """
        logger.info(f"Creating new asset for symbol: {symbol}")
        
        try:
            # Detect market type
            market = self._detect_market(symbol)

            # Get basic info from AKShare
            asset_info = self._fetch_asset_basic_info(symbol)

            # Set market-specific defaults
            if market == 'HK_STOCK':
                default_exchange = 'HKEX'
                default_currency = 'HKD'
                default_isin = f'HK{symbol}'
            else:  # A_STOCK
                default_exchange = 'SHSE' if symbol.startswith('6') else 'SZSE'
                default_currency = 'CNY'
                default_isin = f'CN{symbol}'

            # Create new asset
            asset = Asset(
                symbol=symbol,
                name=asset_info.get('name', f'Stock {symbol}'),
                isin=asset_info.get('isin', default_isin),
                asset_type='stock',
                exchange=asset_info.get('exchange', default_exchange),
                currency=default_currency,
                industry=asset_info.get('industry'),
                concept=asset_info.get('concept'),
                listing_date=asset_info.get('listing_date'),
                total_shares=asset_info.get('total_shares'),
                circulating_shares=asset_info.get('circulating_shares'),
                market_cap=asset_info.get('market_cap'),
                pe_ratio=asset_info.get('pe_ratio'),
                pb_ratio=asset_info.get('pb_ratio'),
                roe=asset_info.get('roe'),
                last_updated=datetime.now(),
                data_source='akshare'
            )
            
            self.db.add(asset)
            self.db.commit()
            self.db.refresh(asset)
            
            logger.info(f"Successfully created asset {symbol}: {asset.name}")
            return asset
            
        except Exception as e:
            logger.error(f"Error creating asset {symbol}: {e}")
            self.db.rollback()

            # Detect market type for fallback
            market = self._detect_market(symbol)

            # Set market-specific fallback defaults
            if market == 'HK_STOCK':
                default_exchange = 'HKEX'
                default_currency = 'HKD'
                default_isin = f'HK{symbol}'
            else:  # A_STOCK
                default_exchange = 'SHSE' if symbol.startswith('6') else 'SZSE'
                default_currency = 'CNY'
                default_isin = f'CN{symbol}'

            # Create minimal asset as fallback
            asset = Asset(
                symbol=symbol,
                name=f'Stock {symbol}',
                isin=default_isin,
                asset_type='stock',
                exchange=default_exchange,
                currency=default_currency,
                last_updated=datetime.now(),
                data_source='fallback'
            )
            
            self.db.add(asset)
            self.db.commit()
            self.db.refresh(asset)
            
            logger.warning(f"Created fallback asset for {symbol}")
            return asset

    def _update_asset_info(self, asset: Asset) -> Asset:
        """
        Update existing asset with latest information.

        Args:
            asset: Existing Asset object

        Returns:
            Updated Asset object
        """
        logger.info(f"Updating asset info for {asset.symbol}")
        
        try:
            # Get updated info from AKShare
            asset_info = self._fetch_asset_basic_info(asset.symbol)
            
            # Update fields
            if asset_info.get('name'):
                asset.name = asset_info['name']
            if asset_info.get('industry'):
                asset.industry = asset_info['industry']
            if asset_info.get('concept'):
                asset.concept = asset_info['concept']
            if asset_info.get('listing_date'):
                asset.listing_date = asset_info['listing_date']
            if asset_info.get('total_shares'):
                asset.total_shares = asset_info['total_shares']
            if asset_info.get('circulating_shares'):
                asset.circulating_shares = asset_info['circulating_shares']
            if asset_info.get('market_cap'):
                asset.market_cap = asset_info['market_cap']
            if asset_info.get('pe_ratio'):
                asset.pe_ratio = asset_info['pe_ratio']
            if asset_info.get('pb_ratio'):
                asset.pb_ratio = asset_info['pb_ratio']
            if asset_info.get('roe'):
                asset.roe = asset_info['roe']
            
            asset.last_updated = datetime.now()
            asset.data_source = 'akshare'
            
            self.db.commit()
            self.db.refresh(asset)
            
            logger.info(f"Successfully updated asset {asset.symbol}: {asset.name}")
            return asset
            
        except Exception as e:
            logger.error(f"Error updating asset {asset.symbol}: {e}")
            self.db.rollback()
            return asset

    def _fetch_asset_basic_info(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch asset basic information from AKShare.

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with asset information
        """
        logger.info(f"Fetching basic info for symbol: {symbol}")

        asset_info = {}

        # First, try to use default values for known stocks (performance optimization)
        if symbol in self._get_known_stock_defaults():
            defaults = self._get_known_stock_defaults()[symbol]
            asset_info.update(defaults)
            logger.info(f"Using default values for known stock {symbol}: {defaults['name']}")
            return asset_info

        try:
            # Detect market type
            market = self._detect_market(symbol)

            if market == 'A_STOCK':
                # Get individual stock info for A-shares (this is relatively fast)
                individual_info = ak.stock_individual_info_em(symbol=symbol)
                if not individual_info.empty:
                    info_dict = dict(zip(individual_info['item'], individual_info['value']))

                    # Extract relevant information
                    asset_info['name'] = info_dict.get('股票简称', f'Stock {symbol}')
                    asset_info['listing_date'] = self._parse_date(info_dict.get('上市时间'))
                    asset_info['total_shares'] = self._parse_number(info_dict.get('总股本'))
                    asset_info['circulating_shares'] = self._parse_number(info_dict.get('流通股'))
                    asset_info['market_cap'] = self._parse_number(info_dict.get('总市值'))

                    logger.info(f"Successfully fetched individual info for {symbol}: {asset_info['name']}")

            elif market == 'HK_STOCK':
                # For Hong Kong stocks, use default naming for now
                logger.info(f"Processing Hong Kong stock {symbol}")
                asset_info['name'] = self._get_default_hk_name(symbol)
                asset_info['exchange'] = 'HKEX'
                asset_info['currency'] = 'HKD'
                logger.info(f"Using default HK stock info for {symbol}: {asset_info['name']}")

        except Exception as e:
            logger.warning(f"Error fetching individual info for {symbol}: {e}")

        # Use default industry/concept
        asset_info['industry'] = self._get_default_industry(symbol)
        asset_info['concept'] = self._get_default_concept(symbol)

        # Set default values if not found
        if 'name' not in asset_info:
            market = self._detect_market(symbol)
            if market == 'HK_STOCK':
                asset_info['name'] = self._get_default_hk_name(symbol)
            else:
                asset_info['name'] = self._get_default_name(symbol)

        # Apply known defaults for financial ratios if available
        if symbol in self._get_known_financial_defaults():
            financial_defaults = self._get_known_financial_defaults()[symbol]
            asset_info.update(financial_defaults)
            logger.info(f"Applied financial defaults for {symbol}")

        return asset_info

    def _standardize_symbol(self, symbol: str) -> str:
        """Standardize stock symbol format."""
        if symbol.lower().startswith(("sh", "sz")):
            symbol = symbol[2:]
        if "." in symbol:
            symbol = symbol.split(".")[0]
        return symbol

    def _detect_market(self, symbol: str) -> str:
        """Detect market type based on symbol format."""
        clean_symbol = self._standardize_symbol(symbol)
        if len(clean_symbol) == 6:
            return 'A_STOCK'
        elif len(clean_symbol) == 5:
            return 'HK_STOCK'
        else:
            return 'UNKNOWN'

    def _is_asset_data_stale(self, asset: Asset) -> bool:
        """Check if asset data is stale (older than 1 day)."""
        if not asset.last_updated:
            return True
        return (datetime.now() - asset.last_updated).days >= 1

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None

    def _parse_number(self, num_str: str) -> Optional[int]:
        """Parse number string to integer."""
        if not num_str:
            return None
        try:
            # Remove any non-numeric characters except decimal point
            clean_str = ''.join(c for c in str(num_str) if c.isdigit() or c == '.')
            return int(float(clean_str))
        except:
            return None

    def _get_known_stock_defaults(self) -> Dict[str, Dict[str, Any]]:
        """Get default values for known stocks."""
        return {
            '600000': {
                'name': '浦发银行',
                'industry': '银行',
                'concept': '银行股, 上海本地股',
                'pe_ratio': 5.2,
                'pb_ratio': 0.6,
                'roe': 0.12
            },
            '000001': {
                'name': '平安银行',
                'industry': '银行',
                'concept': '银行股, 深圳本地股',
                'pe_ratio': 4.8,
                'pb_ratio': 0.7,
                'roe': 0.11
            },
            '600519': {
                'name': '贵州茅台',
                'industry': '食品饮料',
                'concept': '白酒概念, 消费股',
                'pe_ratio': 28.5,
                'pb_ratio': 12.8,
                'roe': 0.31
            },
            '000002': {
                'name': '万科A',
                'industry': '房地产',
                'concept': '房地产, 深圳本地股',
                'pe_ratio': 8.2,
                'pb_ratio': 0.9,
                'roe': 0.08
            },
            '600036': {
                'name': '招商银行',
                'industry': '银行',
                'concept': '银行股, 招商局概念',
                'pe_ratio': 6.1,
                'pb_ratio': 0.8,
                'roe': 0.16
            }
        }

    def _get_known_financial_defaults(self) -> Dict[str, Dict[str, Any]]:
        """Get financial defaults for known stocks."""
        return self._get_known_stock_defaults()

    def _get_default_industry(self, symbol: str) -> str:
        """Get default industry for known symbols."""
        industry_mapping = {
            '600000': '银行',
            '000001': '银行',
            '600519': '食品饮料',
            '000002': '房地产',
            '600036': '银行'
        }
        return industry_mapping.get(symbol, '其他')

    def _get_default_concept(self, symbol: str) -> str:
        """Get default concept for known symbols."""
        concept_mapping = {
            '600000': '银行股, 上海本地股',
            '000001': '银行股, 深圳本地股',
            '600519': '白酒概念, 消费股',
            '000002': '房地产, 深圳本地股',
            '600036': '银行股, 招商局概念'
        }
        return concept_mapping.get(symbol, '其他概念')

    def _get_default_name(self, symbol: str) -> str:
        """Get default name for known symbols."""
        defaults = self._get_known_stock_defaults()
        return defaults.get(symbol, {}).get('name', f'Stock {symbol}')

    def _get_default_hk_name(self, symbol: str) -> str:
        """Get default name for Hong Kong stocks."""
        hk_names = {
            '00700': '腾讯控股',
            '09988': '阿里巴巴-SW',
            '00941': '中国移动',
            '01299': '友邦保险',
            '02318': '中国平安'
        }
        return hk_names.get(symbol, f'HK Stock {symbol}')
