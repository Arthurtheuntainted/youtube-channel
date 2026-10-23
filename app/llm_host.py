"""
Local LLM Host Introduction Generator.
Uses Ollama to create radio-host style intros.
"""

import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class RadioHostLLM:
    def __init__(self, ollama_url: str, model: str):
        self.ollama_url = ollama_url
        self.model = model
        
        # Fallback templates if Ollama fails
        self.fallback_intros = [
            "Good evening, listeners. Our next transmission comes from {name}, arriving under ticket number {ticket}. Tonight, {name_possessive} brings us a tale entitled '{title}'. Settle in, turn up the volume, and let's begin.",
            "Welcome back to Cavern Wireless. Ticket number {ticket} presents '{title}' by {name}. Dim the lights, and let these words carry you away.",
            "You're listening to Cavern Wireless. Our next story, '{title}', comes to us from {name}. Here is ticket number {ticket}.",
            "The air grows still as we present our next tale. '{title}' by {name}, ticket number {ticket}. Listen closely.",
            "From the archives of the unheard, ticket number {ticket}. {name} shares '{title}' with us this evening."
        ]
    
    def generate_intro(self, name: str, title: str, message: str, ticket: str) -> Optional[str]:
        """
        Generate a radio host introduction using local Ollama model.
        Returns intro text or None if generation fails.
        """
        prompt = f"""
You are a warm, atmospheric radio host for an old-fashioned story station called "Cavern Wireless".
Generate a SHORT introduction (30-60 words maximum) for the next story.

Story Details:
- Listener Name: {name}
- Story Title: {title}
- Ticket Number: {ticket}
- Message to Host: {message if message else "No specific message"}

Style Guidelines:
- Sound like a classic 1940s radio presenter
- Be warm, slightly theatrical, and mysterious
- Keep it concise (under 60 words)
- Do NOT invent facts about the listener
- Do NOT alter the story title
- Do NOT mention you are an AI
- Do NOT be repetitive

Generate ONLY the introduction text. No labels, no quotes around it.
"""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 100
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                intro = response.json().get("response", "").strip()
                
                # Clean up common issues
                intro = intro.replace('"', '').replace("'", "'")
                
                # Ensure it's not too long
                if len(intro.split()) > 80:
                    intro = ' '.join(intro.split()[:80]) + "..."
                
                logger.info(f"Generated intro for ticket {ticket}")
                return intro
            else:
                logger.warning(f"Ollama API error: {response.status_code}")
                return self._get_fallback(name, title, ticket)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama connection failed: {e}")
            return self._get_fallback(name, title, ticket)
        except Exception as e:
            logger.error(f"Unexpected error generating intro: {e}")
            return self._get_fallback(name, title, ticket)
    
    def _get_fallback(self, name: str, title: str, ticket: str) -> str:
        """Return a safe fallback introduction."""
        import random
        template = random.choice(self.fallback_intros)
        
        # Handle possessive
        name_possessive = name + "'s" if not name.endswith('s') else name + "'"
        
        return template.format(
            name=name,
            name_possessive=name_possessive,
            title=title,
            ticket=ticket
        )
    
    def test_connection(self) -> bool:
        """Test if Ollama is available."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
