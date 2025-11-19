"""
Text-to-Speech Service using gTTS
"""
from gtts import gTTS
import os
import logging
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

class TTSService:
    """Google Text-to-Speech service"""
    
    def __init__(self, audio_dir: str = "/tmp/audio"):
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"TTS Service initialized. Audio dir: {self.audio_dir}")
    
    def generate_audio(self, text: str, lang: str = "en") -> str:
        """
        Generate audio from text
        
        Args:
            text: Text to convert to speech
            lang: Language code (default: en)
            
        Returns:
            Path to generated audio file
        """
        try:
            # Create hash of text for filename
            text_hash = hashlib.md5(text.encode()).hexdigest()[:16]
            audio_file = self.audio_dir / f"tts_{text_hash}.mp3"
            
            # Check if already exists
            if audio_file.exists():
                logger.info(f"Using cached audio: {audio_file}")
                return str(audio_file)
            
            # Generate audio
            logger.info(f"Generating TTS audio for {len(text)} chars...")
            
            # Limit text length for TTS (max 5000 chars)
            if len(text) > 5000:
                text = text[:5000] + "... (truncated for audio)"
            
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(str(audio_file))
            
            logger.info(f"✅ Audio generated: {audio_file}")
            return str(audio_file)
            
        except Exception as e:
            logger.error(f"❌ TTS generation failed: {e}")
            return None
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Remove audio files older than max_age_hours"""
        import time
        try:
            current_time = time.time()
            removed = 0
            
            for file in self.audio_dir.glob("tts_*.mp3"):
                file_age = current_time - file.stat().st_mtime
                if file_age > (max_age_hours * 3600):
                    file.unlink()
                    removed += 1
            
            if removed > 0:
                logger.info(f"Cleaned up {removed} old audio files")
                
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

# Global TTS service instance
tts_service = TTSService()
