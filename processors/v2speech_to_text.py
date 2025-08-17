import os
import logging
import asyncio
import numpy as np

logger = logging.getLogger(__name__)

class SpeechToText:
    """
    Speech-to-text processor using Whisper with support for English and Burmese
    """
    
    def __init__(self):
        self.models = {}  # Store multiple models for different languages
        self.processors = {}
        self.whisper_models = {}
        self.current_model = None
        self.current_processor = None
        self.current_whisper_model = None
        
        # Model configurations
        self.model_configs = {
            "multilingual": {
                "name": "openai/whisper-base",
                "type": "transformers",
                "languages": ["en", "my", "auto"]
            },
            "burmese": {
                "name": "chuuhtetnaing/whisper-tiny-myanmar", 
                "type": "transformers",
                "languages": ["my"]
            },
            "english": {
                "name": "openai/whisper-base",
                "type": "transformers", 
                "languages": ["en"]
            }
        }
    
    async def load_model(self, model_key: str = "multilingual"):
        """
        Load Whisper model asynchronously
        """
        try:
            if model_key not in self.model_configs:
                raise ValueError(f"Unknown model key: {model_key}")
            
            config = self.model_configs[model_key]
            
            if model_key not in self.models:
                logger.info(f"Loading Whisper model: {config['name']} (type: {config['type']})")
                await self._load_transformers_whisper(config['name'], model_key)
                logger.info(f"Whisper model {config['name']} loaded successfully")
            
            # Set as current model
            self.current_model = self.models[model_key]
            self.current_processor = self.processors[model_key]
            self.current_whisper_model = self.whisper_models[model_key]
            
        except Exception as e:
            logger.error(f"Error loading Whisper model: {str(e)}")
            raise
    
    async def _load_transformers_whisper(self, model_name: str, model_key: str):
        """
        Load Hugging Face Transformers Whisper pipeline
        """
        try:
            from transformers import pipeline, AutoProcessor, AutoModelForSpeechSeq2Seq
        except ImportError as import_error:
            raise ImportError(
                "Missing dependency: transformers. Install with 'pip install transformers torch'"
            ) from import_error
        
        # Load model and processor separately for better control
        logger.info(f"Loading model and processor for {model_name}")
        processor = await asyncio.to_thread(AutoProcessor.from_pretrained, model_name)
        whisper_model = await asyncio.to_thread(AutoModelForSpeechSeq2Seq.from_pretrained, model_name)
        
        # Create ASR pipeline with the loaded model and processor
        model = await asyncio.to_thread(
            pipeline,
            "automatic-speech-recognition",
            model=whisper_model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
        )
        
        # Store the loaded components
        self.models[model_key] = model
        self.processors[model_key] = processor
        self.whisper_models[model_key] = whisper_model
    
    async def transcribe(self, audio_file_path: str, language: str = "auto") -> str:
        """
        Transcribe audio file to text with automatic language detection
        """
        try:
            # Check if file exists
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Determine which model to use based on language
            if language == "auto":
                # Use multilingual model for automatic detection
                await self.load_model("multilingual")
                result = await self._transcribe_with_language_detection(audio_file_path)
            elif language == "my":
                # Use Burmese-specific model
                await self.load_model("burmese")
                result = await self._transcribe_transformers(audio_file_path, force_language="my")
            elif language == "en":
                # Use English model
                await self.load_model("english")
                result = await self._transcribe_transformers(audio_file_path, force_language="en")
            else:
                # Default to multilingual
                await self.load_model("multilingual")
                result = await self._transcribe_with_language_detection(audio_file_path)
            
            # Extract transcription text
            transcription = result.get("text", "").strip()
            detected_language = result.get("language", "unknown")
            
            logger.info(f"Transcription completed: {len(transcription)} characters")
            logger.info(f"Detected language: {detected_language}")
            logger.info(f"Transcription text: {transcription[:200]}...")
            
            return transcription
            
        except Exception as e:
            logger.error(f"Error transcribing audio {audio_file_path}: {str(e)}")
            if "tensor" in str(e).lower() and "padding" in str(e).lower():
                raise Exception(f"Audio processing error: {str(e)}. This may be due to incompatible audio format or corrupted file.")
            elif "model" in str(e).lower() and "load" in str(e).lower():
                raise Exception(f"Model loading error: {str(e)}. Please check if the model is available.")
            else:
                raise
    
    async def _transcribe_with_language_detection(self, audio_file_path: str) -> dict:
        """
        Transcribe with automatic language detection
        """
        logger.info("Using automatic language detection")
        
        try:
            # First, try to detect language without forcing any specific language
            result = await self._transcribe_transformers(audio_file_path, force_language=None)
            
            # If no language detected or confidence is low, try both languages
            detected_lang = result.get("language", "")
            if not detected_lang or detected_lang not in ["en", "my"]:
                logger.info("Language detection unclear, trying both models...")
                
                # Try English model
                try:
                    await self.load_model("english")
                    english_result = await self._transcribe_transformers(audio_file_path, force_language="en")
                    english_text = english_result.get("text", "").strip()
                    
                    # Try Burmese model
                    await self.load_model("burmese")
                    burmese_result = await self._transcribe_transformers(audio_file_path, force_language="my")
                    burmese_text = burmese_result.get("text", "").strip()
                    
                    # Choose the result with more content (heuristic)
                    if len(english_text) > len(burmese_text):
                        result = english_result
                        result["language"] = "en"
                        logger.info("Selected English transcription")
                    else:
                        result = burmese_result
                        result["language"] = "my"
                        logger.info("Selected Burmese transcription")
                        
                except Exception as e:
                    logger.warning(f"Fallback transcription failed: {str(e)}")
                    # Return original result
                    pass
            
            return result
            
        except Exception as e:
            logger.error(f"Error in language detection transcription: {str(e)}")
            raise
    
    async def _transcribe_transformers(self, audio_file_path: str, force_language: str = None) -> dict:
        """
        Transcribe using Hugging Face Transformers Whisper pipeline
        """
        logger.info(f"Using Transformers Whisper pipeline for transcription (language: {force_language or 'auto'})")
        
        try:
            # Preprocess audio to ensure compatibility
            processed_audio_path = await self._preprocess_audio_for_transformers(audio_file_path)
            
            # Use manual processing to avoid batching issues
            output = await self._process_audio_manually(processed_audio_path, force_language)
            logger.info(f"Transformers ASR output: {output}")
            
            # Clean up processed audio file if it's different from original
            if processed_audio_path != audio_file_path and os.path.exists(processed_audio_path):
                try:
                    os.remove(processed_audio_path)
                except Exception as cleanup_error:
                    logger.warning(f"Could not clean up processed audio: {cleanup_error}")
            
            return output
            
        except Exception as e:
            logger.error(f"Error in Transformers transcription: {str(e)}")
            # Try fallback without language specification
            try:
                processed_audio_path = await self._preprocess_audio_for_transformers(audio_file_path)
                output = await self._process_audio_manually(processed_audio_path, None)
                
                # Clean up processed audio file
                if processed_audio_path != audio_file_path and os.path.exists(processed_audio_path):
                    try:
                        os.remove(processed_audio_path)
                    except Exception as cleanup_error:
                        logger.warning(f"Could not clean up processed audio: {cleanup_error}")
                
                return output
            except Exception as fallback_error:
                logger.error(f"Fallback transcription also failed: {str(fallback_error)}")
                raise
    
    async def _preprocess_audio_for_transformers(self, audio_file_path: str) -> str:
        """
        Preprocess audio file to ensure compatibility with Transformers pipeline
        """
        try:
            from pydub import AudioSegment
            
            # Load audio file
            audio = await asyncio.to_thread(AudioSegment.from_file, audio_file_path)
            
            # Convert to mono if stereo
            if audio.channels > 1:
                audio = audio.set_channels(1)
                logger.info("Converted stereo audio to mono")
            
            # Resample to 16kHz if needed (Whisper standard)
            if audio.frame_rate != 16000:
                audio = audio.set_frame_rate(16000)
                logger.info(f"Resampled audio from {audio.frame_rate}Hz to 16000Hz")
            
            # Normalize audio levels
            audio = audio.normalize()
            
            # Ensure minimum duration to avoid tensor issues
            min_duration_ms = 1000  # 1 second minimum
            if len(audio) < min_duration_ms:
                # Pad with silence to reach minimum duration
                silence = AudioSegment.silent(duration=min_duration_ms - len(audio))
                audio = audio + silence
                logger.info(f"Padded audio to minimum duration of {min_duration_ms}ms")
            
            # Generate output path
            output_path = os.path.splitext(audio_file_path)[0] + "_processed.wav"
            
            # Export as WAV with specific parameters
            await asyncio.to_thread(
                audio.export,
                output_path,
                format="wav",
                parameters=["-ar", "16000", "-ac", "1"]  # 16kHz, mono
            )
            
            logger.info(f"Audio preprocessed and saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error preprocessing audio: {str(e)}")
            # Return original path if preprocessing fails
            return audio_file_path

    async def _process_audio_manually(self, audio_file_path: str, force_language: str = None) -> dict:
        """
        Process audio manually to avoid batching issues with the pipeline
        """
        try:
            import torch
            import librosa
            
            # Load audio using librosa
            audio_array, sample_rate = await asyncio.to_thread(
                librosa.load, audio_file_path, sr=16000
            )
            
            # Ensure audio is mono
            if len(audio_array.shape) > 1:
                audio_array = audio_array.mean(axis=1)
            
            # Ensure minimum length to avoid tensor issues
            min_length = 1 * sample_rate  # 1 second minimum
            if len(audio_array) < min_length:
                # Pad with zeros to reach minimum length
                padding_length = min_length - len(audio_array)
                audio_array = np.pad(audio_array, (0, padding_length), mode='constant')
                logger.info(f"Padded audio to minimum length of {min_length} samples")
            
            # Convert to tensor
            audio_tensor = torch.tensor(audio_array).unsqueeze(0)  # Add batch dimension
            
            # Process with the model
            with torch.no_grad():
                # Prepare inputs without padding to avoid batching issues
                inputs = self.current_processor(
                    audio_tensor, 
                    sampling_rate=sample_rate, 
                    padding=False,  # Disable padding to avoid tensor issues
                    return_tensors="pt"
                )
                
                # Generate with language hint if specified
                if force_language:
                    generated_ids = self.current_whisper_model.generate(
                        inputs["input_features"],
                        language=force_language,
                        task="transcribe"
                    )
                else:
                    # Let the model auto-detect language
                    generated_ids = self.current_whisper_model.generate(
                        inputs["input_features"]
                    )
                
                # Decode the generated ids
                transcription = self.current_processor.batch_decode(
                    generated_ids, 
                    skip_special_tokens=True
                )[0]
            
            # Try to detect language from the generated ids
            detected_language = "unknown"
            if not force_language:
                try:
                    # Extract language token if present
                    if len(generated_ids) > 0 and len(generated_ids[0]) > 0:
                        lang_token = generated_ids[0][0].item()
                        # Map token to language (this is model-specific)
                        if hasattr(self.current_processor.tokenizer, 'convert_ids_to_tokens'):
                            lang_str = self.current_processor.tokenizer.convert_ids_to_tokens(lang_token)
                            if lang_str and lang_str.startswith('<'):
                                detected_language = lang_str.strip('<>')
                except Exception as e:
                    logger.warning(f"Could not detect language: {str(e)}")
            else:
                detected_language = force_language
            
            return {"text": transcription, "language": detected_language}
            
        except ImportError:
            # Fallback to pipeline if librosa is not available
            logger.warning("librosa not available, falling back to pipeline method")
            return await self._process_audio_with_pipeline(audio_file_path, force_language)
        except Exception as e:
            logger.error(f"Error in manual audio processing: {str(e)}")
            # Fallback to pipeline method
            try:
                return await self._process_audio_with_pipeline(audio_file_path, force_language)
            except Exception as pipeline_error:
                logger.error(f"Pipeline fallback also failed: {str(pipeline_error)}")
                raise

    async def _process_audio_with_pipeline(self, audio_file_path: str, force_language: str = None) -> dict:
        """
        Fallback method using the pipeline directly
        """
        try:
            # Ensure audio is preprocessed before using pipeline
            processed_audio_path = await self._preprocess_audio_for_transformers(audio_file_path)
            
            if force_language:
                output = await asyncio.to_thread(
                    self.current_model,
                    processed_audio_path,
                    generate_kwargs={"task": "transcribe", "language": force_language},
                )
            else:
                output = await asyncio.to_thread(
                    self.current_model,
                    processed_audio_path,
                )
            
            text = output.get("text", "") if isinstance(output, dict) else str(output)
            detected_language = force_language or "unknown"
            
            # Clean up processed audio file if it's different from original
            if processed_audio_path != audio_file_path and os.path.exists(processed_audio_path):
                try:
                    os.remove(processed_audio_path)
                except Exception as cleanup_error:
                    logger.warning(f"Could not clean up processed audio: {cleanup_error}")
            
            return {"text": text, "language": detected_language}
            
        except Exception as e:
            logger.error(f"Error in pipeline audio processing: {str(e)}")
            raise

    def get_supported_languages(self) -> list:
        """
        Get list of supported languages for transcription
        """
        return ["en", "my", "auto"]  # English, Burmese, and auto-detection

    def get_model_info(self) -> dict:
        """
        Get information about the loaded models
        """
        loaded_models = list(self.models.keys())
        return {
            "loaded_models": loaded_models,
            "current_model": list(self.models.keys())[-1] if self.models else None,
            "supported_languages": self.get_supported_languages(),
            "model_configs": self.model_configs
        }

    async def transcribe_burmese(self, audio_file_path: str) -> str:
        """
        Transcribe audio file to text with forced Burmese language detection
        """
        return await self.transcribe(audio_file_path, language="my")

    async def transcribe_english(self, audio_file_path: str) -> str:
        """
        Transcribe audio file to text with forced English language detection
        """
        return await self.transcribe(audio_file_path, language="en")

    async def transcribe_auto(self, audio_file_path: str) -> str:
        """
        Transcribe audio file to text with automatic language detection
        """
        return await self.transcribe(audio_file_path, language="auto") 
