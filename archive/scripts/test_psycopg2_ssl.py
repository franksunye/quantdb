"""
Test psycopg2 connection to Supabase PostgreSQL database with SSL certificate
"""

import os
import sys
import logging
import psycopg2
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("psycopg2_ssl_test")

# Add project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
load_dotenv()

def test_connection():
    """Test connection to Supabase PostgreSQL database with SSL certificate"""
    try:
        # Get database connection parameters
        db_host = "db.dvusiqfijdmjcsubyapw.supabase.co"
        db_port = 5432
        db_name = "postgres"
        db_user = "postgres"
        db_password = os.getenv('SUPABASE_DB_PASSWORD')
        
        # Get SSL certificate path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ssl_cert = os.path.join(script_dir, '..', 'prod-ca-2021.crt')
        
        # Check if SSL certificate exists
        if not os.path.exists(ssl_cert):
            ssl_cert = os.path.join(script_dir, 'prod-ca-2021.crt')
            if not os.path.exists(ssl_cert):
                logger.warning("SSL certificate file not found. Using sslmode=require instead of verify-full.")
                ssl_mode = "require"
                ssl_cert = None
            else:
                ssl_mode = "verify-full"
        else:
            ssl_mode = "verify-full"
        
        # Display connection info
        logger.info("Connecting to Supabase PostgreSQL database with SSL...")
        logger.info(f"Host: {db_host}")
        logger.info(f"Port: {db_port}")
        logger.info(f"Database: {db_name}")
        logger.info(f"User: {db_user}")
        logger.info(f"SSL Mode: {ssl_mode}")
        if ssl_mode == "verify-full":
            logger.info(f"SSL Certificate: {ssl_cert}")
        
        # Connect to database
        if ssl_mode == "verify-full":
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                dbname=db_name,
                user=db_user,
                password=db_password,
                sslmode=ssl_mode,
                sslrootcert=ssl_cert
            )
        else:
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                dbname=db_name,
                user=db_user,
                password=db_password,
                sslmode=ssl_mode
            )
        
        # Create cursor
        cur = conn.cursor()
        
        # Test connection
        logger.info("Testing connection...")
        
        # Get database info
        cur.execute("SELECT current_database(), current_user, version()")
        db_info = cur.fetchone()
        logger.info(f"Database: {db_info[0]}")
        logger.info(f"User: {db_info[1]}")
        logger.info(f"Version: {db_info[2]}")
        
        # Check SSL connection
        cur.execute("SELECT ssl_is_used(), ssl_version(), ssl_cipher()")
        ssl_info = cur.fetchone()
        logger.info(f"SSL Used: {ssl_info[0]}")
        logger.info(f"SSL Version: {ssl_info[1]}")
        logger.info(f"SSL Cipher: {ssl_info[2]}")
        
        # Get schemas
        cur.execute("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name")
        schemas = cur.fetchall()
        logger.info(f"Schemas: {[schema[0] for schema in schemas]}")
        
        # Get tables in public schema
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
        tables = cur.fetchall()
        logger.info(f"Tables in public schema: {[table[0] for table in tables]}")
        
        # Close cursor and connection
        cur.close()
        conn.close()
        
        logger.info("Connection test successful!")
        return True
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
