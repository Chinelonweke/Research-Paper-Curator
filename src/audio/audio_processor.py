"""
Audio processing utilities.
Handles audio format conversion, validation, and preprocessing.
"""
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Union
import soundfile as sf
from pydub import AudioSegment
from src.core.logging_config import app_logger


class AudioProcessor:
    """
    Audio processing utilities.
    
    Features:
    - Format conversion
    - Audio validation
    - Noise reduction
    - Volume normalization
    """
    
    SUPPORTED_FORMATS = {'.wav', '.mp3', '.ogg', '.flac', '.m4a', '.webm'}
    
    @staticmethod
    def load_audio(file_path: Union[str, Path]) -> Tuple[np.ndarray, int]:
        """
        Load audio file.
        
        Args:
            file_path: Path to audio file
        
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        try:
            file_path = Path(file_path)
            
            if file_path.suffix not in AudioProcessor.SUPPORTED_FORMATS:
                raise ValueError(f"Unsupported audio format: {file_path.suffix}")
            
            # Load using soundfile
            data, samplerate = sf.read(str(file_path))
            
            app_logger.info(f"Loaded audio: {file_path} ({samplerate} Hz, {len(data)} samples)")
            
            return data, samplerate
        
        except Exception as e:
            app_logger.error(f"Error loading audio: {e}")
            raise
    
    @staticmethod
    def save_audio(
        audio_data: np.ndarray,
        output_path: Union[str, Path],
        sample_rate: int = 22050
    ):
        """
        Save audio to file.
        
        Args:
            audio_data: Audio data as numpy array
            output_path: Output file path
            sample_rate: Sample rate
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            sf.write(str(output_path), audio_data, sample_rate)
            
            app_logger.info(f"Saved audio to: {output_path}")
        
        except Exception as e:
            app_logger.error(f"Error saving audio: {e}")
            raise
    
    @staticmethod
    def convert_format(
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        output_format: str = 'wav'
    ):
        """
        Convert audio format.
        
        Args:
            input_path: Input audio file
            output_path: Output audio file
            output_format: Target format (wav, mp3, ogg)
        """
        try:
            audio = AudioSegment.from_file(str(input_path))
            audio.export(str(output_path), format=output_format)
            
            app_logger.info(f"Converted {input_path} to {output_format}")
        
        except Exception as e:
            app_logger.error(f"Error converting audio format: {e}")
            raise
    
    @staticmethod
    def normalize_volume(audio_data: np.ndarray, target_level: float = 0.5) -> np.ndarray:
        """
        Normalize audio volume.
        
        Args:
            audio_data: Audio data
            target_level: Target volume level (0.0 to 1.0)
        
        Returns:
            Normalized audio data
        """
        try:
            max_val = np.abs(audio_data).max()
            
            if max_val > 0:
                normalized = audio_data * (target_level / max_val)
            else:
                normalized = audio_data
            
            return normalized
        
        except Exception as e:
            app_logger.error(f"Error normalizing audio: {e}")
            return audio_data
    
    @staticmethod
    def validate_audio(file_path: Union[str, Path]) -> dict:
        """
        Validate audio file.
        
        Args:
            file_path: Path to audio file
        
        Returns:
            Validation results
        """
        try:
            file_path = Path(file_path)
            
            # Check file exists
            if not file_path.exists():
                return {"valid": False, "error": "File not found"}
            
            # Check format
            if file_path.suffix not in AudioProcessor.SUPPORTED_FORMATS:
                return {"valid": False, "error": f"Unsupported format: {file_path.suffix}"}
            
            # Load and check audio
            data, samplerate = AudioProcessor.load_audio(file_path)
            
            # Check duration
            duration = len(data) / samplerate
            
            if duration > 600:  # 10 minutes max
                return {"valid": False, "error": "Audio too long (max 10 minutes)"}
            
            if duration < 0.1:  # 100ms min
                return {"valid": False, "error": "Audio too short (min 0.1 seconds)"}
            
            return {
                "valid": True,
                "duration": duration,
                "sample_rate": samplerate,
                "channels": data.shape[1] if len(data.shape) > 1 else 1,
                "samples": len(data)
            }
        
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    @staticmethod
    def trim_silence(
        audio_data: np.ndarray,
        sample_rate: int,
        threshold: float = 0.01
    ) -> np.ndarray:
        """
        Trim silence from beginning and end.
        
        Args:
            audio_data: Audio data
            sample_rate: Sample rate
            threshold: Silence threshold
        
        Returns:
            Trimmed audio data
        """
        try:
            # Find non-silent regions
            non_silent = np.abs(audio_data) > threshold
            
            if not non_silent.any():
                return audio_data
            
            # Find first and last non-silent sample
            start = np.argmax(non_silent)
            end = len(audio_data) - np.argmax(non_silent[::-1])
            
            return audio_data[start:end]
        
        except Exception as e:
            app_logger.error(f"Error trimming silence: {e}")
            return audio_data