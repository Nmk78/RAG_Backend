#!/usr/bin/env python3
"""
Simple MongoDB Atlas Connection Test

This script tests the MongoDB Atlas connection to help troubleshoot issues.
"""

import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

def test_connection():
    """
    Test MongoDB Atlas connection
    """
    print("🔗 MongoDB Atlas Connection Test")
    print("=" * 40)
    
    # Get connection string from environment
    mongo_uri = os.getenv("MONGODB_URI")
    
    if not mongo_uri:
        print("❌ MONGODB_URI not found in environment variables")
        print("Please set MONGODB_URI in your .env file")
        return False
    
    print(f"📋 Testing connection string: {mongo_uri[:50]}...")
    
    try:
        # Test connection with timeout
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connection successful!")
        
        # List databases
        databases = client.list_database_names()
        print(f"📊 Available databases: {databases}")
        
        # Test database access
        db_name = os.getenv("MONGODB_DATABASE", "pivot_db")
        db = client[db_name]
        
        # Try to access the database
        collections = db.list_collection_names()
        print(f"📁 Collections in {db_name}: {collections}")
        
        client.close()
        return True
        
    except ConnectionFailure as e:
        print(f"❌ Connection failed: {e}")
        return False
    except ServerSelectionTimeoutError as e:
        print(f"❌ Server selection timeout: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """
    Main function
    """
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv not installed, trying to load .env manually")
    
    success = test_connection()
    
    if success:
        print("\n✅ MongoDB Atlas connection test passed!")
        print("You can now run: python setup_mongodb.py")
    else:
        print("\n❌ MongoDB Atlas connection test failed!")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check your username and password in MongoDB Atlas")
        print("2. Make sure your user has 'Read and write to any database' permissions")
        print("3. Check if your IP address is whitelisted in Network Access")
        print("4. Try resetting your password in MongoDB Atlas")

if __name__ == "__main__":
    main()
