"""
Database migration script for Asset model enhancement.

This script adds new columns to the assets table and populates them with
data from AKShare for existing assets.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import # Migrated to core
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy import BigInteger, Column, Date, DateTime, Float, String, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from core.models import Asset, Base
from core.services.asset_info_service import AssetInfoService
from core.utils.config import DATABASE_URL
from core.utils.logger import get_logger

# Setup logger
logger = get_logger(__name__)


def migrate_database():
    """
    Migrate the database to add new Asset model fields.
    """
    logger.info("Starting Asset model migration...")

    try:
        # Create engine and session
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Check if migration is needed
        with engine.connect() as conn:
            # Check if new columns exist
            result = conn.execute(text("PRAGMA table_info(assets)"))
            columns = [row[1] for row in result.fetchall()]

            new_columns = [
                "industry",
                "concept",
                "listing_date",
                "total_shares",
                "circulating_shares",
                "market_cap",
                "pe_ratio",
                "pb_ratio",
                "roe",
                "last_updated",
                "data_source",
            ]

            missing_columns = [col for col in new_columns if col not in columns]

            if not missing_columns:
                logger.info("All new columns already exist. Migration not needed.")
                return True

            logger.info(f"Adding missing columns: {missing_columns}")

            # Add missing columns
            for column in missing_columns:
                try:
                    if column == "industry":
                        conn.execute(text("ALTER TABLE assets ADD COLUMN industry VARCHAR"))
                    elif column == "concept":
                        conn.execute(text("ALTER TABLE assets ADD COLUMN concept VARCHAR"))
                    elif column == "listing_date":
                        conn.execute(text("ALTER TABLE assets ADD COLUMN listing_date DATE"))
                    elif column == "total_shares":
                        conn.execute(text("ALTER TABLE assets ADD COLUMN total_shares BIGINT"))
                    elif column == "circulating_shares":
                        conn.execute(
                            text("ALTER TABLE assets ADD COLUMN circulating_shares BIGINT")
                        )
                    elif column == "market_cap":
                        conn.execute(text("ALTER TABLE assets ADD COLUMN market_cap BIGINT"))
                    elif column == "pe_ratio":
                        conn.execute(text("ALTER TABLE assets ADD COLUMN pe_ratio FLOAT"))
                    elif column == "pb_ratio":
                        conn.execute(text("ALTER TABLE assets ADD COLUMN pb_ratio FLOAT"))
                    elif column == "roe":
                        conn.execute(text("ALTER TABLE assets ADD COLUMN roe FLOAT"))
                    elif column == "last_updated":
                        conn.execute(text("ALTER TABLE assets ADD COLUMN last_updated DATETIME"))
                    elif column == "data_source":
                        conn.execute(
                            text(
                                "ALTER TABLE assets ADD COLUMN data_source VARCHAR DEFAULT 'akshare'"
                            )
                        )

                    logger.info(f"Successfully added column: {column}")

                except Exception as e:
                    logger.warning(f"Error adding column {column}: {e}")

            conn.commit()

        # Update existing assets with enhanced information
        db = SessionLocal()
        try:
            asset_info_service = AssetInfoService(db)

            # Get all existing assets
            existing_assets = db.query(Asset).all()
            logger.info(f"Found {len(existing_assets)} existing assets to update")

            for asset in existing_assets:
                try:
                    logger.info(f"Updating asset: {asset.symbol}")
                    asset_info_service._update_asset_info(asset)
                except Exception as e:
                    logger.warning(f"Error updating asset {asset.symbol}: {e}")

            # Add some default assets if none exist
            if not existing_assets:
                logger.info("No existing assets found. Adding default assets...")
                default_assets = [
                    "600000",  # 浦发银行
                    "000001",  # 平安银行
                    "600519",  # 贵州茅台
                    "000002",  # 万科A
                    "600036",  # 招商银行
                ]

                for symbol in default_assets:
                    try:
                        asset = asset_info_service.get_or_create_asset(symbol)
                        logger.info(f"Created default asset: {symbol} - {asset.name}")
                    except Exception as e:
                        logger.warning(f"Error creating default asset {symbol}: {e}")

        finally:
            db.close()

        logger.info("Asset model migration completed successfully")
        return True

    except SQLAlchemyError as e:
        logger.error(f"Database error during migration: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        return False


def verify_migration():
    """
    Verify that the migration was successful.
    """
    logger.info("Verifying migration...")

    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Check table structure
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(assets)"))
            columns = [row[1] for row in result.fetchall()]

            expected_columns = [
                "asset_id",
                "symbol",
                "name",
                "isin",
                "asset_type",
                "exchange",
                "currency",
                "industry",
                "concept",
                "listing_date",
                "total_shares",
                "circulating_shares",
                "market_cap",
                "pe_ratio",
                "pb_ratio",
                "roe",
                "last_updated",
                "data_source",
            ]

            missing_columns = [col for col in expected_columns if col not in columns]

            if missing_columns:
                logger.error(f"Migration verification failed. Missing columns: {missing_columns}")
                return False

            logger.info("All expected columns are present")

        # Check data
        db = SessionLocal()
        try:
            assets = db.query(Asset).all()
            logger.info(f"Found {len(assets)} assets in database")

            for asset in assets[:3]:  # Show first 3 assets
                logger.info(f"Asset: {asset.symbol} - {asset.name} - Industry: {asset.industry}")

        finally:
            db.close()

        logger.info("Migration verification completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error during migration verification: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting Asset model migration script...")

    # Run migration
    success = migrate_database()

    if success:
        # Verify migration
        verify_success = verify_migration()

        if verify_success:
            logger.info("Asset model migration and verification completed successfully!")
            sys.exit(0)
        else:
            logger.error("Migration verification failed!")
            sys.exit(1)
    else:
        logger.error("Asset model migration failed!")
        sys.exit(1)
