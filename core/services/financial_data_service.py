"""
Financial data service for QuantDB.

This service provides financial summary and indicators data with intelligent caching:
- Daily cache for financial summary data
- Weekly cache for financial indicators
- Efficient data processing and storage
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..models.financial_data import FinancialSummary, FinancialIndicators, FinancialDataCache
from ..models.asset import Asset
from ..cache.akshare_adapter import AKShareAdapter
from ..utils.logger import logger


class FinancialDataService:
    """
    Service for managing financial data with intelligent caching.
    
    This service implements caching strategies optimized for financial data:
    - Financial summary: Daily cache (data updates quarterly)
    - Financial indicators: Weekly cache (data updates less frequently)
    - Automatic data processing and normalization
    """
    
    def __init__(self, db: Session, akshare_adapter: AKShareAdapter):
        """
        Initialize the financial data service.
        
        Args:
            db: Database session
            akshare_adapter: AKShare adapter for data retrieval
        """
        self.db = db
        self.akshare_adapter = akshare_adapter
        logger.info("Financial data service initialized")

    def get_financial_summary(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get financial summary data for a stock symbol.
        
        Args:
            symbol: Stock symbol
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            Dictionary with financial summary data
        """
        try:
            logger.info(f"Getting financial summary for {symbol}, force_refresh={force_refresh}")
            
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_data = self._get_cached_summary(symbol)
                if cached_data:
                    logger.info(f"Cache hit for financial summary {symbol}")
                    cached_data['cache_hit'] = True
                    return cached_data
            
            # Cache miss or force refresh - fetch from AKShare
            logger.info(f"Cache miss for financial summary {symbol}, fetching from AKShare")
            
            df = self.akshare_adapter.get_financial_summary(symbol)
            
            if df.empty:
                logger.warning(f"No financial summary data available for {symbol}")
                return {
                    'symbol': symbol,
                    'error': 'No financial summary data available',
                    'cache_hit': False,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Process and save data
            summary_data = self._process_financial_summary(symbol, df)
            summary_data['cache_hit'] = False
            
            # Update cache record
            FinancialDataCache.update_cache_record(symbol, 'summary', self.db)
            
            logger.info(f"Successfully retrieved financial summary for {symbol}")
            return summary_data
            
        except Exception as e:
            logger.error(f"Error getting financial summary for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'cache_hit': False,
                'timestamp': datetime.now().isoformat()
            }

    def get_financial_indicators(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get financial indicators data for a stock symbol.
        
        Args:
            symbol: Stock symbol
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            Dictionary with financial indicators data
        """
        try:
            logger.info(f"Getting financial indicators for {symbol}, force_refresh={force_refresh}")
            
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_data = self._get_cached_indicators(symbol)
                if cached_data:
                    logger.info(f"Cache hit for financial indicators {symbol}")
                    cached_data['cache_hit'] = True
                    return cached_data
            
            # Cache miss or force refresh - fetch from AKShare
            logger.info(f"Cache miss for financial indicators {symbol}, fetching from AKShare")
            
            df = self.akshare_adapter.get_financial_indicators(symbol)
            
            if df.empty:
                logger.warning(f"No financial indicators data available for {symbol}")
                return {
                    'symbol': symbol,
                    'error': 'No financial indicators data available',
                    'cache_hit': False,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Process and save data
            indicators_data = self._process_financial_indicators(symbol, df)
            indicators_data['cache_hit'] = False
            
            # Update cache record
            FinancialDataCache.update_cache_record(symbol, 'indicators', self.db)
            
            logger.info(f"Successfully retrieved financial indicators for {symbol}")
            return indicators_data
            
        except Exception as e:
            logger.error(f"Error getting financial indicators for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'cache_hit': False,
                'timestamp': datetime.now().isoformat()
            }

    def get_financial_data_batch(self, symbols: List[str], 
                                data_type: str = 'summary',
                                force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Get financial data for multiple stocks efficiently.
        
        Args:
            symbols: List of stock symbols
            data_type: 'summary' or 'indicators'
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            Dictionary mapping symbols to their financial data
        """
        try:
            logger.info(f"Getting batch financial {data_type} for {len(symbols)} symbols")
            
            result = {}
            
            for symbol in symbols:
                try:
                    if data_type == 'summary':
                        data = self.get_financial_summary(symbol, force_refresh)
                    else:
                        data = self.get_financial_indicators(symbol, force_refresh)
                    
                    result[symbol] = data
                    
                except Exception as e:
                    logger.error(f"Error processing symbol {symbol}: {e}")
                    result[symbol] = {
                        'symbol': symbol,
                        'error': str(e),
                        'cache_hit': False,
                        'timestamp': datetime.now().isoformat()
                    }
            
            logger.info(f"Successfully retrieved batch financial {data_type} for {len(result)} symbols")
            return result
            
        except Exception as e:
            logger.error(f"Error getting batch financial {data_type}: {e}")
            raise

    def _get_cached_summary(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached financial summary data."""
        try:
            # Check if cache is valid
            if not FinancialDataCache.is_cache_valid(symbol, 'summary', self.db):
                return None
            
            # Get latest summary data from database
            summaries = self.db.query(FinancialSummary).filter(
                FinancialSummary.symbol == symbol
            ).order_by(desc(FinancialSummary.report_period)).limit(8).all()
            
            if not summaries:
                return None
            
            # Convert to response format
            quarters = []
            for summary in summaries:
                quarter_data = {
                    'period': summary.report_period,
                    'report_type': summary.report_type,
                    'net_profit': summary.net_profit,
                    'total_revenue': summary.total_revenue,
                    'operating_cost': summary.operating_cost,
                    'gross_profit': summary.gross_profit,
                    'operating_profit': summary.operating_profit,
                    'total_assets': summary.total_assets,
                    'total_liabilities': summary.total_liabilities,
                    'shareholders_equity': summary.shareholders_equity,
                    'operating_cash_flow': summary.operating_cash_flow,
                    'roe': summary.roe,
                    'roa': summary.roa,
                    'gross_margin': summary.gross_margin,
                    'net_margin': summary.net_margin
                }
                quarters.append(quarter_data)
            
            return {
                'symbol': symbol,
                'data_type': 'financial_summary',
                'quarters': quarters,
                'count': len(quarters),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cached summary for {symbol}: {e}")
            return None

    def _get_cached_indicators(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached financial indicators data."""
        try:
            # Check if cache is valid
            if not FinancialDataCache.is_cache_valid(symbol, 'indicators', self.db):
                return None
            
            # Get latest indicators data from database
            indicators = self.db.query(FinancialIndicators).filter(
                FinancialIndicators.symbol == symbol
            ).order_by(desc(FinancialIndicators.report_period)).limit(4).all()
            
            if not indicators:
                return None
            
            # Convert to response format
            periods = []
            for indicator in indicators:
                period_data = {
                    'period': indicator.report_period,
                    'eps': indicator.eps,
                    'pe_ratio': indicator.pe_ratio,
                    'pb_ratio': indicator.pb_ratio,
                    'ps_ratio': indicator.ps_ratio,
                    'revenue_growth': indicator.revenue_growth,
                    'profit_growth': indicator.profit_growth,
                    'eps_growth': indicator.eps_growth,
                    'debt_to_equity': indicator.debt_to_equity,
                    'current_ratio': indicator.current_ratio,
                    'quick_ratio': indicator.quick_ratio,
                    'asset_turnover': indicator.asset_turnover,
                    'inventory_turnover': indicator.inventory_turnover,
                    'receivables_turnover': indicator.receivables_turnover
                }
                periods.append(period_data)
            
            return {
                'symbol': symbol,
                'data_type': 'financial_indicators',
                'periods': periods,
                'count': len(periods),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cached indicators for {symbol}: {e}")
            return None

    def _process_financial_summary(self, symbol: str, df) -> Dict[str, Any]:
        """Process financial summary data from AKShare."""
        try:
            # Get or create asset
            asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()
            asset_id = asset.asset_id if asset else None

            # Create FinancialSummary instances
            summaries = FinancialSummary.from_akshare_data(symbol, asset_id, df)

            # Save to database (replace existing data)
            self.db.query(FinancialSummary).filter(
                FinancialSummary.symbol == symbol
            ).delete()

            for summary in summaries:
                self.db.add(summary)

            self.db.commit()

            # Convert to response format
            quarters = []
            for summary in summaries:
                quarter_data = {
                    'period': summary.report_period,
                    'report_type': summary.report_type,
                    'net_profit': summary.net_profit,
                    'total_revenue': summary.total_revenue,
                    'operating_cost': summary.operating_cost,
                    'gross_profit': summary.gross_profit,
                    'operating_profit': summary.operating_profit,
                    'total_assets': summary.total_assets,
                    'total_liabilities': summary.total_liabilities,
                    'shareholders_equity': summary.shareholders_equity,
                    'operating_cash_flow': summary.operating_cash_flow,
                    'roe': summary.roe,
                    'roa': summary.roa,
                    'gross_margin': summary.gross_margin,
                    'net_margin': summary.net_margin
                }
                quarters.append(quarter_data)

            return {
                'symbol': symbol,
                'data_type': 'financial_summary',
                'quarters': quarters,
                'count': len(quarters),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error processing financial summary for {symbol}: {e}")
            raise

    def _process_financial_indicators(self, symbol: str, df) -> Dict[str, Any]:
        """Process financial indicators data from AKShare."""
        try:
            # Get or create asset
            asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()
            asset_id = asset.asset_id if asset else None

            # Process indicators data (simplified for now)
            # Note: The actual processing depends on the structure of the indicators DataFrame
            indicators_list = []

            if not df.empty:
                # For now, create a simple summary of the indicators
                # This would need to be customized based on actual data structure
                latest_data = {
                    'symbol': symbol,
                    'asset_id': asset_id,
                    'report_period': datetime.now().strftime('%Y%m%d'),
                    'raw_data': df.to_dict('records') if len(df) < 100 else df.head(50).to_dict('records')
                }

                indicator = FinancialIndicators(**latest_data)

                # Save to database (replace existing data)
                self.db.query(FinancialIndicators).filter(
                    FinancialIndicators.symbol == symbol
                ).delete()

                self.db.add(indicator)
                self.db.commit()

                indicators_list.append({
                    'period': indicator.report_period,
                    'eps': indicator.eps,
                    'pe_ratio': indicator.pe_ratio,
                    'pb_ratio': indicator.pb_ratio,
                    'ps_ratio': indicator.ps_ratio,
                    'revenue_growth': indicator.revenue_growth,
                    'profit_growth': indicator.profit_growth,
                    'eps_growth': indicator.eps_growth,
                    'debt_to_equity': indicator.debt_to_equity,
                    'current_ratio': indicator.current_ratio,
                    'quick_ratio': indicator.quick_ratio,
                    'asset_turnover': indicator.asset_turnover,
                    'inventory_turnover': indicator.inventory_turnover,
                    'receivables_turnover': indicator.receivables_turnover
                })

            return {
                'symbol': symbol,
                'data_type': 'financial_indicators',
                'periods': indicators_list,
                'count': len(indicators_list),
                'raw_data_shape': f"{df.shape[0]}x{df.shape[1]}" if not df.empty else "0x0",
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error processing financial indicators for {symbol}: {e}")
            raise
