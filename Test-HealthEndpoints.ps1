#!/usr/bin/env pwsh

# Test ShareGuard Health Endpoints
# This PowerShell script tests the health endpoints with proper authentication

$BaseURL = "http://localhost:8000/api/v1"
$Token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwibmFtZSI6InNoYXJlZ3VhcmQuY29tXFxTaGFyZUd1YXJkU2VydmljZSIsImV4cCI6MTc1MTQxMjQ0NiwiaWF0IjoxNzUxMzI2MDQ2fQ.ipdR0P9Lr_zF65UUnK9_SbxshOIGVxaplS7nF1vzFgg"

Write-Host "=========================================="
Write-Host "ShareGuard Health API Test (PowerShell)"
Write-Host "=========================================="

# Test 1: Health Score
Write-Host "`n1. Testing Health Score Endpoint..."
try {
    $headers = @{
        "Authorization" = "Bearer $Token"
        "Content-Type" = "application/json"
    }
    
    $response = Invoke-RestMethod -Uri "$BaseURL/health/score" -Headers $headers -Method Get
    Write-Host "✅ Health Score Response:"
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "❌ Health Score Failed:"
    Write-Host "Status: $($_.Exception.Response.StatusCode)"
    Write-Host "Error: $($_.Exception.Message)"
}

# Test 2: Health Issues
Write-Host "`n2. Testing Health Issues Endpoint..."
try {
    $response = Invoke-RestMethod -Uri "$BaseURL/health/issues" -Headers $headers -Method Get
    Write-Host "✅ Health Issues Response:"
    Write-Host "Total Issues: $($response.total)"
    Write-Host "Issues Found: $($response.issues.Count)"
} catch {
    Write-Host "❌ Health Issues Failed:"
    Write-Host "Status: $($_.Exception.Response.StatusCode)"
    Write-Host "Error: $($_.Exception.Message)"
}

# Test 3: Health Scan
Write-Host "`n3. Testing Health Scan Endpoint..."
try {
    $response = Invoke-RestMethod -Uri "$BaseURL/health/scan" -Headers $headers -Method Post
    Write-Host "✅ Health Scan Response:"
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Host "❌ Health Scan Failed:"
    Write-Host "Status: $($_.Exception.Response.StatusCode)"
    Write-Host "Error: $($_.Exception.Message)"
}

# Test 4: Health Export
Write-Host "`n4. Testing Health Export Endpoint..."
try {
    $exportUri = "$BaseURL/health/issues/export?format=csv"
    $response = Invoke-WebRequest -Uri $exportUri -Headers $headers -Method Get
    Write-Host "✅ Health Export Response:"
    Write-Host "Status Code: $($response.StatusCode)"
    Write-Host "Content Type: $($response.Headers.'Content-Type')"
    Write-Host "Content Length: $($response.Content.Length) bytes"
} catch {
    Write-Host "❌ Health Export Failed:"
    Write-Host "Status: $($_.Exception.Response.StatusCode)"
    Write-Host "Error: $($_.Exception.Message)"
}

Write-Host "`n=========================================="
Write-Host "Test completed."
Write-Host "=========================================="