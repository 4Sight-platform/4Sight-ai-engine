"""
Quick script to initialize goals for a specific user via API call
"""
import requests
import sys

user_id = sys.argv[1] if len(sys.argv) > 1 else "user_daeaff31acaf"

print(f"Initializing goals for user: {user_id}")
print("="*60)

try:
    response = requests.post(
        f"http://localhost:8001/api/v1/strategy/goals/initialize?user_id={user_id}",
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code in [200, 201]:
        print("\n✅ Goals initialized successfully!")
    else:
        print(f"\n❌ Failed to initialize goals: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
