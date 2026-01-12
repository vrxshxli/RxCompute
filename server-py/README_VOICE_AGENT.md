# AI Voice Agent Setup Guide

Yeh guide aapko Langchain + LangGraph + Langfuse ke saath custom AI voice agent setup karne mein help karega.

## Prerequisites

1. **Ollama Installation** (Local LLM ke liye):
   - Download from: https://ollama.ai
   - Install aur start karein
   - Model download karein: `ollama pull llama3.2:3b` (ya koi aur model)

2. **Langfuse Account** (Optional but recommended):
   - Sign up at: https://cloud.langfuse.com
   - API keys generate karein

## Installation

### 1. Dependencies Install Karein

```bash
cd server-py
pip install -r app/requirements.txt
```

### 2. Environment Variables Setup

`.env` file create karein `server-py/` directory mein:

```env
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Langfuse Configuration (Optional)
LANGFUSE_PUBLIC_KEY=your_public_key_here
LANGFUSE_SECRET_KEY=your_secret_key_here
LANGFUSE_HOST=https://cloud.langfuse.com

# API Configuration
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 3. Server Start Karein

```bash
cd server-py
uvicorn app.main:app --reload --port 8000
```

## Features

### ✅ Implemented Features

1. **Auto-start Voice Agent**: Component load hote hi automatically start hota hai
2. **Welcome Message**: Load hote hi AI apne aap kaam kaise karta hai explain karta hai
3. **LangGraph Workflow**: 
   - Intent classification
   - Navigation handling (login, signup, dashboard)
   - Help commands
   - General queries via LLM
4. **Langfuse Integration**: All AI calls monitor aur track hote hain
5. **Multi-language Support**: English, Hindi, Marathi
6. **Voice Commands**: 
   - "Open login" / "लॉगिन खोलो" / "लॉगिन उघड"
   - "Go to signup" / "साइनअप पर जाओ" / "साइनअप वर जा"
   - "Show dashboard" / "डैशबोर्ड दिखाओ" / "डॅशबोर्ड दाखव"
   - "Help" / "मदद" / "मदत"

## Architecture

### LangGraph Workflow

```
User Input
    ↓
Classify Intent
    ↓
    ├─→ Navigation Intent → Handle Navigation → END
    ├─→ Help Intent → Handle Help → END
    └─→ General Query → LLM Processing → END
```

### Components

1. **voice_agent.py**: 
   - LangGraph workflow definition
   - Intent classification
   - Node functions for different intents
   - Langfuse integration

2. **ai.py**: 
   - FastAPI endpoints
   - `/ai/chat` - Voice input processing
   - `/ai/welcome` - Welcome message

3. **VoiceAgent.jsx**: 
   - Frontend component
   - Auto-start functionality
   - Speech recognition
   - Text-to-speech
   - Action handling

## Customization

### Different LLM Use Karna

Agar aap Ollama ke bajay kisi aur LLM use karna chahte hain:

```python
# voice_agent.py mein
from langchain_openai import ChatOpenAI  # OpenAI ke liye
# ya
from langchain_anthropic import ChatAnthropic  # Anthropic ke liye

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
```

### New Commands Add Karna

1. `classify_intent()` function mein new patterns add karein
2. New node function create karein
3. `route_intent()` mein routing add karein
4. Workflow mein node add karein

## Troubleshooting

### Ollama Connection Error
- Check karein Ollama running hai: `ollama list`
- `OLLAMA_HOST` environment variable check karein

### Langfuse Errors
- Agar Langfuse optional hai, to environment variables empty rakh sakte hain
- Ya Langfuse account create karein

### Voice Recognition Not Working
- Chrome browser use karein (best support)
- Microphone permissions check karein
- HTTPS ya localhost use karein

## API Endpoints

### POST `/ai/chat`
Voice input process karta hai.

**Request:**
```json
{
  "text": "open login",
  "language": "en-IN"
}
```

**Response:**
```json
{
  "reply": "I'll take you to the login page...",
  "action": "navigate:/login",
  "intent": "navigate_login"
}
```

### POST `/ai/welcome`
Welcome message fetch karta hai.

**Request:**
```json
{
  "language": "en-IN"
}
```

**Response:**
```json
{
  "message": "Hello! I'm your AI voice assistant..."
}
```

## Next Steps

1. Dependencies install karein
2. Environment variables set karein
3. Server start karein
4. Frontend mein VoiceAgent component test karein

Happy coding! 🚀

