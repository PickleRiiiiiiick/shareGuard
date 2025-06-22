# Test-SIDResolution.ps1
# Quick smoke-test for ShareGuard SID resolution (ASCII-safe)

<#
.SYNOPSIS
Verifies backend & frontend, runs debug script, prints summary.

.PARAMETER TestPath
Folder used by the Python debug helper. Default: C:\ShareGuardTest

.PARAMETER Verbose
Shows extra troubleshooting hints at the end of the run.
#>

param(
    [string]$TestPath = 'C:\ShareGuardTest',
    [switch]$Verbose
)

Write-Host 'ShareGuard SID Resolution Test' -ForegroundColor Cyan
Write-Host '================================'            -ForegroundColor Cyan
Write-Host "Test Path: $TestPath"                        -ForegroundColor Yellow
Write-Host ''

# ───────── helper functions ─────────

function Test-BackendRunning {
    try {
        Invoke-WebRequest -Uri 'http://localhost:8000/docs' -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop | Out-Null
        Write-Host 'OK    Backend is running'  -ForegroundColor Green
        return $true
    } catch {
        Write-Host 'FAIL  Backend is not running' -ForegroundColor Red
        Write-Host '      Run: .\start-backend.ps1' -ForegroundColor Yellow
        return $false
    }
}

function Test-FrontendRunning {
    try {
        Invoke-WebRequest -Uri 'http://localhost:5173' -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop | Out-Null
        Write-Host 'OK    Frontend is running' -ForegroundColor Green
        return $true
    } catch {
        Write-Host 'FAIL  Frontend is not running' -ForegroundColor Red
        Write-Host '      Run: .\start-frontend.ps1' -ForegroundColor Yellow
        return $false
    }
}

function Test-PythonDebugScript {
    Write-Host 'Running Python debug script…' -ForegroundColor Cyan

    if (-not (Test-Path $TestPath)) {
        Write-Host "Creating test directory: $TestPath" -ForegroundColor Yellow
        try { New-Item -Path $TestPath -ItemType Directory -Force | Out-Null }
        catch {
            Write-Host "FAIL  Could not create directory: $_" -ForegroundColor Red
            return $false
        }
    }

    try {
        $output = & python debug_sid_resolution.py $TestPath 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host 'OK    Python debug script completed' -ForegroundColor Green
        } else {
            Write-Host 'FAIL  Python debug script returned non-zero exit code' -ForegroundColor Red
        }
        Write-Host $output
        return ($LASTEXITCODE -eq 0)
    } catch {
        Write-Host "FAIL  Failed to run Python debug script: $_" -ForegroundColor Red
        return $false
    }
}

function Test-WebInterface {
    Write-Host 'Testing via web interface…' -ForegroundColor Cyan

    if ((Test-BackendRunning) -and (Test-FrontendRunning)) {
        Write-Host 'OK    Both backend and frontend are running' -ForegroundColor Green
        Write-Host 'You can now test SID resolution by:' -ForegroundColor Yellow
        Write-Host '  1. Open http://localhost:5173 in your browser'
        Write-Host '  2. Log in'
        Write-Host "  3. Go to Permissions page and select folder: $TestPath"
        Write-Host '  4. Click the armor icon to view ACLs'
        Write-Host "Expected result: actual user/group names instead of 'Unknown SID'"
        return $true
    } else {
        Write-Host 'FAIL  Backend or frontend not running' -ForegroundColor Red
        return $false
    }
}

# ───────── main flow ─────────

Write-Host 'Step 1: Checking service status…' -ForegroundColor Cyan
$backendRunning  = Test-BackendRunning
$frontendRunning = Test-FrontendRunning
Write-Host ''

Write-Host 'Step 2: Testing Python debug script…' -ForegroundColor Cyan
$pythonSuccess = Test-PythonDebugScript
Write-Host ''

Write-Host 'Step 3: Web-interface instructions…' -ForegroundColor Cyan
Test-WebInterface
Write-Host ''

# ───────── summary ─────────

Write-Host 'Test Summary:' -ForegroundColor Cyan
Write-Host '=============' -ForegroundColor Cyan
Write-Host ('Backend Running : {0}' -f (if ($backendRunning)  { 'OK' } else { 'FAIL' })) -ForegroundColor (if ($backendRunning)  { 'Green' } else { 'Red' })
Write-Host ('Frontend Running: {0}' -f (if ($frontendRunning) { 'OK' } else { 'FAIL' })) -ForegroundColor (if ($frontendRunning) { 'Green' } else { 'Red' })
Write-Host ('Python Debug    : {0}' -f (if ($pythonSuccess)   { 'OK' } else { 'FAIL' })) -ForegroundColor (if ($pythonSuccess)   { 'Green' } else { 'Red' })

Write-Host ''
Write-Host 'To start services if not running:' -ForegroundColor Yellow
Write-Host '  .\startProject.ps1'
Write-Host '  OR individually:'
Write-Host '  .\start-backend.ps1'
Write-Host '  .\start-frontend.ps1'

if ($Verbose) {
    Write-Host ''
    Write-Host 'Additional debugging options:' -ForegroundColor Cyan
    Write-Host '  • Check logs in the logs\ folder'
    Write-Host "  • Use API: GET /api/v1/folders/diagnose-sids?path=$TestPath"
    Write-Host '  • Run: python test_sid_via_api.py'
}
