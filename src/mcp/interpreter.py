"""
MCP protocol interpreter

This module implements the Model Context Protocol (MCP) interpreter,
which translates natural language queries into structured data responses.
It uses the simplified architecture for data retrieval.
"""
import re
import traceback
from typing import Dict, Any, Optional
from datetime import datetime, date, timedelta

from sqlalchemy.orm import Session

from src.mcp.schemas import MCPRequest, MCPResponse
from src.api.models import Asset, Price
from src.cache.akshare_adapter_simplified import AKShareAdapter
from src.enhanced_logger import setup_enhanced_logger, log_function
from src.api.errors import MCPProcessingException

# Setup enhanced logger
logger = setup_enhanced_logger(
    name=__name__,
    detailed=True
)

class MCPInterpreter:
    """
    MCP protocol interpreter class

    Implements basic natural language understanding for financial queries
    """

    def __init__(self, db: Optional[Session] = None,
                akshare_adapter: Optional[AKShareAdapter] = None):
        """
        Initialize the MCP interpreter

        Args:
            db: SQLAlchemy database session (optional)
            akshare_adapter: AKShare adapter instance (optional)
        """
        logger.info("Initializing MCP interpreter")
        self.db = db
        self.akshare_adapter = akshare_adapter or AKShareAdapter()
        logger.info("MCP interpreter initialized with simplified architecture")

        # Define intent patterns
        self.intent_patterns = [
            # Price queries
            (r"(?i).*(?:show|display|get|what is|what are|查询|显示|获取).*(?:price|prices|stock price|stock prices|股价|价格|行情|报价).*(?:for|of|对于|关于|for the stock|of the stock|for the company|of the company|for the security|of the security).*", "get_price"),
            (r"(?i).*(?:how much|价格是多少|多少钱).*(?:stock|share|shares|股票|股份).*(?:cost|worth|value|值|值多少).*", "get_price"),
            (r"(?i).*(?:price|价格).*(?:of|for|对于|关于).*(?:stock|share|shares|股票|股份).*", "get_price"),

            # Trend queries
            (r"(?i).*(?:show|display|get|what is|what are|查询|显示|获取).*(?:trend|trends|performance|chart|走势|趋势|表现|图表).*(?:for|of|对于|关于).*", "get_trend"),
            (r"(?i).*(?:how has|how is|how was|如何|怎么样).*(?:performing|done|trending|表现|走势).*", "get_trend"),
            (r"(?i).*(?:trend|performance|chart|走势|趋势|表现|图表).*(?:of|for|对于|关于).*(?:stock|share|shares|股票|股份).*", "get_trend"),

            # Asset information queries
            (r"(?i).*(?:show|display|get|what is|what are|tell me about|查询|显示|获取|告诉我关于).*(?:information|details|data|info|资料|信息|详情|数据).*(?:for|of|about|on|对于|关于).*", "get_asset_info"),
            (r"(?i).*(?:who is|what is|what does|什么是|谁是).*(?:company|stock|security|公司|股票).*", "get_asset_info"),
            (r"(?i).*(?:information|details|data|info|资料|信息|详情|数据).*(?:of|for|about|on|对于|关于).*(?:stock|share|shares|company|security|股票|股份|公司).*", "get_asset_info"),

            # List assets queries
            (r"(?i).*(?:list|show|display|get|what are|列出|显示|获取|有哪些).*(?:all|available|所有|可用的).*(?:assets|stocks|securities|资产|股票|证券).*", "list_assets"),
            (r"(?i).*(?:what stocks|which stocks|what securities|which securities|哪些股票|什么股票).*(?:are available|can I|do you have|可用|有哪些).*", "list_assets"),
            (r"(?i).*(?:show me|give me|list|列出|给我).*(?:stocks|securities|assets|股票|证券|资产).*", "list_assets"),

            # Compare assets queries
            (r"(?i).*(?:compare|comparison|contrast|versus|vs|对比|比较).*(?:between|of|among|amongst|之间|的).*", "compare_assets"),
            (r"(?i).*(?:how does|which is better|which performs better|哪个更好|哪个表现更好).*(?:compare|compared|比较).*(?:to|with|和|与).*", "compare_assets"),
            (r"(?i).*(?:difference|similarities|区别|相似之处).*(?:between|among|amongst|之间).*", "compare_assets"),

            # Market summary queries (new intent)
            (r"(?i).*(?:market|markets|市场).*(?:summary|overview|status|condition|概况|概述|状态|状况).*", "market_summary"),
            (r"(?i).*(?:how is|what is|how are|what are|如何|怎么样).*(?:market|markets|市场).*(?:doing|performing|today|now|现在|今天).*", "market_summary"),

            # Historical data queries (new intent)
            (r"(?i).*(?:historical|history|past|previous|历史|过去|以前).*(?:data|prices|performance|数据|价格|表现).*", "get_historical_data"),
            (r"(?i).*(?:how was|what was|how did|what did|怎么样|如何).*(?:perform|price|trend|表现|价格|趋势).*(?:in the past|historically|before|过去|以前).*", "get_historical_data"),
        ]

        # Define entity extraction patterns
        # Symbol patterns
        self.symbol_pattern = r"(?i)(?:symbol|ticker|code|代码|股票代码)[:\s]+([A-Za-z0-9\.]+)"
        self.chinese_symbol_pattern = r"(?i)(?:代码|股票代码|编号)[:\s]*(\d{6})"

        # Asset name patterns
        self.asset_name_pattern = r"(?i)(?:called|named|名称|名字|名为)[:\s]+([A-Za-z0-9\s\u4e00-\u9fff]+?)(?:[\.\,]|$|\s(?:for|from|since|in|的|从|自从|在))"
        self.company_pattern = r"(?i)(?:company|corporation|enterprise|公司|企业)[:\s]+([A-Za-z0-9\s\u4e00-\u9fff]+?)(?:[\.\,]|$|\s(?:for|from|since|in|的|从|自从|在))"

        # Date patterns
        self.date_pattern = r"(?i)(?:from|since|after|before|until|on|从|自从|之后|之前|直到|在)[:\s]+(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2}/\d{1,2}/\d{2})"
        self.chinese_date_pattern = r"(\d{4})年(\d{1,2})月(\d{1,2})日"
        self.iso_date_pattern = r"\b(\d{4}-\d{2}-\d{2})\b"

        # Time period patterns
        self.days_pattern = r"(?i)(?:last|past|previous|最近|过去|前)[:\s]+(\d+)[:\s]*(?:days|day|天)"
        self.months_pattern = r"(?i)(?:last|past|previous|最近|过去|前)[:\s]+(\d+)[:\s]*(?:months|month|个月|月)"
        self.years_pattern = r"(?i)(?:last|past|previous|最近|过去|前)[:\s]+(\d+)[:\s]*(?:years|year|年)"
        self.weeks_pattern = r"(?i)(?:last|past|previous|最近|过去|前)[:\s]+(\d+)[:\s]*(?:weeks|week|周|星期)"
        self.quarters_pattern = r"(?i)(?:last|past|previous|最近|过去|前)[:\s]+(\d+)[:\s]*(?:quarters|quarter|季度|季)"

        # Market patterns
        self.market_pattern = r"(?i)(?:market|exchange|index|市场|交易所|指数)[:\s]+([A-Za-z0-9\s\u4e00-\u9fff]+?)(?:[\.\,]|$|\s(?:for|from|since|in|的|从|自从|在))"
        self.index_pattern = r"(?i)(?:index|指数|指标)[:\s]+([A-Za-z0-9\s\u4e00-\u9fff]+?)(?:[\.\,]|$|\s(?:for|from|since|in|的|从|自从|在))"

        # Comparison patterns
        self.comparison_pattern = r"(?i)(?:compare|comparison|contrast|versus|vs|对比|比较)[:\s]+([A-Za-z0-9\s\u4e00-\u9fff]+?)[:\s]+(?:and|with|to|versus|vs|和|与)[:\s]+([A-Za-z0-9\s\u4e00-\u9fff]+?)(?:[\.\,]|$)"

    def set_db(self, db: Session):
        """
        Set the database session

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    @log_function(level='info')
    async def process_request(self, request: MCPRequest) -> MCPResponse:
        """
        Process an MCP protocol request

        Args:
            request: The MCP request to process

        Returns:
            An MCP response with structured data
        """
        # Start a new context for this request
        logger.start_context(metadata={
            "session_id": request.session_id,
            "query": request.query
        })

        logger.info(f"Processing MCP request: {request.query}")
        logger.log_data("request", request.model_dump())

        if not self.db:
            error_msg = "Database session not set"
            logger.error(error_msg)
            logger.end_context()
            raise MCPProcessingException(message=error_msg, details={
                "query": request.query,
                "session_id": request.session_id
            })

        try:
            # Identify intent
            start_time = datetime.now()
            intent = self._identify_intent(request.query)
            intent_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"Identified intent: {intent} (took {intent_time:.4f}s)")
            logger.add_metric("intent_identification_time", intent_time)

            # Extract entities
            start_time = datetime.now()
            entities = self._extract_entities(request.query)
            entity_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"Extracted entities: {entities} (took {entity_time:.4f}s)")
            logger.log_data("entities", entities)
            logger.add_metric("entity_extraction_time", entity_time)

            # Process intent
            data = {}
            start_time = datetime.now()

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
            elif intent == "market_summary":
                data = await self._process_market_summary(entities)
            elif intent == "get_historical_data":
                data = await self._process_historical_data(entities)
            else:
                data = {
                    "message": "I'm not sure how to process this query. Please try a different question.",
                    "query": request.query
                }
                intent = "unknown"

            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Processed intent {intent} (took {processing_time:.4f}s)")
            logger.add_metric("intent_processing_time", processing_time)
            logger.log_data("result_data", data)

            # Update context with the extracted entities
            context = request.context.copy() if request.context else {}
            context.update({"last_entities": entities})

            # Create response
            response = MCPResponse(
                query=request.query,
                intent=intent,
                data=data,
                context=context,
                session_id=request.session_id,
                metadata={
                    "status": "success",
                    "processed_at": datetime.now().isoformat(),
                    "processing_metrics": {
                        "intent_identification_time": intent_time,
                        "entity_extraction_time": entity_time,
                        "intent_processing_time": processing_time,
                        "total_time": intent_time + entity_time + processing_time
                    }
                }
            )

            logger.info(f"MCP request processed successfully: {request.query}")
            logger.end_context()
            return response

        except Exception as e:
            # Get traceback
            tb = traceback.format_exc()

            # Log detailed error
            logger.error(f"Error processing MCP request: {type(e).__name__}: {str(e)}")
            logger.error(f"Traceback: {tb}")
            logger.log_data("error_details", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "query": request.query,
                "session_id": request.session_id
            })

            # End context
            logger.end_context()

            # Wrap in MCPProcessingException if it's not already a QuantDBException
            if not isinstance(e, MCPProcessingException):
                raise MCPProcessingException(
                    message=f"Error processing MCP request: {str(e)}",
                    details={
                        "query": request.query,
                        "error_type": type(e).__name__,
                        "session_id": request.session_id
                    }
                ) from e

            # Re-raise the original exception
            raise

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

        # Extract symbol using multiple patterns
        # 1. Chinese stock symbols (6 digits)
        symbol_match = re.search(r'\b(\d{6})\b', query)
        if symbol_match:
            entities["symbol"] = symbol_match.group(1).strip()
            logger.info(f"Extracted Chinese stock symbol: {entities['symbol']}")

        # 2. Explicit symbol pattern
        if "symbol" not in entities:
            symbol_match = re.search(self.symbol_pattern, query)
            if symbol_match:
                entities["symbol"] = symbol_match.group(1).strip()
                logger.info(f"Extracted symbol from explicit pattern: {entities['symbol']}")

        # 3. Chinese symbol pattern
        if "symbol" not in entities:
            symbol_match = re.search(self.chinese_symbol_pattern, query)
            if symbol_match:
                entities["symbol"] = symbol_match.group(1).strip()
                logger.info(f"Extracted symbol from Chinese pattern: {entities['symbol']}")

        # 4. Symbol-like patterns in database
        if "symbol" not in entities:
            # Try to find symbol-like patterns
            symbol_candidates = re.findall(r'\b([A-Z0-9]{1,6})\b', query)
            if symbol_candidates:
                # Check if any of these are valid symbols in our database
                for candidate in symbol_candidates:
                    if self.db and self.db.query(Asset).filter(Asset.symbol == candidate).first():
                        entities["symbol"] = candidate
                        logger.info(f"Found symbol in database: {entities['symbol']}")
                        break

        # Extract asset name using multiple patterns
        # 1. Asset name pattern
        name_match = re.search(self.asset_name_pattern, query)
        if name_match:
            entities["asset_name"] = name_match.group(1).strip()
            logger.info(f"Extracted asset name: {entities['asset_name']}")

        # 2. Company pattern
        if "asset_name" not in entities:
            company_match = re.search(self.company_pattern, query)
            if company_match:
                entities["asset_name"] = company_match.group(1).strip()
                logger.info(f"Extracted company name: {entities['asset_name']}")

        # 3. Common stock names
        if "asset_name" not in entities:
            # Common Chinese stocks with their symbols
            common_stocks = {
                "平安银行": "000001",
                "浦发银行": "600000",
                "贵州茅台": "600519",
                "中国平安": "601318",
                "招商银行": "600036",
                "工商银行": "601398",
                "建设银行": "601939",
                "上证指数": "000001.SH",
                "深证成指": "399001.SZ",
                "创业板指": "399006",
                "科创50": "000688",
                "中证500": "000905",
                "沪深300": "000300"
            }

            for company, symbol in common_stocks.items():
                if company in query:
                    entities["asset_name"] = company
                    entities["symbol"] = symbol
                    logger.info(f"Found common Chinese stock: {company} ({symbol})")
                    break

        # 4. Common international companies
        if "asset_name" not in entities:
            common_companies = {
                "Apple": "AAPL",
                "Microsoft": "MSFT",
                "Google": "GOOGL",
                "Alphabet": "GOOGL",
                "Amazon": "AMZN",
                "Tesla": "TSLA",
                "Facebook": "META",
                "Meta": "META",
                "Netflix": "NFLX",
                "Nvidia": "NVDA",
                "Intel": "INTC",
                "IBM": "IBM",
                "Oracle": "ORCL",
                "Cisco": "CSCO",
                "Adobe": "ADBE"
            }

            for company, symbol in common_companies.items():
                if company.lower() in query.lower():
                    entities["asset_name"] = company
                    entities["symbol"] = symbol
                    logger.info(f"Found common international company: {company} ({symbol})")
                    break

        # Extract dates using multiple patterns
        # 1. Standard date pattern
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

        # 2. Chinese date format (YYYY年MM月DD日)
        if "start_date" not in entities:
            chinese_date_matches = re.findall(self.chinese_date_pattern, query)
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

        # 3. ISO date format (YYYY-MM-DD)
        if "start_date" not in entities:
            iso_date_matches = re.findall(self.iso_date_pattern, query)
            if iso_date_matches:
                try:
                    # Convert to date objects
                    iso_dates = [datetime.strptime(date_str, "%Y-%m-%d").date() for date_str in iso_date_matches]

                    if len(iso_dates) >= 2:
                        entities["start_date"] = min(iso_dates)
                        entities["end_date"] = max(iso_dates)
                        logger.info(f"Extracted ISO date range: {entities['start_date']} to {entities['end_date']}")
                    elif len(iso_dates) == 1:
                        entities["start_date"] = iso_dates[0]
                        entities["end_date"] = date.today()
                        logger.info(f"Extracted ISO single date: {entities['start_date']} to {entities['end_date']}")
                except ValueError as e:
                    logger.warning(f"Error parsing ISO dates: {e}")

        # Extract time periods
        # 1. Days
        days_match = re.search(self.days_pattern, query)
        if days_match and "start_date" not in entities:
            try:
                days = int(days_match.group(1))
                entities["days"] = days
                entities["start_date"] = date.today() - timedelta(days=days)
                entities["end_date"] = date.today()
                logger.info(f"Extracted time period: {days} days")
            except ValueError as e:
                logger.warning(f"Error parsing days: {e}")

        # 2. Weeks
        weeks_match = re.search(self.weeks_pattern, query)
        if weeks_match and "start_date" not in entities:
            try:
                weeks = int(weeks_match.group(1))
                entities["weeks"] = weeks
                entities["start_date"] = date.today() - timedelta(days=7 * weeks)
                entities["end_date"] = date.today()
                logger.info(f"Extracted time period: {weeks} weeks")
            except ValueError as e:
                logger.warning(f"Error parsing weeks: {e}")

        # 3. Months
        months_match = re.search(self.months_pattern, query)
        if months_match and "start_date" not in entities:
            try:
                months = int(months_match.group(1))
                entities["months"] = months
                # Approximate months as 30 days
                entities["start_date"] = date.today() - timedelta(days=30 * months)
                entities["end_date"] = date.today()
                logger.info(f"Extracted time period: {months} months")
            except ValueError as e:
                logger.warning(f"Error parsing months: {e}")

        # 4. Quarters
        quarters_match = re.search(self.quarters_pattern, query)
        if quarters_match and "start_date" not in entities:
            try:
                quarters = int(quarters_match.group(1))
                entities["quarters"] = quarters
                # Approximate quarters as 90 days
                entities["start_date"] = date.today() - timedelta(days=90 * quarters)
                entities["end_date"] = date.today()
                logger.info(f"Extracted time period: {quarters} quarters")
            except ValueError as e:
                logger.warning(f"Error parsing quarters: {e}")

        # 5. Years
        years_match = re.search(self.years_pattern, query)
        if years_match and "start_date" not in entities:
            try:
                years = int(years_match.group(1))
                entities["years"] = years
                # Approximate years as 365 days
                entities["start_date"] = date.today() - timedelta(days=365 * years)
                entities["end_date"] = date.today()
                logger.info(f"Extracted time period: {years} years")
            except ValueError as e:
                logger.warning(f"Error parsing years: {e}")

        # Extract market and index information
        market_match = re.search(self.market_pattern, query)
        if market_match:
            entities["market"] = market_match.group(1).strip()
            logger.info(f"Extracted market: {entities['market']}")

        index_match = re.search(self.index_pattern, query)
        if index_match:
            entities["index"] = index_match.group(1).strip()
            logger.info(f"Extracted index: {entities['index']}")

        # Extract comparison entities
        comparison_match = re.search(self.comparison_pattern, query)
        if comparison_match:
            entities["comparison"] = {
                "asset1": comparison_match.group(1).strip(),
                "asset2": comparison_match.group(2).strip()
            }
            logger.info(f"Extracted comparison: {entities['comparison']['asset1']} vs {entities['comparison']['asset2']}")

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

            # Get data from database
            logger.info(f"Getting price data from database for {asset.symbol}")
            prices = self.db.query(Price).filter(
                Price.asset_id == asset.asset_id,
                Price.date >= start_date,
                Price.date <= end_date
            ).order_by(Price.date.desc()).limit(30).all()

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

                        # Log success
                        logger.info(f"Successfully stored AKShare price data in database")
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

    async def _process_market_summary(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a market_summary intent

        Args:
            entities: Extracted entities

        Returns:
            Response data with market summary
        """
        try:
            # Get market or index from entities
            market_name = entities.get("market", "")
            index_name = entities.get("index", "")

            # Default to major indices if no specific market/index is mentioned
            major_indices = {
                "上证指数": "000001.SH",
                "深证成指": "399001.SZ",
                "创业板指": "399006",
                "科创50": "000688",
                "中证500": "000905",
                "沪深300": "000300"
            }

            # Determine which indices to include in the summary
            indices_to_include = []

            if market_name:
                # If a specific market is mentioned, try to find matching indices
                for name, symbol in major_indices.items():
                    if market_name.lower() in name.lower():
                        indices_to_include.append((name, symbol))
            elif index_name:
                # If a specific index is mentioned, try to find it
                for name, symbol in major_indices.items():
                    if index_name.lower() in name.lower():
                        indices_to_include.append((name, symbol))
            else:
                # Default to all major indices
                indices_to_include = list(major_indices.items())

            # Limit to top 3 indices to avoid overwhelming response
            indices_to_include = indices_to_include[:3]

            if not indices_to_include:
                return {
                    "message": f"Could not find market or index matching '{market_name or index_name}'. Please try with a different market name."
                }

            # Get current date and previous trading day
            today = date.today()
            yesterday = today - timedelta(days=1)

            # Collect market data
            market_data = []

            for name, symbol in indices_to_include:
                # Find asset in database
                asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()

                if not asset:
                    # If not in database, create a placeholder
                    asset = Asset(
                        symbol=symbol,
                        name=name,
                        exchange="CN",
                        asset_type="INDEX"
                    )
                    self.db.add(asset)
                    self.db.commit()

                # Get latest price data
                latest_prices = self.db.query(Price).filter(
                    Price.asset_id == asset.asset_id
                ).order_by(Price.date.desc()).limit(2).all()

                # If no data or data is old, try to get from AKShare
                if not latest_prices or latest_prices[0].date < yesterday:
                    logger.info(f"No recent price data for {name}, trying AKShare")
                    # Implementation for fetching from AKShare would go here
                    # Similar to _process_get_price method

                # Format the data
                if latest_prices:
                    latest = latest_prices[0]
                    previous = latest_prices[1] if len(latest_prices) > 1 else None

                    # Calculate change
                    change = 0
                    change_pct = 0
                    if previous:
                        change = latest.close - previous.close
                        change_pct = (change / previous.close) * 100

                    market_data.append({
                        "name": name,
                        "symbol": symbol,
                        "latest": {
                            "date": latest.date.isoformat(),
                            "close": latest.close,
                            "change": change,
                            "change_percentage": change_pct,
                            "volume": latest.volume
                        }
                    })

            # Determine overall market sentiment
            sentiment = "neutral"
            if market_data:
                up_count = sum(1 for item in market_data if item["latest"]["change"] > 0)
                down_count = sum(1 for item in market_data if item["latest"]["change"] < 0)

                if up_count > down_count:
                    sentiment = "positive"
                elif down_count > up_count:
                    sentiment = "negative"

            return {
                "market_summary": {
                    "date": today.isoformat(),
                    "indices": market_data,
                    "sentiment": sentiment
                },
                "message": f"Market summary for {today.isoformat()}"
            }

        except Exception as e:
            logger.error(f"Error processing market_summary intent: {e}")
            return {"error": str(e)}

    async def _process_historical_data(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a get_historical_data intent

        Args:
            entities: Extracted entities

        Returns:
            Response data with historical data
        """
        if "symbol" not in entities and "asset_name" not in entities:
            return {
                "message": "Please specify a stock symbol or name to get historical data."
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

            # Get date range - for historical data, use a longer default period
            end_date = entities.get("end_date", date.today())

            # If no start date is specified, default to 1 year ago
            if "start_date" not in entities:
                if "years" in entities:
                    years = entities["years"]
                elif "months" in entities:
                    years = entities["months"] / 12
                elif "quarters" in entities:
                    years = entities["quarters"] / 4
                else:
                    years = 1  # Default to 1 year

                start_date = end_date - timedelta(days=int(365 * years))
            else:
                start_date = entities["start_date"]

            # Get data from database
            logger.info(f"Getting historical data from database for {asset.symbol}")
            prices = self.db.query(Price).filter(
                Price.asset_id == asset.asset_id,
                Price.date >= start_date,
                Price.date <= end_date
            ).order_by(Price.date).all()

            # If no data available, try to get from AKShare
            if not prices:
                try:
                    logger.info(f"No historical data in database, trying AKShare for {asset.symbol}")
                    # Format dates for AKShare
                    start_date_str = start_date.strftime("%Y%m%d")
                    end_date_str = end_date.strftime("%Y%m%d")

                    # Get data from AKShare
                    logger.info(f"Fetching data from AKShare for {asset.symbol} from {start_date_str} to {end_date_str}")
                    try:
                        # First try with real data
                        stock_data = self.akshare_adapter.get_stock_data(
                            symbol=asset.symbol,
                            start_date=start_date_str,
                            end_date=end_date_str,
                            use_mock_data=False
                        )

                        # If no real data, try with mock data for testing
                        if stock_data.empty:
                            logger.warning(f"No real data available for {asset.symbol}, trying mock data")
                            stock_data = self.akshare_adapter.get_stock_data(
                                symbol=asset.symbol,
                                start_date=start_date_str,
                                end_date=end_date_str,
                                use_mock_data=True
                            )
                    except Exception as fetch_error:
                        logger.error(f"Error fetching real data: {fetch_error}, trying mock data")
                        stock_data = self.akshare_adapter.get_stock_data(
                            symbol=asset.symbol,
                            start_date=start_date_str,
                            end_date=end_date_str,
                            use_mock_data=True
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

                        logger.info(f"Successfully stored AKShare historical data in database")
                except Exception as e:
                    logger.error(f"Error getting data from AKShare: {e}")

            if not prices:
                return {
                    "message": f"No historical data available for {asset.name} ({asset.symbol}) in the specified date range."
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

            # Calculate some basic statistics
            if prices:
                start_price = prices[0].close
                end_price = prices[-1].close
                min_price = min(p.low for p in prices)
                max_price = max(p.high for p in prices)
                avg_price = sum(p.close for p in prices) / len(prices)
                price_change = end_price - start_price
                price_change_pct = (price_change / start_price) * 100 if start_price else 0

                # Determine trend
                trend = "stable"
                if price_change_pct > 5:
                    trend = "strongly positive"
                elif price_change_pct > 0:
                    trend = "positive"
                elif price_change_pct < -5:
                    trend = "strongly negative"
                elif price_change_pct < 0:
                    trend = "negative"

            return {
                "asset": {
                    "asset_id": asset.asset_id,
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "exchange": asset.exchange
                },
                "date_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": (end_date - start_date).days
                },
                "prices": price_data,
                "statistics": {
                    "start_price": start_price,
                    "end_price": end_price,
                    "min_price": min_price,
                    "max_price": max_price,
                    "avg_price": avg_price,
                    "price_change": price_change,
                    "price_change_percentage": price_change_pct,
                    "trend": trend
                },
                "message": f"Historical data for {asset.name} ({asset.symbol}) from {start_date.isoformat()} to {end_date.isoformat()}."
            }

        except Exception as e:
            logger.error(f"Error processing get_historical_data intent: {e}")
            return {"error": str(e)}

    async def _process_compare_assets(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a compare_assets intent

        Args:
            entities: Extracted entities

        Returns:
            Response data
        """
        if "comparison" not in entities:
            return {
                "message": "Please specify two assets to compare."
            }

        try:
            # Extract the two assets to compare
            asset1_name = entities["comparison"]["asset1"]
            asset2_name = entities["comparison"]["asset2"]

            # Get date range
            end_date = entities.get("end_date", date.today())
            start_date = entities.get("start_date", end_date - timedelta(days=30))

            # Find assets in database
            asset1 = None
            asset2 = None

            # Try to find by name
            asset1 = self.db.query(Asset).filter(Asset.name.ilike(f"%{asset1_name}%")).first()
            asset2 = self.db.query(Asset).filter(Asset.name.ilike(f"%{asset2_name}%")).first()

            # If not found, try common stocks
            if not asset1 or not asset2:
                common_stocks = {
                    "平安银行": "000001",
                    "浦发银行": "600000",
                    "贵州茅台": "600519",
                    "中国平安": "601318",
                    "招商银行": "600036",
                    "工商银行": "601398",
                    "建设银行": "601939",
                    "上证指数": "000001.SH",
                    "深证成指": "399001.SZ",
                    "创业板指": "399006",
                    "科创50": "000688",
                    "中证500": "000905",
                    "沪深300": "000300"
                }

                # Try to match asset1
                if not asset1:
                    for company, symbol in common_stocks.items():
                        if company.lower() in asset1_name.lower():
                            asset1 = self.db.query(Asset).filter(Asset.symbol == symbol).first()
                            if asset1:
                                break

                # Try to match asset2
                if not asset2:
                    for company, symbol in common_stocks.items():
                        if company.lower() in asset2_name.lower():
                            asset2 = self.db.query(Asset).filter(Asset.symbol == symbol).first()
                            if asset2:
                                break

            # If still not found, try international companies
            if not asset1 or not asset2:
                common_companies = {
                    "Apple": "AAPL",
                    "Microsoft": "MSFT",
                    "Google": "GOOGL",
                    "Alphabet": "GOOGL",
                    "Amazon": "AMZN",
                    "Tesla": "TSLA",
                    "Facebook": "META",
                    "Meta": "META",
                    "Netflix": "NFLX",
                    "Nvidia": "NVDA",
                    "Intel": "INTC",
                    "IBM": "IBM",
                    "Oracle": "ORCL",
                    "Cisco": "CSCO",
                    "Adobe": "ADBE"
                }

                # Try to match asset1
                if not asset1:
                    for company, symbol in common_companies.items():
                        if company.lower() in asset1_name.lower():
                            asset1 = self.db.query(Asset).filter(Asset.symbol == symbol).first()
                            if asset1:
                                break

                # Try to match asset2
                if not asset2:
                    for company, symbol in common_companies.items():
                        if company.lower() in asset2_name.lower():
                            asset2 = self.db.query(Asset).filter(Asset.symbol == symbol).first()
                            if asset2:
                                break

            # Check if both assets were found
            if not asset1 and not asset2:
                return {
                    "message": f"Could not find either asset: {asset1_name} or {asset2_name}."
                }
            elif not asset1:
                return {
                    "message": f"Could not find asset: {asset1_name}."
                }
            elif not asset2:
                return {
                    "message": f"Could not find asset: {asset2_name}."
                }

            # Get price data for both assets
            prices1 = self.db.query(Price).filter(
                Price.asset_id == asset1.asset_id,
                Price.date >= start_date,
                Price.date <= end_date
            ).order_by(Price.date).all()

            prices2 = self.db.query(Price).filter(
                Price.asset_id == asset2.asset_id,
                Price.date >= start_date,
                Price.date <= end_date
            ).order_by(Price.date).all()

            # If no data available, try to get from AKShare
            if not prices1:
                logger.info(f"No price data in database for {asset1.symbol}, trying AKShare")
                # Implementation for fetching from AKShare would go here
                # Similar to _process_get_price method

            if not prices2:
                logger.info(f"No price data in database for {asset2.symbol}, trying AKShare")
                # Implementation for fetching from AKShare would go here
                # Similar to _process_get_price method

            # Check if we have data for both assets
            if not prices1 and not prices2:
                return {
                    "message": f"No price data available for {asset1.name} and {asset2.name} in the specified date range."
                }
            elif not prices1:
                return {
                    "message": f"No price data available for {asset1.name} in the specified date range."
                }
            elif not prices2:
                return {
                    "message": f"No price data available for {asset2.name} in the specified date range."
                }

            # Format response
            price_data1 = [{
                "date": p.date.isoformat(),
                "close": p.close,
                "volume": p.volume
            } for p in prices1]

            price_data2 = [{
                "date": p.date.isoformat(),
                "close": p.close,
                "volume": p.volume
            } for p in prices2]

            # Calculate some basic comparison metrics
            if prices1 and prices2:
                # Calculate price change percentage
                asset1_start_price = prices1[0].close if prices1 else None
                asset1_end_price = prices1[-1].close if prices1 else None
                asset1_change_pct = ((asset1_end_price - asset1_start_price) / asset1_start_price * 100) if asset1_start_price and asset1_end_price else None

                asset2_start_price = prices2[0].close if prices2 else None
                asset2_end_price = prices2[-1].close if prices2 else None
                asset2_change_pct = ((asset2_end_price - asset2_start_price) / asset2_start_price * 100) if asset2_start_price and asset2_end_price else None

                # Determine which performed better
                better_performer = None
                if asset1_change_pct is not None and asset2_change_pct is not None:
                    if asset1_change_pct > asset2_change_pct:
                        better_performer = asset1.name
                    elif asset2_change_pct > asset1_change_pct:
                        better_performer = asset2.name
                    else:
                        better_performer = "Both performed equally"

            return {
                "assets": [
                    {
                        "asset_id": asset1.asset_id,
                        "symbol": asset1.symbol,
                        "name": asset1.name,
                        "exchange": asset1.exchange,
                        "prices": price_data1,
                        "start_price": asset1_start_price,
                        "end_price": asset1_end_price,
                        "change_percentage": asset1_change_pct
                    },
                    {
                        "asset_id": asset2.asset_id,
                        "symbol": asset2.symbol,
                        "name": asset2.name,
                        "exchange": asset2.exchange,
                        "prices": price_data2,
                        "start_price": asset2_start_price,
                        "end_price": asset2_end_price,
                        "change_percentage": asset2_change_pct
                    }
                ],
                "date_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "comparison": {
                    "better_performer": better_performer,
                    "asset1_change": f"{asset1_change_pct:.2f}%" if asset1_change_pct is not None else "N/A",
                    "asset2_change": f"{asset2_change_pct:.2f}%" if asset2_change_pct is not None else "N/A"
                },
                "message": f"Comparison between {asset1.name} and {asset2.name} from {start_date.isoformat()} to {end_date.isoformat()}."
            }

        except Exception as e:
            logger.error(f"Error processing compare_assets intent: {e}")
            return {"error": str(e)}
