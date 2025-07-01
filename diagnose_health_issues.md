# ShareGuard Health Page Issues - Diagnostic Guide

Based on the analysis, here are the identified issues and step-by-step fixes:

## Issues Identified

### 1. ✅ **Fixed: Button Positioning**
- **Problem**: The "Run New Scan" button was hidden behind the fixed navbar
- **Fix Applied**: Added `pt-20` to the main content in `DashboardLayout.tsx`
- **Status**: Fixed

### 2. **Authentication Token Missing**
- **Problem**: Frontend health API requests are being sent without authentication headers
- **Root Cause**: User might not be properly logged in, or token is expired
- **Evidence**: Backend logs show "No Authorization header" for health endpoints

### 3. **Database Tables Missing**
- **Problem**: Health-related database tables might not exist
- **Evidence**: The system needs tables like `health_scans`, `issues`, `health_metrics`, `health_score_history`

### 4. **CSV Export 422 Error**
- **Problem**: Export endpoint returns 422 (Unprocessable Content)
- **Root Cause**: Either authentication or parameter validation issues

## Step-by-Step Fixes

### Step 1: Check Authentication Status
1. Open browser developer tools (F12)
2. Go to Application tab > Local Storage
3. Check if there's an `auth_token` entry
4. If missing or you see login issues, try logging out and back in

### Step 2: Check Login Credentials
The system requires Windows domain authentication with these fields:
- **Username**: Windows username (e.g., "ShareGuardService")
- **Domain**: Windows domain (e.g., "shareguard.com" or "WIN-I2VDDDLDOUA")
- **Password**: Windows password

**To find your domain name:**
```powershell
# In PowerShell on Windows
echo $env:USERDOMAIN
```

### Step 3: Initialize Database Tables
Run this in PowerShell on the Windows machine where ShareGuard is installed:
```powershell
cd C:\ShareGuard
.\venv\Scripts\activate
$env:PYTHONPATH = "C:\ShareGuard\src"
$env:USE_SQLITE = "true"
$env:SQLITE_PATH = "shareguard.db"
python init_health_tables.py
```

### Step 4: Test Health Endpoints
After fixing authentication and tables, test the endpoints:
```bash
# Replace YOUR_TOKEN with actual token from browser
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/health/score
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/health/issues
```

### Step 5: Alternative Quick Test
If you can access other parts of ShareGuard (like Targets or Scan), but only Health fails:

1. **Check browser console**: Look for specific error messages
2. **Check network tab**: See if requests are being made and what responses are returned
3. **Check backend logs**: Look for health-specific errors in `logs/` directory

## Expected Results After Fixes

1. **Button visibility**: "Run New Scan" button should be clearly visible and clickable
2. **Authentication**: Health API requests should include `Authorization: Bearer ...` headers
3. **Health score**: Should display actual data instead of "No health data available"
4. **CSV export**: Should download a CSV file without 422 errors

## Debug Commands

### Check if backend is running:
```bash
curl http://localhost:8000/docs
```

### Check recent auth logs:
```bash
tail -20 logs/auth_middleware_20250630.log
```

### Check database tables (if using SQLite):
```bash
sqlite3 shareguard.db ".tables" | grep -i health
```

## Additional Notes

- The health system requires existing scan data to analyze
- Run a regular folder scan first before running health scans
- Health tables need to be created separately from main application tables
- Authentication uses Windows domain credentials, not local ShareGuard accounts

## Contact Information
If issues persist after following these steps, check:
1. Backend server logs in `logs/` directory
2. Browser developer console for JavaScript errors
3. Network requests in browser dev tools to see specific API failures