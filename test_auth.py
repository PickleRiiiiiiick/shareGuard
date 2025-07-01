# test_auth.py
import requests
import json
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger('auth_test')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('logs/auth_test.log')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

BASE_URL = "http://localhost:8000/api/v1"

def test_auth():
    auth_data = {
        "username": "ShareGuardService",
        "domain": "WIN-I2VDDDLDOUA",
        "password": r"P(5$\#SX07sj"
    }
    
    try:
        logger.info("Attempting login...")
        logger.debug(f"Auth data: {auth_data}")
        
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=auth_data
        )
        
        logger.debug(f"Login response status: {response.status_code}")
        logger.debug(f"Login response headers: {dict(response.headers)}")
        logger.debug(f"Login response body: {response.text}")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            token = response.json()['access_token']
            logger.info("Login successful!")
            logger.debug(f"Full token: {token}")
            print("\nLogin successful!")
            print(f"Token: {token[:20]}...")
            return token
        else:
            logger.error(f"Login failed: {response.text}")
            print("\nLogin failed!")
            print(f"Error: {response.json()}")
            return None
            
    except Exception as e:
        logger.exception("Error during authentication")
        print(f"Error during authentication: {str(e)}")
        return None

def test_protected_endpoint(token):
    try:
        logger.info("Testing protected endpoint access...")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        logger.debug(f"Request headers: {headers}")
        
        params = {
            'skip': 0,
            'limit': 10
        }
        logger.debug(f"Request params: {params}")
        
        response = requests.get(
            f"{BASE_URL}/targets",
            headers=headers,
            params=params
        )
        
        logger.debug(f"Protected endpoint response status: {response.status_code}")
        logger.debug(f"Protected endpoint response headers: {dict(response.headers)}")
        logger.debug(f"Protected endpoint response body: {response.text}")
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            logger.error(f"Protected endpoint error: {response.text}")
            print(f"Response: {response.text}")
        
    except Exception as e:
        logger.exception("Error accessing protected endpoint")
        print(f"Error accessing protected endpoint: {str(e)}")

def test_token_verification(token):
    try:
        logger.info("Testing token verification...")
        headers = {
            'Authorization': f'Bearer {token}'
        }
        logger.debug(f"Verification request headers: {headers}")
        
        response = requests.get(
            f"{BASE_URL}/auth/verify",
            headers=headers
        )
        
        logger.debug(f"Verification response status: {response.status_code}")
        logger.debug(f"Verification response headers: {dict(response.headers)}")
        logger.debug(f"Verification response body: {response.text}")
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Token verified successfully")
            print(f"Response: {response.json()}")
        else:
            logger.error(f"Token verification failed: {response.text}")
            print(f"Token verification failed: {response.json()}")
        
    except Exception as e:
        logger.exception("Error during token verification")
        print(f"Error during token verification: {str(e)}")

def test_logout(token):
    try:
        logger.info("Testing logout...")
        headers = {
            'Authorization': f'Bearer {token}'
        }
        logger.debug(f"Logout request headers: {headers}")
        
        response = requests.post(
            f"{BASE_URL}/auth/logout",
            headers=headers
        )
        
        logger.debug(f"Logout response status: {response.status_code}")
        logger.debug(f"Logout response headers: {dict(response.headers)}")
        logger.debug(f"Logout response body: {response.text}")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        logger.info("Verifying token is invalidated...")
        verify_response = requests.get(
            f"{BASE_URL}/auth/verify",
            headers=headers
        )
        logger.debug(f"Post-logout verification status: {verify_response.status_code}")
        print(f"Verification after logout status: {verify_response.status_code}")
        
    except Exception as e:
        logger.exception("Error during logout")
        print(f"Error during logout: {str(e)}")

if __name__ == "__main__":
    print("Starting authentication test suite...")
    print("-" * 50)
    
    # Test full authentication flow
    token = test_auth()
    
    if token:
        test_protected_endpoint(token)
        test_token_verification(token)
        test_logout(token)
    
    print("-" * 50)
    print("Test suite completed!")