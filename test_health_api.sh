#!/bin/bash

# ShareGuard Health API Test Script
echo "=========================================="
echo "ShareGuard Health API Debug Test"
echo "=========================================="

BASE_URL="http://localhost:8000/api/v1"

# Test 1: Check if backend is running
echo -e "\n1. Testing backend connectivity..."
curl -s -o /dev/null -w "Backend status: %{http_code}\n" "$BASE_URL/../docs"

# Test 2: Login to get token
echo -e "\n2. Testing authentication..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"ShareGuardService","domain":"WIN-I2VDDDLDOUA","password":"P(5$\\#SX07sj"}')

echo "Login response: $LOGIN_RESPONSE"

# Extract token (this is a simple extraction, might need adjustment based on actual response)
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get token, trying alternative credentials..."
    # Try alternative login - check if there are other service accounts
    LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
      -H "Content-Type: application/json" \
      -d '{"username":"Administrator","domain":"WIN-I2VDDDLDOUA","password":"ShareGuard123!"}')
    echo "Alternative login response: $LOGIN_RESPONSE"
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
fi

if [ -n "$TOKEN" ]; then
    echo "✅ Token obtained: ${TOKEN:0:50}..."
    AUTH_HEADER="Authorization: Bearer $TOKEN"
else
    echo "❌ No token available, testing without auth..."
    AUTH_HEADER="X-Test: NoAuth"
fi

# Test 3: Health score endpoint
echo -e "\n3. Testing health score endpoint..."
curl -s -X GET "$BASE_URL/health/score" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -w "\nStatus Code: %{http_code}\n"

# Test 4: Health issues endpoint
echo -e "\n4. Testing health issues endpoint..."
curl -s -X GET "$BASE_URL/health/issues" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -w "\nStatus Code: %{http_code}\n"

# Test 5: Health export endpoint (the one causing 422)
echo -e "\n5. Testing health export endpoint..."
echo "Test 5a: Basic CSV export"
curl -s -X GET "$BASE_URL/health/issues/export?format=csv" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -w "\nStatus Code: %{http_code}\n"

echo -e "\nTest 5b: CSV export with severity"
curl -s -X GET "$BASE_URL/health/issues/export?format=csv&severity=high" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -w "\nStatus Code: %{http_code}\n"

# Test 6: Health scan endpoint
echo -e "\n6. Testing health scan endpoint..."
curl -s -X POST "$BASE_URL/health/scan" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -w "\nStatus Code: %{http_code}\n"

# Test 7: Check if tables exist (through API)
echo -e "\n7. Additional diagnostics..."
echo "Check recent auth middleware logs:"
tail -10 logs/auth_middleware_20250630.log

echo -e "\n=========================================="
echo "Test completed. Check responses above."
echo "=========================================="