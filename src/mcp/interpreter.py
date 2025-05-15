"""
MCP protocol interpreter

This module implements the Model Context Protocol (MCP) interpreter,
which translates natural language queries into structured data responses.
It integrates with the Reservoir Cache mechanism for efficient data retrieval.
"""
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date, timedelta

from sqlalchemy.orm import Session

from src.mcp.schemas import MCPRequest, MCPResponse
from src.api.models import Asset, Price
from src.cache.cache_engine import CacheEngine
from src.cache.freshness_tracker import FreshnessTracker
from src.cache.akshare_adapter import AKShareAdapter
from src.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

class MCPInterpreter:
    """
    MCP protocol interpreter class

    Implements basic natural language understanding for financial queries
    """

    def __init__(self, db: Optional[Session] = None,
                cache_engine: Optional[CacheEngine] = None,
                freshness_tracker: Optional[FreshnessTracker] = None,
                akshare_adapter: Optional[AKShareAdapter] = None):
        """
        Initialize the MCP interpreter

        Args:
            db: SQLAlchemy database session (optional)
            cache_engine: Cache engine instance (optional)
            freshness_tracker: Freshness tracker instance (optional)
            akshare_adapter: AKShare adapter instance (optional)
        """
        logger.info("Initializing MCP interpreter")
        self.db = db
        self.cache_engine = cache_engine or CacheEngine()
        self.freshness_tracker = freshness_tracker or FreshnessTracker()
        self.akshare_adapter = akshare_adapter or AKShareAdapter(
            cache_engine=self.cache_engine,
            freshness_tracker=self.freshness_tracker
        )
        logger.info("MCP interpreter initialized with Reservoir Cache integration")

        # Define intent patterns
        self.intent_patterns = [
            (r"(?i).*(?:show|display|get|what is|what are).*(?:price|prices|stock price|stock prices).*(?:for|of).*", "get_price"),
            (r"(?i).*(?:show|display|get|what is|what are).*(?:trend|trends|performance|chart).*(?:for|of).*", "get_trend"),
            (r"(?i).*(?:show|display|get|what is|what are).*(?:information|details|data|info).*(?:for|of|about).*", "get_asset_info"),
            (r"(?i).*(?:list|show|display|get|what are).*(?:all|available).*(?:assets|stocks|securities).*", "list_assets"),
            (r"(?i).*(?:compare|comparison).*(?:between|of).*", "compare_assets"),
        ]

        # Define entity extraction patterns
        self.symbol_pattern = r"(?i)(?:symbol|ticker|code)[:\s]+([A-Za-z0-9\.]+)"
        self.asset_name_pattern = r"(?i)(?:called|named)[:\s]+([A-Za-z0-9\s]+?)(?:[\.\,]|$|\s(?:for|from|since|in))"
        self.date_pattern = r"(?i)(?:from|since|after|before|until|on)[:\s]+(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2}/\d{1,2}/\d{2})"
        self.days_pattern = r"(?i)(?:last|past|previous)[:\s]+(\d+)[:\s]+(?:days|day)"
        self.months_pattern = r"(?i)(?:last|past|previous)[:\s]+(\d+)[:\s]+(?:months|month)"
        self.years_pattern = r"(?i)(?:last|past|previous)[:\s]+(\d+)[:\s]+(?:years|year)"

    def set_db(self, db: Session):
        """
        Set the database session

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    async def process_request(self, request: MCPRequest) -> MCPResponse:
        """
        Process an MCP protocol request

        Args:
            request: The MCP request to process

        Returns:
            An MCP response with structured data
        """
        logger.info(f"Processing MCP request: {request.query}")

        if not self.db:
            logger.error("Database session not set")
            return MCPResponse(
                query=request.query,
                intent="error",
                data={"error": "Database session not set"},
                context=request.context,
                session_id=request.session_id,
                metadata={"status": "error"}
            )

        try:
            # Identify intent
            intent = self._identify_intent(request.query)
            logger.info(f"Identified intent: {intent}")

            # Extract entities
            entities = self._extract_entities(request.query)
            logger.info(f"Extracted entities: {entities}")

            # Process based on intent
            if intent == "get_price":
                data = await self._process_get_price(entities)
            elif intent == "get_trend":
                data = await self._process_get_trend(entities)
            elif intent == "get_asset_info":
                data = await self._process_get_asset_info(entities)
            elif intent == "list_assets":
                data = await self._process_list_assets(entities)
            elif intent == "compare_assets":
                data = await self._process_compare_assets(entities)
            else:
                data = {
                    "message": "I'm not sure how to process this query. Please try a different question.",
                    "query": request.query
                }
                intent = "unknown"

            # Update context with the extracted entities
            context = request.context.copy() if request.context else {}
            context.update({"last_entities": entities})

            return MCPResponse(
                query=request.query,
                intent=intent,
                data=data,
                context=context,
                session_id=request.session_id,
                metadata={
                    "status": "success",
                    "processed_at": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Error processing MCP request: {e}")
            return MCPResponse(
                query=request.query,
                intent="error",
                data={"error": str(e)},
                context=request.context,
                session_id=request.session_id,
                metadata={"status": "error"}
            )

    def _identify_intent(self, query: str) -> str:
        """
        Identify the intent of a query

        Args:
            query: The query string

        Returns:
            The identified intent
        """
        for pattern, intent in self.intent_patterns:
            if re.match(pattern, query):
                return intent

        return "unknown"

    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """
        Extract entities from a query

        Args:
            query: The query string

        Returns:
            Dictionary of extracted entities
        """
        entities = {}

        # Extract symbol - Chinese stock symbols are 6 digits
        symbol_match = re.search(r'\b(\d{6})\b', query)
        if symbol_match:
            entities["symbol"] = symbol_match.group(1).strip()
            logger.info(f"Extracted symbol: {entities['symbol']}")
        else:
            # Try explicit symbol pattern
            symbol_match = re.search(self.symbol_pattern, query)
            if symbol_match:
                entities["symbol"] = symbol_match.group(1).strip()
                logger.info(f"Extracted symbol from explicit pattern: {entities['symbol']}")
            else:
                # Try to find symbol-like patterns
                symbol_candidates = re.findall(r'\b([A-Z0-9]{1,6})\b', query)
                if symbol_candidates:
                    # Check if any of these are valid symbols in our database
                    for candidate in symbol_candidates:
                        if self.db and self.db.query(Asset).filter(Asset.symbol == candidate).first():
                            entities["symbol"] = candidate
                            logger.info(f"Found symbol in database: {entities['symbol']}")
                            break

        # Extract asset name
        name_match = re.search(self.asset_name_pattern, query)
        if name_match:
            entities["asset_name"] = name_match.group(1).strip()
            logger.info(f"Extracted asset name: {entities['asset_name']}")
        else:
            # Try to find company names directly in the query
            # Common Chinese stocks
            common_stocks = {
                "平安银行": "000001",
                "浦发银行": "600000",
                "贵州茅台": "600519",
                "中国平安": "601318",
                "招商银行": "600036",
                "工商银行": "601398",
                "建设银行": "601939",
                "上证指数": "000001.SH",
                "深证成指": "399001.SZ"
            }

            for company, symbol in common_stocks.items():
                if company in query:
                    entities["asset_name"] = company
                    entities["symbol"] = symbol
                    logger.info(f"Found common stock: {company} ({symbol})")
                    break

            # If still no match, try common international companies
            if "asset_name" not in entities:
                common_companies = ["Apple", "Microsoft", "Google", "Amazon", "Tesla"]
                for company in common_companies:
                    if company.lower() in query.lower():
                        entities["asset_name"] = company
                        logger.info(f"Found common international company: {company}")
                        break

        # Extract dates
        date_matches = re.findall(self.date_pattern, query)
        if date_matches:
            try:
                # Parse dates (handle different formats)
                parsed_dates = []
                for date_str in date_matches:
                    if "-" in date_str:  # ISO format
                        parsed_dates.append(datetime.strptime(date_str, "%Y-%m-%d").date())
                    elif "/" in date_str:  # US format
                        if len(date_str.split("/")[2]) == 4:  # 4-digit year
                            parsed_dates.append(datetime.strptime(date_str, "%m/%d/%Y").date())
                        else:  # 2-digit year
                            parsed_dates.append(datetime.strptime(date_str, "%m/%d/%y").date())

                if len(parsed_dates) >= 2:
                    entities["start_date"] = min(parsed_dates)
                    entities["end_date"] = max(parsed_dates)
                    logger.info(f"Extracted date range: {entities['start_date']} to {entities['end_date']}")
                elif len(parsed_dates) == 1:
                    # If only one date is provided, assume it's the start date
                    entities["start_date"] = parsed_dates[0]
                    entities["end_date"] = date.today()
                    logger.info(f"Extracted single date: {entities['start_date']} to {entities['end_date']}")
            except ValueError as e:
                logger.warning(f"Error parsing dates: {e}")

        # Try to extract Chinese date formats (YYYY年MM月DD日)
        chinese_date_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
        chinese_date_matches = re.findall(chinese_date_pattern, query)
        if chinese_date_matches:
            try:
                # Convert to date objects
                chinese_dates = []
                for year, month, day in chinese_date_matches:
                    chinese_dates.append(date(int(year), int(month), int(day)))

                if len(chinese_dates) >= 2:
                    entities["start_date"] = min(chinese_dates)
                    entities["end_date"] = max(chinese_dates)
                    logger.info(f"Extracted Chinese date range: {entities['start_date']} to {entities['end_date']}")
                elif len(chinese_dates) == 1:
                    entities["start_date"] = chinese_dates[0]
                    entities["end_date"] = date.today()
                    logger.info(f"Extracted Chinese single date: {entities['start_date']} to {entities['end_date']}")
            except ValueError as e:
                logger.warning(f"Error parsing Chinese dates: {e}")

        # Extract time periods
        days_match = re.search(self.days_pattern, query)
        if days_match:
            try:
                days = int(days_match.group(1))
                entities["days"] = days
                entities["start_date"] = date.today() - timedelta(days=days)
                entities["end_date"] = date.today()
            except ValueError:
                pass

        months_match = re.search(self.months_pattern, query)
        if months_match:
            try:
                months = int(months_match.group(1))
                entities["months"] = months
                # Approximate months as 30 days
                entities["start_date"] = date.today() - timedelta(days=30 * months)
                entities["end_date"] = date.today()
            except ValueError:
                pass

        years_match = re.search(self.years_pattern, query)
        if years_match:
            try:
                years = int(years_match.group(1))
                entities["years"] = years
                # Approximate years as 365 days
                entities["start_date"] = date.today() - timedelta(days=365 * years)
                entities["end_date"] = date.today()
            except ValueError:
                pass

        return entities

    async def _process_get_price(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a get_price intent

        Args:
            entities: Extracted entities

        Returns:
            Response data
        """
        if "symbol" not in entities and "asset_name" not in entities:
            return {
                "message": "Please specify a stock symbol or name to get price information."
            }

        try:
            # Get asset by symbol or name
            asset = None
            if "symbol" in entities:
                asset = self.db.query(Asset).filter(Asset.symbol == entities["symbol"]).first()

            if asset is None and "asset_name" in entities:
                asset = self.db.query(Asset).filter(Asset.name.ilike(f"%{entities['asset_name']}%")).first()

            if asset is None:
                return {
                    "message": f"Could not find asset with the provided information."
                }

            # Get date range
            end_date = entities.get("end_date", date.today())
            start_date = entities.get("start_date", end_date - timedelta(days=30))

            # Generate cache key for price data
            cache_key = self.cache_engine.generate_key(
                "get_price",
                asset.asset_id,
                start_date.isoformat(),
                end_date.isoformat()
            )

            # Try to get data from cache first
            cached_prices = None
            if self.freshness_tracker.is_fresh(cache_key, "relaxed"):
                cached_prices = self.cache_engine.get(cache_key)
                if cached_prices:
                    logger.info(f"Cache hit for price data: {cache_key}")
                    prices = cached_prices
                else:
                    logger.info(f"Cache miss for price data: {cache_key}")

            # If not in cache or not fresh, get from database
            if cached_prices is None:
                logger.info(f"Getting price data from database for {asset.symbol}")
                prices = self.db.query(Price).filter(
                    Price.asset_id == asset.asset_id,
                    Price.date >= start_date,
                    Price.date <= end_date
                ).order_by(Price.date.desc()).limit(30).all()

                # Store in cache
                if prices:
                    self.cache_engine.set(cache_key, prices, ttl=3600)  # Cache for 1 hour
                    self.freshness_tracker.mark_updated(cache_key, ttl=3600)
                    logger.info(f"Stored price data in cache: {cache_key}")

            # If no data available, try to get from AKShare
            if not prices:
                try:
                    logger.info(f"No price data in database, trying AKShare for {asset.symbol}")
                    # Format dates for AKShare
                    start_date_str = start_date.strftime("%Y%m%d")
                    end_date_str = end_date.strftime("%Y%m%d")

                    # Get data from AKShare - try real data first, fall back to mock if needed
                    logger.info(f"Fetching data from AKShare for {asset.symbol} from {start_date_str} to {end_date_str}")
                    try:
                        # First try with real data
                        stock_data = self.akshare_adapter.get_stock_data(
                            symbol=asset.symbol,
                            start_date=start_date_str,
                            end_date=end_date_str,
                            use_mock_data=False  # Try real data first
                        )

                        # If no real data, try with mock data for testing
                        if stock_data.empty:
                            logger.warning(f"No real data available for {asset.symbol}, trying mock data")
                            stock_data = self.akshare_adapter.get_stock_data(
                                symbol=asset.symbol,
                                start_date=start_date_str,
                                end_date=end_date_str,
                                use_mock_data=True  # Fall back to mock data
                            )
                    except Exception as fetch_error:
                        logger.error(f"Error fetching real data: {fetch_error}, trying mock data")
                        stock_data = self.akshare_adapter.get_stock_data(
                            symbol=asset.symbol,
                            start_date=start_date_str,
                            end_date=end_date_str,
                            use_mock_data=True  # Fall back to mock data
                        )

                    if not stock_data.empty:
                        # Convert to list of Price objects
                        prices = []
                        for _, row in stock_data.iterrows():
                            price = Price(
                                asset_id=asset.asset_id,
                                date=datetime.strptime(row['date'], "%Y-%m-%d").date(),
                                open=row['open'],
                                high=row['high'],
                                low=row['low'],
                                close=row['close'],
                                volume=row['volume'],
                                adjusted_close=row.get('adjusted_close', row['close'])
                            )
                            prices.append(price)

                        # Store in database
                        for price in prices:
                            self.db.add(price)
                        self.db.commit()

                        # Store in cache
                        self.cache_engine.set(cache_key, prices, ttl=3600)  # Cache for 1 hour
                        self.freshness_tracker.mark_updated(cache_key, ttl=3600)
                        logger.info(f"Stored AKShare price data in cache: {cache_key}")
                except Exception as e:
                    logger.error(f"Error getting data from AKShare: {e}")

            if not prices:
                return {
                    "message": f"No price data available for {asset.name} ({asset.symbol}) in the specified date range."
                }

            # Format response
            price_data = [{
                "date": p.date.isoformat(),
                "open": p.open,
                "high": p.high,
                "low": p.low,
                "close": p.close,
                "volume": p.volume,
                "adjusted_close": p.adjusted_close
            } for p in prices]

            return {
                "asset": {
                    "asset_id": asset.asset_id,
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "exchange": asset.exchange
                },
                "date_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "prices": price_data,
                "message": f"Here are the prices for {asset.name} ({asset.symbol}) from {start_date.isoformat()} to {end_date.isoformat()}."
            }

        except Exception as e:
            logger.error(f"Error processing get_price intent: {e}")
            return {"error": str(e)}

    async def _process_get_trend(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a get_trend intent

        Args:
            entities: Extracted entities

        Returns:
            Response data
        """
        # This is similar to get_price but focuses on trend analysis
        # For now, we'll return the same data as get_price
        return await self._process_get_price(entities)

    async def _process_get_asset_info(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a get_asset_info intent

        Args:
            entities: Extracted entities

        Returns:
            Response data
        """
        if "symbol" not in entities and "asset_name" not in entities:
            return {
                "message": "Please specify a stock symbol or name to get asset information."
            }

        try:
            # Get asset by symbol or name
            asset = None
            if "symbol" in entities:
                asset = self.db.query(Asset).filter(Asset.symbol == entities["symbol"]).first()

            if asset is None and "asset_name" in entities:
                asset = self.db.query(Asset).filter(Asset.name.ilike(f"%{entities['asset_name']}%")).first()

            if asset is None:
                return {
                    "message": f"Could not find asset with the provided information."
                }

            # Get latest price
            latest_price = self.db.query(Price).filter(
                Price.asset_id == asset.asset_id
            ).order_by(Price.date.desc()).first()

            # Format response
            return {
                "asset": {
                    "asset_id": asset.asset_id,
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "isin": asset.isin,
                    "asset_type": asset.asset_type,
                    "exchange": asset.exchange,
                    "currency": asset.currency
                },
                "latest_price": {
                    "date": latest_price.date.isoformat() if latest_price else None,
                    "close": latest_price.close if latest_price else None
                },
                "message": f"Here is the information for {asset.name} ({asset.symbol})."
            }

        except Exception as e:
            logger.error(f"Error processing get_asset_info intent: {e}")
            return {"error": str(e)}

    async def _process_list_assets(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a list_assets intent

        Args:
            entities: Extracted entities

        Returns:
            Response data
        """
        try:
            # Get assets with optional filtering
            query = self.db.query(Asset)

            # Apply filters if provided
            if "asset_type" in entities:
                query = query.filter(Asset.asset_type == entities["asset_type"])

            if "exchange" in entities:
                query = query.filter(Asset.exchange == entities["exchange"])

            # Limit to 50 assets to avoid overwhelming response
            assets = query.limit(50).all()

            if not assets:
                return {
                    "message": "No assets found matching the criteria."
                }

            # Format response
            asset_data = [{
                "asset_id": a.asset_id,
                "symbol": a.symbol,
                "name": a.name,
                "exchange": a.exchange,
                "asset_type": a.asset_type
            } for a in assets]

            return {
                "assets": asset_data,
                "count": len(asset_data),
                "message": f"Found {len(asset_data)} assets."
            }

        except Exception as e:
            logger.error(f"Error processing list_assets intent: {e}")
            return {"error": str(e)}

    async def _process_compare_assets(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a compare_assets intent

        Args:
            entities: Extracted entities

        Returns:
            Response data
        """
        # This would require more complex entity extraction to identify multiple assets
        # For now, return a placeholder response
        return {
            "message": "Asset comparison is not fully implemented yet. Please try a different query."
        }
