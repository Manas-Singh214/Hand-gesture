from gtts import gTTS
import pygame
import os
import tempfile
from typing import Optional
import config  # Import the config module directly

class TextToSpeech:
    def __init__(self):
        """Initialize the text-to-speech engine."""
        pygame.mixer.init()
        self.temp_files = []
        
    def speak(self, text: str, language: str = None, slow: bool = None) -> bool:
        """
        Convert text to speech and play it.
        
        Args:
            text: The text to be spoken
            language: Language code (e.g., 'en' for English)
            slow: Whether to speak slowly
            
        Returns:
            bool: True if speech was generated and played successfully, False otherwise
        """
        if not text:
            return False
            
        language = language or config.TTS_LANGUAGE
        slow = slow if slow is not None else config.TTS_SLOW
        
        # Clean up any old temporary files that are no longer in use
        self.cleanup()
        
        try:
            # Create a temporary file for the speech
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as fp:
                temp_file = fp.name
            
            # Generate speech
            tts = gTTS(text=text, lang=language, slow=slow)
            tts.save(temp_file)
            self.temp_files.append(temp_file)
            
            # Play the speech
            self._play_audio(temp_file)
            return True
            
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            # Clean up the temp file if we created it but failed to use it
            try:
                if 'temp_file' in locals() and os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass
            return False
    
    def _play_audio(self, file_path: str) -> None:
        """Play an audio file using pygame."""
        try:
            # Initialize pygame mixer if not already done
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            # Unload any currently playing audio
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except:
                pass
            
            # Give the system a moment to release the file
            pygame.time.delay(100)
            
            # Load and play the new audio
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Don't wait for the audio to finish - let it play in the background
            # The file will be cleaned up when the application exits or when cleanup() is called
            
        except Exception as e:
            print(f"Error playing audio: {e}")
            # Try to reinitialize the mixer if there was an error
            try:
                pygame.mixer.quit()
                pygame.mixer.init()
            except Exception as e:
                print(f"Error reinitializing mixer: {e}")
    
    def cleanup(self) -> None:
        """Clean up temporary files."""
        # Stop any currently playing audio
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                # Give the system a moment to release the file
                pygame.time.delay(100)
        except Exception as e:
            print(f"Error stopping audio during cleanup: {e}")
        
        # Clean up temporary files
        remaining_files = []
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Warning: Could not delete {file_path}: {e}")
                # If we couldn't delete it now, we'll try again later
                remaining_files.append(file_path)
        
        self.temp_files = remaining_files
    
    def __del__(self):
        """Clean up resources."""
        self.cleanup()
        try:
            pygame.mixer.quit()
        except:
            pass
