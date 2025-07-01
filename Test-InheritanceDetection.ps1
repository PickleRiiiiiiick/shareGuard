# Test inheritance detection on Windows
Write-Host "Testing Inheritance Detection" -ForegroundColor Cyan
Write-Host ("=" * 60)

# Test folders
$testPaths = @(
    "C:\ShareGuardTest\Finance",
    "C:\ShareGuardTest\HR", 
    "C:\ShareGuardTest\IT"
)

foreach ($path in $testPaths) {
    Write-Host "`nChecking: $path" -ForegroundColor Yellow
    Write-Host ("-" * 40)
    
    if (Test-Path $path) {
        try {
            # Get ACL
            $acl = Get-Acl -Path $path
            
            # Check if inheritance is enabled
            $inheritanceEnabled = -not $acl.AreAccessRulesProtected
            
            Write-Host "  Inheritance Enabled: $inheritanceEnabled"
            Write-Host "  Owner: $($acl.Owner)"
            Write-Host "  Access Rules Count: $($acl.Access.Count)"
            
            # Count inherited vs explicit rules
            $inherited = ($acl.Access | Where-Object { $_.IsInherited }).Count
            $explicit = ($acl.Access | Where-Object { -not $_.IsInherited }).Count
            
            Write-Host "  Inherited Rules: $inherited"
            Write-Host "  Explicit Rules: $explicit"
            
            if (-not $inheritanceEnabled) {
                Write-Host "  WARNING: INHERITANCE IS DISABLED (Broken Inheritance)" -ForegroundColor Red
            }
        }
        catch {
            Write-Host "  Error: $_" -ForegroundColor Red
        }
    }
    else {
        Write-Host "  Path does not exist!" -ForegroundColor Red
    }
}

Write-Host "`n$('=' * 60)"
Write-Host "Now running Python scanner to compare results..."
Write-Host "$('=' * 60)"

# Activate virtual environment and run Python test
Push-Location $PSScriptRoot
if (Test-Path "venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
    python test_inheritance_detection.py
}
else {
    Write-Host "Virtual environment not found. Please run from project root." -ForegroundColor Red
}
Pop-Location