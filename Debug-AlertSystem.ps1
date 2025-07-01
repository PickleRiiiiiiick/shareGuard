<#
.SYNOPSIS
  Debug ShareGuard’s change-monitor / alert pipeline.

.DESCRIPTION
  1. Shows the last log file with colour-coded highlights.
  2. Runs a tiny Python snippet to query recent DB activity.
  3. Creates a test ACL change, tails the log for 10 s, then cleans up.
#>

param(
    [ValidateSet('DEBUG','INFO','WARN','ERROR')]
    [string]$LogLevel = 'DEBUG'
)

Write-Host "`nShareGuard Alert System Debugger" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# 0. Prep
# ---------------------------------------------------------------------------
$env:LOG_LEVEL = $LogLevel
$LogFolder     = "logs"                   # relative to script root
$TempPy        = Join-Path $env:TEMP "sg_db_check_$([guid]::NewGuid()).py"

# ---------------------------------------------------------------------------
# 1. Log inspection
# ---------------------------------------------------------------------------
Write-Host '1. Checking log files…' -ForegroundColor Green
$latestLog = $null
if (Test-Path $LogFolder) {
    $latestLog = Get-ChildItem -Path $LogFolder -Filter '*.log' |
                 Sort-Object LastWriteTime -Descending |
                 Select-Object -First 1
}
if ($latestLog) {
    Write-Host "   Latest log : $($latestLog.Name)" -ForegroundColor White
    Write-Host '   Showing last 20 change_monitor entries:' -ForegroundColor Cyan

    Get-Content $latestLog.FullName |
        Select-String 'change_monitor' |
        Select-Object -Last 20 |
        ForEach-Object {
            switch -Regex ($_.Line) {
                'ERROR'   { Write-Host "   $_" -ForegroundColor Red }
                'WARNING' { Write-Host "   $_" -ForegroundColor Yellow }
                'INFO.*detected|INFO.*Generated|INFO.*Created alert' {
                            Write-Host "   $_" -ForegroundColor Green }
                default   { Write-Host "   $_" -ForegroundColor Gray }
            }
        }
} else {
    Write-Host '   No log directory or .log files found.' -ForegroundColor Red
}
Write-Host ''

# ---------------------------------------------------------------------------
# 2. Database snapshot (via Python)
# ---------------------------------------------------------------------------
Write-Host '2. Checking database for recent activity…' -ForegroundColor Green
@"
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
sys.path.append('src')            # project source
from src.db.database import DATABASE_URL

engine = create_engine(DATABASE_URL, future=True)

def run(q, header):
    print(f"\n{header}")
    with engine.connect() as c:
        rows = c.execute(text(q)).fetchall()
        if not rows:
            print("  (no rows)")
        return rows

# --- 1. Scan jobs ---------------------------------------------------------
run("""
    SELECT id, scan_type, status, start_time, end_time, parameters
    FROM   scan_jobs
    WHERE  scan_type = 'change_detection'
    ORDER  BY start_time DESC
    LIMIT  5
""", "Recent Scan Jobs:")

# --- 2. Permission changes ------------------------------------------------
run("""
    SELECT id, change_type, detected_time, current_state
    FROM   permission_changes
    ORDER  BY detected_time DESC
    LIMIT  10
""", "Recent Permission Changes:")

# --- 3. Alerts ------------------------------------------------------------
run("""
    SELECT a.id, a.severity, a.message, a.created_at, ac.alert_type
    FROM   alerts           AS a
    LEFT JOIN alert_configurations ac ON ac.id = a.config_id
    ORDER  BY a.created_at DESC
    LIMIT  10
""", "Recent Alerts:")

# --- 4. Active alert configs ---------------------------------------------
run("""
    SELECT id, name, alert_type, severity
    FROM   alert_configurations
    WHERE  is_active = 1
""", "Active Alert Configurations:")
"@ | Out-File -Encoding UTF8 -FilePath $TempPy

try { python $TempPy }
catch { Write-Host "   (Python error) $_" -ForegroundColor Red }
finally { Remove-Item $TempPy -ErrorAction SilentlyContinue }

Write-Host ''

# ---------------------------------------------------------------------------
# 3. Live test (ACL change)
# ---------------------------------------------------------------------------
Write-Host '3. Creating test ACL change…' -ForegroundColor Green
$testFolder = "C:\ShareGuardTest\HR\debug_test_$(Get-Date -f 'yyyyMMddHHmmss')"

try {
    New-Item -Path $testFolder -ItemType Directory -Force | Out-Null
    Write-Host "   [+] Created $testFolder"

    $acl = Get-Acl $testFolder
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule `
        ('Guest','ReadAndExecute',
         'ContainerInherit,ObjectInherit','None','Allow')
    $acl.AddAccessRule($rule)
    Set-Acl $testFolder $acl
    Write-Host '   [+] Added Guest:ReadAndExecute'

    Write-Host '   Waiting 10 s for monitor to pick up change…' -ForegroundColor Yellow

    $printed = @{}            # avoids duplicate lines
    $end = (Get-Date).AddSeconds(10)
    while (Get-Date -lt $end) {
        # Refresh latest log in case rotation happened
        if (Test-Path $LogFolder) {
            $latestLog = Get-ChildItem $LogFolder -Filter '*.log' |
                         Sort-Object LastWriteTime -Descending |
                         Select-Object -First 1
        }
        if ($latestLog) {
            Get-Content $latestLog.FullName -Tail 50 |
                Select-String 'change_monitor|notification_service|alert' |
                Select-String 'detected|Generated|Created|Processing|Matching' |
                ForEach-Object {
                    $txt = $_.Line.Trim()
                    if (-not $printed.ContainsKey($txt)) {
                        $printed[$txt] = $true
                        switch -Regex ($txt) {
                            'ERROR' { Write-Host "   LOG: $txt" -ForegroundColor Red }
                            'Generated.*alert|Created alert' {
                                      Write-Host "   LOG: $txt" -ForegroundColor Green }
                            default { Write-Host "   LOG: $txt" -ForegroundColor Gray }
                        }
                    }
                }
        }
        Start-Sleep -Milliseconds 500
    }

} catch {
    Write-Host "   [x] Error during test: $_" -ForegroundColor Red
} finally {
    if (Test-Path $testFolder) {
        Remove-Item $testFolder -Recurse -Force
        Write-Host "   [+] Cleaned up test folder"
    }
}

# ---------------------------------------------------------------------------
# 4. Tips
# ---------------------------------------------------------------------------
Write-Host "`nDebugging Tips:"         -ForegroundColor Cyan
Write-Host " 1. Make sure monitoring is *running* in the web UI."
Write-Host " 2. Confirm C:\\ShareGuardTest\\HR is inside the scan target list."
Write-Host " 3. Look for 'permission_added' events in the log."
Write-Host " 4. Check alert configs for the 'new_access' rule."
Write-Host " 5. Any log lines in RED need attention."

