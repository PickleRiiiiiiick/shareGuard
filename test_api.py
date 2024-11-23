import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    # Step 1: Login and get token
    login_data = {
        "username": "ShareGuardService",
        "domain": "shareguard.com",
        "password": "P(5$\\#SX07sj"
    }
    
    print("1. Logging in to get token...")
    login_response = requests.post(
        f"{base_url}/api/v1/auth/login",
        json=login_data
    )
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return
        
    # Extract token from login response
    token = login_response.json()['access_token']
    print(f"Login successful! Token obtained.")
    
    # Set up headers for authenticated requests
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # Step 2: Test count endpoint
    print("\n2. Testing count endpoint...")
    count_response = requests.get(
        f"{base_url}/api/v1/targets/count",
        headers=headers
    )
    print(f"Count response: {count_response.text}")
    
    # Step 3: Test paginated list
    print("\n3. Testing paginated list...")
    list_response = requests.get(
        f"{base_url}/api/v1/targets?skip=0&limit=10&sort_by=name",
        headers=headers
    )
    print(f"List response status: {list_response.status_code}")
    
    if list_response.status_code == 200:
        targets = list_response.json()
        print(f"\nRetrieved {len(targets)} targets:")
        for target in targets:
            print(f"- {target['name']} ({target['path']})")
    else:
        print(f"List request failed: {list_response.text}")

if __name__ == "__main__":
    test_api()