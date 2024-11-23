import jwt
import logging
from datetime import datetime
import requests
from src.utils.logger import setup_logger
from config.settings import SECURITY_CONFIG

logger = setup_logger('token_debug')

def debug_token_validation():
    """Debug token validation process"""
    base_url = "http://localhost:8000"
    credentials = {
        "username": "ShareGuardService",
        "domain": "shareguard.com",
        "password": "P(5$\\#SX07sj"
    }

    # Step 1: Get token
    login_response = requests.post(
        f"{base_url}/api/v1/auth/login",
        json=credentials
    )
    token_data = login_response.json()
    token = token_data['access_token']

    # Step 2: Manual token validation
    try:
        logger.info("Testing manual token validation...")
        decoded = jwt.decode(
            token,
            SECURITY_CONFIG["secret_key"],
            algorithms=[SECURITY_CONFIG["algorithm"]]
        )
        logger.info(f"Manual token validation successful: {decoded}")
    except Exception as e:
        logger.error(f"Manual token validation failed: {str(e)}")

    # Step 3: Database session check
    from src.db.database import SessionLocal
    from src.db.models.auth import AuthSession
    
    db = SessionLocal()
    try:
        logger.info("Checking database session...")
        session = db.query(AuthSession).filter(
            AuthSession.token == token,
            AuthSession.is_active == True
        ).first()
        
        if session:
            logger.info(f"Found active session: {session.id}")
            logger.info(f"Session expires at: {session.expires_at}")
            logger.info(f"Session is active: {session.is_active}")
        else:
            logger.error("No active session found in database")
            
        # Check all sessions for this token
        all_sessions = db.query(AuthSession).filter(
            AuthSession.token == token
        ).all()
        logger.info(f"Total sessions found for token: {len(all_sessions)}")
        for s in all_sessions:
            logger.info(f"Session {s.id}: active={s.is_active}, expires={s.expires_at}")
            
    finally:
        db.close()

    # Step 4: Test verification endpoint with debug headers
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Debug': 'true'  # Add debug header
    }
    
    verify_response = requests.get(
        f"{base_url}/api/v1/auth/verify",
        headers=headers
    )
    
    logger.info(f"Verification response: {verify_response.status_code}")
    logger.info(f"Verification body: {verify_response.text}")

if __name__ == "__main__":
    logger.info("Starting token debugging...")
    debug_token_validation()
    logger.info("Token debugging complete")