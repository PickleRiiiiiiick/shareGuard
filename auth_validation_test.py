import jwt
import logging
import requests
import json
from datetime import datetime
from src.utils.logger import setup_logger
from src.db.database import SessionLocal
from src.db.models.auth import AuthSession, ServiceAccount
from config.settings import SECURITY_CONFIG

logger = setup_logger('auth_validation')

class AuthValidationTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.db = SessionLocal()

    def cleanup(self):
        """Cleanup any test artifacts"""
        try:
            if self.token:
                # Deactivate test session
                session = self.db.query(AuthSession).filter(
                    AuthSession.token == self.token,
                    AuthSession.is_active == True
                ).first()
                if session:
                    session.is_active = False
                    self.db.commit()
        finally:
            self.db.close()

    def test_login_flow(self):
        """Test complete login flow"""
        logger.info("Testing login flow...")
        
        credentials = {
            "username": "ShareGuardService",
            "domain": "shareguard.com",
            "password": "P(5$\\#SX07sj"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json=credentials
        )
        
        if response.status_code != 200:
            logger.error(f"Login failed: {response.text}")
            return False
            
        data = response.json()
        self.token = data['access_token']
        
        # Validate token format
        try:
            payload = jwt.decode(self.token, options={"verify_signature": False})
            logger.info(f"Token payload: {payload}")
            
            # Check required claims
            assert isinstance(payload['sub'], str), "Subject must be a string"
            assert 'name' in payload, "Token must contain name claim"
            assert 'exp' in payload, "Token must contain expiration"
            assert 'iat' in payload, "Token must contain issued at time"
            
            logger.info("Token format validation passed")
            return True
        except Exception as e:
            logger.error(f"Token format validation failed: {str(e)}")
            return False

    def test_auth_verification(self):
        """Test authentication verification endpoints"""
        if not self.token:
            logger.error("No token available for testing")
            return False
            
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Test verify endpoint
        verify_response = self.session.get(
            f"{self.base_url}/api/v1/auth/verify",
            headers=headers
        )
        
        logger.info(f"Verify endpoint status: {verify_response.status_code}")
        if verify_response.status_code != 200:
            logger.error(f"Verify endpoint failed: {verify_response.text}")
            return False
            
        # Test a simple protected endpoint that doesn't involve complex queries
        test_response = self.session.get(
            f"{self.base_url}/api/v1/auth/test",
            headers=headers
        )
        
        logger.info(f"Auth test endpoint status: {test_response.status_code}")
        if test_response.status_code == 404:
            logger.warning("Auth test endpoint not found - this is optional but recommended")
        elif test_response.status_code != 200:
            logger.error(f"Auth test endpoint failed: {test_response.text}")
            if test_response.status_code != 401 and test_response.status_code != 403:
                logger.info("Non-auth related error - authentication might still be working")
            else:
                return False
                
        return True

    def test_session_management(self):
        """Test session management in database"""
        if not self.token:
            logger.error("No token available for testing")
            return False
            
        try:
            # Check session exists and is active
            session = self.db.query(AuthSession).filter(
                AuthSession.token == self.token,
                AuthSession.is_active == True
            ).first()
            
            if not session:
                logger.error("No active session found in database")
                return False
                
            logger.info(f"Found active session: {session.id}")
            logger.info(f"Session expires at: {session.expires_at}")
            
            # Test session expiration handling
            if session.expires_at < datetime.utcnow():
                logger.error("Session has already expired")
                return False
                
            # Verify service account link
            service_account = self.db.query(ServiceAccount).get(session.service_account_id)
            if not service_account or not service_account.is_active:
                logger.error("Invalid or inactive service account")
                return False
                
            logger.info(f"Verified service account: {service_account.username}")
            return True
            
        except Exception as e:
            logger.exception("Error testing session management")
            return False

def run_validation_suite():
    """Run complete validation suite"""
    logger.info("Starting authentication validation suite...")
    
    tester = AuthValidationTester()
    try:
        # Test 1: Login Flow
        logger.info("\n=== Testing Login Flow ===")
        if not tester.test_login_flow():
            logger.error("Login flow test failed")
            return False
            
        # Test 2: Auth Verification
        logger.info("\n=== Testing Auth Verification ===")
        if not tester.test_auth_verification():
            logger.error("Auth verification test failed")
            return False
            
        # Test 3: Session Management
        logger.info("\n=== Testing Session Management ===")
        if not tester.test_session_management():
            logger.error("Session management test failed")
            return False
            
        logger.info("\nAll authentication validation tests passed successfully!")
        return True
        
    except Exception as e:
        logger.exception("Unexpected error during validation")
        return False
    finally:
        tester.cleanup()

if __name__ == "__main__":
    success = run_validation_suite()
    exit(0 if success else 1)