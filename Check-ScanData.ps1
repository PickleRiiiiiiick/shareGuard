#!/usr/bin/env pwsh

# Check for existing scan data in ShareGuard
$Token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6InNoYXJlZ3VhcmQuY29tXFxTaGFyZUd1YXJkU2VydmljZSIsImV4cCI6MTc1MTQxMjQ0NiwiaWF0IjoxNzUxMzI2MDQ2fQ.ipdR0P9Lr_zF65UUnK9_SbxshOIGVxaplS7nF1vzFgg"
$BaseURL = "http://localhost:8000/api/v1"

$headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

Write-Host "Checking ShareGuard scan data..."

# Check targets
Write-Host "`n1. Checking scan targets:"
try {
    $targets = Invoke-RestMethod -Uri "$BaseURL/targets/" -Headers $headers -Method Get
    Write-Host "✅ Targets found: $($targets.Count)"
    if ($targets.Count -gt 0) {
        $targets | ForEach-Object { Write-Host "  - $($_.path)" }
    }
} catch {
    Write-Host "❌ Could not fetch targets: $($_.Exception.Message)"
}

# Check recent scans (if endpoint exists)
Write-Host "`n2. Checking recent scans:"
try {
    $scans = Invoke-RestMethod -Uri "$BaseURL/scan/recent" -Headers $headers -Method Get
    Write-Host "✅ Recent scans found: $($scans.Count)"
} catch {
    Write-Host "ℹ️  Recent scans endpoint not available or no scans found"
}

Write-Host "`n=========================================="
Write-Host "Summary:"
Write-Host "- If you see targets above, try running a scan on them"
Write-Host "- If no targets, add some folders in the Targets page"
Write-Host "- After folder scan completes, run health scan"
Write-Host "=========================================="