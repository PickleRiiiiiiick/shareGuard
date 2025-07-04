#!/usr/bin/env python3
"""Comprehensive WebSocket authentication debugging"""

import asyncio
import websockets
import json
import jwt
import sys
import logging
from datetime import datetime
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/api/v1/alerts/notifications"

async def test_websocket_auth_flow():
    """Test complete WebSocket authentication flow"""
    
    print("=== ShareGuard WebSocket Authentication Debug ===\n")
    
    # Step 1: Get authentication token
    print("[1] Getting authentication token...")
    try:
        login_response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "username": "ShareGuardService",
                "password": "ShareGuardService"
            }
        )
        
        if login_response.status_code != 200:
            print(f"✗ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return
            
        token_data = login_response.json()
        token = token_data["access_token"]
        print(f"✓ Got token: {token[:50]}...")
        
        # Decode token to check contents
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            print(f"✓ Token decoded successfully:")
            print(f"   - Subject: {decoded.get('sub')}")
            print(f"   - Name: {decoded.get('name')}")
            print(f"   - Expires: {datetime.fromtimestamp(decoded.get('exp'))}")
            print(f"   - Issued: {datetime.fromtimestamp(decoded.get('iat'))}")
        except Exception as e:
            print(f"⚠ Token decode warning: {e}")
        
    except Exception as e:
        print(f"✗ Failed to get token: {e}")
        return
    
    print("\n[2] Testing WebSocket connection...")
    
    # Test different connection methods
    test_methods = [
        ("Token in query params", f"{WS_URL}?token={token}&filters={{}}"),
        ("Token in header", WS_URL, {"Authorization": f"Bearer {token}"}),
        ("Token in subprotocol", WS_URL, None, [f"bearer-{token}"])
    ]
    
    for method_name, url, headers, subprotocols in [
        (m[0], m[1], m[2] if len(m) > 2 else None, m[3] if len(m) > 3 else None) 
        for m in test_methods
    ]:
        print(f"\n[3] Testing: {method_name}")
        print(f"   URL: {url[:100]}...")
        
        try:
            # Build connection parameters
            connect_params = {"uri": url}
            if headers:
                connect_params["extra_headers"] = headers
            if subprotocols:
                connect_params["subprotocols"] = subprotocols
            
            # Try to connect
            async with websockets.connect(**connect_params) as websocket:
                print(f"✓ WebSocket connected successfully!")
                
                # Wait for initial message
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"✓ Received initial message: {data.get('type')}")
                    
                    # Send a ping
                    await websocket.send(json.dumps({"type": "ping"}))
                    print("✓ Sent ping")
                    
                    # Wait for pong
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    pong_data = json.loads(response)
                    print(f"✓ Received response: {pong_data.get('type')}")
                    
                    # Test complete
                    print(f"✓ {method_name} works correctly!")
                    
                except asyncio.TimeoutError:
                    print("⚠ Timeout waiting for messages")
                except Exception as e:
                    print(f"⚠ Error during communication: {e}")
                
        except websockets.exceptions.InvalidStatusCode as e:
            print(f"✗ Connection failed with status {e.status_code}")
            if hasattr(e, 'headers'):
                print(f"   Headers: {dict(e.headers)}")
        except Exception as e:
            print(f"✗ Connection error: {type(e).__name__}: {e}")
    
    print("\n[4] Testing direct HTTP call to WebSocket endpoint...")
    try:
        # Try GET request to WebSocket endpoint
        response = requests.get(
            f"{BASE_URL}/api/v1/alerts/notifications",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"   HTTP GET status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n[5] Checking service status...")
    try:
        status_response = requests.get(
            f"{BASE_URL}/api/v1/alerts/websocket-debug",
            headers={"Authorization": f"Bearer {token}"}
        )
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"✓ Service status:")
            print(f"   - WebSocket stats: {status.get('websocket_stats')}")
            print(f"   - Service running: {status.get('notification_service_running')}")
        else:
            print(f"✗ Failed to get status: {status_response.status_code}")
    except Exception as e:
        print(f"✗ Error getting status: {e}")

async def test_raw_websocket():
    """Test raw WebSocket connection without authentication"""
    print("\n\n[6] Testing raw WebSocket connection (no auth)...")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("⚠ Connected without authentication!")
            message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            print(f"   Received: {message}")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"✓ Connection properly rejected with status {e.status_code}")
    except Exception as e:
        print(f"✓ Connection failed as expected: {type(e).__name__}")

async def test_websocket_with_logging():
    """Test WebSocket with detailed logging"""
    print("\n\n[7] Testing with detailed WebSocket logging...")
    
    # Get fresh token
    try:
        login_response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "username": "ShareGuardService",
                "password": "ShareGuardService"
            }
        )
        token = login_response.json()["access_token"]
    except Exception as e:
        print(f"Failed to get token: {e}")
        return
    
    # Enable websockets debug logging
    websockets_logger = logging.getLogger('websockets')
    websockets_logger.setLevel(logging.DEBUG)
    websockets_logger.addHandler(logging.StreamHandler())
    
    url = f"{WS_URL}?token={token}&filters={{}}"
    print(f"Connecting to: {url}")
    
    try:
        async with websockets.connect(url) as websocket:
            print("Connected!")
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("ShareGuard WebSocket Authentication Debug Tool")
    print("=" * 50)
    
    # Run tests
    asyncio.run(test_websocket_auth_flow())
    asyncio.run(test_raw_websocket())
    asyncio.run(test_websocket_with_logging())
    
    print("\n" + "=" * 50)
    print("Debug session completed!")