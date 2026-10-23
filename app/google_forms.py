"""
Google Sheets integration for Cavern Wireless.
Polls for new form submissions and validates them.
"""

import logging
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class GoogleFormsPoller:
    def __init__(self, sheet_id: str, credentials_path: str):
        self.sheet_id = sheet_id
        self.credentials_path = credentials_path
        self.service = None
        self.last_processed_row = 0
        
        # Expected columns (0-indexed)
        self.COL_TIMESTAMP = 0
        self.COL_NAME = 1
        self.COL_TITLE = 2
        self.COL_STORY = 3
        self.COL_MESSAGE = 4
        
    def authenticate(self) -> bool:
        """Authenticate with Google Sheets API."""
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("Google Sheets authentication successful.")
            return True
        except Exception as e:
            logger.error(f"Google Sheets authentication failed: {e}")
            return False
    
    def generate_hash(self, name: str, title: str, story: str) -> str:
        """Generate unique hash for duplicate detection."""
        content = f"{name.strip().lower()}|{title.strip().lower()}|{story.strip()}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def poll_submissions(self) -> List[Dict[str, Any]]:
        """
        Poll Google Sheet for new submissions.
        Returns list of new submissions since last poll.
        """
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=self.sheet_id,
                range='Sheet1!A:E'  # Assumes data in first sheet, columns A-E
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return []
            
            # Skip header row if it looks like headers
            start_index = 0
            if len(values) > 0 and values[0][0].lower() == 'timestamp':
                start_index = 1
            
            new_submissions = []
            
            for i, row in enumerate(values[start_index:], start=start_index + 1):
                # Skip already processed rows
                if i <= self.last_processed_row:
                    continue
                
                # Ensure row has enough columns
                while len(row) < 5:
                    row.append('')
                
                timestamp = row[self.COL_TIMESTAMP] if row[self.COL_TIMESTAMP] else datetime.now().isoformat()
                name = row[self.COL_NAME].strip() if row[self.COL_NAME] else ''
                title = row[self.COL_TITLE].strip() if row[self.COL_TITLE] else ''
                story = row[self.COL_STORY].strip() if row[self.COL_STORY] else ''
                message = row[self.COL_MESSAGE].strip() if row[self.COL_MESSAGE] else ''
                
                # Basic validation
                if not name or not title or not story:
                    logger.warning(f"Skipping incomplete submission at row {i}")
                    continue
                
                submission_hash = self.generate_hash(name, title, story)
                
                new_submissions.append({
                    'row_number': i,
                    'timestamp': timestamp,
                    'name': name,
                    'title': title,
                    'story': story,
                    'message': message,
                    'submission_hash': submission_hash
                })
                
                # Update last processed row
                self.last_processed_row = i
            
            if new_submissions:
                logger.info(f"Found {len(new_submissions)} new submissions.")
            
            return new_submissions
            
        except Exception as e:
            logger.error(f"Error polling Google Sheets: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test if Google Sheets connection is working."""
        try:
            if not self.service:
                if not self.authenticate():
                    return False
            
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=self.sheet_id,
                range='Sheet1!A1'
            ).execute()
            
            return 'values' in result
        except Exception as e:
            logger.error(f"Google Sheets connection test failed: {e}")
            return False
