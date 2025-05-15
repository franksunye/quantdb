"""
Development environment setup script
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_command(command, cwd=None):
    """Run a shell command and log the output"""
    logger.info(f"Running command: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=True,
            cwd=cwd
        )
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def create_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        "data/raw",
        "data/processed",
        "logs",
        "database",
        "coverage_reports",
        "coverage_reports/html"
    ]

    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True)
            logger.info(f"Created directory: {path}")
        else:
            logger.info(f"Directory already exists: {path}")

def install_dependencies():
    """Install Python dependencies"""
    logger.info("Installing dependencies...")
    if not run_command("pip install -r requirements.txt"):
        return False

    # Install development dependencies
    logger.info("Installing development dependencies...")
    dev_dependencies = [
        "pytest",
        "pytest-cov",
        "flake8",
        "black",
        "isort",
        "mypy",
        "pre-commit"
    ]

    return run_command(f"pip install {' '.join(dev_dependencies)}")

def initialize_database():
    """Initialize the database"""
    logger.info("Initializing database...")
    if not run_command("python -m src.scripts.init_db"):
        return False

    # Initialize test data
    logger.info("Initializing test data...")
    return run_command("python -m tests.init_test_db")

def setup_pre_commit():
    """Set up pre-commit hooks"""
    logger.info("Setting up pre-commit hooks...")
    return run_command("pre-commit install")

def fix_deprecation_warnings():
    """Fix deprecation warnings"""
    logger.info("Fixing deprecation warnings...")
    return run_command("python fix_deprecation_warnings.py")

def run_tests():
    """Run tests"""
    logger.info("Running tests...")
    return run_command("python run_specific_tests.py")

def main():
    """Main setup function"""
    logger.info("Setting up development environment...")

    # Create directories
    create_directories()

    # Install dependencies
    if not install_dependencies():
        logger.error("Failed to install dependencies")
        return False

    # Initialize database
    if not initialize_database():
        logger.error("Failed to initialize database")
        return False

    # Set up pre-commit hooks
    if not setup_pre_commit():
        logger.error("Failed to set up pre-commit hooks")
        logger.warning("Continuing despite pre-commit setup failure")

    # Fix deprecation warnings
    if not fix_deprecation_warnings():
        logger.error("Failed to fix deprecation warnings")
        logger.warning("Continuing despite deprecation warnings fix failure")

    # Run tests
    if not run_tests():
        logger.error("Some tests failed")
        logger.warning("Continuing despite test failures")

    logger.info("Development environment setup completed successfully")
    logger.info("\nNext steps:")
    logger.info("1. Run tests: python run_specific_tests.py")
    logger.info("2. Run tests with coverage: python run_coverage.py")
    logger.info("3. Start the API server: python -m src.api.main")

    return True

if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("Development environment setup failed")
        sys.exit(1)
