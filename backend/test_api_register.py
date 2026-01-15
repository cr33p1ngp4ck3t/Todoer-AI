"""Test registration endpoint via HTTP"""
import requests
import uuid

# Generate unique credentials
unique_id = str(uuid.uuid4())[:8]
username = f"user_{unique_id}"
email = f"{username}@example.com"
password = "SecurePass123"

print(f"Testing registration with:")
print(f"  Username: {username}")
print(f"  Email: {email}")
print(f"  Password: {password}")
print()

try:
    response = requests.post(
        "http://localhost:8000/users/register",
        json={
            "username": username,
            "email": email,
            "password": password,
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")
    print(f"Response Headers: {dict(response.headers)}")

    if response.status_code == 201:
        print("\nSUCCESS! Registration worked!")
        data = response.json()
        print(f"  User ID: {data['id']}")
        print(f"  Username: {data['username']}")
        print(f"  Email: {data['email']}")
        print(f"  Created at: {data['created_at']}")
    else:
        print(f"\nFAILED: Expected 201, got {response.status_code}")

except Exception as e:
    print(f"\nERROR: {e}")
