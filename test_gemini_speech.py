#!/usr/bin/env python3
"""
Test script to verify Gemini-based speech transcription
"""

import asyncio
import logging
import os
from processors.speech_to_text import SpeechToText

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_gemini_speech():
    """Test the Gemini-based speech transcription functionality"""
    try:
        # Initialize speech-to-text processor
        stt = SpeechToText()
        
        # Test model info
        model_info = stt.get_model_info()
        logger.info(f"Model info: {model_info}")
        
        # Test with a sample audio file if available
        test_audio_path = "./data/test_audio.wav"
        if os.path.exists(test_audio_path):
            logger.info(f"Testing transcription with {test_audio_path}")
            
            # Test automatic language detection
            try:
                transcription = await stt.transcribe_auto(test_audio_path)
                logger.info(f"Auto transcription successful: {transcription[:100]}...")
            except Exception as e:
                logger.error(f"Auto transcription failed: {str(e)}")
            
            # Test English transcription
            try:
                transcription = await stt.transcribe_english(test_audio_path)
                logger.info(f"English transcription successful: {transcription[:100]}...")
            except Exception as e:
                logger.error(f"English transcription failed: {str(e)}")
            
            # Test Burmese transcription
            try:
                transcription = await stt.transcribe_burmese(test_audio_path)
                logger.info(f"Burmese transcription successful: {transcription[:100]}...")
            except Exception as e:
                logger.error(f"Burmese transcription failed: {str(e)}")
                
        else:
            logger.info("No test audio file found. Testing service initialization...")
            
            # Test that the service is properly initialized
            if stt.gemini_client:
                logger.info("✅ Gemini client initialized successfully")
            else:
                logger.error("❌ Gemini client not initialized")
        
        logger.info("Gemini speech transcription test completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_gemini_speech())
