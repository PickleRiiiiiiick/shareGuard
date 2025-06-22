# Simple SID Resolution Test Script
param([string]$TestPath = "C:\ShareGuardTest")

Write-Host "ShareGuard SID Resolution Test" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Check if backend is running
Write-Host "Step 1: Checking backend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ Backend is running" -ForegroundColor Green
    $backendRunning = $true
} catch {
    Write-Host "❌ Backend is not running" -ForegroundColor Red
    Write-Host "   Start it with: .\start-backend.ps1" -ForegroundColor Yellow
    $backendRunning = $false
}

# Test 2: Check if frontend is running
Write-Host "Step 2: Checking frontend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ Frontend is running" -ForegroundColor Green
    $frontendRunning = $true
} catch {
    Write-Host "❌ Frontend is not running" -ForegroundColor Red
    Write-Host "   Start it with: .\start-frontend.ps1" -ForegroundColor Yellow
    $frontendRunning = $false
}

# Test 3: Try to run Python debug script
Write-Host "Step 3: Testing Python debug script..." -ForegroundColor Yellow

# Create test directory if it doesn't exist
if (-not (Test-Path $TestPath)) {
    Write-Host "Creating test directory: $TestPath" -ForegroundColor Yellow
    New-Item -Path $TestPath -ItemType Directory -Force | Out-Null
}

try {
    Write-Host "Running debug script on: $TestPath" -ForegroundColor White
    $output = & python debug_sid_resolution.py $TestPath 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Python debug script completed" -ForegroundColor Green
        Write-Host "Output:" -ForegroundColor White
        Write-Host $output
        $pythonSuccess = $true
    } else {
        Write-Host "❌ Python debug script failed" -ForegroundColor Red
        Write-Host $output
        $pythonSuccess = $false
    }
} catch {
    Write-Host "❌ Could not run Python debug script: $_" -ForegroundColor Red
    $pythonSuccess = $false
}

# Summary
Write-Host ""
Write-Host "Test Summary:" -ForegroundColor Cyan
Write-Host "=============" -ForegroundColor Cyan
Write-Host "Backend Running: $(if ($backendRunning) { '✓' } else { '❌' })" -ForegroundColor $(if ($backendRunning) { 'Green' } else { 'Red' })
Write-Host "Frontend Running: $(if ($frontendRunning) { '✓' } else { '❌' })" -ForegroundColor $(if ($frontendRunning) { 'Green' } else { 'Red' })
Write-Host "Python Debug: $(if ($pythonSuccess) { '✓' } else { '❌' })" -ForegroundColor $(if ($pythonSuccess) { 'Green' } else { 'Red' })

Write-Host ""
if ($backendRunning -and $frontendRunning) {
    Write-Host "🎉 Ready to test! Open http://localhost:5173 in your browser" -ForegroundColor Green
    Write-Host "1. Log in to the application" -ForegroundColor White
    Write-Host "2. Go to Permissions page" -ForegroundColor White
    Write-Host "3. Select folder: $TestPath" -ForegroundColor White
    Write-Host "4. Click the armor icon to view ACLs" -ForegroundColor White
    Write-Host "5. Look for actual names instead of 'Unknown SID'" -ForegroundColor White
} else {
    Write-Host "To start services:" -ForegroundColor Yellow
    Write-Host "  .\startProject.ps1" -ForegroundColor White
}