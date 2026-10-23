"""
Cavern Wireless - Main Entry Point
Automated AI Story Radio Station
"""

import os
import sys
import logging
import signal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import Config
from app.database import Database
from web.app import app, set_scheduler
from app.scheduler import RadioScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/radio_station.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: RadioScheduler = None

def signal_handler(sig, frame):
    """Handle Ctrl+C and other signals gracefully."""
    logger.info("Received shutdown signal...")
    if scheduler:
        scheduler.stop()
    sys.exit(0)

def main():
    global scheduler
    
    logger.info("=" * 60)
    logger.info("CAVERN WIRELESS - Automated Story Radio Station")
    logger.info("=" * 60)
    
    # Validate configuration
    if not Config.validate():
        logger.error("Configuration validation failed. Check your .env file.")
        sys.exit(1)
    
    # Initialize database
    db = Database(Config.DB_PATH)
    logger.info(f"Database initialized at {Config.DB_PATH}")
    
    # Create scheduler
    scheduler = RadioScheduler()
    
    # Set scheduler for web app
    set_scheduler(scheduler)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start scheduler
    scheduler.start()
    
    # Start Flask web server (blocking)
    logger.info(f"Starting web interface at http://{Config.WEB_HOST}:{Config.WEB_PORT}")
    logger.info("Public status: http://localhost:" + str(Config.WEB_PORT))
    logger.info("Admin panel: http://localhost:" + str(Config.WEB_PORT) + "/admin")
    logger.info("")
    logger.info("Press Ctrl+C to stop the station")
    logger.info("=" * 60)
    
    try:
        app.run(
            host=Config.WEB_HOST,
            port=Config.WEB_PORT,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        pass
    finally:
        if scheduler:
            scheduler.stop()
        logger.info("Cavern Wireless stopped.")

if __name__ == '__main__':
    main()
