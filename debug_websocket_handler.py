#!/usr/bin/env python3
"""Debug WebSocket handler with real token"""

import socket
import base64
import urllib.parse
import sqlite3

def get_valid_token_from_db():
    """Get a valid token from the database"""
    try:
        conn = sqlite3.connect('shareguard.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT token FROM auth_sessions 
            WHERE is_active = 1 
            ORDER BY created_at DESC 
            LIMIT 1;
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
    except:
        pass
    return None

def test_websocket_with_real_token():
    """Test WebSocket with a real token from the database"""
    print("Testing WebSocket with real database token...")
    
    # Get valid token from database (same one browser is using)
    token = get_valid_token_from_db()
    if not token:
        print("❌ No valid token found in database")
        return
    
    print(f"✓ Got token from database: {token[:50]}...")
    
    host = "localhost"
    port = 8000
    
    ws_key = base64.b64encode(b'1234567890123456').decode('utf-8')
    params = urllib.parse.urlencode({
        "token": token,
        "filters": "{}",
        "user_id": "test_user"
    })
    
    handshake = f"""GET /api/v1/alerts/notifications?{params} HTTP/1.1\r
Host: {host}:{port}\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Key: {ws_key}\r
Sec-WebSocket-Version: 13\r
Origin: http://localhost:5174\r
User-Agent: ShareGuard-Debug/1.0\r
\r
"""
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15)
        sock.connect((host, port))
        
        print("✓ TCP connection established")
        print("Sending WebSocket handshake...")
        
        sock.send(handshake.encode())
        
        # Read response
        response = b""
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                break
            response += chunk
            if b"\r\n\r\n" in response:
                break
                
        response_text = response.decode('utf-8', errors='ignore')
        
        print("Response received:")
        print("-" * 50)
        print(response_text)
        print("-" * 50)
        
        if "101 Switching Protocols" in response_text:
            print("\n🎉 WebSocket handshake SUCCESSFUL!")
            
            # Try to read WebSocket messages
            print("Waiting for WebSocket messages...")
            try:
                sock.settimeout(10)
                
                # Read initial connection message
                data = sock.recv(1024)
                if data:
                    print(f"✓ Received WebSocket data: {len(data)} bytes")
                    
                    # Parse WebSocket frame (simplified)
                    if len(data) >= 2:
                        opcode = data[0] & 0x0F
                        payload_len = data[1] & 0x7F
                        
                        if opcode == 1 and payload_len < 126:  # Text frame
                            payload = data[2:2+payload_len]
                            try:
                                text = payload.decode('utf-8')
                                print(f"✓ WebSocket message: {text}")
                            except:
                                print(f"✓ WebSocket binary data")
                        elif opcode == 8:  # Close frame
                            if payload_len >= 2:
                                close_code = (data[2] << 8) | data[3]
                                print(f"✗ WebSocket closed with code: {close_code}")
                                if close_code == 1008:
                                    print("   Reason: Authentication required/failed")
                                elif close_code == 1011:
                                    print("   Reason: Internal server error")
                            else:
                                print("✗ WebSocket closed without code")
                                
            except socket.timeout:
                print("⚠ No WebSocket messages received (timeout)")
                
        elif "403" in response_text:
            print("\n✗ 403 Forbidden - Still failing")
        elif "401" in response_text:
            print("\n✗ 401 Unauthorized - Auth issue")
        elif "400" in response_text:
            print("\n✗ 400 Bad Request - Protocol issue")
        else:
            print("\n? Unexpected response")
            
        sock.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    print("ShareGuard WebSocket Handler Debug")
    print("=" * 40)
    
    test_websocket_with_real_token()
    
    print("\n" + "=" * 40)
    print("Debug completed!")