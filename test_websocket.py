#!/usr/bin/env python3
"""Test script for WebSocket alerts connection"""

import asyncio
import websockets
import json
import sys
from urllib.parse import urlencode

# Configuration
BASE_URL = "ws://localhost:8000/api/v1/alerts/notifications"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6InNoYXJlZ3VhcmQuY29tXFxTaGFyZUd1YXJkU2VydmljZSIsImV4cCI6MTc1MTY2NjQwMSwiaWF0IjoxNzUxNTgwMDAxfQ.rkiw2vL9jxiFhIedmBpvyQxsKHE2JcjdvHvgYf5ehvo"

async def test_websocket_connection():
    """Test WebSocket connection with different configurations"""
    
    print("Testing WebSocket connection to alerts endpoint...")
    print(f"Base URL: {BASE_URL}")
    print(f"Token: {TOKEN[:20]}...")
    print("-" * 50)
    
    # Test 1: Basic connection with token in query params
    try:
        print("\nTest 1: Connecting with token in query params...")
        params = {"filters": "{}", "token": TOKEN}
        url = f"{BASE_URL}?{urlencode(params)}"
        
        async with websockets.connect(url) as websocket:
            print("✓ Connected successfully!")
            
            # Send a test message
            test_message = json.dumps({"type": "ping"})
            await websocket.send(test_message)
            print(f"Sent: {test_message}")
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"Received: {response}")
            except asyncio.TimeoutError:
                print("No response received within 5 seconds")
            
            # Keep connection open for a bit to receive any messages
            print("\nListening for messages (10 seconds)...")
            try:
                async for message in asyncio.wait_for(
                    websocket.__aiter__().__anext__(), 
                    timeout=10.0
                ):
                    print(f"Message: {message}")
            except asyncio.TimeoutError:
                print("No additional messages received")
                
    except Exception as e:
        print(f"✗ Connection failed: {type(e).__name__}: {e}")
    
    # Test 2: Try with Authorization header
    try:
        print("\n\nTest 2: Connecting with Authorization header...")
        headers = {"Authorization": f"Bearer {TOKEN}"}
        params = {"filters": "{}"}
        url = f"{BASE_URL}?{urlencode(params)}"
        
        async with websockets.connect(url, extra_headers=headers) as websocket:
            print("✓ Connected successfully with Authorization header!")
            
            # Wait for initial message
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"Initial message: {response}")
            except asyncio.TimeoutError:
                print("No initial message received")
                
    except Exception as e:
        print(f"✗ Connection failed: {type(e).__name__}: {e}")
    
    # Test 3: Try without authentication
    try:
        print("\n\nTest 3: Connecting without authentication...")
        params = {"filters": "{}"}
        url = f"{BASE_URL}?{urlencode(params)}"
        
        async with websockets.connect(url) as websocket:
            print("✓ Connected without authentication (unexpected!)")
            
    except Exception as e:
        print(f"✗ Connection failed (expected): {type(e).__name__}: {e}")

async def test_http_endpoint():
    """Test if the HTTP endpoint is accessible"""
    import aiohttp
    
    print("\n\nTesting HTTP endpoint availability...")
    
    async with aiohttp.ClientSession() as session:
        # Test root endpoint
        try:
            async with session.get("http://localhost:8000/") as response:
                print(f"Root endpoint: {response.status}")
        except Exception as e:
            print(f"Root endpoint failed: {e}")
        
        # Test API docs
        try:
            async with session.get("http://localhost:8000/docs") as response:
                print(f"API docs endpoint: {response.status}")
        except Exception as e:
            print(f"API docs failed: {e}")
        
        # Test alerts endpoint (HTTP)
        try:
            headers = {"Authorization": f"Bearer {TOKEN}"}
            async with session.get("http://localhost:8000/api/v1/alerts", headers=headers) as response:
                print(f"Alerts HTTP endpoint: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"Alerts count: {len(data) if isinstance(data, list) else 'N/A'}")
        except Exception as e:
            print(f"Alerts HTTP endpoint failed: {e}")

if __name__ == "__main__":
    print("ShareGuard WebSocket Alert Connection Test")
    print("=" * 50)
    
    # Run tests
    asyncio.run(test_websocket_connection())
    asyncio.run(test_http_endpoint())
    
    print("\n" + "=" * 50)
    print("Test completed!")