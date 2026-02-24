from dotenv import load_dotenv
import os
from core.db import MongoDB

# Load environment variables first
load_dotenv()

try:
    print("⏳ Attempting to connect to MongoDB Atlas...")
    db = MongoDB()
    
    # Try creating a test user to verify write access
    db.create_user("test_admin", "securepassword123")
    
    # Fetch the user to verify read access
    user = db.users.find_one({"username": "test_admin"})
    
    if user:
        print("✅ SUCCESS: Connected to MongoDB and verified read/write access!")
        print(f"📁 Active Database: {db.db.name}")
        
        # Clean up the test user
        db.users.delete_one({"username": "test_admin"})
        print("🧹 Cleaned up test data.")
    else:
        print("❌ FAILED: Could connect, but couldn't verify data creation.")

except Exception as e:
    print(f"❌ ERROR: Connection failed. Check your password and IP whitelist in Atlas.\nDetails: {e}")