<#
.SYNOPSIS
  Verifies that Windows auditing is configured as required by ShareGuard.

.DESCRIPTION
  1. Confirms that File-System auditing is enabled (Success & Failure).
  2. Checks the Security event-log size.
  3. Lists audit rules on test folders.
  4. (If run as Administrator) adds a broad audit rule to each test folder.
  5. Performs a create / modify-ACL / delete cycle to trigger events.
  6. Prints a concise remediation summary.
#>

# ----------------------  Settings  ----------------------
$TestPaths  = @(
  'C:\ShareGuardTest\HR',
  'C:\ShareGuardTest\Finance',
  'C:\ShareGuardTest\IT',
  'C:\ShareGuardTest\Public'
)
$MinLogSizeBytes = 100MB   # adjust if you need more history
# -------------------------------------------------------

Write-Host "`nShareGuard Windows Auditing Configuration Check" -ForegroundColor Cyan
Write-Host "=============================================`n" -ForegroundColor Cyan

# --- 0. Elevation check ------------------------------------------------------
$isAdmin = ([Security.Principal.WindowsPrincipal] `
           [Security.Principal.WindowsIdentity]::GetCurrent()
          ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "WARNING: run this script as Administrator for full functionality`n" -ForegroundColor Yellow
}

# Store compliance flags so the summary can’t throw later
$FileSystemAuditOK  = $false
$SecurityLogOK      = $false

# --- 1. File-System audit policy --------------------------------------------
Write-Host "1. Checking audit policy for *File System*…" -ForegroundColor Green
try {
    $auditLine = (& auditpol /get /subcategory:"File System" /r) |
                 Where-Object { $_ -match 'File System' }

    if ($auditLine) {
        # Collapse multiple spaces to a single comma → tokenize like CSV
        $parts = ($auditLine -replace '\s{2,}',',').Split(',')
        $inclusion = $parts[2].Trim()   # Success / Failure / No Auditing / -
        Write-Host "   Inclusion setting : $inclusion"

        if ($inclusion -match 'Success|Failure') {
            Write-Host "   ✔ File-System auditing is enabled`n" -ForegroundColor Green
            $FileSystemAuditOK = $true
        }
        else {
            Write-Host "   ✖ File-System auditing is *not* enabled!" -ForegroundColor Red
            Write-Host "     › Run:  auditpol /set /subcategory:'File System' /success:enable /failure:enable`n" -ForegroundColor Yellow
        }
    }
    else {
        throw "unexpected AuditPol output"
    }
}
catch {
    Write-Host "   ERROR: could not read audit policy – $_`n" -ForegroundColor Red
}

# --- 2. Security event log ---------------------------------------------------
Write-Host "2. Checking Security event-log settings…" -ForegroundColor Green
try {
    $secLog = Get-WinEvent -ListLog Security -ErrorAction Stop
    Write-Host "   Log enabled : $($secLog.IsEnabled)"
    Write-Host "   Max size    : {0:N1} MB" -f ($secLog.MaximumSizeInBytes/1MB)
    Write-Host "   Current size: {0:N1} MB" -f ($secLog.FileSize/1MB)

    if ($secLog.MaximumSizeInBytes -ge $MinLogSizeBytes) {
        Write-Host "   ✔ Log size is adequate`n" -ForegroundColor Green
        $SecurityLogOK = $true
    }
    else {
        Write-Host "   ✖ Log size is small – consider raising it" -ForegroundColor Yellow
        Write-Host "     › wevtutil sl Security /ms:$($MinLogSizeBytes)" -ForegroundColor Yellow
        Write-Host ""
    }
}
catch {
    Write-Host "   ERROR: could not query Security log – $_`n" -ForegroundColor Red
}

# --- 3. Audit rules on test folders -----------------------------------------
Write-Host "3. Checking audit rules on test folders…" -ForegroundColor Green
foreach ($path in $TestPaths) {
    if (Test-Path $path) {
        Write-Host "   $path"
        try {
            $acl = Get-Acl -Path $path        # no “-Audit” parameter
            if ($acl.Audit.Count) {
                Write-Host "     ✔ $($acl.Audit.Count) audit rule(s) defined" -ForegroundColor Green
                $acl.Audit | ForEach-Object {
                    Write-Host "       – $($_.IdentityReference) : $($_.FileSystemRights) ($($_.AuditFlags))" -ForegroundColor Gray
                }
            }
            else {
                Write-Host "     ✖ No audit rules found" -ForegroundColor Yellow
            }
        }
        catch { Write-Host "     ERROR: $_" -ForegroundColor Red }
    }
    else {
        Write-Host "   ✖ Path not found: $path" -ForegroundColor Yellow
    }
}
Write-Host ""

# --- 4. Optional: add broad audit rule --------------------------------------
if ($isAdmin) {
    Write-Host "4. Ensuring audit rules exist (Administrator)…" -ForegroundColor Green
    foreach ($path in $TestPaths | Where-Object { Test-Path $_ }) {
        try {
            $acl = Get-Acl $path
            $rule = New-Object System.Security.AccessControl.FileSystemAuditRule (
                'Everyone','FullControl',
                'ContainerInherit,ObjectInherit','None',
                'Success,Failure'
            )
            $acl.AddAuditRule($rule)
            Set-Acl -Path $path -AclObject $acl
            Write-Host "   ✔ Audit rule applied to $path" -ForegroundColor Green
        }
        catch { Write-Host "   ERROR: $path – $_" -ForegroundColor Red }
    }
    Write-Host ""
}
else {
    Write-Host "4. Skipping audit-rule setup (run as Administrator to enable) `n" -ForegroundColor Yellow
}

# --- 5. Trigger events -------------------------------------------------------
Write-Host "5. Generating test activity…" -ForegroundColor Green
$testFile = "C:\ShareGuardTest\Public\audit_test_{0:yyyyMMdd_HHmmss}.txt" -f (Get-Date)
try {
    'Test file for auditing' | Out-File -Encoding UTF8 -FilePath $testFile
    Write-Host "   ✔ Created $testFile" -ForegroundColor Green

    $acl = Get-Acl $testFile
    $perm = New-Object System.Security.AccessControl.FileSystemAccessRule (
        'Users','ReadAndExecute','Allow'
    )
    $acl.AddAccessRule($perm)
    Set-Acl $testFile $acl
    Write-Host "   ✔ Added Users Read&Execute" -ForegroundColor Green

    Remove-Item $testFile -Force
    Write-Host "   ✔ Deleted $testFile" -ForegroundColor Green
    Write-Host "   › These actions should appear in the Security log if auditing is active`n" -ForegroundColor Yellow
}
catch { Write-Host "   ERROR during test: $_`n" -ForegroundColor Red }

# --- 6. Summary --------------------------------------------------------------
Write-Host "`nSummary & Recommendations" -ForegroundColor Cyan
Write-Host "--------------------------" -ForegroundColor Cyan

$todo = @()
if (-not $FileSystemAuditOK) {
    $todo += "Enable File-System auditing:  auditpol /set /subcategory:'File System' /success:enable /failure:enable"
}
if (-not $SecurityLogOK) {
    $todo += "Increase Security log size (≥ $([math]::Round($MinLogSizeBytes/1MB)) MB):  wevtutil sl Security /ms:$MinLogSizeBytes"
}

if ($todo.Count) {
    Write-Host "⚠ Recommended actions:" -ForegroundColor Yellow
    $todo | ForEach-Object { Write-Host "  • $_" -ForegroundColor Yellow }
}
else {
    Write-Host "✔ Windows auditing appears correctly configured for ShareGuard" -ForegroundColor Green
}

Write-Host "`nRemember: start ShareGuard monitoring from its web interface (Monitoring → Start)." -ForegroundColor Cyan
