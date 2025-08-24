#!/usr/bin/env python3
"""
Fix Vector Search in MongoDB Atlas

This script diagnoses and fixes vector search issues.
"""

import os
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import OperationFailure

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def check_vector_search_index():
    """
    Check if vector search index exists and is working
    """
    try:
        mongo_uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DATABASE", "pivot_db")
        collection_name = os.getenv("MONGODB_COLLECTION", "documents")
        
        client = MongoClient(mongo_uri)
        db = client[db_name]
        
        logger.info("🔍 Checking vector search index...")
        
        # Check if vector search index exists
        try:
            indexes = db.command("listSearchIndexes", collection_name)
            logger.info(f"📊 Found {len(indexes.get('indexes', []))} search indexes")
            
            vector_index_exists = False
            for index in indexes.get("indexes", []):
                logger.info(f"   Index: {index.get('name')} - Status: {index.get('status')}")
                if index.get('name') == 'vector_index':
                    vector_index_exists = True
                    if index.get('status') == 'READY':
                        logger.info("✅ Vector search index exists and is ready!")
                    else:
                        logger.warning(f"⚠️  Vector search index status: {index.get('status')}")
            
            if not vector_index_exists:
                logger.warning("⚠️  Vector search index not found!")
                return False
                
        except OperationFailure as e:
            if "command not found" in str(e):
                logger.error("❌ Vector search not available on this cluster tier")
                logger.info("💡 You need M10 or higher cluster tier for vector search")
                return False
            else:
                logger.error(f"❌ Error checking search indexes: {e}")
                return False
        
        # Check if documents have embeddings
        collection = db[collection_name]
        total_docs = collection.count_documents({})
        docs_with_embeddings = collection.count_documents({"embedding": {"$exists": True}})
        
        logger.info(f"📊 Total documents: {total_docs}")
        logger.info(f"📊 Documents with embeddings: {docs_with_embeddings}")
        
        if docs_with_embeddings == 0:
            logger.error("❌ No documents have embeddings! This is why vector search fails.")
            return False
        
        # Test vector search
        logger.info("🧪 Testing vector search...")
        try:
            # Create a simple test vector (768 dimensions like Gemini)
            test_vector = [0.1] * 768
            
            pipeline = [
                {
                    "$vectorSearch": {
                        "queryVector": test_vector,
                        "path": "embedding",
                        "numCandidates": 10,
                        "limit": 5,
                        "index": "vector_index"
                    }
                },
                {
                    "$project": {
                        "content": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            results = list(collection.aggregate(pipeline))
            logger.info(f"✅ Vector search test successful! Found {len(results)} results")
            
            if results:
                logger.info(f"   Top result score: {results[0].get('score', 'N/A')}")
                logger.info(f"   Content preview: {results[0].get('content', '')[:100]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Vector search test failed: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error checking vector search: {e}")
        return False
    finally:
        client.close()

def create_vector_search_index():
    """
    Create vector search index
    """
    try:
        mongo_uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DATABASE", "pivot_db")
        collection_name = os.getenv("MONGODB_COLLECTION", "documents")
        
        client = MongoClient(mongo_uri)
        db = client[db_name]
        
        logger.info("🔧 Creating vector search index...")
        
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
        try:
            db.command({
                "createSearchIndex": collection_name,
                "name": "vector_index",
                "definition": vector_index
            })
            logger.info("✅ Vector search index creation started!")
            logger.info("⚠️  Note: Index creation may take a few minutes to complete")
            return True
            
        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info("✅ Vector search index already exists")
                return True
            elif "command not found" in str(e):
                logger.error("❌ Vector search not available on this cluster tier")
                logger.info("💡 You need M10 or higher cluster tier for vector search")
                return False
            else:
                logger.error(f"❌ Error creating vector search index: {e}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Error creating vector search index: {e}")
        return False
    finally:
        client.close()

async def reindex_documents():
    """
    Re-index documents with embeddings
    """
    try:
        from services.gemini_client import GeminiClient
        from retriever.mongodb_vectorstore import MongoDBVectorStore
        
        logger.info("🔄 Re-indexing documents with embeddings...")
        
        # Initialize components
        gemini_client = GeminiClient()
        vector_store = MongoDBVectorStore()
        
        # Get all documents without embeddings
        collection = vector_store.collection
        docs_without_embeddings = collection.find({"embedding": {"$exists": False}})
        
        count = 0
        for doc in docs_without_embeddings:
            try:
                # Generate embedding for the document
                content = doc.get("content", "")
                if content:
                    embeddings = await gemini_client.get_embeddings([content])
                    embedding = embeddings[0]
                    
                    # Update document with embedding
                    collection.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {"embedding": embedding}}
                    )
                    count += 1
                    
            except Exception as e:
                logger.error(f"Error processing document {doc.get('_id')}: {e}")
        
        logger.info(f"✅ Re-indexed {count} documents with embeddings")
        return count > 0
        
    except Exception as e:
        logger.error(f"❌ Error re-indexing documents: {e}")
        return False

async def main():
    """
    Main function to fix vector search
    """
    logger.info("🚀 Fixing Vector Search in MongoDB Atlas")
    logger.info("=" * 50)
    
    # Step 1: Check current status
    logger.info("\n📋 Step 1: Checking current vector search status...")
    vector_search_working = check_vector_search_index()
    
    if vector_search_working:
        logger.info("✅ Vector search is working!")
        return
    
    # Step 2: Create vector search index if needed
    logger.info("\n🔧 Step 2: Creating vector search index...")
    index_created = create_vector_search_index()
    
    if not index_created:
        logger.error("❌ Cannot create vector search index")
        logger.info("💡 You need to upgrade to M10 or higher cluster tier")
        return
    
    # Step 3: Re-index documents
    logger.info("\n🔄 Step 3: Re-indexing documents...")
    reindex_success = await reindex_documents()
    
    if reindex_success:
        logger.info("✅ Documents re-indexed successfully!")
    else:
        logger.warning("⚠️  Document re-indexing may have failed")
    
    # Step 4: Final check
    logger.info("\n📋 Step 4: Final vector search check...")
    final_check = check_vector_search_index()
    
    if final_check:
        logger.info("🎉 Vector search is now working!")
    else:
        logger.error("❌ Vector search still not working")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
if __name__ == "__main__":
    main()

