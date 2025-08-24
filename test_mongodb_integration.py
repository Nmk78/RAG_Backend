#!/usr/bin/env python3
"""
MongoDB Atlas Integration Test Script

This script tests the MongoDB Atlas integration to ensure everything is working correctly.
"""

import asyncio
import logging
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from retriever.mongodb_vectorstore import MongoDBVectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mongodb_integration():
    """
    Test MongoDB Atlas integration
    """
    logger.info("🧪 Testing MongoDB Atlas Integration")
    logger.info("=" * 50)
    
    try:
        # Test 1: Initialize MongoDB Vector Store
        logger.info("📋 Test 1: Initializing MongoDB Vector Store...")
        vector_store = MongoDBVectorStore()
        logger.info("✅ MongoDB Vector Store initialized successfully")
        
        # Test 2: Add test documents
        logger.info("📋 Test 2: Adding test documents...")
        test_documents = [
            "Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",
            "Natural language processing (NLP) is a branch of AI that helps computers understand and interpret human language.",
            "Deep learning is a type of machine learning that uses neural networks with multiple layers to model complex patterns."
        ]
        test_metadata = {
            "file_id": "test_file_001",
            "filename": "test_document.txt",
            "source": "test"
        }
        
        await vector_store.add_documents(test_documents, test_metadata)
        logger.info(f"✅ Added {len(test_documents)} test documents")
        
        # Test 3: Similarity search
        logger.info("📋 Test 3: Testing similarity search...")
        query = "What is machine learning?"
        results = await vector_store.similarity_search(query, k=2)
        
        if results:
            logger.info(f"✅ Similarity search successful - Found {len(results)} results")
            for i, result in enumerate(results):
                logger.info(f"   Result {i+1}: {result['page_content'][:100]}...")
        else:
            logger.warning("⚠️  Similarity search returned no results")
        
        # Test 4: Filtered search
        logger.info("📋 Test 4: Testing filtered search...")
        filter_dict = {"source": "test"}
        filtered_results = await vector_store.similarity_search_with_filter(query, filter_dict, k=2)
        
        if filtered_results:
            logger.info(f"✅ Filtered search successful - Found {len(filtered_results)} results")
        else:
            logger.warning("⚠️  Filtered search returned no results")
        
        # Test 5: Get collection stats
        logger.info("📋 Test 5: Getting collection statistics...")
        stats = await vector_store.get_collection_stats()
        logger.info(f"✅ Collection stats: {stats}")
        
        # Test 6: List files
        logger.info("📋 Test 6: Listing files...")
        files = await vector_store.list_files()
        logger.info(f"✅ Found {len(files)} files in collection")
        for file_info in files:
            logger.info(f"   File: {file_info['filename']} ({file_info['document_count']} documents)")
        
        # Test 7: Delete test documents
        logger.info("📋 Test 7: Cleaning up test documents...")
        await vector_store.delete_by_metadata({"source": "test"})
        logger.info("✅ Test documents cleaned up")
        
        # Test 8: Close connections
        logger.info("📋 Test 8: Closing connections...")
        await vector_store.close()
        logger.info("✅ Connections closed successfully")
        
        logger.info("\n🎉 All MongoDB Atlas integration tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        return False

async def test_api_endpoints():
    """
    Test API endpoints with MongoDB
    """
    logger.info("\n🌐 Testing API Endpoints with MongoDB")
    logger.info("=" * 50)
    
    try:
        import requests
        import json
        
        base_url = "http://localhost:8000"
        
        # Test 1: Health check
        logger.info("📋 Test 1: Health check...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"✅ Health check passed - Vector store: {health_data.get('vector_store')}")
        else:
            logger.error(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test 2: Text query
        logger.info("📋 Test 2: Text query...")
        text_data = {"query": "What is artificial intelligence?"}
        response = requests.post(f"{base_url}/api/v2/text", json=text_data)
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Text query successful - Response: {result['response'][:100]}...")
        else:
            logger.error(f"❌ Text query failed: {response.status_code} - {response.text}")
            return False
        
        # Test 3: List files
        logger.info("📋 Test 3: List files...")
        response = requests.get(f"{base_url}/api/v2/files")
        if response.status_code == 200:
            files_data = response.json()
            logger.info(f"✅ List files successful - Found {files_data.get('count', 0)} files")
        else:
            logger.error(f"❌ List files failed: {response.status_code} - {response.text}")
            return False
        
        logger.info("\n🎉 All API endpoint tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ API test failed: {str(e)}")
        return False

def main():
    """
    Main test function
    """
    logger.info("🚀 MongoDB Atlas Integration Test Suite")
    logger.info("=" * 60)
    
    # Check configuration
    logger.info(f"📋 Configuration:")
    logger.info(f"   Vector Store Type: {Config.VECTOR_STORE_TYPE}")
    logger.info(f"   MongoDB Database: {Config.MONGODB_DATABASE}")
    logger.info(f"   MongoDB Collection: {Config.MONGODB_COLLECTION}")
    
    if Config.VECTOR_STORE_TYPE != "mongodb":
        logger.error("❌ VECTOR_STORE_TYPE is not set to 'mongodb'")
        logger.error("   Please set VECTOR_STORE_TYPE=mongodb in your .env file")
        sys.exit(1)
    
    if not Config.MONGODB_URI:
        logger.error("❌ MONGODB_URI is not set")
        logger.error("   Please set MONGODB_URI in your .env file")
        sys.exit(1)
    
    # Run tests
    success = True
    
    # Test MongoDB integration
    if not asyncio.run(test_mongodb_integration()):
        success = False
    
    # Test API endpoints (only if API is running)
    try:
        if not asyncio.run(test_api_endpoints()):
            success = False
    except Exception as e:
        logger.warning(f"⚠️  API tests skipped (API may not be running): {str(e)}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    if success:
        logger.info("🎉 All tests passed! MongoDB Atlas integration is working correctly.")
        logger.info("\n📝 Next steps:")
        logger.info("   1. Your MongoDB Atlas integration is ready")
        logger.info("   2. You can now use the API with MongoDB Atlas")
        logger.info("   3. Monitor your MongoDB Atlas cluster for performance")
    else:
        logger.error("❌ Some tests failed. Please check the configuration and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
