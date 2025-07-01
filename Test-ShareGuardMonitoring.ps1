# Test-ShareGuardMonitoring.ps1
# Script to test ShareGuard monitoring and alerting system

Write-Host "`nShareGuard Monitoring System Test" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Test API endpoints
$baseUrl = "http://localhost:8000/api/v1"
$token = $null

# 1. Check if backend is running
Write-Host "1. Checking backend availability..." -ForegroundColor Green
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "   ✓ Backend is running: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Backend is not running! Start it with .\start-backend.ps1" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. Login to get token
Write-Host "2. Authenticating..." -ForegroundColor Green
try {
    $loginBody = @{
        username = "admin"
        password = "admin"
    } | ConvertTo-Json
    
    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
    $token = $loginResponse.access_token
    Write-Host "   ✓ Authentication successful" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Authentication failed: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Create headers with auth token
$headers = @{
    "Authorization" = "Bearer $token"
}

# 3. Check monitoring status
Write-Host "3. Checking monitoring status..." -ForegroundColor Green
try {
    $status = Invoke-RestMethod -Uri "$baseUrl/alerts/monitoring/status" -Method Get -Headers $headers
    Write-Host "   Change Monitoring: $(if($status.change_monitoring_active){'Active'}else{'Inactive'})" -ForegroundColor $(if($status.change_monitoring_active){'Green'}else{'Yellow'})
    Write-Host "   Group Monitoring: $(if($status.group_monitoring_active){'Active'}else{'Inactive'})" -ForegroundColor $(if($status.group_monitoring_active){'Green'}else{'Yellow'})
    
    if ($status.notification_service_stats) {
        Write-Host "   Active Connections: $($status.notification_service_stats.active_connections)" -ForegroundColor White
        Write-Host "   Unique Users: $($status.notification_service_stats.unique_users)" -ForegroundColor White
        Write-Host "   Notifications Sent: $($status.notification_service_stats.notifications_sent)" -ForegroundColor White
    }
    
    if ($status.group_monitoring_stats) {
        Write-Host "   Groups Monitored: $($status.group_monitoring_stats.groups_monitored)" -ForegroundColor White
        Write-Host "   Users Tracked: $($status.group_monitoring_stats.users_tracked)" -ForegroundColor White
    }
} catch {
    Write-Host "   ✗ Failed to get monitoring status: $_" -ForegroundColor Red
}
Write-Host ""

# 4. Check active scan targets
Write-Host "4. Checking active scan targets..." -ForegroundColor Green
try {
    $targets = Invoke-RestMethod -Uri "$baseUrl/targets" -Method Get -Headers $headers
    $activeTargets = $targets | Where-Object { $_.scan_frequency -ne 'disabled' }
    
    if ($activeTargets.Count -eq 0) {
        Write-Host "   ✗ No active scan targets found!" -ForegroundColor Red
        Write-Host "   Create scan targets in the web UI first" -ForegroundColor Yellow
    } else {
        Write-Host "   ✓ Found $($activeTargets.Count) active scan target(s):" -ForegroundColor Green
        foreach ($target in $activeTargets) {
            Write-Host "     - $($target.path) [$($target.scan_frequency)]" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "   ✗ Failed to get scan targets: $_" -ForegroundColor Red
}
Write-Host ""

# 5. Check alert configurations
Write-Host "5. Checking alert configurations..." -ForegroundColor Green
try {
    $configs = Invoke-RestMethod -Uri "$baseUrl/alerts/configurations" -Method Get -Headers $headers
    $activeConfigs = $configs | Where-Object { $_.is_active }
    
    if ($activeConfigs.Count -eq 0) {
        Write-Host "   ✗ No active alert configurations found!" -ForegroundColor Red
        Write-Host "   Create alert configurations in the web UI" -ForegroundColor Yellow
    } else {
        Write-Host "   ✓ Found $($activeConfigs.Count) active alert configuration(s):" -ForegroundColor Green
        foreach ($config in $activeConfigs) {
            Write-Host "     - $($config.name) [$($config.alert_type)] Severity: $($config.severity)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "   ✗ Failed to get alert configurations: $_" -ForegroundColor Red
}
Write-Host ""

# 6. Start monitoring if not active
if (-not $status.change_monitoring_active) {
    Write-Host "6. Starting monitoring..." -ForegroundColor Green
    try {
        $startResult = Invoke-RestMethod -Uri "$baseUrl/alerts/monitoring/start" -Method Post -Headers $headers
        Write-Host "   ✓ $($startResult.message)" -ForegroundColor Green
        Start-Sleep -Seconds 2
    } catch {
        Write-Host "   ✗ Failed to start monitoring: $_" -ForegroundColor Red
    }
} else {
    Write-Host "6. Monitoring is already active" -ForegroundColor Green
}
Write-Host ""

# 7. Test WebSocket connection
Write-Host "7. Testing WebSocket connection..." -ForegroundColor Green
Write-Host "   Note: WebSocket test requires manual verification in browser console" -ForegroundColor Yellow
Write-Host "   Open browser DevTools and check for WebSocket errors" -ForegroundColor Yellow
Write-Host ""

# 8. Create a test change
Write-Host "8. Creating a test permission change..." -ForegroundColor Green
$testPath = "C:\ShareGuardTest\Public\alert_test_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
try {
    # Create file
    "Test file for alert system" | Out-File -FilePath $testPath
    Write-Host "   ✓ Created test file: $testPath" -ForegroundColor Green
    
    # Add permission
    $acl = Get-Acl -Path $testPath
    $permission = New-Object System.Security.AccessControl.FileSystemAccessRule(
        "Everyone",
        "FullControl",
        "Allow"
    )
    $acl.SetAccessRule($permission)
    Set-Acl -Path $testPath -AclObject $acl
    Write-Host "   ✓ Added Everyone:FullControl permission" -ForegroundColor Green
    
    Write-Host "   Waiting 10 seconds for change detection..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Check for recent changes
    $recentChanges = Invoke-RestMethod -Uri "$baseUrl/alerts/changes/recent?hours=1" -Method Get -Headers $headers
    if ($recentChanges.Count -gt 0) {
        Write-Host "   ✓ Detected $($recentChanges.Count) recent change(s)" -ForegroundColor Green
        $latestChange = $recentChanges[0]
        Write-Host "     - Type: $($latestChange.change_type)" -ForegroundColor Gray
        Write-Host "     - Time: $($latestChange.detected_time)" -ForegroundColor Gray
    } else {
        Write-Host "   ⚠ No changes detected yet" -ForegroundColor Yellow
    }
    
    # Check for alerts
    $alerts = Invoke-RestMethod -Uri "$baseUrl/alerts?hours=1" -Method Get -Headers $headers
    if ($alerts.Count -gt 0) {
        Write-Host "   ✓ Generated $($alerts.Count) alert(s)" -ForegroundColor Green
        $latestAlert = $alerts[0]
        Write-Host "     - Message: $($latestAlert.message)" -ForegroundColor Gray
        Write-Host "     - Severity: $($latestAlert.severity)" -ForegroundColor Gray
    } else {
        Write-Host "   ⚠ No alerts generated yet" -ForegroundColor Yellow
    }
    
    # Cleanup
    Remove-Item -Path $testPath -Force -ErrorAction SilentlyContinue
    Write-Host "   ✓ Cleaned up test file" -ForegroundColor Green
    
} catch {
    Write-Host "   ✗ Error during test: $_" -ForegroundColor Red
}
Write-Host ""

# Summary
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "=======" -ForegroundColor Cyan

$issues = @()

if (-not $status.change_monitoring_active) {
    $issues += "Change monitoring is not active"
}

if ($activeTargets.Count -eq 0) {
    $issues += "No active scan targets configured"
}

if ($activeConfigs.Count -eq 0) {
    $issues += "No alert configurations created"
}

if ($status.notification_service_stats.active_connections -eq 0) {
    $issues += "No WebSocket connections active (check browser console)"
}

if ($issues.Count -eq 0) {
    Write-Host "✓ Monitoring system appears to be working correctly" -ForegroundColor Green
} else {
    Write-Host "Issues found:" -ForegroundColor Yellow
    foreach ($issue in $issues) {
        Write-Host "  - $issue" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Troubleshooting tips:" -ForegroundColor Cyan
Write-Host "1. Ensure Windows auditing is enabled (run .\Enable-ShareGuardAuditing.ps1 as Admin)" -ForegroundColor White
Write-Host "2. Restart the backend after making configuration changes" -ForegroundColor White
Write-Host "3. Check browser console for WebSocket errors" -ForegroundColor White
Write-Host "4. Verify scan targets are set to 'Active' in the web UI" -ForegroundColor White
Write-Host "5. Create alert configurations for the types of changes you want to monitor" -ForegroundColor White