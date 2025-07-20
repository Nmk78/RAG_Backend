import os
import logging
import asyncio
from typing import Optional
from pydub import AudioSegment

logger = logging.getLogger(__name__)

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = {'.wav', '.mp3', '.m4a', '.aac', '.ogg', '.flac'}

def validate_audio_file(filename: str) -> bool:
    """
    Validate if file is a supported audio file
    """
    from utils.mime_utils import get_file_extension
    file_extension = get_file_extension(filename)
    return file_extension in SUPPORTED_AUDIO_FORMATS

async def convert_audio_format(input_path: str, output_format: str = 'wav') -> str:
    """
    Convert audio file to specified format
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Audio file not found: {input_path}")
        
        # Get file extension
        input_extension = os.path.splitext(input_path)[1].lower()
        
        # If already in target format, return original path
        if input_extension == f'.{output_format}':
            return input_path
        
        # Generate output path
        output_path = os.path.splitext(input_path)[0] + f'.{output_format}'
        
        # Convert audio format
        logger.info(f"Converting {input_path} to {output_format}")
        
        # Load audio file
        audio = await asyncio.to_thread(AudioSegment.from_file, input_path)
        
        # Export to new format
        await asyncio.to_thread(
            audio.export,
            output_path,
            format=output_format
        )
        
        logger.info(f"Audio conversion completed: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error converting audio format: {str(e)}")
        raise

async def get_audio_info(file_path: str) -> dict:
    """
    Get information about an audio file
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # Load audio file
        audio = await asyncio.to_thread(AudioSegment.from_file, file_path)
        
        # Get audio information
        duration_seconds = len(audio) / 1000.0  # Convert from milliseconds
        sample_rate = audio.frame_rate
        channels = audio.channels
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        return {
            "duration_seconds": duration_seconds,
            "duration_formatted": format_duration(duration_seconds),
            "sample_rate": sample_rate,
            "channels": channels,
            "file_size_mb": round(file_size_mb, 2),
            "format": os.path.splitext(file_path)[1].lower()
        }
        
    except Exception as e:
        logger.error(f"Error getting audio info: {str(e)}")
        raise

def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable format
    """
    try:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes:02d}:{remaining_seconds:02d}"
    except Exception:
        return "00:00"

async def normalize_audio(file_path: str, target_db: float = -20.0) -> str:
    """
    Normalize audio to target dB level
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # Load audio file
        audio = await asyncio.to_thread(AudioSegment.from_file, file_path)
        
        # Normalize audio
        normalized_audio = await asyncio.to_thread(
            audio.normalize,
            headroom=target_db
        )
        
        # Generate output path
        output_path = os.path.splitext(file_path)[0] + "_normalized.wav"
        
        # Export normalized audio
        await asyncio.to_thread(
            normalized_audio.export,
            output_path,
            format="wav"
        )
        
        logger.info(f"Audio normalization completed: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error normalizing audio: {str(e)}")
        raise

async def trim_audio(file_path: str, start_seconds: float = 0, end_seconds: Optional[float] = None) -> str:
    """
    Trim audio file to specified time range
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # Load audio file
        audio = await asyncio.to_thread(AudioSegment.from_file, file_path)
        
        # Convert seconds to milliseconds
        start_ms = int(start_seconds * 1000)
        end_ms = int(end_seconds * 1000) if end_seconds else len(audio)
        
        # Trim audio
        trimmed_audio = audio[start_ms:end_ms]
        
        # Generate output path
        output_path = os.path.splitext(file_path)[0] + "_trimmed.wav"
        
        # Export trimmed audio
        await asyncio.to_thread(
            trimmed_audio.export,
            output_path,
            format="wav"
        )
        
        logger.info(f"Audio trimming completed: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error trimming audio: {str(e)}")
        raise

def get_supported_audio_formats() -> dict:
    """
    Get information about supported audio formats
    """
    return {
        "supported_formats": list(SUPPORTED_AUDIO_FORMATS),
        "recommended_format": "wav",
        "max_duration_minutes": 30,
        "max_file_size_mb": 50
    }

async def cleanup_temp_audio_files(directory: str, max_age_hours: int = 24) -> int:
    """
    Clean up temporary audio files older than specified age
    """
    try:
        import time
        from datetime import datetime, timedelta
        
        if not os.path.exists(directory):
            return 0
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        deleted_count = 0
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            if os.path.isfile(file_path):
                # Check if it's a temporary audio file
                if any(filename.endswith(ext) for ext in SUPPORTED_AUDIO_FORMATS):
                    # Check file modification time
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"Deleted old temp file: {file_path}")
        
        logger.info(f"Cleaned up {deleted_count} temporary audio files")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up temp audio files: {str(e)}")
        return 0 