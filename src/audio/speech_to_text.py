"""
Speech-to-Text using OpenAI Whisper.
Converts audio input to text for voice-based queries.
"""
import whisper
import torch
from typing import Optional, Union
import numpy as np
from pathlib import Path
import soundfile as sf
from src.core.logging_config import app_logger
from src.core.config import settings


class SpeechToText:
    """
    Speech-to-Text engine using Whisper.
    
    Features:
    - Multiple language support
    - High accuracy transcription
    - Automatic language detection
    - GPU acceleration
    """
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize speech-to-text engine.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            app_logger.info(f"Loading Whisper model: {model_size} on {self.device}")
            self.model = whisper.load_model(model_size, device=self.device)
            app_logger.info("✅ Whisper model loaded successfully")
        except Exception as e:
            app_logger.error(f"❌ Failed to load Whisper model: {e}")
            raise
    
    def transcribe_file(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> dict:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es', 'fr')
            task: 'transcribe' or 'translate' (to English)
        
        Returns:
            Dictionary with transcription results
        """
        try:
            app_logger.info(f"Transcribing audio: {audio_path}")
            
            # Transcribe
            result = self.model.transcribe(
                str(audio_path),
                language=language,
                task=task,
                fp16=self.device == "cuda"
            )
            
            app_logger.info(f"✅ Transcription complete: {len(result['text'])} characters")
            
            return {
                "text": result["text"],
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", []),
                "confidence": self._calculate_confidence(result)
            }
        
        except Exception as e:
            app_logger.error(f"Error transcribing audio: {e}")
            raise
    
    def transcribe_audio_data(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio from numpy array.
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate of audio
            language: Language code
        
        Returns:
            Transcription results
        """
        try:
            # Ensure audio is in correct format
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize audio
            if audio_data.max() > 1.0:
                audio_data = audio_data / 32768.0
            
            # Resample if needed
            if sample_rate != 16000:
                audio_data = self._resample_audio(audio_data, sample_rate, 16000)
            
            # Transcribe
            result = self.model.transcribe(
                audio_data,
                language=language,
                fp16=self.device == "cuda"
            )
            
            return {
                "text": result["text"],
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", [])
            }
        
        except Exception as e:
            app_logger.error(f"Error transcribing audio data: {e}")
            raise
    
    def _calculate_confidence(self, result: dict) -> float:
        """Calculate average confidence from segments."""
        segments = result.get("segments", [])
        
        if not segments:
            return 0.0
        
        # Average no_speech_prob (lower is better)
        avg_no_speech = sum(s.get("no_speech_prob", 0.5) for s in segments) / len(segments)
        
        # Convert to confidence score
        confidence = 1.0 - avg_no_speech
        
        return round(confidence, 3)
    
    def _resample_audio(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio to target sample rate."""
        import librosa
        return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
    
    def detect_language(self, audio_path: Union[str, Path]) -> str:
        """
        Detect language from audio file.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Detected language code
        """
        try:
            audio = whisper.load_audio(str(audio_path))
            audio = whisper.pad_or_trim(audio)
            
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            
            _, probs = self.model.detect_language(mel)
            detected_lang = max(probs, key=probs.get)
            
            app_logger.info(f"Detected language: {detected_lang} (confidence: {probs[detected_lang]:.2f})")
            
            return detected_lang
        
        except Exception as e:
            app_logger.error(f"Error detecting language: {e}")
            return "en"  # Default to English


# Global instance
_speech_to_text: Optional[SpeechToText] = None


def get_speech_to_text() -> SpeechToText:
    """Get global speech-to-text instance."""
    global _speech_to_text
    if _speech_to_text is None:
        model_size = getattr(settings, 'whisper_model_size', 'base')
        _speech_to_text = SpeechToText(model_size=model_size)
    return _speech_to_text