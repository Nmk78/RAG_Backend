#!/usr/bin/env python3
"""
Test Quivel RAG Retrieval

This script tests if the RAG pipeline can now retrieve the Quivel story.
"""

import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_quivel_retrieval():
    """
    Test if RAG can retrieve Quivel story
    """
    try:
        from services.rag_pipeline import RAGPipeline
        
        logger.info("🧪 Testing Quivel Story Retrieval with RAG")
        logger.info("=" * 50)
        
        # Initialize RAG pipeline
        rag = RAGPipeline()
        
        # Test query
        query = "Do you know Quivel?"
        logger.info(f"Query: {query}")
        
        # Retrieve context
        context = await rag.retrieve_context(query)
        
        logger.info(f"Retrieved context length: {len(context)} characters")
        logger.info(f"Context preview: {context[:300]}...")
        
        if "Quivel" in context:
            logger.info("✅ RAG successfully retrieved Quivel context!")
        else:
            logger.warning("⚠️  RAG did not retrieve Quivel context")
        
        # Test another query
        query2 = "Tell me about the boy named Quivel"
        logger.info(f"\nQuery 2: {query2}")
        
        context2 = await rag.retrieve_context(query2)
        
        logger.info(f"Retrieved context length: {len(context2)} characters")
        logger.info(f"Context preview: {context2[:300]}...")
        
        if "Quivel" in context2:
            logger.info("✅ RAG successfully retrieved Quivel context for second query!")
        else:
            logger.warning("⚠️  RAG did not retrieve Quivel context for second query")
        
        # Test with Gemini
        from services.orchestrator import Orchestrator
        
        logger.info("\n🤖 Testing with Gemini...")
        orchestrator = Orchestrator()
        
        response = await orchestrator.handle_text("Do you know Quivel?")
        
        logger.info(f"Gemini Response: {response}")
        
        if "Quivel" in response:
            logger.info("✅ Gemini used Quivel context successfully!")
        else:
            logger.warning("⚠️  Gemini may not have used Quivel context")
        
    except Exception as e:
        logger.error(f"❌ Error testing Quivel RAG: {e}")
        raise

async def main():
    """
    Main test function
    """
    logger.info("🚀 Testing Quivel RAG Retrieval")
    logger.info("=" * 50)
    
    await test_quivel_retrieval()
    
    logger.info("\n✅ Quivel RAG test completed!")

if __name__ == "__main__":
    asyncio.run(main())
