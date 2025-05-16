"""
Data import API routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.api.database import get_db
from src.services.data_import import DataImportService
from src.api.schemas import ImportResponse, ImportRequest
from src.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

# Create router
router = APIRouter(
    tags=["import"],
    responses={404: {"description": "Not found"}},
)

@router.post("/stock", response_model=ImportResponse)
async def import_stock_data(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Import stock data from AKShare

    This endpoint triggers a background task to import stock data from AKShare.
    """
    try:
        # Create data import service
        import_service = DataImportService(db)

        # Add import task to background tasks
        background_tasks.add_task(
            _import_stock_data_task,
            import_service=import_service,
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date
        )

        return {
            "status": "success",
            "message": f"Import task for stock {request.symbol} has been scheduled",
            "task_id": f"import_stock_{request.symbol}_{request.start_date}_{request.end_date}"
        }

    except Exception as e:
        logger.error(f"Error scheduling stock data import: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index", response_model=ImportResponse)
async def import_index_data(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Import index data from AKShare

    This endpoint triggers a background task to import index data from AKShare.
    """
    try:
        # Create data import service
        import_service = DataImportService(db)

        # Add import task to background tasks
        background_tasks.add_task(
            _import_index_data_task,
            import_service=import_service,
            index_symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date
        )

        return {
            "status": "success",
            "message": f"Import task for index {request.symbol} has been scheduled",
            "task_id": f"import_index_{request.symbol}_{request.start_date}_{request.end_date}"
        }

    except Exception as e:
        logger.error(f"Error scheduling index data import: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index/constituents", response_model=ImportResponse)
async def import_index_constituents(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Import index constituents from AKShare

    This endpoint triggers a background task to import index constituents from AKShare.
    """
    try:
        # Create data import service
        import_service = DataImportService(db)

        # Add import task to background tasks
        background_tasks.add_task(
            _import_index_constituents_task,
            import_service=import_service,
            index_symbol=request.symbol
        )

        return {
            "status": "success",
            "message": f"Import task for index constituents {request.symbol} has been scheduled",
            "task_id": f"import_constituents_{request.symbol}"
        }

    except Exception as e:
        logger.error(f"Error scheduling index constituents import: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def _import_stock_data_task(
    import_service: DataImportService,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Background task to import stock data"""
    try:
        result = import_service.import_from_akshare(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        logger.info(f"Stock data import completed: {result}")
    except Exception as e:
        logger.error(f"Error in stock data import task: {e}")

async def _import_index_data_task(
    import_service: DataImportService,
    index_symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Background task to import index data"""
    try:
        result = import_service.import_index_data(
            index_symbol=index_symbol,
            start_date=start_date,
            end_date=end_date
        )
        logger.info(f"Index data import completed: {result}")
    except Exception as e:
        logger.error(f"Error in index data import task: {e}")

async def _import_index_constituents_task(
    import_service: DataImportService,
    index_symbol: str
):
    """Background task to import index constituents"""
    try:
        result = import_service.import_index_constituents(
            index_symbol=index_symbol
        )
        logger.info(f"Index constituents import completed: {result}")
    except Exception as e:
        logger.error(f"Error in index constituents import task: {e}")
