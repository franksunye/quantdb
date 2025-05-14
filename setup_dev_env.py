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
        "database"
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
    return run_command("pip install -r requirements.txt")

def initialize_database():
    """Initialize the database"""
    logger.info("Initializing database...")
    return run_command("python -m src.scripts.init_db")

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
    
    logger.info("Development environment setup completed successfully")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("Development environment setup failed")
        sys.exit(1)
