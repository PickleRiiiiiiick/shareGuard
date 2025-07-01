#!/usr/bin/env python3
"""
Update test scripts to use the correct Windows domain
"""
import socket

# Get the Windows computer name
computer_name = socket.gethostname()
print(f"Windows computer name: {computer_name}")

# Update test_auth.py
with open('test_auth.py', 'r') as f:
    content = f.read()

# Replace the domain in test_auth.py
content = content.replace('"shareguard.com"', f'"{computer_name}"')

with open('test_auth.py', 'w') as f:
    f.write(content)

print(f"Updated test_auth.py to use domain: {computer_name}")

# Update Quick-AlertTest.ps1
with open('Quick-AlertTest.ps1', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Replace the domain in PowerShell script
content = content.replace("'shareguard.com'", f"'{computer_name}'")

with open('Quick-AlertTest.ps1', 'w', encoding='utf-8-sig') as f:
    f.write(content)

print(f"Updated Quick-AlertTest.ps1 to use domain: {computer_name}")

print("\nTest scripts have been updated to use the correct Windows domain!")
print(f"You can now login with:")
print(f"  Username: ShareGuardService")
print(f"  Domain: {computer_name}")
print(f"  Password: <Windows password for ShareGuardService>")