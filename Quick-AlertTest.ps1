<#
.SYNOPSIS
  Smoke-tests the ShareGuard alert pipeline:
    1. Confirms the backend is up
    2. Logs in (username / password / domain)
    3. Makes sure change-monitoring is running
    4. Verifies at least one active NEW_ACCESS alert config
    5. Creates a test ACL change, waits, then checks that:
         • the change was detected
         • an alert was generated
    6. Cleans up and prints a summary
#>

# ──────── Editable settings ────────
$BaseUrl     = 'http://localhost:5173'      # API base
$Username    = 'ShareGuardService'          # API / AD account
$Password    = 'Vn\2/YA/A954'               # keep backslash raw inside single quotes
$Domain      = 'WIN-I2VDDDLDOUA'                       # AD / tenant / “LOCAL”
$AclUser     = 'SHAREGUARD\hortiz'                # ← User that will receive the test ACL
$TestFolder  = "C:\ShareGuardTest\Test" -f (Get-Date)
$WaitSeconds = 15                           # how long to wait for detection
# ────────────────────────────────────

Write-Host "`nShareGuard Quick Alert Test" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

function Show-State ($msg, [bool]$ok) {
    if ($ok) { Write-Host "   [+] $msg" -ForegroundColor Green }
    else     { Write-Host "   [x] $msg" -ForegroundColor Red   }
}

# ── 1. Backend health ────────────────────────────────
Write-Host '1. Checking backend…' -ForegroundColor Green
try {
    Invoke-RestMethod "$BaseUrl/health" -TimeoutSec 5 -ErrorAction Stop | Out-Null
    Show-State 'Backend is running' $true
} catch {
    Show-State 'Backend is NOT running. Start it first.' $false
    return
}

# ── 2. Login ─────────────────────────────────────────
Write-Host '2. Authenticating…' -ForegroundColor Green
try {
    $body = @{
        username = $Username
        password = $Password
        domain   = $Domain
    } | ConvertTo-Json

    $token = (Invoke-RestMethod "$BaseUrl/api/v1/auth/login" `
              -Method Post -Body $body -ContentType 'application/json' `
              -ErrorAction Stop).access_token

    $Headers = @{ Authorization = "Bearer $token" }
    Show-State 'Login succeeded' $true
} catch {
    Show-State "Login failed: $_" $false
    return
}

# ── 3. Ensure monitoring is running ──────────────────
Write-Host '3. Verifying monitoring status…' -ForegroundColor Green
try {
    $status = Invoke-RestMethod "$BaseUrl/api/v1/alerts/monitoring/status" -Headers $Headers
    if (-not $status.change_monitoring_active) {
        Write-Host '   (re)starting change monitor…' -ForegroundColor Yellow
        Invoke-RestMethod "$BaseUrl/api/v1/alerts/monitoring/start" `
            -Method Post -Headers $Headers | Out-Null
        Start-Sleep -Seconds 2
    }
    Show-State 'Change-monitoring is active' $true
} catch {
    Show-State "Could not query/start monitor: $_" $false
}

# ── 4. Confirm alert configs ─────────────────────────
Write-Host '4. Looking for active NEW_ACCESS configurations…' -ForegroundColor Green
$newAccessConfigs = @()
try {
    $configs = Invoke-RestMethod "$BaseUrl/api/v1/alerts/configurations" -Headers $Headers
    $newAccessConfigs = $configs | Where-Object {
        $_.alert_type -eq 'new_access' -and $_.is_active
    }
    Show-State "$($newAccessConfigs.Count) active NEW_ACCESS configuration(s)" `
               ($newAccessConfigs.Count -gt 0)
} catch {
    Show-State "Could not fetch configurations: $_" $false
}

# ── 5. Create a test ACL change ──────────────────────
Write-Host '5. Creating test permission change…' -ForegroundColor Green
$recentChanges = @(); $recentAlerts = @()

try {
    # Create test folder
    New-Item -Path $TestFolder -ItemType Directory -Force | Out-Null
    Show-State "Created $TestFolder" $true

    # Add ACL rule for $AclUser
    $acl   = Get-Acl $TestFolder
    $rule  = New-Object System.Security.AccessControl.FileSystemAccessRule `
             ($AclUser,'FullControl','ContainerInherit,ObjectInherit','None','Allow')
    $acl.AddAccessRule($rule); Set-Acl $TestFolder $acl
    Show-State "Added FullControl for $AclUser" $true

    Write-Host "   Waiting $WaitSeconds s for detection…" -ForegroundColor Yellow
    1..$WaitSeconds | ForEach-Object { Write-Host -NoNewline '.'; Start-Sleep 1 }
    Write-Host ''

    # ---- Check recent changes ----
    Write-Host '6. Checking backend for detected changes…' -ForegroundColor Green
    $since          = (Get-Date).AddMinutes(-2)
    $changes        = Invoke-RestMethod "$BaseUrl/api/v1/alerts/changes/recent?hours=1" `
                       -Headers $Headers
    $recentChanges  = $changes | Where-Object {
        [datetime]$_.detected_time -gt $since
    }
    Show-State "$($recentChanges.Count) change(s) detected" `
               ($recentChanges.Count -gt 0)

    # ---- Check recent alerts ----
    Write-Host '7. Checking backend for generated alerts…' -ForegroundColor Green
    $alerts        = Invoke-RestMethod "$BaseUrl/api/v1/alerts?hours=1" -Headers $Headers
    $recentAlerts  = $alerts | Where-Object {
        [datetime]$_.created_at -gt $since
    }
    Show-State "$($recentAlerts.Count) alert(s) generated" `
               ($recentAlerts.Count -gt 0)

} catch {
    Show-State "Error during test: $_" $false
} finally {
    if (Test-Path $TestFolder) {
        Remove-Item $TestFolder -Recurse -Force
        Show-State 'Cleaned up test folder' $true
    }
}

# ── 8. Summary ───────────────────────────────────────
Write-Host "`nSummary" -ForegroundColor Cyan
Write-Host '-------'  -ForegroundColor Cyan

switch ($true) {
    { $recentChanges.Count -eq 0 } {
        Write-Host '[!] No permission changes were detected.' -ForegroundColor Yellow
        Write-Host '    › Is auditing enabled?  Run Enable-ShareGuardAuditing.ps1'
        Write-Host "    › Is '$TestFolder' inside the scan target list?"
        break
    }
    { $recentAlerts.Count -eq 0 } {
        Write-Host '[!] Changes detected but **no alerts** generated.' -ForegroundColor Yellow
        Write-Host '    › Check NEW_ACCESS alert configs / matching logic.'
        break
    }
    default {
        Write-Host '[+] Alert pipeline looks **healthy** — great!' -ForegroundColor Green
        Write-Host "    Detected $($recentChanges.Count) change(s) → $($recentAlerts.Count) alert(s)."
    }
}

Write-Host "`nSee logs in  logs\change_monitor_*.log  for details." -ForegroundColor Cyan
