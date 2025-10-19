"""
Text-to-Speech using Coqui TTS.
Converts text responses to natural-sounding speech.
"""
from TTS.api import TTS
import torch
from typing import Optional, Union
from pathlib import Path
import numpy as np
from src.core.logging_config import app_logger


class TextToSpeech:
    """
    Text-to-Speech engine using Coqui TTS.
    
    Features:
    - Multiple voice models
    - Natural-sounding speech
    - Multi-language support
    - GPU acceleration
    """
    
    def __init__(self, model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"):
        """
        Initialize text-to-speech engine.
        
        Args:
            model_name: TTS model name
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            app_logger.info(f"Loading TTS model: {model_name}")
            self.tts = TTS(model_name=model_name).to(self.device)
            app_logger.info("✅ TTS model loaded successfully")
        except Exception as e:
            app_logger.error(f"❌ Failed to load TTS model: {e}")
            raise
    
    def synthesize_to_file(
        self,
        text: str,
        output_path: Union[str, Path],
        speaker: Optional[str] = None,
        language: Optional[str] = None
    ) -> Path:
        """
        Synthesize speech and save to file.
        
        Args:
            text: Text to synthesize
            output_path: Output audio file path
            speaker: Speaker name (for multi-speaker models)
            language: Language code
        
        Returns:
            Path to generated audio file
        """
        try:
            app_logger.info(f"Synthesizing speech: {len(text)} characters")
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Synthesize
            self.tts.tts_to_file(
                text=text,
                file_path=str(output_path),
                speaker=speaker,
                language=language
            )
            
            app_logger.info(f"✅ Speech saved to: {output_path}")
            
            return output_path
        
        except Exception as e:
            app_logger.error(f"Error synthesizing speech: {e}")
            raise
    
    def synthesize_to_audio(
        self,
        text: str,
        speaker: Optional[str] = None,
        language: Optional[str] = None
    ) -> np.ndarray:
        """
        Synthesize speech and return as numpy array.
        
        Args:
            text: Text to synthesize
            speaker: Speaker name
            language: Language code
        
        Returns:
            Audio data as numpy array
        """
        try:
            # Synthesize
            wav = self.tts.tts(
                text=text,
                speaker=speaker,
                language=language
            )
            
            return np.array(wav)
        
        except Exception as e:
            app_logger.error(f"Error synthesizing speech: {e}")
            raise
    
    def list_available_models(self) -> list:
        """List available TTS models."""
        return TTS().list_models()
    
    def list_speakers(self) -> Optional[list]:
        """List available speakers for multi-speaker models."""
        if hasattr(self.tts, 'speakers'):
            return self.tts.speakers
        return None


class SimpleTTS:
    """
    Simple TTS using gTTS (Google Text-to-Speech).
    Fallback option for basic functionality.
    """
    
    def __init__(self):
        """Initialize simple TTS."""
        from gtts import gTTS
        self.gTTS = gTTS
    
    def synthesize_to_file(
        self,
        text: str,
        output_path: Union[str, Path],
        language: str = 'en'
    ) -> Path:
        """
        Synthesize speech using gTTS.
        
        Args:
            text: Text to synthesize
            output_path: Output file path
            language: Language code
        
        Returns:
            Path to generated file
        """
        try:
            tts = self.gTTS(text=text, lang=language, slow=False)
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            tts.save(str(output_path))
            
            app_logger.info(f"✅ Simple TTS saved to: {output_path}")
            
            return output_path
        
        except Exception as e:
            app_logger.error(f"Error with simple TTS: {e}")
            raise


# Global instance
_text_to_speech: Optional[TextToSpeech] = None


def get_text_to_speech() -> TextToSpeech:
    """Get global text-to-speech instance."""
    global _text_to_speech
    if _text_to_speech is None:
        try:
            _text_to_speech = TextToSpeech()
        except:
            app_logger.warning("Using simple TTS as fallback")
            _text_to_speech = SimpleTTS()
    return _text_to_speech