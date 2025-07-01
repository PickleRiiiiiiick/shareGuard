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

print("Starting health scan for all configured targets...")

# Trigger health scan
response = requests.post(f"{BASE_URL}/api/v1/health/scan", headers=headers)
print(f"Health scan response: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Wait for scan to complete
print("\nWaiting for scan to complete...")
time.sleep(10)

# Get health score and issues
print("\n--- Health Score ---")
response = requests.get(f"{BASE_URL}/api/v1/health/score", headers=headers)
print(json.dumps(response.json(), indent=2))

print("\n--- Health Issues ---")
response = requests.get(f"{BASE_URL}/api/v1/health/issues", headers=headers)
issues_data = response.json()
print(f"Total issues found: {issues_data.get('total', 0)}")
print(f"Issues per page: {len(issues_data.get('issues', []))}")

if issues_data.get('issues'):
    print("\nIssues by folder:")
    folder_issues = {}
    for issue in issues_data['issues']:
        folder = issue.get('path', 'Unknown')
        if folder not in folder_issues:
            folder_issues[folder] = []
        folder_issues[folder].append({
            'type': issue.get('issue_type'),
            'severity': issue.get('severity'),
            'description': issue.get('description')
        })
    
    for folder, issues in folder_issues.items():
        print(f"\n{folder}:")
        for issue in issues:
            print(f"  - [{issue['severity']}] {issue['type']}: {issue['description'][:100]}...")

# Get debug paths info
print("\n--- Debug Paths Info ---")
response = requests.get(f"{BASE_URL}/api/v1/health/debug/paths", headers=headers)
paths_data = response.json()
print(f"Total scan results: {paths_data.get('total_scan_results', 0)}")
print(f"Total active targets: {paths_data.get('total_active_targets', 0)}")
print(f"Unique paths for health scan: {paths_data.get('total_unique_paths', 0)}")
print(f"Scan targets: {json.dumps(paths_data.get('scan_targets', []), indent=2)}")