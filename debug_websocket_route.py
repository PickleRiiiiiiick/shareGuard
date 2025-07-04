#!/usr/bin/env python3
"""Debug WebSocket route registration"""

import urllib.request
import json

def check_openapi_routes():
    """Check if WebSocket route is registered in OpenAPI"""
    print("Checking OpenAPI schema for WebSocket routes...")
    
    try:
        req = urllib.request.Request("http://localhost:8000/openapi.json")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
        # Look for WebSocket routes
        paths = data.get('paths', {})
        
        print("\nRegistered API paths:")
        for path, methods in paths.items():
            if 'alerts' in path:
                print(f"  {path}: {list(methods.keys())}")
        
        # Check specifically for the notifications endpoint
        notifications_path = "/api/v1/alerts/notifications"
        if notifications_path in paths:
            print(f"\n✓ Found notifications endpoint: {paths[notifications_path]}")
        else:
            print(f"\n✗ Notifications endpoint not found in OpenAPI")
            
        # Check all paths containing 'websocket' or 'notification'
        ws_paths = [p for p in paths.keys() if 'websocket' in p.lower() or 'notification' in p.lower()]
        if ws_paths:
            print(f"\nWebSocket/notification paths: {ws_paths}")
        else:
            print("\nNo WebSocket/notification paths found")
            
    except Exception as e:
        print(f"Error checking OpenAPI: {e}")

def test_websocket_options():
    """Test OPTIONS request to WebSocket endpoint"""
    print("\n\nTesting OPTIONS request to WebSocket endpoint...")
    
    try:
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/alerts/notifications",
            method="OPTIONS"
        )
        req.add_header("Origin", "http://localhost:5173")
        req.add_header("Access-Control-Request-Method", "GET")
        req.add_header("Access-Control-Request-Headers", "upgrade,connection,sec-websocket-key,sec-websocket-version")
        
        with urllib.request.urlopen(req) as response:
            print(f"OPTIONS response: {response.status}")
            headers = dict(response.headers)
            for key, value in headers.items():
                if 'access-control' in key.lower() or 'cors' in key.lower():
                    print(f"  {key}: {value}")
                    
    except urllib.error.HTTPError as e:
        print(f"OPTIONS failed: {e.code} - {e.reason}")
        
    except Exception as e:
        print(f"OPTIONS error: {e}")

def test_websocket_get():
    """Test regular GET request to WebSocket endpoint"""
    print("\n\nTesting GET request to WebSocket endpoint...")
    
    try:
        req = urllib.request.Request("http://localhost:8000/api/v1/alerts/notifications")
        with urllib.request.urlopen(req) as response:
            print(f"GET response: {response.status}")
            content = response.read().decode()
            print(f"Content: {content[:200]}...")
            
    except urllib.error.HTTPError as e:
        print(f"GET failed: {e.code} - {e.reason}")
        try:
            error_content = e.read().decode()
            print(f"Error content: {error_content}")
        except:
            pass
            
    except Exception as e:
        print(f"GET error: {e}")

if __name__ == "__main__":
    print("ShareGuard WebSocket Route Debug")
    print("=" * 40)
    
    check_openapi_routes()
    test_websocket_options()
    test_websocket_get()
    
    print("\n" + "=" * 40)
    print("Debug completed!")