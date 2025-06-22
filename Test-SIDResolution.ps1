# Test-SIDResolution.ps1
# PowerShell script to test SID resolution fixes

param(
    [string]$TestPath = "C:\ShareGuardTest",
    [switch]$Verbose
)

Write-Host "ShareGuard SID Resolution Test" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Test Path: $TestPath" -ForegroundColor Yellow
Write-Host ""

# Function to test if backend is running
function Test-BackendRunning {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Backend is running" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "❌ Backend is not running" -ForegroundColor Red
        Write-Host "   Run: .\start-backend.ps1" -ForegroundColor Yellow
        return $false
    }
}

# Function to test if frontend is running
function Test-FrontendRunning {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Frontend is running" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "❌ Frontend is not running" -ForegroundColor Red
        Write-Host "   Run: .\start-frontend.ps1" -ForegroundColor Yellow
        return $false
    }
}

# Function to run Python debug script
function Test-PythonDebugScript {
    Write-Host "Running Python debug script..." -ForegroundColor Cyan
    
    if (Test-Path $TestPath) {
        try {
            $output = python debug_sid_resolution.py $TestPath 2>&1
            Write-Host $output
            return $true
        }
        catch {
            Write-Host "❌ Failed to run Python debug script: $_" -ForegroundColor Red
            return $false
        }
    }
    else {
        Write-Host "❌ Test path does not exist: $TestPath" -ForegroundColor Red
        Write-Host "   Creating test directory..." -ForegroundColor Yellow
        
        try {
            New-Item -Path $TestPath -ItemType Directory -Force | Out-Null
            Write-Host "✓ Created test directory: $TestPath" -ForegroundColor Green
            
            # Run the debug script on the new directory
            $output = python debug_sid_resolution.py $TestPath 2>&1
            Write-Host $output
            return $true
        }
        catch {
            Write-Host "❌ Failed to create test directory: $_" -ForegroundColor Red
            return $false
        }
    }
}

# Function to test via web interface
function Test-WebInterface {
    Write-Host "Testing via web interface..." -ForegroundColor Cyan
    
    if ((Test-BackendRunning) -and (Test-FrontendRunning)) {
        Write-Host "✓ Both backend and frontend are running" -ForegroundColor Green
        Write-Host "You can now test SID resolution by:" -ForegroundColor Yellow
        Write-Host "1. Opening http://localhost:5173 in your browser" -ForegroundColor White
        Write-Host "2. Logging in" -ForegroundColor White
        Write-Host "3. Going to Permissions page" -ForegroundColor White
        Write-Host "4. Selecting folder: $TestPath" -ForegroundColor White
        Write-Host "5. Clicking the armor icon to view ACLs" -ForegroundColor White
        Write-Host ""
        Write-Host "Expected result: You should see actual user/group names instead of 'Unknown SID'" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "❌ Backend or frontend not running" -ForegroundColor Red
        return $false
    }
}

# Main execution
Write-Host "Step 1: Checking service status..." -ForegroundColor Cyan
$backendRunning = Test-BackendRunning
$frontendRunning = Test-FrontendRunning
Write-Host ""

Write-Host "Step 2: Testing Python debug script..." -ForegroundColor Cyan
$pythonSuccess = Test-PythonDebugScript
Write-Host ""

Write-Host "Step 3: Web interface test instructions..." -ForegroundColor Cyan
Test-WebInterface
Write-Host ""

# Summary
Write-Host "Test Summary:" -ForegroundColor Cyan
Write-Host "=============" -ForegroundColor Cyan
Write-Host "Backend Running: $(if ($backendRunning) { '✓' } else { '❌' })" -ForegroundColor $(if ($backendRunning) { 'Green' } else { 'Red' })
Write-Host "Frontend Running: $(if ($frontendRunning) { '✓' } else { '❌' })" -ForegroundColor $(if ($frontendRunning) { 'Green' } else { 'Red' })
Write-Host "Python Debug: $(if ($pythonSuccess) { '✓' } else { '❌' })" -ForegroundColor $(if ($pythonSuccess) { 'Green' } else { 'Red' })

Write-Host ""
Write-Host "To start services if not running:" -ForegroundColor Yellow
Write-Host "  .\startProject.ps1" -ForegroundColor White
Write-Host "  OR separately:" -ForegroundColor White
Write-Host "  .\start-backend.ps1" -ForegroundColor White
Write-Host "  .\start-frontend.ps1" -ForegroundColor White

if ($Verbose) {
    Write-Host ""
    Write-Host "Additional debugging options:" -ForegroundColor Cyan
    Write-Host "- Check logs in logs/ directory" -ForegroundColor White
    Write-Host "- Use API endpoint: GET /api/v1/folders/diagnose-sids?path=$TestPath" -ForegroundColor White
    Write-Host "- Run: python test_sid_via_api.py" -ForegroundColor White
}