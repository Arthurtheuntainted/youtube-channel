"""
Audio playback engine for Cavern Wireless.
Plays broadcast files to configured audio output device.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional
import time

logger = logging.getLogger(__name__)

class PlaybackEngine:
    def __init__(self, output_device: str):
        self.output_device = output_device
        self.current_process: Optional[subprocess.Popen] = None
        self.is_playing = False
    
    def play_file(self, audio_path: Path) -> bool:
        """
        Play audio file to configured output device.
        Blocks until playback completes.
        """
        if not audio_path.exists():
            logger.error(f"Audio file not found: {audio_path}")
            return False
        
        logger.info(f"Starting playback: {audio_path.name}")
        self.is_playing = True
        
        try:
            if sys.platform.startswith('win'):
                # Windows: Use PowerShell with specific audio device
                # Note: Direct device selection requires additional libraries
                # For now, we rely on system default or VB-CABLE as default
                cmd = [
                    'powershell', '-c',
                    f'(New-Object Media.SoundPlayer "{audio_path}").PlaySync()'
                ]
                
                # Alternative: Use ffplay with device selection (more reliable)
                cmd = [
                    'ffplay',
                    '-nodisp',
                    '-autoexit',
                    '-af', f'volume=1.0',
                    str(audio_path)
                ]
                
                process = subprocess.run(cmd, capture_output=True, timeout=600)
                
                if process.returncode == 0:
                    logger.info(f"Playback completed: {audio_path.name}")
                    return True
                else:
                    logger.error(f"Playback failed: {process.stderr.decode()}")
                    return False
            else:
                # Linux/macOS fallback
                cmd = ['aplay' if sys.platform.startswith('linux') else 'afplay', str(audio_path)]
                result = subprocess.run(cmd, timeout=600)
                return result.returncode == 0
                
        except subprocess.TimeoutExpired:
            logger.error("Playback timed out")
            return False
        except FileNotFoundError as e:
            logger.error(f"Audio player not found: {e}")
            return False
        except Exception as e:
            logger.error(f"Playback error: {e}")
            return False
        finally:
            self.is_playing = False
    
    def stop(self):
        """Stop current playback."""
        if self.current_process and self.current_process.poll() is None:
            self.current_process.terminate()
            logger.info("Playback stopped by user")
        self.is_playing = False
    
    def is_currently_playing(self) -> bool:
        """Check if currently playing audio."""
        return self.is_playing
