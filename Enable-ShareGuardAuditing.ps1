# Enable-ShareGuardAuditing.ps1
# Script to enable Windows auditing for ShareGuard

param(
    [switch]$Force
)

# Check if running as administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "`nShareGuard Windows Auditing Setup" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# 1. Enable File System auditing
Write-Host "1. Enabling File System auditing..." -ForegroundColor Green
try {
    $result = auditpol /set /subcategory:"File System" /success:enable /failure:enable
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ File System auditing enabled successfully" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Failed to enable File System auditing" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ✗ Error: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. Increase Security log size to 500 MB
Write-Host "2. Configuring Security event log..." -ForegroundColor Green
try {
    # Set max size to 500 MB
    wevtutil sl Security /ms:524288000
    Write-Host "   ✓ Security log max size set to 500 MB" -ForegroundColor Green
    
    # Set retention policy to overwrite as needed
    wevtutil sl Security /rt:false
    Write-Host "   ✓ Security log retention set to overwrite as needed" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Error configuring Security log: $_" -ForegroundColor Red
}
Write-Host ""

# 3. Create missing test folders
Write-Host "3. Creating test folders..." -ForegroundColor Green
$testPaths = @(
    "C:\ShareGuardTest",
    "C:\ShareGuardTest\HR",
    "C:\ShareGuardTest\Finance",
    "C:\ShareGuardTest\IT",
    "C:\ShareGuardTest\Public"
)

foreach ($path in $testPaths) {
    if (-not (Test-Path $path)) {
        try {
            New-Item -Path $path -ItemType Directory -Force | Out-Null
            Write-Host "   ✓ Created: $path" -ForegroundColor Green
        } catch {
            Write-Host "   ✗ Failed to create: $path - $_" -ForegroundColor Red
        }
    } else {
        Write-Host "   • Exists: $path" -ForegroundColor Gray
    }
}
Write-Host ""

# 4. Apply audit rules to all test folders
Write-Host "4. Applying audit rules to test folders..." -ForegroundColor Green
foreach ($path in $testPaths) {
    if (Test-Path $path) {
        try {
            $acl = Get-Acl $path
            
            # Create audit rule for Everyone - all access types
            $auditRule = New-Object System.Security.AccessControl.FileSystemAuditRule(
                "Everyone",
                "FullControl",
                "ContainerInherit,ObjectInherit",
                "None",
                "Success,Failure"
            )
            
            # Add the audit rule
            $acl.AddAuditRule($auditRule)
            
            # Apply the ACL
            Set-Acl -Path $path -AclObject $acl
            Write-Host "   ✓ Audit rule applied to: $path" -ForegroundColor Green
            
        } catch {
            Write-Host "   ✗ Error setting audit rule on ${path}: $_" -ForegroundColor Red
        }
    }
}
Write-Host ""

# 5. Verify configuration
Write-Host "5. Verifying configuration..." -ForegroundColor Green

# Check audit policy
$auditLine = (& auditpol /get /subcategory:"File System" /r) | Where-Object { $_ -match 'File System' }
if ($auditLine) {
    $parts = ($auditLine -replace '\s{2,}',',').Split(',')
    $inclusion = $parts[2].Trim()
    if ($inclusion -match 'Success|Failure') {
        Write-Host "   ✓ File System auditing is enabled: $inclusion" -ForegroundColor Green
    } else {
        Write-Host "   ✗ File System auditing is NOT enabled" -ForegroundColor Red
    }
}

# Check Security log
$secLog = Get-WinEvent -ListLog Security -ErrorAction SilentlyContinue
if ($secLog) {
    Write-Host "   ✓ Security log size: $([math]::Round($secLog.MaximumSizeInBytes / 1MB, 0)) MB" -ForegroundColor Green
}
Write-Host ""

# 6. Test file creation
Write-Host "6. Testing audit system..." -ForegroundColor Green
$testFile = "C:\ShareGuardTest\Public\audit_test_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
try {
    # Create test file
    "Audit test file created at $(Get-Date)" | Out-File -FilePath $testFile
    Write-Host "   ✓ Created test file: $testFile" -ForegroundColor Green
    
    # Modify permissions
    $acl = Get-Acl -Path $testFile
    $permission = New-Object System.Security.AccessControl.FileSystemAccessRule(
        "Users",
        "FullControl",
        "Allow"
    )
    $acl.SetAccessRule($permission)
    Set-Acl -Path $testFile -AclObject $acl
    Write-Host "   ✓ Modified permissions on test file" -ForegroundColor Green
    
    # Remove test file
    Remove-Item -Path $testFile -Force
    Write-Host "   ✓ Removed test file" -ForegroundColor Green
    
} catch {
    Write-Host "   ✗ Error during test: $_" -ForegroundColor Red
}
Write-Host ""

# Summary
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "=======" -ForegroundColor Cyan
Write-Host "✓ Windows File System auditing is now enabled" -ForegroundColor Green
Write-Host "✓ Security event log configured for 500 MB" -ForegroundColor Green
Write-Host "✓ Test folders created with audit rules" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart the ShareGuard backend (close and reopen PowerShell window)" -ForegroundColor Yellow
Write-Host "2. Go to ShareGuard web interface" -ForegroundColor Yellow
Write-Host "3. Navigate to Monitoring page and click 'Start Monitoring'" -ForegroundColor Yellow
Write-Host "4. Make permission changes on monitored folders" -ForegroundColor Yellow
Write-Host "5. Wait 5 seconds for changes to be detected" -ForegroundColor Yellow
Write-Host ""
Write-Host "The alerting system should now work properly!" -ForegroundColor Green