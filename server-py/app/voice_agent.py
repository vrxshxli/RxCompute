"""
Voice Agent using Langchain + LangGraph + Langfuse
Custom AI voice model implementation without OpenAI
"""
import os
import re
from typing import TypedDict, Annotated, Literal
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
# Langfuse imports (optional)
try:
    from langfuse import Langfuse
    from langfuse.decorators import langfuse_context, observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    # Create a no-op decorator if Langfuse is not available
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

try:
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
except ImportError:
    # Fallback if prompts not available
    ChatPromptTemplate = None
    MessagesPlaceholder = None

# Initialize Langfuse for monitoring (optional)
langfuse = None
if LANGFUSE_AVAILABLE:
    try:
        langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
        if langfuse_public_key and langfuse_secret_key:
            langfuse = Langfuse(
                public_key=langfuse_public_key,
                secret_key=langfuse_secret_key,
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
            )
        else:
            print("Langfuse keys not provided. Monitoring disabled.")
    except Exception as e:
        print(f"Warning: Langfuse initialization failed: {e}")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

llm = ChatOllama(
    base_url=OLLAMA_HOST,
    model=MODEL_NAME,
    temperature=0.7,
)

SYSTEM_PROMPT = """You are Rxcompute, a helpful voice assistant for a pharmacy management platform.
You help users navigate the website, answer questions, and perform actions.

Your capabilities:
1. Navigation: Help users navigate to login, signup, dashboard pages
2. Information: Answer questions about the platform, pharmacy services, and features
3. Commands: Understand and execute voice commands like "open login", "go to register", etc.

You should respond naturally and conversationally in the user's preferred language (English, Hindi, or Marathi).
Keep responses concise and actionable. Always confirm actions before executing them.
Remember: Your name is Rxcompute."""

# Define the state for the voice agent
class VoiceAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_input: str
    language: str
    intent: str
    action: str
    response: str

# Intent classification function
def classify_intent(text: str, language: str) -> str:
    """Classify user intent from the input text"""
    text_lower = text.lower()
    
    # Navigation intents
    login_patterns = [
        r"(open|go to|navigate to|show|खोल|जाओ|उघड|दाखव)\s*(login|लॉगिन|लॉग इन|लॉगइन)",
        r"login|लॉगिन"
    ]
    signup_patterns = [
        r"(open|go to|navigate to|show|register|sign up|खोल|जाओ|उघड|नोंदणी|साइनअप)",
        r"register|signup|साइनअप|नोंदणी"
    ]
    dashboard_patterns = [
        r"(open|go to|navigate to|show|dashboard|खोल|जाओ|उघड|डॅशबोर्ड|डैशबोर्ड)"
    ]
    help_patterns = [
        r"(help|what can you do|how|मदद|क्या कर सकते हो|कसे)"
    ]
    
    if any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in login_patterns):
        return "navigate_login"
    if any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in signup_patterns):
        return "navigate_signup"
    if any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in dashboard_patterns):
        return "navigate_dashboard"
    if any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in help_patterns):
        return "help"
    
    return "general_query"

# Node functions for LangGraph
@observe()
def classify_intent_node(state: VoiceAgentState) -> VoiceAgentState:
    """Classify the user's intent"""
    intent = classify_intent(state["user_input"], state.get("language", "en-IN"))
    state["intent"] = intent
    return state

@observe()
def handle_navigation_node(state: VoiceAgentState) -> VoiceAgentState:
    """Handle navigation intents"""
    intent = state["intent"]
    language = state.get("language", "en-IN")
    
    responses = {
        "navigate_login": {
            "en-IN": "I'll take you to the login page. Opening login page now.",
            "hi-IN": "मैं आपको लॉगिन पेज पर ले जा रहा हूँ। लॉगिन पेज खोल रहा हूँ।",
            "mr-IN": "मी तुम्हाला लॉगिन पेजवर नेत आहे. लॉगिन पेज उघडत आहे."
        },
        "navigate_signup": {
            "en-IN": "I'll take you to the registration page. Opening signup page now.",
            "hi-IN": "मैं आपको रजिस्ट्रेशन पेज पर ले जा रहा हूँ। साइनअप पेज खोल रहा हूँ।",
            "mr-IN": "मी तुम्हाला नोंदणी पेजवर नेत आहे. साइनअप पेज उघडत आहे."
        },
        "navigate_dashboard": {
            "en-IN": "I'll take you to the dashboard. Opening dashboard now.",
            "hi-IN": "मैं आपको डैशबोर्ड पर ले जा रहा हूँ। डैशबोर्ड खोल रहा हूँ।",
            "mr-IN": "मी तुम्हाला डॅशबोर्डवर नेत आहे. डॅशबोर्ड उघडत आहे."
        }
    }
    
    action_map = {
        "navigate_login": "navigate:/login",
        "navigate_signup": "navigate:/signup",
        "navigate_dashboard": "navigate:/dashboard/user"
    }
    
    response = responses.get(intent, {}).get(language, responses.get(intent, {}).get("en-IN", ""))
    action = action_map.get(intent, "")
    
    state["response"] = response
    state["action"] = action
    return state

@observe()
def handle_help_node(state: VoiceAgentState) -> VoiceAgentState:
    """Handle help requests"""
    language = state.get("language", "en-IN")
    
    help_responses = {
        "en-IN": """I'm Rxcompute, your voice assistant. I can help you with:
- Navigation: Say "open login", "go to signup", or "show dashboard"
- Information: Ask me questions about the platform
- Commands: I understand voice commands in English, Hindi, and Marathi

Just speak naturally and I'll help you!""",
        "hi-IN": """मैं Rxcompute हूँ, आपकी आवाज़ सहायक। मैं आपकी मदद कर सकता हूँ:
- नेविगेशन: "लॉगिन खोलो", "साइनअप पर जाओ", या "डैशबोर्ड दिखाओ" कहें
- जानकारी: प्लेटफॉर्म के बारे में मुझसे सवाल पूछें
- कमांड: मैं अंग्रेजी, हिंदी और मराठी में आवाज़ कमांड समझता हूँ

बस सामान्य रूप से बोलें और मैं आपकी मदद करूंगा!""",
        "mr-IN": """मी Rxcompute आहे, तुमचा व्हॉइस असिस्टंट. मी तुम्हाला मदत करू शकतो:
- नेव्हिगेशन: "लॉगिन उघड", "साइनअप वर जा", किंवा "डॅशबोर्ड दाखव" म्हणा
- माहिती: प्लॅटफॉर्मबद्दल मला प्रश्न विचारा
- कमांड: मी इंग्रजी, हिंदी आणि मराठीमध्ये व्हॉइस कमांड समजतो

फक्त नैसर्गिकरित्या बोला आणि मी तुम्हाला मदत करेन!"""
    }
    
    state["response"] = help_responses.get(language, help_responses["en-IN"])
    state["action"] = ""
    return state

@observe()
def handle_general_query_node(state: VoiceAgentState) -> VoiceAgentState:
    """Handle general queries using LLM"""
    user_input = state["user_input"]
    language = state.get("language", "en-IN")
    
    # Get chat history from state
    chat_history = state.get("messages", [])
    
    # Format messages for LLM
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in chat_history[-5:]:  # Last 5 messages for context
        if isinstance(msg, HumanMessage):
            messages.append(HumanMessage(content=msg.content))
        elif isinstance(msg, AIMessage):
            messages.append(AIMessage(content=msg.content))
    
    messages.append(HumanMessage(content=f"User ({language}): {user_input}"))
    
    # Generate response
    try:
        response = llm.invoke(messages)
        response_text = response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        print(f"Error in LLM invocation: {e}")
        # Fallback response
        response_text = (
            "I apologize, but I'm having trouble processing that right now. "
            "Please try again or say 'help' for assistance."
        )
    
    state["response"] = response_text
    state["action"] = ""
    
    # Update messages
    if "messages" not in state:
        state["messages"] = []
    state["messages"].append(HumanMessage(content=user_input))
    state["messages"].append(AIMessage(content=response_text))
    
    return state

# Router function to decide which node to call
def route_intent(state: VoiceAgentState) -> Literal["navigation", "help", "general"]:
    """Route based on intent"""
    intent = state.get("intent", "general_query")
    
    if intent.startswith("navigate_"):
        return "navigation"
    elif intent == "help":
        return "help"
    else:
        return "general"

# Build the LangGraph workflow
def create_voice_agent_graph():
    """Create the LangGraph workflow for voice agent"""
    workflow = StateGraph(VoiceAgentState)
    
    # Add nodes
    workflow.add_node("classify", classify_intent_node)
    workflow.add_node("navigation", handle_navigation_node)
    workflow.add_node("help", handle_help_node)
    workflow.add_node("general", handle_general_query_node)
    
    # Set entry point
    workflow.set_entry_point("classify")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "classify",
        route_intent,
        {
            "navigation": "navigation",
            "help": "help",
            "general": "general"
        }
    )
    
    # All nodes end
    workflow.add_edge("navigation", END)
    workflow.add_edge("help", END)
    workflow.add_edge("general", END)
    
    return workflow.compile()

# Create the graph instance
voice_agent_graph = create_voice_agent_graph()

@observe()
def process_voice_input(user_input: str, language: str = "en-IN", chat_history: list = None) -> dict:
    """
    Process voice input through the LangGraph workflow
    
    Args:
        user_input: The user's voice input text
        language: Language code (en-IN, hi-IN, mr-IN)
        chat_history: Previous conversation messages
    
    Returns:
        dict with 'response' and 'action' keys
    """
    # Initialize state
    initial_state = {
        "user_input": user_input,
        "language": language,
        "messages": chat_history or [],
        "intent": "",
        "action": "",
        "response": ""
    }
    
    # Run the graph
    result = voice_agent_graph.invoke(initial_state)
    
    return {
        "response": result.get("response", ""),
        "action": result.get("action", ""),
        "intent": result.get("intent", "")
    }

@observe()
def get_welcome_message(language: str = "en-IN") -> str:
    """Get welcome message when voice agent loads"""
    welcome_messages = {
        "en-IN": """Hello! I am Rxcompute, your AI voice assistant. 
I'm here to help you navigate the website and answer your questions.

Here's how I work:
- I listen to your voice commands and respond naturally
- I can help you navigate to different pages like login, signup, or dashboard
- I can answer questions about the platform and pharmacy services
- I understand commands in English, Hindi, and Marathi

Just speak naturally and I'll help you! You can say things like:
- "Open login" to go to the login page
- "Go to signup" to register
- "Show dashboard" to see your dashboard
- Or ask me any question about the platform

How can I help you today?""",
        "hi-IN": """नमस्कार! मैं Rxcompute हूँ, आपका AI वॉइस असिस्टेंट।
मैं यहाँ आपकी वेबसाइट नेविगेट करने और आपके सवालों के जवाब देने में मदद करने के लिए हूँ।

मैं कैसे काम करता हूँ:
- मैं आपकी आवाज़ कमांड सुनता हूँ और स्वाभाविक रूप से जवाब देता हूँ
- मैं आपको लॉगिन, साइनअप, या डैशबोर्ड जैसे विभिन्न पेजों पर नेविगेट करने में मदद कर सकता हूँ
- मैं प्लेटफॉर्म और फार्मेसी सेवाओं के बारे में सवालों के जवाब दे सकता हूँ
- मैं अंग्रेजी, हिंदी और मराठी में कमांड समझता हूँ

बस सामान्य रूप से बोलें और मैं आपकी मदद करूंगा! आप कह सकते हैं:
- "लॉगिन खोलो" लॉगिन पेज पर जाने के लिए
- "साइनअप पर जाओ" रजिस्टर करने के लिए
- "डैशबोर्ड दिखाओ" अपना डैशबोर्ड देखने के लिए
- या प्लेटफॉर्म के बारे में कोई सवाल पूछें

आज मैं आपकी कैसे मदद कर सकता हूँ?""",
        "mr-IN": """नमस्कार! मी Rxcompute आहे, तुमचा AI व्हॉइस असिस्टंट.
मी तुम्हाला वेबसाइट नेव्हिगेट करण्यात आणि तुमच्या प्रश्नांची उत्तरे देण्यात मदत करण्यासाठी येथे आहे.

मी कसे काम करतो:
- मी तुमच्या व्हॉइस कमांड ऐकतो आणि नैसर्गिकरित्या प्रतिसाद देतो
- मी तुम्हाला लॉगिन, साइनअप, किंवा डॅशबोर्ड सारख्या वेगवेगळ्या पृष्ठांवर नेव्हिगेट करण्यात मदत करू शकतो
- मी प्लॅटफॉर्म आणि फार्मसी सेवांबद्दल प्रश्नांची उत्तरे देऊ शकतो
- मी इंग्रजी, हिंदी आणि मराठीमध्ये कमांड समजतो

फक्त नैसर्गिकरित्या बोला आणि मी तुम्हाला मदत करेन! तुम्ही असे म्हणू शकता:
- "लॉगिन उघड" लॉगिन पृष्ठावर जाण्यासाठी
- "साइनअप वर जा" नोंदणी करण्यासाठी
- "डॅशबोर्ड दाखव" तुमचा डॅशबोर्ड पाहण्यासाठी
- किंवा प्लॅटफॉर्मबद्दल कोणताही प्रश्न विचारा

आज मी तुम्हाला कशी मदत करू शकतो?"""
    }
    
    return welcome_messages.get(language, welcome_messages["en-IN"])

@observe()
def get_language_selection_prompt() -> dict:
    """Get language selection prompt in all languages"""
    return {
        "en-IN": "Hello! I am Rxcompute. Please select your preferred language. Say English, Hindi, or Marathi.",
        "hi-IN": "नमस्कार! मैं Rxcompute हूँ। कृपया अपनी पसंदीदा भाषा चुनें। अंग्रेजी, हिंदी, या मराठी कहें।",
        "mr-IN": "नमस्कार! मी Rxcompute आहे. कृपया तुमची आवडती भाषा निवडा. इंग्रजी, हिंदी, किंवा मराठी म्हणा."
    }

