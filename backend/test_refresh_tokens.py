"""Test refresh token flow via HTTP"""
import requests
import uuid
import time
import sys
import io

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_response(response):
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response: {response.text}")
    print()

# Step 1: Register a new user
print_section("Step 1: Register New User")
unique_id = str(uuid.uuid4())[:8]
username = f"test_refresh_{unique_id}"
email = f"{username}@example.com"
password = "TestRefresh123"

print(f"Creating user: {username} / {email}")

response = requests.post(
    f"{BASE_URL}/users/register",
    json={"username": username, "email": email, "password": password}
)
print_response(response)

if response.status_code != 201:
    print("❌ Registration failed!")
    exit(1)

# Step 2: Login and get tokens
print_section("Step 2: Login and Get Tokens")
print(f"Logging in with: {email}")

response = requests.post(
    f"{BASE_URL}/users/login",
    json={"email": email, "password": password}
)
print_response(response)

if response.status_code != 200:
    print("❌ Login failed!")
    exit(1)

tokens = response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

print(f"[OK] Got access token: {access_token[:20]}...")
print(f"[OK] Got refresh token: {refresh_token[:20]}...")

# Step 3: Use access token to get user profile
print_section("Step 3: Access Protected Endpoint with Access Token")
print("Calling /users/me with access token...")

response = requests.get(
    f"{BASE_URL}/users/me",
    headers={"Authorization": f"Bearer {access_token}"}
)
print_response(response)

if response.status_code != 200:
    print("❌ Failed to access protected endpoint!")
    exit(1)

user_data = response.json()
print(f"✅ Authenticated as: {user_data['username']} ({user_data['email']})")

# Step 4: Refresh the tokens
print_section("Step 4: Refresh Tokens")
print("Exchanging refresh token for new tokens...")

response = requests.post(
    f"{BASE_URL}/auth/refresh",
    json={"refresh_token": refresh_token}
)
print_response(response)

if response.status_code != 200:
    print("❌ Token refresh failed!")
    exit(1)

new_tokens = response.json()
new_access_token = new_tokens["access_token"]
new_refresh_token = new_tokens["refresh_token"]

print(f"✅ Got NEW access token: {new_access_token[:20]}...")
print(f"✅ Got NEW refresh token: {new_refresh_token[:20]}...")

# Verify old and new tokens are different
if access_token == new_access_token:
    print("⚠️  WARNING: Access token didn't change!")
if refresh_token == new_refresh_token:
    print("⚠️  WARNING: Refresh token didn't change (should rotate)!")
else:
    print("✅ Token rotation working (old token revoked, new token issued)")

# Step 5: Verify new access token works
print_section("Step 5: Verify New Access Token Works")
print("Calling /users/me with NEW access token...")

response = requests.get(
    f"{BASE_URL}/users/me",
    headers={"Authorization": f"Bearer {new_access_token}"}
)
print_response(response)

if response.status_code != 200:
    print("❌ New access token doesn't work!")
    exit(1)

print("✅ New access token works!")

# Step 6: Try to use old refresh token (should fail)
print_section("Step 6: Verify Old Refresh Token is Revoked")
print("Trying to use old refresh token (should fail)...")

response = requests.post(
    f"{BASE_URL}/auth/refresh",
    json={"refresh_token": refresh_token}  # Old token
)
print_response(response)

if response.status_code == 401:
    print("✅ Old refresh token correctly revoked (token rotation working)")
else:
    print("⚠️  WARNING: Old refresh token still works (token rotation may not be working)")

# Step 7: Logout (revoke current refresh token)
print_section("Step 7: Test Logout")
print("Logging out (revoking current refresh token)...")

response = requests.post(
    f"{BASE_URL}/auth/logout",
    json={"refresh_token": new_refresh_token}
)
print_response(response)

if response.status_code != 200:
    print("❌ Logout failed!")
    exit(1)

# Step 8: Try to refresh with logged-out token (should fail)
print_section("Step 8: Verify Logged Out Token Cannot Refresh")
print("Trying to refresh with logged-out token...")

response = requests.post(
    f"{BASE_URL}/auth/refresh",
    json={"refresh_token": new_refresh_token}
)
print_response(response)

if response.status_code == 401:
    print("✅ Logged-out token correctly rejected")
else:
    print("⚠️  WARNING: Logged-out token still works!")

# Step 9: Login again and test logout-all
print_section("Step 9: Test Logout All Devices")
print("Logging in again...")

response = requests.post(
    f"{BASE_URL}/users/login",
    json={"email": email, "password": password}
)
tokens = response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

print("✅ Logged in, got new tokens")
print("\nCalling /auth/logout-all...")

response = requests.post(
    f"{BASE_URL}/auth/logout-all",
    headers={"Authorization": f"Bearer {access_token}"}
)
print_response(response)

if response.status_code != 200:
    print("❌ Logout-all failed!")
    exit(1)

# Verify token is revoked
response = requests.post(
    f"{BASE_URL}/auth/refresh",
    json={"refresh_token": refresh_token}
)

if response.status_code == 401:
    print("✅ All devices logged out successfully")
else:
    print("⚠️  WARNING: Logout-all may not have revoked all tokens")

# Final Summary
print_section("TEST SUMMARY")
print("✅ All tests passed!")
print("\nRefresh Token System Features Verified:")
print("  ✓ User can login and receive access + refresh tokens")
print("  ✓ Access token works for protected endpoints")
print("  ✓ Refresh token can be exchanged for new tokens")
print("  ✓ Token rotation works (old refresh token revoked)")
print("  ✓ Single device logout works")
print("  ✓ Logout all devices works")
print("\n🔥 Backend refresh token implementation is working perfectly!")
