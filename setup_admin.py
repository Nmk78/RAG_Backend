#!/usr/bin/env python3
"""
Setup Admin User for RAG Chatbot

This script creates the first admin user for the system.
Run this once after setting up the database.
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def setup_admin():
    """Setup the first admin user"""
    try:
        from services.auth_service import AuthService
        
        print("🚀 Setting up Admin User for RAG Chatbot")
        print("=" * 50)
        
        # Initialize auth service
        auth_service = AuthService()
        
        # Get admin credentials from environment or prompt user
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")
        admin_username = os.getenv("ADMIN_USERNAME")
        
        if not admin_email:
            admin_email = input("Enter admin email: ").strip()
        
        if not admin_password:
            admin_password = input("Enter admin password: ").strip()
        
        if not admin_username:
            admin_username = input("Enter admin username: ").strip()
        
        if not admin_email or not admin_password or not admin_username:
            print("❌ All fields are required")
            return
        
        print(f"\n📋 Admin User Details:")
        print(f"   Email: {admin_email}")
        print(f"   Username: {admin_username}")
        print(f"   Password: {'*' * len(admin_password)}")
        
        # Confirm creation
        confirm = input("\nCreate admin user? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Admin user creation cancelled")
            return
        
        # Create admin user
        print("\n🔧 Creating admin user...")
        admin_user = await auth_service.create_admin_user(
            admin_email,
            admin_password,
            admin_username
        )
        
        print("✅ Admin user created successfully!")
        print(f"\n📊 User Details:")
        print(f"   ID: {admin_user.id}")
        print(f"   Email: {admin_user.email}")
        print(f"   Username: {admin_user.username}")
        print(f"   Role: {admin_user.role}")
        print(f"   Status: {admin_user.status}")
        print(f"   Created: {admin_user.created_at}")
        
        print("\n🎉 Setup completed! You can now login with these credentials.")
        
        # Clean up
        auth_service.close()
        
    except Exception as e:
        print(f"❌ Error setting up admin user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(setup_admin())
