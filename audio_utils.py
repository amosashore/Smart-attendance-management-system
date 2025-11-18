"""
Enhanced audio utilities with better error handling and fallback mechanisms
"""
import pyttsx3
import pygame
import threading
from pathlib import Path
from typing import Optional
import time

from config import CHIME_PATH, ENABLE_AUDIO, SPEECH_RATE, AUDIO_VOLUME
from logger import get_logger

logger = get_logger(__name__)

# Initialize pygame mixer with error handling
try:
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except Exception as e:
    logger.warning(f"Pygame mixer initialization failed: {e}")
    PYGAME_AVAILABLE = False


class AudioManager:
    """Manages audio playback and text-to-speech"""
    
    def __init__(self):
        self.tts_engine: Optional[pyttsx3.Engine] = None
        self.is_speaking = False
        self._init_tts()
    
    def _init_tts(self):
        """Initialize text-to-speech engine"""
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty("rate", SPEECH_RATE)
            self.tts_engine.setProperty("volume", AUDIO_VOLUME)
            logger.info("Text-to-speech engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            self.tts_engine = None
    
    def play_sound(self, sound_file: Path, volume: float = AUDIO_VOLUME, 
                   fallback: bool = True) -> bool:
        """
        Play a sound file
        
        Args:
            sound_file: Path to sound file
            volume: Volume level (0.0 to 1.0)
            fallback: Use system beep as fallback
        
        Returns:
            True if successful
        """
        if not ENABLE_AUDIO:
            logger.debug("Audio is disabled")
            return False
        
        if not sound_file.exists():
            logger.warning(f"Sound file not found: {sound_file}")
            if fallback:
                return self._system_beep()
            return False
        
        if not PYGAME_AVAILABLE:
            logger.warning("Pygame not available")
            if fallback:
                return self._system_beep()
            return False
        
        try:
            pygame.mixer.music.load(str(sound_file))
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play()
            logger.debug(f"Playing sound: {sound_file.name}")
            return True
        except Exception as e:
            logger.error(f"Error playing sound: {e}")
            if fallback:
                return self._system_beep()
            return False
    
    def _system_beep(self) -> bool:
        """Fallback system beep"""
        try:
            # Windows beep
            import winsound
            winsound.Beep(1000, 200)
            return True
        except Exception:
            logger.debug("System beep not available")
            return False
    
    def speak(self, message: str, async_mode: bool = True, 
              rate: Optional[int] = None) -> bool:
        """
        Speak a message using text-to-speech
        
        Args:
            message: Text to speak
            async_mode: Run in background thread
            rate: Speech rate (overrides default)
        
        Returns:
            True if started successfully
        """
        if not ENABLE_AUDIO:
            logger.debug("Audio is disabled")
            return False
        
        if not message or not message.strip():
            logger.warning("Empty message provided to TTS")
            return False
        
        if self.tts_engine is None:
            logger.warning("TTS engine not available")
            return False
        
        if self.is_speaking:
            logger.debug("Already speaking, queuing message")
        
        if async_mode:
            thread = threading.Thread(
                target=self._speak_sync,
                args=(message, rate),
                daemon=True
            )
            thread.start()
            return True
        else:
            return self._speak_sync(message, rate)
    
    def _speak_sync(self, message: str, rate: Optional[int] = None) -> bool:
        """Synchronous speech (internal)"""
        try:
            self.is_speaking = True
            
            if rate:
                original_rate = self.tts_engine.getProperty("rate")
                self.tts_engine.setProperty("rate", rate)
            
            logger.info(f"Speaking: {message}")
            self.tts_engine.say(message)
            self.tts_engine.runAndWait()
            
            if rate:
                self.tts_engine.setProperty("rate", original_rate)
            
            self.is_speaking = False
            return True
        except Exception as e:
            logger.error(f"Error during speech: {e}")
            self.is_speaking = False
            return False
    
    def stop_speech(self):
        """Stop current speech"""
        if self.tts_engine and self.is_speaking:
            try:
                self.tts_engine.stop()
                self.is_speaking = False
                logger.debug("Speech stopped")
            except Exception as e:
                logger.error(f"Error stopping speech: {e}")
    
    def set_voice(self, voice_id: Optional[str] = None, 
                  gender: Optional[str] = None) -> bool:
        """
        Set TTS voice
        
        Args:
            voice_id: Specific voice ID
            gender: 'male' or 'female' to auto-select
        
        Returns:
            True if successful
        """
        if not self.tts_engine:
            return False
        
        try:
            voices = self.tts_engine.getProperty('voices')
            
            if voice_id:
                for voice in voices:
                    if voice.id == voice_id:
                        self.tts_engine.setProperty('voice', voice.id)
                        logger.info(f"Voice set to: {voice.name}")
                        return True
            
            if gender:
                gender_lower = gender.lower()
                for voice in voices:
                    voice_name = voice.name.lower()
                    if gender_lower in voice_name or gender_lower in voice.id.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        logger.info(f"Voice set to: {voice.name}")
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Error setting voice: {e}")
            return False
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        if not self.tts_engine:
            return []
        
        try:
            voices = self.tts_engine.getProperty('voices')
            return [{'id': v.id, 'name': v.name, 'languages': v.languages} for v in voices]
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []


# Global audio manager instance
audio_manager = AudioManager()


# Backward compatible functions
def play_chime() -> bool:
    """Play notification chime (backward compatible)"""
    return audio_manager.play_sound(CHIME_PATH)


def speak_message(message: str):
    """Speak a message (backward compatible)"""
    audio_manager.speak(message, async_mode=True)


def get_time_based_greeting() -> str:
    """Get greeting based on current time of day"""
    from datetime import datetime
    
    current_hour = datetime.now().hour
    
    if 5 <= current_hour < 12:
        return "Good morning"
    elif 12 <= current_hour < 17:
        return "Good afternoon"
    elif 17 <= current_hour < 21:
        return "Good evening"
    else:
        return "Good night"
