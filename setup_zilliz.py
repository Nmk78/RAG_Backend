#!/usr/bin/env python3
"""
Setup Zilliz Cloud for RAG Chatbot

This script helps set up and test Zilliz Cloud integration.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def check_zilliz_config():
    """
    Check Zilliz Cloud configuration
    """
    logger.info("🔍 Checking Zilliz Cloud configuration...")
    
    zilliz_uri = os.getenv("ZILLIZ_URI")
    zilliz_token = os.getenv("ZILLIZ_TOKEN")
    
    if not zilliz_uri:
        logger.error("❌ ZILLIZ_URI not found in environment variables")
        return False
    
    if not zilliz_token:
        logger.error("❌ ZILLIZ_TOKEN not found in environment variables")
        return False
    
    logger.info("✅ Zilliz Cloud configuration found")
    logger.info(f"   URI: {zilliz_uri}")
    logger.info(f"   Token: {zilliz_token[:10]}...")
    
    return True

def test_zilliz_connection():
    """
    Test Zilliz Cloud connection
    """
    try:
        logger.info("🧪 Testing Zilliz Cloud connection...")
        
        from pymilvus import connections
        
        zilliz_uri = os.getenv("ZILLIZ_URI")
        zilliz_token = os.getenv("ZILLIZ_TOKEN")
        
        # Connect to Zilliz Cloud
        connections.connect(
            alias="default",
            uri=zilliz_uri,
            token=zilliz_token
        )
        
        logger.info("✅ Successfully connected to Zilliz Cloud!")
        
        # Test basic operations
        from pymilvus import utility
        
        # List collections
        collections = utility.list_collections()
        logger.info(f"📊 Found {len(collections)} collections")
        
        for collection in collections:
            logger.info(f"   - {collection}")
        
        # Disconnect
        connections.disconnect("default")
        logger.info("🔌 Disconnected from Zilliz Cloud")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error connecting to Zilliz Cloud: {str(e)}")
        return False

def main():
    """
    Main setup function
    """
    logger.info("🚀 Setting up Zilliz Cloud for RAG Chatbot")
    logger.info("=" * 50)
    
    # Step 1: Check configuration
    if not check_zilliz_config():
        logger.error("❌ Configuration check failed")
        return
    
    # Step 2: Test connection
    if not test_zilliz_connection():
        logger.error("❌ Connection test failed")
        return
    
    logger.info("🎉 Zilliz Cloud setup completed successfully!")
    logger.info("\n📋 Next steps:")
    logger.info("1. Upload documents to test vector storage")
    logger.info("2. Test RAG pipeline with Zilliz")
    logger.info("3. Monitor performance and adjust settings")

if __name__ == "__main__":
    main()
