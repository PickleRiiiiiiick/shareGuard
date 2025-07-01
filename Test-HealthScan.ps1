# Test Health Scan Script

$BaseUrl = "http://localhost:8000"
$Token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6InNoYXJlZ3VhcmQuY29tXFxTaGFyZUd1YXJkU2VydmljZSIsImV4cCI6MTc1MTQ5Mzk2OCwiaWF0IjoxNzUxNDA3NTY4fQ.Fi9xgkQIhXjr4wsJE0T4N_rAymyGF-jlbwhBXit5sHg"

$Headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

Write-Host "Starting health scan for all configured targets..." -ForegroundColor Yellow

# Trigger health scan
$response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/health/scan" -Method POST -Headers $Headers
Write-Host "Health scan response:" -ForegroundColor Green
$response | ConvertTo-Json -Depth 10

# Wait for scan to complete
Write-Host "`nWaiting for scan to complete..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Get health score and issues
Write-Host "`n--- Health Score ---" -ForegroundColor Cyan
$scoreResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/health/score" -Method GET -Headers $Headers
$scoreResponse | ConvertTo-Json -Depth 10

Write-Host "`n--- Health Issues ---" -ForegroundColor Cyan
$issuesResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/health/issues" -Method GET -Headers $Headers
Write-Host "Total issues found: $($issuesResponse.total)" -ForegroundColor Green
Write-Host "Issues per page: $($issuesResponse.items.Count)" -ForegroundColor Green

if ($issuesResponse.items) {
    Write-Host "`nIssues by folder:" -ForegroundColor Yellow
    $folderIssues = @{}
    
    foreach ($issue in $issuesResponse.items) {
        $folder = $issue.path
        if (-not $folderIssues.ContainsKey($folder)) {
            $folderIssues[$folder] = @()
        }
        $folderIssues[$folder] += @{
            Type = $issue.issue_type
            Severity = $issue.severity
            Description = $issue.description
        }
    }
    
    foreach ($folder in $folderIssues.Keys) {
        Write-Host "`n$folder:" -ForegroundColor Magenta
        foreach ($issue in $folderIssues[$folder]) {
            $desc = if ($issue.Description.Length -gt 100) { $issue.Description.Substring(0, 100) + "..." } else { $issue.Description }
            Write-Host "  - [$($issue.Severity)] $($issue.Type): $desc" -ForegroundColor White
        }
    }
}

# Get debug paths info
Write-Host "`n--- Debug Paths Info ---" -ForegroundColor Cyan
$pathsResponse = Invoke-RestMethod -Uri "$BaseUrl/api/v1/health/debug/paths" -Method GET -Headers $Headers
Write-Host "Total scan results: $($pathsResponse.total_scan_results)" -ForegroundColor Green
Write-Host "Total active targets: $($pathsResponse.total_active_targets)" -ForegroundColor Green
Write-Host "Unique paths for health scan: $($pathsResponse.total_unique_paths)" -ForegroundColor Green
Write-Host "Scan targets:" -ForegroundColor Yellow
$pathsResponse.scan_targets | ConvertTo-Json -Depth 10