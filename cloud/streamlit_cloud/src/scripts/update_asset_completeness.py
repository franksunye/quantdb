"""
Asset data completeness update script.

This script updates existing assets to ensure 100% data completeness,
focusing on industry, concept, and missing financial indicators.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import # Migrated to core
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.utils.config import DATABASE_URL
from core.models import Asset
from core.services.asset_info_service import AssetInfoService
from core.utils.logger import get_logger

# Setup logger
logger = get_logger(__name__)


def update_asset_completeness():
    """
    Update existing assets to ensure 100% data completeness.
    """
    logger.info("Starting asset data completeness update...")

    try:
        # Create engine and session
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        db = SessionLocal()
        try:
            asset_info_service = AssetInfoService(db)

            # Get all existing assets
            existing_assets = db.query(Asset).all()
            logger.info(f"Found {len(existing_assets)} existing assets to update")

            updated_count = 0

            for asset in existing_assets:
                logger.info(f"Updating asset: {asset.symbol} - {asset.name}")

                # Check what data is missing
                missing_data = []
                if not asset.industry:
                    missing_data.append("industry")
                if not asset.concept:
                    missing_data.append("concept")
                if not asset.pe_ratio:
                    missing_data.append("pe_ratio")
                if not asset.pb_ratio:
                    missing_data.append("pb_ratio")

                if missing_data:
                    logger.info(f"Missing data for {asset.symbol}: {missing_data}")

                    try:
                        # Update asset info
                        updated_asset = asset_info_service._update_asset_info(asset)

                        # Verify updates
                        verification = []
                        if updated_asset.industry:
                            verification.append(f"industry: {updated_asset.industry}")
                        if updated_asset.concept:
                            verification.append(f"concept: {updated_asset.concept}")
                        if updated_asset.pe_ratio:
                            verification.append(f"PE: {updated_asset.pe_ratio}")
                        if updated_asset.pb_ratio:
                            verification.append(f"PB: {updated_asset.pb_ratio}")

                        logger.info(
                            f"Successfully updated {asset.symbol}: {', '.join(verification)}"
                        )
                        updated_count += 1

                    except Exception as e:
                        logger.error(f"Error updating asset {asset.symbol}: {e}")
                else:
                    logger.info(f"Asset {asset.symbol} already has complete data")

            logger.info(f"Asset completeness update completed. Updated {updated_count} assets.")
            return True

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error during asset completeness update: {e}")
        return False


def verify_completeness():
    """
    Verify that all assets have complete data.
    """
    logger.info("Verifying asset data completeness...")

    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        db = SessionLocal()
        try:
            assets = db.query(Asset).all()
            logger.info(f"Verifying {len(assets)} assets...")

            complete_count = 0
            incomplete_assets = []

            for asset in assets:
                missing_fields = []

                # Check required fields
                if not asset.name or asset.name.startswith("Stock "):
                    missing_fields.append("name")
                if not asset.industry:
                    missing_fields.append("industry")
                if not asset.concept:
                    missing_fields.append("concept")
                if not asset.pe_ratio:
                    missing_fields.append("pe_ratio")
                if not asset.pb_ratio:
                    missing_fields.append("pb_ratio")

                if missing_fields:
                    incomplete_assets.append(
                        {"symbol": asset.symbol, "name": asset.name, "missing": missing_fields}
                    )
                    logger.warning(f"Incomplete data for {asset.symbol}: missing {missing_fields}")
                else:
                    complete_count += 1
                    logger.info(f"✅ Complete data for {asset.symbol}: {asset.name}")

            # Summary
            total_assets = len(assets)
            completeness_rate = (complete_count / total_assets * 100) if total_assets > 0 else 0

            logger.info(f"\n=== Asset Data Completeness Summary ===")
            logger.info(f"Total assets: {total_assets}")
            logger.info(f"Complete assets: {complete_count}")
            logger.info(f"Incomplete assets: {len(incomplete_assets)}")
            logger.info(f"Completeness rate: {completeness_rate:.1f}%")

            if incomplete_assets:
                logger.info(f"\nIncomplete assets:")
                for asset in incomplete_assets:
                    logger.info(
                        f"  {asset['symbol']} ({asset['name']}): missing {asset['missing']}"
                    )

            return completeness_rate == 100.0

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error during completeness verification: {e}")
        return False


def show_asset_summary():
    """
    Show a summary of all assets with their key information.
    """
    logger.info("Showing asset summary...")

    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        db = SessionLocal()
        try:
            assets = db.query(Asset).all()

            logger.info(f"\n=== Asset Summary ({len(assets)} assets) ===")
            for asset in assets:
                logger.info(f"Symbol: {asset.symbol}")
                logger.info(f"  Name: {asset.name}")
                logger.info(f"  Industry: {asset.industry or 'N/A'}")
                logger.info(f"  Concept: {asset.concept or 'N/A'}")
                logger.info(f"  PE Ratio: {asset.pe_ratio or 'N/A'}")
                logger.info(f"  PB Ratio: {asset.pb_ratio or 'N/A'}")
                logger.info(f"  Data Source: {asset.data_source}")
                logger.info(f"  Last Updated: {asset.last_updated}")
                logger.info("")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error showing asset summary: {e}")


if __name__ == "__main__":
    logger.info("Starting Asset Data Completeness Update Script...")

    # Show current state
    logger.info("=== BEFORE UPDATE ===")
    show_asset_summary()
    verify_completeness()

    # Update assets
    logger.info("\n=== UPDATING ASSETS ===")
    success = update_asset_completeness()

    if success:
        # Verify results
        logger.info("\n=== AFTER UPDATE ===")
        show_asset_summary()
        verification_success = verify_completeness()

        if verification_success:
            logger.info("✅ Asset data completeness update completed successfully!")
            logger.info("All assets now have 100% complete data.")
            sys.exit(0)
        else:
            logger.warning("⚠️ Some assets still have incomplete data.")
            sys.exit(1)
    else:
        logger.error("❌ Asset data completeness update failed!")
        sys.exit(1)
