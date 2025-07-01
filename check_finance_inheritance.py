import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6InNoYXJlZ3VhcmQuY29tXFxTaGFyZUd1YXJkU2VydmljZSIsImV4cCI6MTc1MTQ5Mzk2OCwiaWF0IjoxNzUxNDA3NTY4fQ.Fi9xgkQIhXjr4wsJE0T4N_rAymyGF-jlbwhBXit5sHg"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Check Finance folder scan data
path = "C:\\ShareGuardTest\\Finance"
encoded_path = "C%3A%5CShareGuardTest%5CFinance"

print(f"Checking scan data for: {path}")
response = requests.get(f"{BASE_URL}/api/v1/health/debug/scan-data/{encoded_path}", headers=headers)

if response.status_code == 200:
    data = response.json()
    print(f"\nScan found: {data.get('has_stored_scan')}")
    print(f"Success: {data.get('success')}")
    
    # Check if inheritance_enabled field exists
    perms_data = data.get('permissions_data', {})
    print(f"\nChecking for inheritance_enabled field...")
    print(f"Has inheritance_enabled field: {data.get('has_inheritance_enabled_field')}")
    print(f"Inheritance enabled value: {data.get('inheritance_enabled_value')}")
    
    # Check in the actual permissions structure
    if 'permissions' in perms_data:
        perms = perms_data.get('permissions', {})
        if 'inheritance_enabled' in perms:
            print(f"Found inheritance_enabled in permissions: {perms['inheritance_enabled']}")
        else:
            print("inheritance_enabled NOT found in permissions structure")
            
    # Pretty print the permissions_data_keys
    print(f"\nPermissions data keys: {data.get('permissions_data_keys', [])}")
    
    # Check if we need to rescan
    print("\n--- Performing fresh scan to check current scanner output ---")
    response = requests.post(f"{BASE_URL}/api/v1/health/debug/fresh-scan?path={encoded_path}", headers=headers)
    if response.status_code == 200:
        fresh_data = response.json()
        print(f"Fresh scan success: {fresh_data.get('scan_success')}")
        print(f"Inheritance enabled: {fresh_data.get('inheritance_enabled')}")
        print(f"Issues found: {fresh_data.get('raw_issues_found')}")
        print(f"Significant issues: {fresh_data.get('significant_issues_found')}")
        if fresh_data.get('issues_details'):
            print("\nIssue details:")
            for issue in fresh_data['issues_details']:
                print(f"  - Type: {issue.get('type')}, Severity: {issue.get('severity')}")
                print(f"    Title: {issue.get('title')}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)