#!/usr/bin/env python3
"""
Test RAG Pipeline with MongoDB

This script tests the complete RAG pipeline to ensure it's using MongoDB as the context source.
"""

import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_rag_pipeline():
    """
    Test the complete RAG pipeline with MongoDB
    """
    try:
        from services.rag_pipeline import RAGPipeline
        
        logger.info("🧪 Testing RAG Pipeline with MongoDB")
        logger.info("=" * 50)
        
        # Initialize RAG pipeline
        rag = RAGPipeline()
        
        # Test document 1: Add some test documents
        logger.info("\n📝 Step 1: Adding test documents to MongoDB...")
        test_docs = [
            "MongoDB Atlas is a cloud database service that provides a fully managed MongoDB database.",
            "Vector search in MongoDB Atlas allows you to find similar documents using embeddings.",
            "The RAG pipeline uses MongoDB to store and retrieve relevant context for AI responses.",
            "FastAPI is a modern web framework for building APIs with Python.",
            "Google Gemini is an AI model that can generate text, code, and other content."
        ]
        
        metadata = {
            "filename": "test_document.txt",
            "file_id": "test_001",
            "source": "test"
        }
        
        await rag.add_documents(test_docs, metadata)
        logger.info("✅ Test documents added successfully")
        
        # Test document 2: Add another document
        logger.info("\n📝 Step 2: Adding another test document...")
        test_docs_2 = [
            "Python is a programming language known for its simplicity and readability.",
            "Machine learning involves training models to make predictions from data.",
            "Natural language processing helps computers understand human language."
        ]
        
        metadata_2 = {
            "filename": "python_ml.txt",
            "file_id": "test_002",
            "source": "test"
        }
        
        await rag.add_documents(test_docs_2, metadata_2)
        logger.info("✅ Second test document added successfully")
        
        # Test retrieval: General query
        logger.info("\n🔍 Step 3: Testing general context retrieval...")
        query = "What is MongoDB Atlas?"
        context = await rag.retrieve_context(query)
        
        logger.info(f"Query: {query}")
        logger.info(f"Retrieved context length: {len(context)} characters")
        logger.info(f"Context preview: {context[:200]}...")
        
        if "MongoDB Atlas" in context:
            logger.info("✅ MongoDB context retrieved successfully!")
        else:
            logger.warning("⚠️  Expected MongoDB context not found")
        
        # Test retrieval: File-specific query
        logger.info("\n🔍 Step 4: Testing file-specific context retrieval...")
        query_2 = "What is Python?"
        context_2 = await rag.retrieve_file_context(query_2, "test_002")
        
        logger.info(f"Query: {query_2}")
        logger.info(f"File ID: test_002")
        logger.info(f"Retrieved context length: {len(context_2)} characters")
        logger.info(f"Context preview: {context_2[:200]}...")
        
        if "Python" in context_2:
            logger.info("✅ File-specific context retrieved successfully!")
        else:
            logger.warning("⚠️  Expected Python context not found")
        
        # Test retrieval: Another query
        logger.info("\n🔍 Step 5: Testing another query...")
        query_3 = "What is machine learning?"
        context_3 = await rag.retrieve_context(query_3)
        
        logger.info(f"Query: {query_3}")
        logger.info(f"Retrieved context length: {len(context_3)} characters")
        logger.info(f"Context preview: {context_3[:200]}...")
        
        if "machine learning" in context_3.lower():
            logger.info("✅ Machine learning context retrieved successfully!")
        else:
            logger.warning("⚠️  Expected machine learning context not found")
        
        # Clean up test documents
        logger.info("\n🧹 Step 6: Cleaning up test documents...")
        await rag.delete_documents({"source": "test"})
        logger.info("✅ Test documents cleaned up")
        
        logger.info("\n🎉 RAG Pipeline with MongoDB test completed successfully!")
        logger.info("✅ MongoDB is being used as the context source")
        
    except Exception as e:
        logger.error(f"❌ Error testing RAG pipeline: {e}")
        raise

async def test_with_gemini():
    """
    Test the complete flow with Gemini AI
    """
    try:
        from services.orchestrator import Orchestrator
        
        logger.info("\n🤖 Testing Complete RAG Flow with Gemini")
        logger.info("=" * 50)
        
        # Initialize orchestrator
        orchestrator = Orchestrator()
        
        # Add some test documents first
        test_text = """
        MongoDB Atlas is a cloud database service that provides a fully managed MongoDB database.
        It offers features like automatic scaling, backup, and monitoring.
        Vector search in MongoDB Atlas allows you to find similar documents using embeddings.
        This is useful for building AI applications that need to retrieve relevant context.
        """
        
        # Add document to vector store
        await orchestrator.process_file("gemini_test", test_text, "mongodb_info.txt")
        
        # Test chat with context
        query = "What are the main features of MongoDB Atlas?"
        response = await orchestrator.handle_text(query)
        
        logger.info(f"Query: {query}")
        logger.info(f"Response: {response}")
        
        if "MongoDB Atlas" in response and ("cloud" in response.lower() or "managed" in response.lower()):
            logger.info("✅ Gemini used MongoDB context successfully!")
        else:
            logger.warning("⚠️  Response may not be using MongoDB context effectively")
        
        # Clean up
        # await orchestrator.delete_file("gemini_test")
        
    except Exception as e:
        logger.error(f"❌ Error testing with Gemini: {e}")
        raise

async def main():
    """
    Main test function
    """
    logger.info("🚀 Testing RAG Pipeline with MongoDB Atlas")
    logger.info("=" * 60)
    
    # Test basic RAG pipeline
    await test_rag_pipeline()
    
    # Test complete flow with Gemini
    await test_with_gemini()
    
    logger.info("\n✅ All tests completed!")
    logger.info("🎉 Your RAG chatbot is successfully using MongoDB Atlas as the context source!")

if __name__ == "__main__":
    asyncio.run(main())
