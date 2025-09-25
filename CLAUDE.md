# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pingo-robot is a Chinese intelligent voice conversation system that supports voice recognition (ASR), natural language understanding (NLU), text-to-speech (TTS), and AI chatbot capabilities. The system supports multiple voice engines and AI backends including Baidu, Azure, OpenAI, DeepSeek, and various TTS engines.

## Development Commands

### Setup and Installation
```bash
# Install system dependencies (Ubuntu)
sudo apt -y install portaudio19-dev
sudo apt-get install python3.10-dev
sudo apt install ffmpeg

# Install Python dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Direct execution
python pingo.py

# Windows PowerShell execution
.\run.ps1

# Help command
python pingo.py -h
```

### Utility Commands
```bash
# Calculate MD5 hash (for password configuration)
python pingo.py md5 <string>
```

## Architecture Overview

### Core Components

1. **Main Application (`pingo.py`)**: Entry point that initializes the conversation system and web server
2. **Configuration System (`config.py`, `config.json`)**: Manages all system settings including API keys, engine selections, and server configuration
3. **Conversation Engine (`robot/conversation.py`)**: Core conversation handling and orchestration
4. **Robot Modules (`robot/`)**: Modular components for different functionalities:
   - `ASR.py`: Automatic Speech Recognition engines
   - `TTS.py`: Text-to-Speech engines  
   - `NLU.py`: Natural Language Understanding
   - `AI.py`: AI chatbot backends
   - `Player.py`: Audio playback
   - `History.py`: Conversation history management
   - `detector.py`: Voice activation detection

### Web Interface (`server/`)

The system includes a comprehensive web management interface:
- **Authentication**: Login/logout handlers
- **Configuration**: Web-based configuration management
- **Chat Interface**: Real-time chat via WebSocket
- **Voice Handling**: Audio upload and processing
- **Logging**: System log viewing
- **Menu Management**: Dynamic menu system for demonstrations

### Key Configuration Areas

- **Voice Engines**: Supports Baidu, Azure, Xunfei, OpenAI, Edge TTS, VITS, ChatTTS
- **AI Backends**: Unit Robot, OpenAI ChatGPT, DeepSeek
- **Wake Word Detection**: Porcupine offline wake word detection
- **Audio Caching**: Cached audio responses in `cach/` directory
- **Database**: SQLite database for system data in `db/pingo.db`

### Important Files

- `config.json`: Main configuration file with API keys and engine settings
- `gvar.py`: Global variables and shared state
- `requirements.txt`: Python dependencies
- `run.ps1`: Windows PowerShell startup script
- `static/`: Wake word detection models
- `server/templates/`: Web interface templates
- `server/static/`: Web assets (CSS, JS, images)

### Development Notes

- The system requires Python >= 3.10
- Voice activation is currently disabled in the main loop (lines 72-73 in pingo.py)
- The web server runs on port 5001 by default (configurable)
- Default credentials: username `pingo`, password `pingo@2023`
- Audio files are cached in the `cach/` directory to improve performance
- The system supports both Windows (PGamePlayer) and Linux (SoxPlayer) audio playback

### External Dependencies

- **Porcupine**: Requires access key from https://console.picovoice.ai/
- **VITS**: Requires separate VITS server setup (https://github.com/zwssunny/vits-simple-api)
- **ChatTTS**: Requires ChatTTS environment setup (https://github.com/2noise/ChatTTS)
- **Baidu Unit**: Requires Baidu AI platform setup for NLU