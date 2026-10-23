"""
Main scheduler for Cavern Wireless.
Coordinates polling, moderation, TTS generation, and playback.
"""

import logging
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from app.config import Config
from app.database import Database
from app.google_forms import GoogleFormsPoller
from app.moderation import ModerationEngine
from app.llm_host import RadioHostLLM
from app.tts import PiperTTS
from app.audio import AudioProcessor
from app.playback import PlaybackEngine

logger = logging.getLogger(__name__)

class RadioScheduler:
    def __init__(self):
        self.config = Config
        self.db = Database(self.config.DB_PATH)
        
        # Initialize components
        self.poller = GoogleFormsPoller(
            self.config.GOOGLE_SHEET_ID,
            self.config.GOOGLE_CREDENTIALS_PATH
        )
        
        self.moderator = ModerationEngine(
            self.config.OLLAMA_URL,
            self.config.OLLAMA_MODEL
        )
        
        self.llm_host = RadioHostLLM(
            self.config.OLLAMA_URL,
            self.config.OLLAMA_MODEL
        )
        
        self.tts = PiperTTS(
            self.config.TTS_ENGINE_PATH,
            self.config.TTS_MODEL_PATH,
            self.config.TTS_VOICE,
            self.config.TTS_SPEED
        )
        
        self.audio_processor = AudioProcessor()
        self.playback = PlaybackEngine(self.config.AUDIO_OUTPUT_DEVICE)
        
        # State
        self.stop_event = threading.Event()
        self.is_running = False
        self.current_story_id: Optional[int] = None
        
        # Ensure directories exist
        self.config.AUDIO_DIR_GENERATED.mkdir(parents=True, exist_ok=True)
        self.config.AUDIO_DIR_FILLER.mkdir(parents=True, exist_ok=True)
    
    def process_new_submissions(self):
        """Check for new form submissions and add to queue."""
        submissions = self.poller.poll_submissions()
        
        for sub in submissions:
            logger.info(f"Processing submission: {sub['title']} by {sub['name']}")
            
            # Run moderation checks
            is_approved, reason = self.moderator.full_scan(
                sub['name'],
                sub['title'],
                sub['story'],
                sub['message']
            )
            
            if not is_approved:
                logger.warning(f"Submission rejected: {reason}")
                # Could log rejection to DB here if needed
                continue
            
            # Add to database
            ticket = self.db.add_story(
                name=sub['name'],
                title=sub['title'],
                text=sub['story'],
                message=sub['message'],
                submission_hash=sub['submission_hash'],
                requires_approval=self.config.REQUIRE_ADMIN_APPROVAL
            )
            
            if ticket:
                logger.info(f"Story queued with ticket {ticket}")
            else:
                logger.warning("Failed to add story (possibly duplicate)")
    
    def generate_broadcast(self, story: dict) -> Optional[Path]:
        """Generate complete broadcast audio for a story."""
        ticket = story['ticket_number']
        story_id = story['id']
        
        logger.info(f"Generating broadcast for {ticket}")
        
        # 1. Generate host introduction
        intro_text = self.llm_host.generate_intro(
            name=story['name'],
            title=story['story_title'],
            message=story.get('message_to_host', ''),
            ticket=ticket
        )
        
        if not intro_text:
            logger.error("Failed to generate host introduction")
            return None
        
        # 2. Generate TTS for intro
        intro_audio = self.tts.generate_intro_audio(
            intro_text, ticket, self.config.AUDIO_DIR_GENERATED
        )
        
        if not intro_audio:
            logger.error("Failed to generate intro audio")
            return None
        
        # 3. Generate TTS for story (unchanged text)
        story_audio = self.tts.generate_story_audio(
            story['story_text'], ticket, self.config.AUDIO_DIR_GENERATED
        )
        
        if not story_audio:
            logger.error("Failed to generate story audio")
            return None
        
        # 4. Combine into final broadcast
        broadcast_path = self.config.AUDIO_DIR_GENERATED / f"broadcast_{ticket}.wav"
        
        if self.audio_processor.combine_broadcast(intro_audio, story_audio, broadcast_path):
            logger.info(f"Broadcast file ready: {broadcast_path}")
            return broadcast_path
        else:
            logger.error("Failed to combine broadcast audio")
            return None
    
    def play_filler(self):
        """Play filler audio when queue is empty."""
        logger.info("Queue empty, playing filler audio...")
        
        # Check for filler files
        filler_files = list(self.config.AUDIO_DIR_FILLER.glob("*.wav"))
        
        if filler_files:
            # Play random filler
            import random
            filler_path = random.choice(filler_files)
            self.playback.play_file(filler_path)
        else:
            # Generate 60 seconds of silence as fallback
            silence_path = self.config.AUDIO_DIR_FILLER / "silence_60s.wav"
            if not silence_path.exists():
                self.audio_processor.generate_silence(60.0, silence_path)
            
            if silence_path.exists():
                self.playback.play_file(silence_path)
        
        logger.info("Filler playback completed")
    
    def run_broadcast_loop(self):
        """Main broadcast loop - runs continuously."""
        logger.info("Starting broadcast loop...")
        
        while not self.stop_event.is_set():
            try:
                # Check global playback status
                if self.db.get_playback_status() == 'PAUSED':
                    time.sleep(5)
                    continue
                
                # Get next queued story
                story = self.db.get_next_queued_story()
                
                if story:
                    # Mark as playing
                    self.db.mark_playing(story['id'])
                    self.current_story_id = story['id']
                    
                    # Generate broadcast audio
                    broadcast_path = self.generate_broadcast(story)
                    
                    if broadcast_path and broadcast_path.exists():
                        # Get duration for logging
                        duration = self.audio_processor.get_audio_duration(broadcast_path)
                        
                        # Play the broadcast
                        success = self.playback.play_file(broadcast_path)
                        
                        if success:
                            self.db.mark_completed(story['id'], int(duration))
                            logger.info(f"Broadcast completed: {story['ticket_number']} ({duration:.1f}s)")
                        else:
                            self.db.mark_failed(story['id'], "Playback failed")
                    else:
                        self.db.mark_failed(story['id'], "Audio generation failed")
                    
                    self.current_story_id = None
                else:
                    # No stories in queue - play filler
                    self.play_filler()
                    
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                time.sleep(10)  # Prevent tight error loop
        
        logger.info("Broadcast loop stopped")
    
    def poll_submissions_loop(self):
        """Background loop to check for new submissions."""
        logger.info("Starting submission poller...")
        
        while not self.stop_event.is_set():
            try:
                self.process_new_submissions()
            except Exception as e:
                logger.error(f"Error polling submissions: {e}")
            
            # Wait before next poll
            self.stop_event.wait(self.config.POLL_INTERVAL_SECONDS)
        
        logger.info("Submission poller stopped")
    
    def recover_from_crash(self):
        """Recover any stories stuck in PLAYING status."""
        recovered = self.db.recover_playing_story()
        if recovered:
            logger.info(f"Recovered {recovered} stuck stories")
    
    def start(self):
        """Start all scheduler threads."""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        logger.info("Starting Cavern Wireless scheduler...")
        
        # Recover from any previous crash
        self.recover_from_crash()
        
        # Test connections
        if not self.llm_host.test_connection():
            logger.warning("Ollama not available - using fallback intros")
        
        if not self.tts.test_connection():
            logger.error("Piper TTS not available - broadcasts will fail")
        
        if not self.audio_processor.test_ffmpeg():
            logger.error("FFmpeg not available - audio processing will fail")
        
        self.is_running = True
        self.stop_event.clear()
        
        # Start broadcast loop (main thread)
        self.broadcast_thread = threading.Thread(target=self.run_broadcast_loop, daemon=True)
        self.broadcast_thread.start()
        
        # Start poller thread
        self.poller_thread = threading.Thread(target=self.poll_submissions_loop, daemon=True)
        self.poller_thread.start()
        
        logger.info("Scheduler started successfully")
    
    def stop(self):
        """Stop all scheduler threads."""
        logger.info("Stopping scheduler...")
        self.stop_event.set()
        self.playback.stop()
        self.is_running = False
        
        # Wait for threads to finish
        if hasattr(self, 'broadcast_thread'):
            self.broadcast_thread.join(timeout=10)
        if hasattr(self, 'poller_thread'):
            self.poller_thread.join(timeout=10)
        
        logger.info("Scheduler stopped")
    
    def get_status(self) -> dict:
        """Get current scheduler status."""
        return {
            'is_running': self.is_running,
            'current_story_id': self.current_story_id,
            'queue_count': self.db.get_queue_count(),
            'playback_status': self.db.get_playback_status(),
            'ollama_available': self.llm_host.test_connection(),
            'tts_available': self.tts.test_connection(),
            'ffmpeg_available': self.audio_processor.test_ffmpeg(),
            'google_connected': self.poller.test_connection()
        }
