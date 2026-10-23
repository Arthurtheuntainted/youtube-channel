"""
Audio processing with FFmpeg.
Combines intro, story, silence, and normalizes for broadcast.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional, List
import tempfile

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
    
    def _find_ffmpeg(self) -> str:
        """Find FFmpeg in system PATH or common locations."""
        # Try PATH first
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return "ffmpeg"
        except FileNotFoundError:
            pass
        
        # Common Windows location
        win_path = Path("C:/ffmpeg/bin/ffmpeg.exe")
        if win_path.exists():
            return str(win_path)
        
        logger.error("FFmpeg not found. Please install FFmpeg.")
        return ""
    
    def has_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        return bool(self.ffmpeg_path)
    
    def generate_silence(self, duration_seconds: float, output_path: Path) -> bool:
        """Generate a silence audio file."""
        if not self.has_ffmpeg():
            return False
        
        cmd = [
            self.ffmpeg_path,
            "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=mono:d={duration_seconds}",
            "-y",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Silence generation failed: {e}")
            return False
    
    def combine_broadcast(self, intro_audio: Path, story_audio: Path, 
                          output_path: Path) -> bool:
        """
        Combine intro + silence + story + silence into final broadcast file.
        Also normalizes volume.
        
        Structure:
        - 2 seconds silence (lead-in)
        - Host introduction
        - 1.5 seconds silence (pause)
        - Story narration
        - 3 seconds silence (fade out buffer)
        """
        if not self.has_ffmpeg():
            logger.error("FFmpeg not available")
            return False
        
        if not intro_audio.exists():
            logger.error(f"Intro audio not found: {intro_audio}")
            return False
            
        if not story_audio.exists():
            logger.error(f"Story audio not found: {story_audio}")
            return False
        
        # Create temp files for silence segments
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as sil1_tmp:
            sil1_path = Path(sil1_tmp.name)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as sil2_tmp:
            sil2_path = Path(sil2_tmp.name)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as sil3_tmp:
            sil3_path = Path(sil3_tmp.name)
        
        try:
            # Generate silence segments
            if not self.generate_silence(2.0, sil1_path):
                logger.error("Failed to generate lead-in silence")
                return False
            
            if not self.generate_silence(1.5, sil2_path):
                logger.error("Failed to generate mid silence")
                return False
                
            if not self.generate_silence(3.0, sil3_path):
                logger.error("Failed to generate outro silence")
                return False
            
            # Create concat file
            concat_file = output_path.parent / f"concat_{output_path.stem}.txt"
            with open(concat_file, 'w') as f:
                f.write(f"file '{sil1_path.as_posix()}'\n")
                f.write(f"file '{intro_audio.as_posix()}'\n")
                f.write(f"file '{sil2_path.as_posix()}'\n")
                f.write(f"file '{story_audio.as_posix()}'\n")
                f.write(f"file '{sil3_path.as_posix()}'\n")
            
            # Concatenate and normalize
            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",  # EBU R128 normalization
                "-ar", "44100",
                "-ac", "2",  # Convert to stereo for OBS compatibility
                "-y",
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg concat failed: {result.stderr}")
                return False
            
            # Verify output
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"Broadcast file created: {output_path} ({output_path.stat().st_size} bytes)")
                return True
            else:
                logger.error("Generated broadcast file is empty")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg processing timed out")
            return False
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            return False
        finally:
            # Cleanup temp files
            for p in [sil1_path, sil2_path, sil3_path]:
                if p.exists():
                    try:
                        p.unlink()
                    except:
                        pass
            
            concat_file = output_path.parent / f"concat_{output_path.stem}.txt"
            if concat_file.exists():
                concat_file.unlink()
    
    def get_audio_duration(self, audio_path) -> float:
        """Get duration of audio file in seconds."""
        audio_path = Path(audio_path) if not isinstance(audio_path, Path) else audio_path
        if not self.has_ffmpeg() or not audio_path.exists():
            return 0.0
        
        cmd = [
            self.ffmpeg_path,
            "-i", str(audio_path),
            "-f", "null",
            "-"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            # Parse duration from stderr
            for line in result.stderr.split('\n'):
                if 'Duration:' in line:
                    parts = line.split('Duration:')[1].split(',')[0].strip()
                    # Format: HH:MM:SS.ms
                    h, m, s = parts.split(':')
                    return float(h) * 3600 + float(m) * 60 + float(s)
        except Exception as e:
            logger.error(f"Failed to get duration: {e}")
        
        return 0.0
    
    def test_ffmpeg(self) -> bool:
        """Test FFmpeg availability."""
        return self.has_ffmpeg()
