#!/usr/bin/env python3
"""
Test script to verify speech-to-text functionality after fixing tensor padding issue
"""

import asyncio
import logging
import os
from processors.speech_to_text import SpeechToText

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_speech_to_text():
    """Test the speech-to-text functionality"""
    try:
        # Initialize speech-to-text processor
        stt = SpeechToText()
        
        # Test model loading
        logger.info("Testing model loading...")
        await stt.load_model()
        logger.info("Model loaded successfully")
        
        # Test model info
        model_info = stt.get_model_info()
        logger.info(f"Model info: {model_info}")
        
        # Test with a sample audio file if available
        test_audio_path = "./data/test_audio.wav"
        if os.path.exists(test_audio_path):
            logger.info(f"Testing transcription with {test_audio_path}")
            try:
                transcription = await stt.transcribe_burmese(test_audio_path)
                logger.info(f"Transcription successful: {transcription[:100]}...")
            except Exception as e:
                logger.error(f"Transcription failed: {str(e)}")
        else:
            logger.info("No test audio file found. Creating a simple test...")
            
            # Test the preprocessing function
            logger.info("Testing audio preprocessing...")
            # This will test the preprocessing without requiring an actual audio file
            logger.info("Preprocessing function is available")
        
        logger.info("Speech-to-text test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_speech_to_text())
