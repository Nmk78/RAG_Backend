import os
import logging
import asyncio
import numpy as np

logger = logging.getLogger(__name__)

class SpeechToText:
    """
    Speech-to-text processor using Whisper (supports multiple implementations)
    """
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.whisper_model = None
        self.model_name = "chuuhtetnaing/whisper-tiny-myanmar"
        self.whisper_type = "transformers"  # Force transformers
    
    async def load_model(self, model_name: str = "base", whisper_type: str = "auto"):
        """
        Load Whisper model asynchronously
        """
        try:
            # Temporary override: only use the transformers model for Myanmar
            forced_model = "chuuhtetnaing/whisper-tiny-myanmar"
            forced_type = "transformers"
            if self.model is None or self.model_name != forced_model or self.whisper_type != forced_type:
                logger.info(f"Loading Whisper model: {forced_model} (type: {forced_type})")
                self.whisper_type = forced_type
                self.model_name = forced_model
                await self._load_transformers_whisper(forced_model)
                logger.info(f"Whisper model {forced_model} loaded successfully ({forced_type})")
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
                    try:
                        import transformers  # noqa: F401
                        return "transformers"
                    except ImportError:
                        raise ImportError("No Whisper implementation found. Install faster-whisper, openai-whisper, whisperx, or transformers")
    
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
    
    async def _load_transformers_whisper(self, model_name: str):
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
        self.processor = await asyncio.to_thread(AutoProcessor.from_pretrained, model_name)
        self.whisper_model = await asyncio.to_thread(AutoModelForSpeechSeq2Seq.from_pretrained, model_name)
        
        # Create ASR pipeline with the loaded model and processor
        self.model = await asyncio.to_thread(
            pipeline,
            "automatic-speech-recognition",
            model=self.whisper_model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
        )
    
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
            elif self.whisper_type == "transformers":
                result = await self._transcribe_transformers(audio_file_path)
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
            # Provide more specific error messages for common issues
            if "tensor" in str(e).lower() and "padding" in str(e).lower():
                raise Exception(f"Audio processing error: {str(e)}. This may be due to incompatible audio format or corrupted file.")
            elif "model" in str(e).lower() and "load" in str(e).lower():
                raise Exception(f"Model loading error: {str(e)}. Please check if the model is available.")
            else:
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

    async def _transcribe_transformers(self, audio_file_path: str) -> dict:
        """
        Transcribe using Hugging Face Transformers Whisper pipeline
        """
        logger.info(f"Using Transformers Whisper pipeline for transcription")
        try:
            # Preprocess audio to ensure compatibility
            processed_audio_path = await self._preprocess_audio_for_transformers(audio_file_path)
            
            # Use manual processing to avoid batching issues
            output = await self._process_audio_manually(processed_audio_path)
            logger.info(f"Transformers ASR output: {output}")
            text = output.get("text", "") if isinstance(output, dict) else str(output)
            
            # Clean up processed audio file if it's different from original
            if processed_audio_path != audio_file_path and os.path.exists(processed_audio_path):
                try:
                    os.remove(processed_audio_path)
                except Exception as cleanup_error:
                    logger.warning(f"Could not clean up processed audio: {cleanup_error}")
            
            return {"text": text}
        except Exception as e:
            logger.error(f"Error in Transformers transcription: {str(e)}")
            # Try without language specification as fallback
            try:
                processed_audio_path = await self._preprocess_audio_for_transformers(audio_file_path)
                output = await self._process_audio_manually(processed_audio_path, use_language_hint=False)
                text = output.get("text", "") if isinstance(output, dict) else str(output)
                
                # Clean up processed audio file
                if processed_audio_path != audio_file_path and os.path.exists(processed_audio_path):
                    try:
                        os.remove(processed_audio_path)
                    except Exception as cleanup_error:
                        logger.warning(f"Could not clean up processed audio: {cleanup_error}")
                
                return {"text": text}
            except Exception as fallback_error:
                logger.error(f"Fallback transcription also failed: {str(fallback_error)}")
                raise
    
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

    async def _process_audio_manually(self, audio_file_path: str, use_language_hint: bool = True) -> dict:
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
                inputs = self.processor(
                    audio_tensor, 
                    sampling_rate=sample_rate, 
                    padding=False,  # Disable padding to avoid tensor issues
                    return_tensors="pt"
                )
                
                # Generate with language hint if requested
                if use_language_hint:
                    generated_ids = self.whisper_model.generate(
                        inputs["input_features"],
                        language="my",
                        task="transcribe"
                    )
                else:
                    generated_ids = self.whisper_model.generate(
                        inputs["input_features"]
                    )
                
                # Decode the generated ids
                transcription = self.processor.batch_decode(
                    generated_ids, 
                    skip_special_tokens=True
                )[0]
            
            return {"text": transcription}
            
        except ImportError:
            # Fallback to pipeline if librosa is not available
            logger.warning("librosa not available, falling back to pipeline method")
            return await self._process_audio_with_pipeline(audio_file_path, use_language_hint)
        except Exception as e:
            logger.error(f"Error in manual audio processing: {str(e)}")
            # Fallback to pipeline method
            try:
                return await self._process_audio_with_pipeline(audio_file_path, use_language_hint)
            except Exception as pipeline_error:
                logger.error(f"Pipeline fallback also failed: {str(pipeline_error)}")
                raise

    async def _process_audio_with_pipeline(self, audio_file_path: str, use_language_hint: bool = True) -> dict:
        """
        Fallback method using the pipeline directly
        """
        try:
            # Ensure audio is preprocessed before using pipeline
            processed_audio_path = await self._preprocess_audio_for_transformers(audio_file_path)
            
            if use_language_hint:
                output = await asyncio.to_thread(
                    self.model,
                    processed_audio_path,
                    generate_kwargs={"task": "transcribe", "language": "my"},
                )
            else:
                output = await asyncio.to_thread(
                    self.model,
                    processed_audio_path,
                )
            
            text = output.get("text", "") if isinstance(output, dict) else str(output)
            
            # Clean up processed audio file if it's different from original
            if processed_audio_path != audio_file_path and os.path.exists(processed_audio_path):
                try:
                    os.remove(processed_audio_path)
                except Exception as cleanup_error:
                    logger.warning(f"Could not clean up processed audio: {cleanup_error}")
            
            return {"text": text}
            
        except Exception as e:
            logger.error(f"Error in pipeline audio processing: {str(e)}")
            raise 

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
            # Temporary: always use the fine-tuned Burmese Whisper model via Transformers
            await self.load_model("chuuhtetnaing/whisper-tiny-myanmar", whisper_type="transformers")
            
            # Check if file exists
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Transcribe audio with forced Burmese language
            logger.info(f"Transcribing Burmese audio file: {audio_file_path}")
            logger.info(f"Using Whisper type: {self.whisper_type}, Model: {self.model_name}")
            
            if self.whisper_type == "transformers":
                result = await self._transcribe_transformers(audio_file_path)
                # Ensure language tag
                result["language"] = result.get("language", "my")
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
            # Provide more specific error messages for common issues
            if "tensor" in str(e).lower() and "padding" in str(e).lower():
                raise Exception(f"Audio processing error: {str(e)}. This may be due to incompatible audio format or corrupted file.")
            elif "model" in str(e).lower() and "load" in str(e).lower():
                raise Exception(f"Model loading error: {str(e)}. Please check if the model is available.")
            else:
                raise 
