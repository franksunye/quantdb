"""
Asset information service for the QuantDB system.

This module provides services for retrieving and updating asset information
from AKShare, including company names, industry classifications, and financial metrics.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any

import akshare as ak
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.api.models import Asset
from src.logger_unified import get_logger

# Setup logger
logger = get_logger(__name__)


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

    def get_or_create_asset(self, symbol: str) -> Asset:
        """
        Get existing asset or create new one with enhanced information.

        Args:
            symbol: Stock symbol (e.g., "600000")

        Returns:
            Asset object with enhanced information
        """
        logger.info(f"Getting or creating asset for symbol: {symbol}")
        
        # Standardize symbol
        symbol = self._standardize_symbol(symbol)
        
        # Check if asset exists
        asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()
        
        if asset:
            logger.info(f"Asset {symbol} found in database")
            # Update if data is stale (older than 1 day)
            if self._is_asset_data_stale(asset):
                logger.info(f"Asset {symbol} data is stale, updating...")
                asset = self._update_asset_info(asset)
        else:
            logger.info(f"Asset {symbol} not found, creating new...")
            asset = self._create_new_asset(symbol)
        
        return asset

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
            # Get basic info from AKShare
            asset_info = self._fetch_asset_basic_info(symbol)
            
            # Create new asset
            asset = Asset(
                symbol=symbol,
                name=asset_info.get('name', f'Stock {symbol}'),
                isin=asset_info.get('isin', f'CN{symbol}'),
                asset_type='stock',
                exchange=asset_info.get('exchange', 'SHSE' if symbol.startswith('6') else 'SZSE'),
                currency='CNY',
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
            
            # Create minimal asset as fallback
            asset = Asset(
                symbol=symbol,
                name=f'Stock {symbol}',
                isin=f'CN{symbol}',
                asset_type='stock',
                exchange='SHSE' if symbol.startswith('6') else 'SZSE',
                currency='CNY',
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
        
        try:
            # Get individual stock info
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
            
        except Exception as e:
            logger.warning(f"Error fetching individual info for {symbol}: {e}")
        
        try:
            # Get real-time data for financial ratios
            realtime_data = ak.stock_zh_a_spot_em()
            if not realtime_data.empty:
                stock_data = realtime_data[realtime_data['代码'] == symbol]
                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    asset_info['pe_ratio'] = self._safe_float(row.get('市盈率-动态'))
                    asset_info['pb_ratio'] = self._safe_float(row.get('市净率'))
                    
                    logger.info(f"Successfully fetched realtime data for {symbol}")
            
        except Exception as e:
            logger.warning(f"Error fetching realtime data for {symbol}: {e}")
        
        # Set default values if not found
        if 'name' not in asset_info:
            asset_info['name'] = self._get_default_name(symbol)
        
        return asset_info

    def _get_default_name(self, symbol: str) -> str:
        """Get default name for known symbols."""
        known_names = {
            '600000': '浦发银行',
            '000001': '平安银行',
            '600519': '贵州茅台',
            '000002': '万科A',
            '600036': '招商银行'
        }
        return known_names.get(symbol, f'Stock {symbol}')

    def _standardize_symbol(self, symbol: str) -> str:
        """Standardize stock symbol format."""
        if symbol.lower().startswith(('sh', 'sz')):
            symbol = symbol[2:]
        if '.' in symbol:
            symbol = symbol.split('.')[0]
        return symbol.zfill(6)

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
            # Remove units like 万, 亿
            if '万' in str(num_str):
                return int(float(str(num_str).replace('万', '')) * 10000)
            elif '亿' in str(num_str):
                return int(float(str(num_str).replace('亿', '')) * 100000000)
            else:
                return int(float(str(num_str)))
        except:
            return None

    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float."""
        if value is None or value == '-':
            return None
        try:
            return float(value)
        except:
            return None
