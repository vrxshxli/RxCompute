from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.voice_agent import process_voice_input, get_welcome_message, get_language_selection_prompt

router = APIRouter(prefix="/ai", tags=["ai"])

class ChatRequest(BaseModel):
    text: str
    language: str | None = None  # e.g., 'en-IN', 'hi-IN', 'mr-IN'

class ChatResponse(BaseModel):
    reply: str
    action: str | None = None  # Navigation action like "navigate:/login"
    intent: str | None = None  # Detected intent

class WelcomeRequest(BaseModel):
    language: str | None = None

class WelcomeResponse(BaseModel):
    message: str

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Process voice input through LangGraph workflow with Langfuse monitoring
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    
    language = req.language or "en-IN"
    
    try:
        # Process through LangGraph workflow
        result = process_voice_input(
            user_input=req.text.strip(),
            language=language,
            chat_history=[]  # Can be extended to maintain conversation history
        )
        
        return ChatResponse(
            reply=result.get("response", ""),
            action=result.get("action", ""),
            intent=result.get("intent", "")
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing voice input: {str(e)}"
        )

def _welcome_message(language: str | None) -> WelcomeResponse:
    lang = language or "en-IN"
    try:
        message = get_welcome_message(language=lang)
        return WelcomeResponse(message=message)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting welcome message: {str(e)}"
        )


@router.post("/welcome", response_model=WelcomeResponse)
async def welcome_post(req: WelcomeRequest):
    """
    Get welcome message (POST)
    """
    return _welcome_message(req.language)


@router.get("/welcome", response_model=WelcomeResponse)
async def welcome_get(language: str | None = None):
    """
    Get welcome message (GET) — for quick manual testing (browser/curl)
    """
    return _welcome_message(language)

class LanguagePromptResponse(BaseModel):
    prompts: dict  # All language prompts

@router.get("/language-prompt", response_model=LanguagePromptResponse)
async def language_prompt():
    """
    Get language selection prompt in all languages
    """
    try:
        prompts = get_language_selection_prompt()
        return LanguagePromptResponse(prompts=prompts)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting language prompt: {str(e)}"
        )
