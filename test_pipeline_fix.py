#!/usr/bin/env python3
"""
Simple test to verify pipeline initialization fix
"""

import asyncio
import logging
from processors.speech_to_text import SpeechToText

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_pipeline_initialization():
    """Test that the pipeline initializes correctly without invalid parameters"""
    try:
        # Initialize speech-to-text processor
        stt = SpeechToText()
        
        # Test model loading - this should not raise the padding parameter error
        logger.info("Testing pipeline initialization...")
        await stt.load_model()
        logger.info("✅ Pipeline initialized successfully!")
        
        # Test model info
        model_info = stt.get_model_info()
        logger.info(f"✅ Model info: {model_info}")
        
        logger.info("✅ All tests passed! The tensor padding issue has been resolved.")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        if "padding" in str(e).lower():
            logger.error("❌ The padding parameter issue is still present!")
        raise

if __name__ == "__main__":
    asyncio.run(test_pipeline_initialization())
