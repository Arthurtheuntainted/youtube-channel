"""
Local Text-to-Speech using Piper.
Converts text to audio files for broadcast.
"""

import logging
import subprocess
import os
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class PiperTTS:
    def __init__(self, engine_path: str, model_path: str, voice: str, speed: float):
        self.engine_path = Path(engine_path)
        self.model_path = Path(model_path)
        self.voice = voice
        self.speed = speed
        
        # Validate paths
        if not self.engine_path.exists():
            logger.warning(f"Piper engine not found at {engine_path}")
        if not self.model_path.exists():
            logger.warning(f"TTS model not found at {model_path}")
    
    def generate_speech(self, text: str, output_path: Path) -> bool:
        """
        Generate speech audio file from text using Piper.
        Returns True if successful, False otherwise.
        """
        if not self.engine_path.exists():
            logger.error("Piper engine not found. TTS will fail.")
            return False
        
        if not self.model_path.exists():
            logger.error("TTS model not found. TTS will fail.")
            return False
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build Piper command
            cmd = [
                str(self.engine_path),
                "--model", str(self.model_path),
                "--output_file", str(output_path)
            ]
            
            # Add speed if not 1.0
            if self.speed != 1.0:
                cmd.extend(["--length_scale", str(1.0 / self.speed)])
            
            # Run Piper with text via stdin
            process = subprocess.run(
                cmd,
                input=text.encode('utf-8'),
                capture_output=True,
                timeout=120  # 2 minute timeout for long stories
            )
            
            if process.returncode == 0 and output_path.exists():
                # Verify file has content
                if output_path.stat().st_size > 0:
                    logger.info(f"TTS generated: {output_path} ({output_path.stat().st_size} bytes)")
                    return True
                else:
                    logger.error(f"Generated empty audio file: {output_path}")
                    return False
            else:
                logger.error(f"Piper failed: {process.stderr.decode()}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"TTS generation timed out for text length: {len(text)}")
            return False
        except Exception as e:
            logger.error(f"TTS generation error: {e}")
            return False
    
    def generate_intro_audio(self, intro_text: str, ticket: str, output_dir: Path) -> Optional[Path]:
        """Generate audio for host introduction."""
        output_path = output_dir / f"intro_{ticket}.wav"
        if self.generate_speech(intro_text, output_path):
            return output_path
        return None
    
    def generate_story_audio(self, story_text: str, ticket: str, output_dir: Path) -> Optional[Path]:
        """Generate audio for story narration."""
        output_path = output_dir / f"story_{ticket}.wav"
        if self.generate_speech(story_text, output_path):
            return output_path
        return None
    
    def test_connection(self) -> bool:
        """Test if Piper is working with a short phrase."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            success = self.generate_speech("Testing radio station.", tmp_path)
            return success
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
