#!/usr/bin/env python3
"""
Simple MongoDB Connection String Update

This script helps you update your MongoDB connection string.
"""

import urllib.parse
import os

def update_connection_string():
    """
    Update MongoDB connection string
    """
    print("🔗 Simple MongoDB Connection String Update")
    print("=" * 50)
    
    print("\n📋 Instructions:")
    print("1. Go to MongoDB Atlas Dashboard")
    print("2. Go to Database Access")
    print("3. Find user 'nay304095' and reset password")
    print("4. Or create a new user with 'Read and write to any database' permissions")
    print("5. Go to your cluster → Connect → Connect your application")
    print("6. Copy the connection string")
    
    print("\n📝 Paste your connection string here (replace <password> and <dbname>):")
    connection_string = input("Connection string: ").strip()
    
    if not connection_string:
        print("❌ No connection string provided")
        return
    
    # Extract database name from connection string
    if "/" in connection_string:
        db_name = connection_string.split("/")[-1].split("?")[0]
    else:
        db_name = input("Enter database name (e.g., pivot_db): ").strip()
    
    print(f"\n✅ Database name: {db_name}")
    
    # Update .env file
    env_file = ".env"
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            # Update the lines
            updated_lines = []
            for line in lines:
                if line.startswith("MONGODB_URI="):
                    updated_lines.append(f"MONGODB_URI={connection_string}\n")
                elif line.startswith("MONGODB_DATABASE="):
                    updated_lines.append(f"MONGODB_DATABASE={db_name}\n")
                elif line.startswith("MONGODB_COLLECTION="):
                    updated_lines.append("MONGODB_COLLECTION=documents\n")
                else:
                    updated_lines.append(line)
            
            with open(env_file, 'w') as f:
                f.writelines(updated_lines)
            
            print("✅ .env file updated successfully!")
            print(f"📋 Updated values:")
            print(f"MONGODB_URI={connection_string}")
            print(f"MONGODB_DATABASE={db_name}")
            print("MONGODB_COLLECTION=documents")
            
        except Exception as e:
            print(f"❌ Error updating .env file: {e}")
            print("Please update it manually with:")
            print(f"MONGODB_URI={connection_string}")
            print(f"MONGODB_DATABASE={db_name}")
            print("MONGODB_COLLECTION=documents")
    
    print("\n✅ Now try running: python test_mongodb_connection.py")

if __name__ == "__main__":
    update_connection_string()
