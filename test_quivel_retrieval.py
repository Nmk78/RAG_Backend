#!/usr/bin/env python3
"""
Test Quivel Story Retrieval

This script tests if the Quivel story is properly stored and can be retrieved from MongoDB.
"""

import os
import logging
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def test_quivel_story():
    """
    Test if the Quivel story is in MongoDB and can be retrieved
    """
    try:
        # Get MongoDB connection
        mongo_uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DATABASE", "pivot_db")
        collection_name = os.getenv("MONGODB_COLLECTION", "documents")
        
        if not mongo_uri:
            logger.error("❌ MONGODB_URI not found")
            return
        
        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]
        
        logger.info("🔍 Checking MongoDB for Quivel story...")
        
        # Check total documents
        total_docs = collection.count_documents({})
        logger.info(f"📊 Total documents in collection: {total_docs}")
        
        # Search for documents containing "Quivel"
        quivel_docs = collection.find({"content": {"$regex": "Quivel", "$options": "i"}})
        quivel_count = collection.count_documents({"content": {"$regex": "Quivel", "$options": "i"}})
        
        logger.info(f"🔍 Found {quivel_count} documents containing 'Quivel'")
        
        if quivel_count > 0:
            logger.info("✅ Quivel story found in MongoDB!")
            
            # Show first few documents
            for i, doc in enumerate(quivel_docs.limit(3)):
                logger.info(f"📄 Document {i+1}:")
                logger.info(f"   Content preview: {doc.get('content', '')[:100]}...")
                logger.info(f"   File ID: {doc.get('file_id', 'N/A')}")
                logger.info(f"   Filename: {doc.get('filename', 'N/A')}")
                logger.info("")
        else:
            logger.warning("⚠️  No documents containing 'Quivel' found")
            
            # Show all documents to see what's there
            logger.info("📋 All documents in collection:")
            all_docs = collection.find().limit(5)
            for i, doc in enumerate(all_docs):
                logger.info(f"   Doc {i+1}: {doc.get('content', '')[:50]}...")
        
        # Test text search
        logger.info("\n🔍 Testing text search for 'Quivel'...")
        try:
            text_results = collection.find(
                {"$text": {"$search": "Quivel"}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(3)
            
            text_count = collection.count_documents({"$text": {"$search": "Quivel"}})
            logger.info(f"📊 Text search found {text_count} documents")
            
            if text_count > 0:
                logger.info("✅ Text search working for Quivel!")
            else:
                logger.warning("⚠️  Text search not finding Quivel")
                
        except Exception as e:
            logger.error(f"❌ Text search error: {e}")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Error testing Quivel retrieval: {e}")

def test_simple_search():
    """
    Test simple regex search
    """
    try:
        mongo_uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DATABASE", "pivot_db")
        collection_name = os.getenv("MONGODB_COLLECTION", "documents")
        
        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]
        
        logger.info("\n🔍 Testing simple search patterns...")
        
        # Test different search terms
        search_terms = ["Quivel", "Echo", "train station", "dog", "town"]
        
        for term in search_terms:
            count = collection.count_documents({"content": {"$regex": term, "$options": "i"}})
            logger.info(f"   '{term}': {count} documents")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Error in simple search: {e}")

def main():
    """
    Main test function
    """
    logger.info("🚀 Testing Quivel Story Retrieval")
    logger.info("=" * 50)
    
    test_quivel_story()
    test_simple_search()
    
    logger.info("\n✅ Quivel retrieval test completed!")

if __name__ == "__main__":
    main()
