import os
import logging
import asyncio

logger = logging.getLogger(__name__)

class SpeechToText:
    """
    Speech-to-text processor using Whisper (supports multiple implementations)
    """
    
    def __init__(self):
        self.model = None
        self.model_name = "base"  # Can be "tiny", "base", "small", "medium", "large"
        self.whisper_type = None  # "openai", "faster", or "whisperx"
    
    async def load_model(self, model_name: str = "base", whisper_type: str = "auto"):
        """
        Load Whisper model asynchronously
        """
        try:
            if self.model is None or self.model_name != model_name or self.whisper_type != whisper_type:
                logger.info(f"Loading Whisper model: {model_name} (type: {whisper_type})")
                
                # Auto-detect available Whisper implementation
                if whisper_type == "auto":
                    whisper_type = self._detect_whisper_implementation()
                
                self.whisper_type = whisper_type
                self.model_name = model_name
                
                if whisper_type == "faster":
                    await self._load_faster_whisper(model_name)
                elif whisper_type == "openai":
                    await self._load_openai_whisper(model_name)
                elif whisper_type == "whisperx":
                    await self._load_whisperx(model_name)
                else:
                    raise ValueError(f"Unsupported Whisper type: {whisper_type}")
                
                logger.info(f"Whisper model {model_name} loaded successfully ({whisper_type})")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {str(e)}")
            raise
    
    def _detect_whisper_implementation(self) -> str:
        """
        Auto-detect available Whisper implementation
        """
        try:
            import faster_whisper
            return "faster"
        except ImportError:
            try:
                import whisper
                return "openai"
            except ImportError:
                try:
                    import whisperx
                    return "whisperx"
                except ImportError:
                    raise ImportError("No Whisper implementation found. Install faster-whisper, openai-whisper, or whisperx")
    
    async def _load_faster_whisper(self, model_name: str):
        """
        Load faster-whisper model
        """
        import faster_whisper
        self.model = await asyncio.to_thread(faster_whisper.WhisperModel, model_name)
    
    async def _load_openai_whisper(self, model_name: str):
        """
        Load OpenAI Whisper model
        """
        import whisper
        self.model = await asyncio.to_thread(whisper.load_model, model_name)
    
    async def _load_whisperx(self, model_name: str):
        """
        Load WhisperX model
        """
        import whisperx
        self.model = await asyncio.to_thread(whisperx.load_model, model_name)
    
    async def transcribe(self, audio_file_path: str, model_name: str = "base") -> str:
        """
        Transcribe audio file to text
        """
        try:
            # Load model if not loaded
            await self.load_model(model_name)
            
            # Check if file exists
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Transcribe audio based on implementation
            logger.info(f"Transcribing audio file: {audio_file_path}")
            logger.info(f"Using Whisper type: {self.whisper_type}, Model: {self.model_name}")
            
            if self.whisper_type == "faster":
                result = await self._transcribe_faster_whisper(audio_file_path)
            elif self.whisper_type == "openai":
                result = await self._transcribe_openai_whisper(audio_file_path)
            elif self.whisper_type == "whisperx":
                result = await self._transcribe_whisperx(audio_file_path)
            else:
                raise ValueError(f"Unsupported Whisper type: {self.whisper_type}")
            
            # Log the full result to see language detection info
            logger.info(f"Transcription result: {result}")
            
            # Extract transcription text
            transcription = result.get("text", "").strip()
            
            # Log detected language if available
            if "language" in result:
                logger.info(f"Detected language: {result['language']} (confidence: {result.get('language_probability', 'N/A')})")
            elif "lang" in result:
                logger.info(f"Detected language: {result['lang']}")
            
            if not transcription:
                logger.warning("No transcription generated from audio file")
                return ""
            
            logger.info(f"Transcription completed: {len(transcription)} characters")
            logger.info(f"Transcription text: {transcription[:200]}...")  # Log first 200 chars
            return transcription
            
        except Exception as e:
            logger.error(f"Error transcribing audio {audio_file_path}: {str(e)}")
            raise
    
    async def _transcribe_faster_whisper(self, audio_file_path: str) -> dict:
        """
        Transcribe using faster-whisper
        """
        logger.info(f"Using faster-whisper for transcription")
        segments, info = await asyncio.to_thread(self.model.transcribe, audio_file_path)
        logger.info(f"Faster-whisper info: {info}")
        
        # Convert generator to list to get count and process segments
        segments_list = list(segments)
        logger.info(f"Number of segments: {len(segments_list)}")
        
        text = " ".join([segment.text for segment in segments_list])
        result = {"text": text}
        
        # Add language info if available
        if hasattr(info, 'language') and info.language:
            result["language"] = info.language
            result["language_probability"] = getattr(info, 'language_probability', None)
            logger.info(f"Faster-whisper detected language: {info.language}")
        
        return result
    
    async def _transcribe_openai_whisper(self, audio_file_path: str) -> dict:
        """
        Transcribe using OpenAI Whisper
        """
        logger.info(f"Using OpenAI Whisper for transcription")
        result = await asyncio.to_thread(self.model.transcribe, audio_file_path)
        logger.info(f"OpenAI Whisper result: {result}")
        
        # OpenAI Whisper includes language info in the result
        if "language" in result:
            logger.info(f"OpenAI Whisper detected language: {result['language']}")
        
        return result
    
    async def _transcribe_whisperx(self, audio_file_path: str) -> dict:
        """
        Transcribe using WhisperX
        """
        logger.info(f"Using WhisperX for transcription")
        result = await asyncio.to_thread(self.model.transcribe, audio_file_path)
        logger.info(f"WhisperX result: {result}")
        
        # Extract text from segments
        text = result["segments"][0]["text"] if result["segments"] else ""
        
        # WhisperX might include language info
        if "language" in result:
            logger.info(f"WhisperX detected language: {result['language']}")
        
        return {"text": text, "language": result.get("language")}
    
    async def transcribe_with_timestamps(self, audio_file_path: str, model_name: str = "base") -> dict:
        """
        Transcribe audio with timestamps
        """
        try:
            # Load model if needed
            await self.load_model(model_name)
            
            # Check if file exists
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Transcribe with word-level timestamps
            logger.info(f"Transcribing audio with timestamps: {audio_file_path}")
            result = await asyncio.to_thread(
                self.model.transcribe,
                audio_file_path,
                word_timestamps=True
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error transcribing audio with timestamps {audio_file_path}: {str(e)}")
            raise
    
    def get_supported_languages(self) -> list:
        """
        Get list of supported languages for transcription
        Focused on Burmese and English only
        """
        return ["my", "en"]  # Burmese first, then English

    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model
        """
        return {
            "model_name": self.model_name,
            "model_loaded": self.model is not None,
            "supported_languages": self.get_supported_languages()
        } 

    def synthesize_speech(self, text: str, output_path: str, voice: str = None, rate: int = None) -> bool:
        """
        Synthesize speech from text and save to output_path (Text-to-Speech)
        Uses pyttsx3 for cross-platform TTS.
        """
        try:
            import pyttsx3
            engine = pyttsx3.init()
            if voice:
                engine.setProperty('voice', voice)
            if rate:
                engine.setProperty('rate', rate)
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            logger.info(f"Synthesized speech saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error synthesizing speech: {str(e)}")
            return False

    async def transcribe_burmese(self, audio_file_path: str, model_name: str = "base") -> str:
        """
        Transcribe audio file to text with forced Burmese language detection
        """
        try:
            # Load model if not loaded
            await self.load_model(model_name)
            
            # Check if file exists
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Transcribe audio with forced Burmese language
            logger.info(f"Transcribing Burmese audio file: {audio_file_path}")
            logger.info(f"Using Whisper type: {self.whisper_type}, Model: {self.model_name}")
            
            if self.whisper_type == "faster":
                segments, info = await asyncio.to_thread(
                    self.model.transcribe, 
                    audio_file_path, 
                    language="my",  # Force Burmese language detection
                    task="transcribe"  # Explicitly set task
                )
                logger.info(f"Faster-whisper Burmese transcription info: {info}")
                # Convert generator to list to process segments
                segments_list = list(segments)
                logger.info(f"Number of segments: {len(segments_list)}")
                text = " ".join([segment.text for segment in segments_list])
                result = {"text": text, "language": "my"}
            elif self.whisper_type == "openai":
                result = await asyncio.to_thread(
                    self.model.transcribe, 
                    audio_file_path, 
                    language="my"  # Force Burmese language detection
                )
                logger.info(f"OpenAI Whisper Burmese transcription result: {result}")
            elif self.whisper_type == "whisperx":
                result = await asyncio.to_thread(
                    self.model.transcribe, 
                    audio_file_path, 
                    language="my"  # Force Burmese language detection
                )
                logger.info(f"WhisperX Burmese transcription result: {result}")
            else:
                raise ValueError(f"Unsupported Whisper type: {self.whisper_type}")
            
            # Extract transcription text
            transcription = result.get("text", "").strip()
            
            if not transcription:
                logger.warning("No transcription generated from Burmese audio file")
                return ""
            
            logger.info(f"Burmese transcription completed: {len(transcription)} characters")
            logger.info(f"Burmese transcription text: {transcription[:200]}...")  # Log first 200 chars
            return transcription
            
        except Exception as e:
            logger.error(f"Error transcribing Burmese audio {audio_file_path}: {str(e)}")
            raise 
