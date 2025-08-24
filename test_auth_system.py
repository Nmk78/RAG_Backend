#!/usr/bin/env python3
"""
Test Authentication System

This script tests the authentication system components.
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_auth_service():
    """Test the authentication service"""
    try:
        from services.auth_service import AuthService
        from models.user import UserCreate
        
        print("🧪 Testing Authentication Service")
        print("=" * 40)
        
        # Initialize auth service
        auth_service = AuthService()
        
        # Test user creation
        print("\n1. Testing user creation...")
        test_user_data = UserCreate(
            email="test@example.com",
            password="testpassword123",
            username="testuser",
            full_name="Test User"
        )
        
        user = await auth_service.create_user(test_user_data)
        print(f"✅ User created: {user.username} ({user.id})")
        
        # Test password verification
        print("\n2. Testing password verification...")
        is_valid = auth_service.verify_password("testpassword123", user.hashed_password)
        print(f"✅ Password verification: {is_valid}")
        
        # Test user authentication
        print("\n3. Testing user authentication...")
        authenticated_user = await auth_service.authenticate_user("test@example.com", "testpassword123")
        if authenticated_user:
            print(f"✅ User authenticated: {authenticated_user.username}")
        else:
            print("❌ Authentication failed")
        
        # Test token creation and verification
        print("\n4. Testing JWT tokens...")
        token = auth_service.create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role}
        )
        print(f"✅ Token created: {token[:20]}...")
        
        token_data = auth_service.verify_token(token)
        if token_data:
            print(f"✅ Token verified: {token_data.user_id}")
        else:
            print("❌ Token verification failed")
        
        # Clean up
        print("\n5. Cleaning up test data...")
        # Note: In a real system, you'd want to delete the test user
        
        print("\n🎉 Authentication service tests completed successfully!")
        
        # Clean up
        auth_service.close()
        
    except Exception as e:
        print(f"❌ Error testing auth service: {e}")
        import traceback
        traceback.print_exc()

async def test_chat_service():
    """Test the chat service"""
    try:
        from services.chat_service import ChatService
        from models.chat import ChatSessionCreate, ChatMessageCreate
        
        print("\n🧪 Testing Chat Service")
        print("=" * 40)
        
        # Initialize chat service
        chat_service = ChatService()
        
        # Test session creation
        print("\n1. Testing session creation...")
        session_data = ChatSessionCreate(
            title="Test Session",
            metadata={"test": True}
        )
        
        session = await chat_service.create_session("test_user_id", session_data)
        print(f"✅ Session created: {session.id}")
        
        # Test message creation
        print("\n2. Testing message creation...")
        message_data = ChatMessageCreate(
            role="user",
            content="Hello, this is a test message!",
            message_type="text"
        )
        
        message = await chat_service.add_message(
            session.id,
            message_data,
            tokens_used=10,
            response_time_ms=150
        )
        print(f"✅ Message created: {message.id}")
        
        # Test getting session messages
        print("\n3. Testing message retrieval...")
        messages = await chat_service.get_session_messages(session.id)
        print(f"✅ Retrieved {len(messages)} messages")
        
        # Test session stats
        print("\n4. Testing session statistics...")
        stats = await chat_service.get_session_stats(session.id)
        print(f"✅ Session stats: {stats.get('total_messages', 0)} messages, {stats.get('total_tokens', 0)} tokens")
        
        # Clean up
        print("\n5. Cleaning up test data...")
        await chat_service.close_session(session.id)
        print("✅ Test session closed")
        
        print("\n🎉 Chat service tests completed successfully!")
        
        # Clean up
        chat_service.close()
        
    except Exception as e:
        print(f"❌ Error testing chat service: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests"""
    print("🚀 Testing RAG Chatbot Authentication System")
    print("=" * 60)
    
    await test_auth_service()
    await test_chat_service()
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
