#!/usr/bin/env python3
"""
MongoDB Atlas Connection String Helper

This script helps you get the correct MongoDB Atlas connection string.
"""

import urllib.parse

def get_connection_string():
    """
    Get the correct MongoDB Atlas connection string
    """
    print("🔗 MongoDB Atlas Connection String Helper")
    print("=" * 50)
    
    print("\n📋 Step 1: Get your cluster name from MongoDB Atlas")
    print("1. Go to MongoDB Atlas Dashboard")
    print("2. Look at your cluster name (it should look like: cluster0.abc123def)")
    print("3. Copy the FULL cluster name including the unique ID")
    
    # Get credentials from user
    username = input("\nEnter your MongoDB Atlas username: ")
    password = input("Enter your MongoDB Atlas password: ")
    
    # Encode credentials
    encoded_username = urllib.parse.quote_plus(username)
    encoded_password = urllib.parse.quote_plus(password)
    
    print(f"\n✅ Encoded credentials:")
    print(f"Username: {encoded_username}")
    print(f"Password: {encoded_password}")
    
    # Get cluster details
    print("\n📋 Step 2: Enter your cluster details")
    cluster_name = input("Enter your FULL cluster name (e.g., cluster0.abc123def): ")
    database_name = input("Enter your database name (e.g., pivot): ")
    
    # Build connection string
    connection_string = f"mongodb+srv://{encoded_username}:{encoded_password}@{cluster_name}.mongodb.net/{database_name}?retryWrites=true&w=majority"
    
    print("\n🔗 Your MongoDB Atlas Connection String:")
    print("=" * 60)
    print(connection_string)
    
    print("\n📝 For your .env file:")
    print("=" * 40)
    print(f"MONGODB_URI={connection_string}")
    print(f"MONGODB_DATABASE={database_name}")
    print("MONGODB_COLLECTION=documents")
    
    print("\n✅ Copy these values to your .env file!")
    print("\n💡 Common cluster name formats:")
    print("- cluster0.abc123def")
    print("- mycluster.xyz789ghi")
    print("- rag-cluster.abc123def")

if __name__ == "__main__":
    get_connection_string()
