import os
from dotenv import load_dotenv
import logging
import psycopg2
from psycopg2 import OperationalError

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_db_connection(database_url):
    """Test the database connection"""
    try:
        # Extract connection parameters from DATABASE_URL
        db_params = database_url.replace('postgresql://', '')
        user_pass, host_db = db_params.split('@')
        user, password = user_pass.split(':')
        host_port, db_name = host_db.split('/')
        host = host_port.split(':')[0]
        port = host_port.split(':')[1] if ':' in host_port else '5432'

        # Try to connect
        conn = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.close()
        logger.info("Database connection test successful")
        return True
    except OperationalError as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

class Config:
    # Get database URL from environment variable
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        logger.error("DATABASE_URL not found in environment variables")
        raise ValueError("DATABASE_URL environment variable is required")

    # Test database connection
    if not test_db_connection(DATABASE_URL):
        raise ValueError("Could not connect to the database. Please check your connection settings.")

    # Log the database URL (with password masked)
    masked_url = DATABASE_URL.replace(DATABASE_URL.split(':')[2].split('@')[0], '****')
    logger.info("Using database URL: %s", masked_url)

    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True  # Enable SQL query logging
    
    # Pool configuration
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    } 