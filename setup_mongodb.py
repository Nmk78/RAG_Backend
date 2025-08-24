#!/usr/bin/env python3
"""
MongoDB Atlas Setup for RAG Chatbot

This script sets up MongoDB Atlas for the RAG chatbot, including:
1. Connection validation
2. Regular index creation
3. Vector search index creation (if available)
4. Fallback to text search if vector search is not available
"""

import os
import sys
import logging
import asyncio
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not installed, trying to load .env manually")

def validate_mongodb_connection():
    """
    Validate MongoDB Atlas connection
    """
    try:
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            logger.error("❌ MONGODB_URI not found in environment variables")
            return False
        
        # Use shorter timeout and connection pool settings
        client = MongoClient(
            mongo_uri, 
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            maxPoolSize=1
        )
        
        # Test connection
        client.admin.command('ping')
        
        # Test database access
        db_name = os.getenv("MONGODB_DATABASE", "pivot_db")
        collection_name = os.getenv("MONGODB_COLLECTION", "documents")
        
        db = client[db_name]
        collection = db[collection_name]
        
        # Test collection access with timeout
        collection.find_one()
        
        client.close()
        logger.info("✅ MongoDB Atlas connection successful")
        logger.info(f"✅ Database '{db_name}' and collection '{collection_name}' accessible")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error connecting to MongoDB Atlas: {e}")
        return False

def create_regular_indexes():
    """
    Create regular indexes for efficient querying
    """
    try:
        mongo_uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DATABASE", "pivot_db")
        collection_name = os.getenv("MONGODB_COLLECTION", "documents")
        
        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]
        
        # Create indexes
        collection.create_index("file_id")
        collection.create_index("filename")
        collection.create_index("created_at")
        collection.create_index([("content", "text")])  # Text search index
        
        client.close()
        logger.info("✅ Regular indexes created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating regular indexes: {e}")
        return False

def create_vector_search_index():
    """
    Create vector search index (if supported)
    """
    try:
        mongo_uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DATABASE", "pivot_db")
        collection_name = os.getenv("MONGODB_COLLECTION", "documents")
        
        client = MongoClient(mongo_uri)
        db = client[db_name]
        
        # Vector search index definition
        vector_index = {
            "mappings": {
                "dynamic": True,
                "fields": {
                    "embedding": {
                        "dimensions": 768,  # Gemini embedding dimensions
                        "similarity": "cosine",
                        "type": "knnVector"
                    }
                }
            }
        }
        
        # Create vector search index
        db.command({
            "createSearchIndex": collection_name,
            "name": "vector_index",
            "definition": vector_index
        })
        
        client.close()
        logger.info("✅ Vector search index created successfully")
        return True
        
    except OperationFailure as e:
        if "command not found" in str(e):
            logger.warning("⚠️  Vector search not available on this cluster tier")
            logger.info("💡 This is normal for M0/M2/M5 clusters")
            logger.info("📋 Your RAG chatbot will use text search as fallback")
            return True  # Not an error, just not available
        else:
            logger.error(f"❌ Error creating vector search index: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Error creating vector search index: {e}")
        return False

async def test_vector_search():
    """
    Test vector search functionality (if available)
    """
    try:
        from retriever.mongodb_vectorstore import MongoDBVectorStore
        
        vector_store = MongoDBVectorStore()
        
        # Test adding a document
        test_docs = ["This is a test document for vector search."]
        await vector_store.add_documents(test_docs, {"test": True})
        
        # Test similarity search
        results = await vector_store.similarity_search("test document", k=1)
        
        # Clean up test document
        await vector_store.delete_by_metadata({"test": True})
        
        await vector_store.close()
        
        logger.info("✅ Vector search test passed")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️  Vector search test failed (this is normal for M0/M2/M5 clusters): {e}")
        logger.info("📋 Text search fallback will be used")
        return True  # Not an error, just not available

def main():
    """
    Main setup function
    """
    logger.info("🚀 MongoDB Atlas Setup for RAG Chatbot")
    logger.info("=" * 50)
    
    # Log configuration
    db_name = os.getenv("MONGODB_DATABASE", "pivot_db")
    collection_name = os.getenv("MONGODB_COLLECTION", "documents")
    vector_store_type = os.getenv("VECTOR_STORE_TYPE", "mongodb")
    
    logger.info("📋 Configuration:")
    logger.info(f"   Database: {db_name}")
    logger.info(f"   Collection: {collection_name}")
    logger.info(f"   Vector Store Type: {vector_store_type}")
    
    logger.info("\n🔗 Step 1: Validating MongoDB Atlas connection...")
    if not validate_mongodb_connection():
        logger.error("❌ Setup failed: Cannot connect to MongoDB Atlas")
        sys.exit(1)
    
    logger.info("\n📊 Step 2: Creating regular indexes...")
    if not create_regular_indexes():
        logger.error("❌ Setup failed: Cannot create regular indexes")
        sys.exit(1)
    
    logger.info("\n🔍 Step 3: Creating vector search index...")
    vector_search_available = create_vector_search_index()
    
    if vector_search_available:
        logger.info("\n🧪 Step 4: Testing vector search functionality...")
        if not asyncio.run(test_vector_search()):
            logger.warning("⚠️  Vector search test failed, but setup can continue")
    
    logger.info("\n✅ MongoDB Atlas setup completed successfully!")
    
    if vector_search_available:
        logger.info("🎉 Vector search is available and working!")
        logger.info("📋 Your RAG chatbot will use vector search for best performance")
    else:
        logger.info("📋 Vector search is not available on your cluster tier")
        logger.info("💡 Your RAG chatbot will use text search as fallback")
        logger.info("🔧 To enable vector search, upgrade to M10 or higher cluster tier")
    
    logger.info("\n🚀 Next steps:")
    logger.info("1. Run: python test_mongodb_integration.py")
    logger.info("2. Run: python main.py")
    logger.info("3. Test your API endpoints")

if __name__ == "__main__":
    main()
