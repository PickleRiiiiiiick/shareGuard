import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6InNoYXJlZ3VhcmQuY29tXFxTaGFyZUd1YXJkU2VydmljZSIsImV4cCI6MTc1MTQ5Mzk2OCwiaWF0IjoxNzUxNDA3NTY4fQ.Fi9xgkQIhXjr4wsJE0T4N_rAymyGF-jlbwhBXit5sHg"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

print("=== Testing Complete Flow ===")

# 1. Check current Finance folder data
print("\n1. Checking current Finance folder scan data...")
path = "C:\\ShareGuardTest\\Finance"
encoded_path = "C%3A%5CShareGuardTest%5CFinance"

response = requests.get(f"{BASE_URL}/api/v1/health/debug/scan-data/{encoded_path}", headers=headers)
if response.status_code == 200:
    data = response.json()
    permissions = data.get('permissions_data', {}).get('permissions', {})
    print(f"Current inheritance_enabled: {permissions.get('inheritance_enabled', 'NOT FOUND')}")
else:
    print(f"Error getting scan data: {response.status_code}")

# 2. Perform fresh scan to update data
print("\n2. Performing fresh scan of Finance folder...")
response = requests.post(f"{BASE_URL}/api/v1/health/debug/fresh-scan?path={encoded_path}", headers=headers)
if response.status_code == 200:
    fresh_data = response.json()
    print(f"Fresh scan inheritance_enabled: {fresh_data.get('inheritance_enabled', 'NOT FOUND')}")
    print(f"Issues found: {fresh_data.get('raw_issues_found', 0)}")
    print(f"Significant issues: {fresh_data.get('significant_issues_found', 0)}")
    if fresh_data.get('issues_details'):
        for issue in fresh_data['issues_details']:
            print(f"  - {issue.get('type')}: {issue.get('title')} (Risk: {issue.get('risk_score', 0)})")
else:
    print(f"Error in fresh scan: {response.status_code}")

# 3. Trigger health scan
print("\n3. Triggering health scan...")
response = requests.post(f"{BASE_URL}/api/v1/health/scan", headers=headers)
if response.status_code == 200:
    scan_data = response.json()
    print(f"Health scan started for {len(scan_data.get('target_paths', []))} paths")
    
    # Wait for completion
    print("Waiting 15 seconds for scan completion...")
    time.sleep(15)
    
    # 4. Check health score
    print("\n4. Checking health score...")
    response = requests.get(f"{BASE_URL}/api/v1/health/score", headers=headers)
    if response.status_code == 200:
        score_data = response.json()
        print(f"Health score: {score_data.get('score', 'N/A')}")
        print(f"Total issues: {score_data.get('issues', {}).get('total', 0)}")
        issue_types = score_data.get('issue_types', {})
        for issue_type, count in issue_types.items():
            if count > 0:
                print(f"  - {issue_type}: {count}")
    
    # 5. Get detailed issues
    print("\n5. Getting detailed issues...")
    response = requests.get(f"{BASE_URL}/api/v1/health/issues?limit=50", headers=headers)
    if response.status_code == 200:
        issues_data = response.json()
        print(f"Issues returned: {len(issues_data.get('issues', []))}")
        
        if issues_data.get('issues'):
            print("\nDetailed issues:")
            for issue in issues_data['issues']:
                print(f"  Path: {issue.get('path')}")
                print(f"  Type: {issue.get('type')} | Severity: {issue.get('severity')}")
                print(f"  Title: {issue.get('title')}")
                print(f"  Risk Score: {issue.get('risk_score')}")
                print(f"  Description: {issue.get('description', '')[:100]}...")
                print("  ---")
        else:
            print("No issues returned in the response")
            
        # Check if there's an error
        if 'error' in issues_data:
            print(f"Error in issues response: {issues_data['error']}")
            
else:
    print(f"Error starting health scan: {response.status_code}")

print("\n=== Test Complete ===")