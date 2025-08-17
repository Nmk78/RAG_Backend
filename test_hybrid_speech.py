#!/usr/bin/env python3
"""
Test script to verify hybrid speech transcription (Gemini + Whisper fallback)
"""

import asyncio
import logging
import os
from processors.speech_to_text import SpeechToText

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_hybrid_speech():
    """Test the hybrid speech transcription functionality"""
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
                logger.info(f"✅ Auto transcription successful: {transcription[:100]}...")
            except Exception as e:
                logger.error(f"❌ Auto transcription failed: {str(e)}")
            
            # Test English transcription
            try:
                transcription = await stt.transcribe_english(test_audio_path)
                logger.info(f"✅ English transcription successful: {transcription[:100]}...")
            except Exception as e:
                logger.error(f"❌ English transcription failed: {str(e)}")
            
            # Test Burmese transcription
            try:
                transcription = await stt.transcribe_burmese(test_audio_path)
                logger.info(f"✅ Burmese transcription successful: {transcription[:100]}...")
            except Exception as e:
                logger.error(f"❌ Burmese transcription failed: {str(e)}")
                
        else:
            logger.info("No test audio file found. Testing service initialization...")
            
            # Test that the service is properly initialized
            if stt.gemini_client:
                logger.info("✅ Gemini client initialized successfully")
            else:
                logger.warning("⚠️ Gemini client not initialized - will use Whisper fallback")
            
            # Test the fallback method directly
            try:
                # Create a dummy audio file for testing
                dummy_audio_path = "./data/dummy_test.wav"
                if not os.path.exists("./data"):
                    os.makedirs("./data")
                
                # Create a simple WAV file for testing
                import wave
                import struct
                
                # Create a 1-second silent WAV file
                with wave.open(dummy_audio_path, 'w') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(16000)  # 16kHz
                    
                    # Generate 1 second of silence
                    frames = b'\x00\x00' * 16000  # 16000 samples of silence
                    wav_file.writeframes(frames)
                
                logger.info(f"Created test audio file: {dummy_audio_path}")
                
                # Test fallback transcription
                try:
                    transcription = await stt._transcribe_with_whisper_fallback(dummy_audio_path, "en")
                    logger.info(f"✅ Whisper fallback test successful: {transcription[:100]}...")
                except Exception as e:
                    logger.warning(f"⚠️ Whisper fallback test failed: {str(e)}")
                
                # Clean up test file
                try:
                    os.remove(dummy_audio_path)
                except:
                    pass
                    
            except Exception as e:
                logger.warning(f"⚠️ Could not create test audio file: {str(e)}")
        
        logger.info("Hybrid speech transcription test completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_hybrid_speech())
