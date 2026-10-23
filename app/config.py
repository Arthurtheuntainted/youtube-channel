"""
Configuration management for Cavern Wireless.
Loads environment variables and provides typed access.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    # Google Sheets
    GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")
    GOOGLE_CREDENTIALS_PATH: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    
    # Ollama (Local LLM)
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
    
    # Piper TTS
    TTS_ENGINE_PATH: str = os.getenv("TTS_ENGINE_PATH", "C:/piper/piper.exe")
    TTS_MODEL_PATH: str = os.getenv("TTS_MODEL_PATH", "C:/piper/voices/en_US-lessac-medium.onnx")
    TTS_VOICE: str = os.getenv("TTS_VOICE", "en_US-lessac-medium")
    TTS_SPEED: float = float(os.getenv("TTS_SPEED", "1.0"))
    
    # Web Interface
    WEB_HOST: str = os.getenv("WEB_HOST", "127.0.0.1")
    WEB_PORT: int = int(os.getenv("WEB_PORT", "5000"))
    
    # Audio
    AUDIO_OUTPUT_DEVICE: str = os.getenv("AUDIO_OUTPUT_DEVICE", "VB-Audio Virtual Cable")
    AUDIO_DIR_GENERATED: Path = Path("audio/generated")
    AUDIO_DIR_FILLER: Path = Path("audio/filler")
    
    # Database
    DB_PATH: Path = Path("data/radio_station.db")
    
    # Admin
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "changeMe123!")
    
    # Polling
    POLL_INTERVAL_SECONDS: int = 30
    
    # Moderation
    REQUIRE_ADMIN_APPROVAL: bool = os.getenv("REQUIRE_ADMIN_APPROVAL", "false").lower() == "true"
    
    @classmethod
    def validate(cls) -> bool:
        """Check if critical config is present."""
        if not cls.GOOGLE_SHEET_ID:
            print("ERROR: GOOGLE_SHEET_ID not set in .env")
            return False
        if not Path(cls.GOOGLE_CREDENTIALS_PATH).exists():
            print(f"ERROR: Credentials file not found at {cls.GOOGLE_CREDENTIALS_PATH}")
            return False
        return True
