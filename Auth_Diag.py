import jwt
import sys
from datetime import datetime
import requests
import json
from pprint import pprint
from pathlib import Path
import time
from src.utils.logger import setup_logger

# Set up custom logger
logger = setup_logger('auth_diagnostic')

def decode_token(token):
    """Decode token without verification to inspect payload"""
    try:
        logger.debug("Attempting to decode token...")
        decoded = jwt.decode(token, options={"verify_signature": False})
        logger.debug("Token decoded successfully")
        return decoded
    except jwt.InvalidTokenError as e:
        logger.error(f"Error decoding token: {str(e)}")
        return f"Error decoding token: {str(e)}"

def pretty_print_request(req):
    """Print request details for debugging"""
    logger.debug(f'\n{"-"*20} Request Details {"-"*20}')
    logger.debug(f'Method: {req.method}')
    logger.debug(f'URL: {req.url}')
    logger.debug('Headers:')
    for header, value in req.headers.items():
        if header.lower() == 'authorization':
            logger.debug(f'{header}: Bearer <token-truncated>')
        else:
            logger.debug(f'{header}: {value}')
    if req.body:
        logger.debug('Body:')
        try:
            body = json.loads(req.body)
            logger.debug(json.dumps(body, indent=2))
        except:
            logger.debug(req.body)

def test_token_lifecycle(base_url, credentials):
    """Test complete token lifecycle"""
    session = requests.Session()
    
    try:
        # Step 1: Login attempt
        logger.info("\n=== Testing Login ===")
        logger.debug(f"Attempting login to {base_url}/api/v1/auth/login")
        logger.debug(f"Using credentials for user: {credentials['username']}@{credentials['domain']}")
        
        login_response = session.post(
            f"{base_url}/api/v1/auth/login",
            json=credentials,
            timeout=10  # Add timeout
        )
        pretty_print_request(login_response.request)
        
        logger.info(f"Login Status: {login_response.status_code}")
        logger.debug(f"Login Response Headers: {dict(login_response.headers)}")
        logger.debug(f"Login Response Body: {login_response.text}")
        
        if login_response.status_code != 200:
            logger.error(f"Login failed with status {login_response.status_code}")
            logger.error(f"Response: {login_response.text}")
            return False
            
        token_data = login_response.json()
        token = token_data['access_token']
        logger.info("Successfully obtained access token")
        
        # Step 2: Token analysis
        logger.info("\n=== Token Analysis ===")
        decoded = decode_token(token)
        logger.info("Decoded token payload:")
        logger.debug(json.dumps(decoded, indent=2))
        
        current_time = datetime.utcnow().timestamp()
        if isinstance(decoded, dict) and 'exp' in decoded:
            logger.info("Analyzing token expiration:")
            logger.debug(f"Current time (UTC): {current_time}")
            logger.debug(f"Token exp time: {decoded['exp']}")
            expiry_diff = decoded['exp'] - current_time
            logger.info(f"Token expires in: {expiry_diff/3600:.2f} hours")

        # Small delay to ensure server processing
        time.sleep(1)

        # Step 3: Token verification
        logger.info("\n=== Testing Token Verification ===")
        headers = {'Authorization': f'Bearer {token}'}
        logger.debug("Sending verification request...")
        
        verify_response = session.get(
            f"{base_url}/api/v1/auth/verify",
            headers=headers,
            timeout=10
        )
        pretty_print_request(verify_response.request)
        
        logger.info(f"Verification Status: {verify_response.status_code}")
        logger.debug(f"Verification Headers: {dict(verify_response.headers)}")
        logger.debug(f"Verification Body: {verify_response.text}")
        
        if verify_response.status_code != 200:
            logger.error("Token verification failed")
            try:
                error_detail = verify_response.json()
                logger.error(f"Error details: {json.dumps(error_detail, indent=2)}")
            except:
                logger.error("Could not parse error response")
            return False

        # Small delay before next request
        time.sleep(1)
        
        # Step 4: Protected endpoint test
        logger.info("\n=== Testing Protected Endpoint ===")
        logger.debug("Attempting to access protected endpoint...")
        
        test_response = session.get(
            f"{base_url}/api/v1/targets",
            headers=headers,
            timeout=10
        )
        pretty_print_request(test_response.request)
        
        logger.info(f"Protected Endpoint Status: {test_response.status_code}")
        logger.debug(f"Protected Endpoint Headers: {dict(test_response.headers)}")
        logger.debug(f"Protected Endpoint Body: {test_response.text}")
        
        if test_response.status_code != 200:
            logger.error("Protected endpoint test failed")
            try:
                error_detail = test_response.json()
                logger.error(f"Error details: {json.dumps(error_detail, indent=2)}")
            except:
                logger.error("Could not parse error response")
            return False
            
        return True

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: Could not connect to {base_url}")
        logger.error(f"Error details: {str(e)}")
        return False
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error: Request to {base_url} timed out")
        logger.error(f"Error details: {str(e)}")
        return False
    except Exception as e:
        logger.exception("Unexpected error during testing")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    base_url = "http://localhost:8000"
    credentials = {
        "username": "ShareGuardService",
        "domain": "shareguard.com",
        "password": "P(5$\\#SX07sj"
    }
    
    logger.info("Starting authentication test suite...")
    logger.info("-" * 50)
    
    try:
        # Check if server is running first
        requests.get(f"{base_url}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        logger.error(f"Could not connect to server at {base_url}")
        logger.error("Please ensure the server is running")
        sys.exit(1)
        
    success = test_token_lifecycle(base_url, credentials)
    
    logger.info("-" * 50)
    if success:
        logger.info("All tests passed successfully!")
        sys.exit(0)
    else:
        logger.error("Test suite failed!")
        sys.exit(1)