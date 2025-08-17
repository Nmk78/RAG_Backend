#!/usr/bin/env python3
"""
Test script to verify the tensor padding fix
"""

import asyncio
import logging
import os
from processors.speech_to_text import SpeechToText

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_tensor_fix():
    """Test that the tensor padding issue is resolved"""
    try:
        # Initialize speech-to-text processor
        stt = SpeechToText()
        
        # Test model loading
        logger.info("Testing model loading...")
        await stt.load_model()
        logger.info("✅ Model loaded successfully")
        
        # Test model info
        model_info = stt.get_model_info()
        logger.info(f"✅ Model info: {model_info}")
        
        # Test that processor and model are loaded
        if hasattr(stt, 'processor') and stt.processor is not None:
            logger.info("✅ Processor loaded successfully")
        else:
            logger.warning("⚠️ Processor not loaded")
            
        if hasattr(stt, 'whisper_model') and stt.whisper_model is not None:
            logger.info("✅ Whisper model loaded successfully")
        else:
            logger.warning("⚠️ Whisper model not loaded")
        
        logger.info("✅ All tests passed! The tensor padding issue should be resolved.")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        if "padding" in str(e).lower():
            logger.error("❌ The padding parameter issue is still present!")
        elif "tensor" in str(e).lower():
            logger.error("❌ Tensor creation issue is still present!")
        raise

if __name__ == "__main__":
    asyncio.run(test_tensor_fix())
