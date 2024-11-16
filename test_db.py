# test_db.py
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from config.settings import get_db_url
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    try:
        load_dotenv()  # Load environment variables
        engine = create_engine(get_db_url())
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT @@VERSION")).scalar()
            logger.info(f"Connected successfully. SQL Server version: {result}")
            return True
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()