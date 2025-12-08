# Audio System Documentation

## Overview
The Smart Attendance System now features a dual-engine audio system with automatic fallback for high-quality voice announcements.

## Supported Engines

### 1. Google Text-to-Speech (gTTS) - **Primary Engine**
- **Quality:** Natural-sounding, high-quality voices
- **Voice:** Female voice (default)
- **Languages:** Supports 100+ languages
- **Internet:** Requires internet connection
- **Advantages:**
  - Professional, natural-sounding speech
  - Consistent voice across all platforms
  - No voice installation required
  - Better pronunciation and intonation

### 2. pyttsx3 (Microsoft SAPI) - **Fallback Engine**
- **Quality:** Good, system-based voices
- **Voice:** Microsoft Zira (female, if available)
- **Languages:** Depends on installed system voices
- **Internet:** Works offline
- **Advantages:**
  - No internet required
  - Instant response
  - Works in restricted networks

## How It Works

### Automatic Engine Selection
1. **Primary:** System attempts to use gTTS for best quality
2. **Fallback:** If gTTS unavailable or internet issues, uses pyttsx3
3. **Queue-based:** All speech requests are queued to prevent threading conflicts

### Audio Flow
```
Registration/Recognition → Queue Message → Worker Thread → Speech Engine → Speaker
                               ↓
                         (gTTS or pyttsx3)
```

## Features

### Time-Based Greetings
- **Morning (5 AM - 12 PM):** "Good morning"
- **Afternoon (12 PM - 5 PM):** "Good afternoon"
- **Evening (5 PM - 9 PM):** "Good evening"
- **Night (9 PM - 5 AM):** "Good night"

### Emotion-Based Greetings
When facial expression detection is enabled:
- **Happy:** "You look cheerful today!"
- **Sad:** "Hope you have a better day ahead"
- **Angry:** "Take a deep breath. Better days are coming"
- **Surprised:** "What a pleasant surprise!"
- **Neutral:** Standard time-based greeting

### Context-Aware Announcements

#### Registration
```
"Good morning [Name]! Welcome! Registration successful."
```

#### Recognition (First time today)
```
"Good afternoon [Name]! Welcome! Your attendance has been marked successfully."
```

#### Recognition (Already marked)
```
"Good evening [Name]! Welcome."
```

## Configuration

### Enable/Disable Audio
Set in `config.py` or environment variable:
```python
ENABLE_AUDIO = True  # or False
```

### Adjust Speech Settings
```python
SPEECH_RATE = 150    # Words per minute (pyttsx3 only)
AUDIO_VOLUME = 0.9   # Volume level (0.0 to 1.0)
```

### Switch Engine Programmatically
```python
from audio_utils import set_speech_engine

set_speech_engine('gtts')      # Use Google TTS
set_speech_engine('pyttsx3')   # Use Microsoft TTS
```

### Check System Status
```python
from audio_utils import get_audio_system_info

info = get_audio_system_info()
print(f"Engine: {info['preferred_engine']}")
print(f"gTTS Available: {info['gtts_available']}")
print(f"pyttsx3 Available: {info['pyttsx3_available']}")
```

## Installation

### Requirements
```bash
pip install gTTS>=2.5.0 playsound>=1.3.0 pyttsx3>=2.90 pygame>=2.5.0
```

### Or use requirements.txt
```bash
pip install -r requirements.txt
```

## Troubleshooting

### No Sound Playing

1. **Check Audio is Enabled**
   - Verify `ENABLE_AUDIO = True` in config.py
   - Check sidebar "System Info" for audio status

2. **Internet Connection (for gTTS)**
   - gTTS requires internet to generate speech
   - System will auto-fallback to pyttsx3 if offline

3. **Check Logs**
   - Look in `logs/` folder for error messages
   - Search for "Audio" or "Speech" in logs

4. **Verify Dependencies**
   ```bash
   python -c "from gtts import gTTS; print('gTTS OK')"
   python -c "import pyttsx3; print('pyttsx3 OK')"
   python -c "import pygame; print('pygame OK')"
   ```

### Robotic/Poor Quality Voice

- **Solution:** System is using pyttsx3 fallback
- **Fix:** Install gTTS and ensure internet connection
  ```bash
  pip install gTTS
  ```

### Speech Delays

- **gTTS:** Small delay (1-2 seconds) for audio generation - normal
- **pyttsx3:** Instant - no delay

### Threading Errors

The queue-based system prevents threading conflicts. If you see errors:
1. Restart the application
2. Check if multiple instances are running
3. Verify logs for specific error messages

## API Reference

### Main Functions

#### `_queue_speech(message: str)`
Queue a message for speech announcement
```python
from audio_utils import _queue_speech
_queue_speech("Hello, this is a test")
```

#### `speak_nigerian_greeting(name: str, context: str)`
Standard greeting announcement
```python
speak_nigerian_greeting("John Doe", context="registration")
```

#### `speak_emotion_greeting(name: str, emotion: str, context: str)`
Emotion-based greeting announcement
```python
speak_emotion_greeting("Jane Smith", "happy", context="recognition")
```

#### `play_chime()`
Play notification chime sound
```python
from audio_utils import play_chime
play_chime()
```

#### `get_time_based_greeting()`
Get current time-appropriate greeting
```python
greeting = get_time_based_greeting()  # Returns "Good morning", etc.
```

## Performance

### gTTS (Google TTS)
- **Generation Time:** 0.5-2 seconds (internet dependent)
- **Audio Quality:** Excellent (natural voice)
- **File Size:** ~50-200 KB per message (temporary)
- **Memory:** Low impact (temp files auto-cleaned)

### pyttsx3 (Microsoft TTS)
- **Generation Time:** Instant (offline)
- **Audio Quality:** Good (robotic but clear)
- **File Size:** N/A (direct synthesis)
- **Memory:** Low impact

## Best Practices

1. **Use gTTS for production** - Better user experience
2. **Keep pyttsx3 as fallback** - Ensures offline functionality
3. **Add delays** - 0.5s between chime and speech for better UX
4. **Monitor logs** - Check audio system status regularly
5. **Test both engines** - Ensure fallback works correctly

## Version History

### v2.1 (December 2025)
- Added gTTS support for natural voices
- Implemented dual-engine system with automatic fallback
- Enhanced queue-based architecture
- Added emotion-based greetings
- Improved error handling and logging

### v2.0 (November 2025)
- Queue-based audio system
- Time-based greetings
- Threading issue fixes

### v1.0 (Initial)
- Basic pyttsx3 integration
- Simple announcements

---

**Note:** For the best experience, ensure a stable internet connection to use Google TTS. The system will automatically switch to offline mode if needed.
