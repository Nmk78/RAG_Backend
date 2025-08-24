#!/usr/bin/env python3
"""
Update MongoDB Atlas Credentials

This script helps update your MongoDB Atlas credentials in the .env file.
"""

import urllib.parse
import os

def update_credentials():
    """
    Update MongoDB Atlas credentials
    """
    print("🔐 Update MongoDB Atlas Credentials")
    print("=" * 40)
    
    print("\n📋 Current connection string shows username: nay304095")
    print("But we were using: naymyokhant")
    print("\nLet's get the correct credentials:")
    
    # Get the correct credentials
    username = input("Enter the CORRECT MongoDB Atlas username: ")
    password = input("Enter the CORRECT MongoDB Atlas password: ")
    
    # Encode credentials
    encoded_username = urllib.parse.quote_plus(username)
    encoded_password = urllib.parse.quote_plus(password)
    
    print(f"\n✅ Encoded credentials:")
    print(f"Username: {encoded_username}")
    print(f"Password: {encoded_password}")
    
    # Get cluster details
    cluster_name = input("\nEnter your cluster name (from current connection string): ")
    database_name = input("Enter your database name (e.g., pivot_db): ")
    
    # Build connection string
    connection_string = f"mongodb+srv://{encoded_username}:{encoded_password}@{cluster_name}.mongodb.net/{database_name}?retryWrites=true&w=majority"
    
    print("\n🔗 Your updated MongoDB Atlas Connection String:")
    print("=" * 60)
    print(connection_string)
    
    print("\n📝 Update your .env file with:")
    print("=" * 40)
    print(f"MONGODB_URI={connection_string}")
    print(f"MONGODB_DATABASE={database_name}")
    print("MONGODB_COLLECTION=documents")
    
    # Try to update .env file automatically
    env_file = ".env"
    if os.path.exists(env_file):
        update_env = input("\nWould you like to update the .env file automatically? (y/n): ")
        if update_env.lower() == 'y':
            try:
                with open(env_file, 'r') as f:
                    lines = f.readlines()
                
                # Update the lines
                updated_lines = []
                for line in lines:
                    if line.startswith("MONGODB_URI="):
                        updated_lines.append(f"MONGODB_URI={connection_string}\n")
                    elif line.startswith("MONGODB_DATABASE="):
                        updated_lines.append(f"MONGODB_DATABASE={database_name}\n")
                    elif line.startswith("MONGODB_COLLECTION="):
                        updated_lines.append("MONGODB_COLLECTION=documents\n")
                    else:
                        updated_lines.append(line)
                
                with open(env_file, 'w') as f:
                    f.writelines(updated_lines)
                
                print("✅ .env file updated successfully!")
                
            except Exception as e:
                print(f"❌ Error updating .env file: {e}")
                print("Please update it manually with the values above.")
    
    print("\n✅ Now try running: python test_mongodb_connection.py")

if __name__ == "__main__":
    update_credentials()
