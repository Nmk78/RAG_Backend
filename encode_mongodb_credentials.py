#!/usr/bin/env python3
"""
MongoDB Atlas Credentials Encoder

This script helps encode username and password for MongoDB Atlas connection string.
"""

import urllib.parse

def encode_credentials():
    """
    Encode username and password for MongoDB Atlas connection string
    """
    print("🔐 MongoDB Atlas Credentials Encoder")
    print("=" * 40)
    
    # Get credentials from user
    username = input("Enter your MongoDB Atlas username: ")
    password = input("Enter your MongoDB Atlas password: ")
    
    # Encode credentials
    encoded_username = urllib.parse.quote_plus(username)
    encoded_password = urllib.parse.quote_plus(password)
    
    print("\n📋 Encoded Credentials:")
    print(f"Original Username: {username}")
    print(f"Encoded Username:  {encoded_username}")
    print(f"Original Password: {password}")
    print(f"Encoded Password:  {encoded_password}")
    
    # Get cluster details
    cluster_name = input("\nEnter your cluster name (e.g., cluster0.abc123): ")
    database_name = input("Enter your database name (e.g., PIVOT_RAG): ")
    
    # Build connection string
    connection_string = f"mongodb+srv://{encoded_username}:{encoded_password}@{cluster_name}.mongodb.net/{database_name}?retryWrites=true&w=majority"
    
    print("\n🔗 Your MongoDB Atlas Connection String:")
    print("=" * 50)
    print(connection_string)
    
    print("\n📝 For your .env file:")
    print("=" * 30)
    print(f"MONGODB_URI={connection_string}")
    print(f"MONGODB_DATABASE={database_name}")
    print("MONGODB_COLLECTION=documents")
    
    print("\n✅ Copy these values to your .env file and try running setup_mongodb.py again!")

if __name__ == "__main__":
    encode_credentials()
