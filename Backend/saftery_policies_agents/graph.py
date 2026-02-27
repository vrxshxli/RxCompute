"""
LangGraph State Machine — chains agents together.

Current chain:
  [Conversation] → [Safety] → [Response]

The Conversation Agent is a passthrough placeholder here because
your team already handles extraction in the Flutter app / chat router.
The Safety Agent is the real work.

Future: add Order Agent, Prediction Agent, Scheduler Agent as new nodes.
"""

from langgraph.graph import StateGraph, END
from langfuse.decorators import observe

from saftery_policies_agents.state import AgentState
from saftery_policies_agents.safety_agent import run_safety_agent


# ━━━ Conversation Passthrough ━━━━━━━━━━━━━━━━━━━━━━━
# Replace this with your real Conversation Agent import
# when you integrate it. For now, assumes the router
# pre-fills matched_medicines before calling the graph.

@observe(name="conversation_passthrough")
def conversation_node(state: AgentState) -> dict:
    """Pass-through: medicines already matched by router."""
    if state.get("matched_medicines"):
        return state
    return {
        **state,
        "is_greeting": True,
        "general_response": "Hello! I'm your AI pharmacist. How can I help?",
        "response_type": "chat",
        "response_message": "Hello! I'm your AI pharmacist. How can I help?",
    }


# ━━━ Response Builder ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="build_response")
def build_response(state: AgentState) -> dict:
    """Format final response for Flutter."""
    if state.get("response_type") == "safety_warning":
        return state
    if state.get("matched_medicines") and not state.get("has_blocks"):
        return {
            **state,
            "response_type": "medicine_cards",
            "response_message": state.get("safety_summary", "Ready to order."),
        }
    return state


# ━━━ Routing Logic ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def after_conversation(state: AgentState) -> str:
    if state.get("is_greeting") or state.get("response_type") == "chat":
        return "respond"
    if state.get("matched_medicines"):
        return "safety_check"
    return "respond"


def after_safety(state: AgentState) -> str:
    return "respond"


# ━━━ Build + Compile Graph ━━━━━━━━━━━━━━━━━━━━━━━━━━

def _build():
    g = StateGraph(AgentState)
    g.add_node("conversation", conversation_node)
    g.add_node("safety_check", run_safety_agent)
    g.add_node("respond", build_response)
    g.set_entry_point("conversation")
    g.add_conditional_edges("conversation", after_conversation, {
        "safety_check": "safety_check",
        "respond": "respond",
    })
    g.add_conditional_edges("safety_check", after_safety, {
        "respond": "respond",
    })
    g.add_edge("respond", END)
    return g.compile()


agent_graph = _build()


# ━━━ Public API ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="rxcompute_safety_chain")
def process_with_safety(
    user_id: int,
    matched_medicines: list[dict],
    user_message: str = "",
) -> dict:
    """
    Run the full LangGraph chain and return results.

    Call from your router:
        from saftery_policies_agents.graph import process_with_safety
        result = process_with_safety(user_id=1, matched_medicines=[...])
    """
    initial: AgentState = {
        "user_id": user_id,
        "user_message": user_message,
        "matched_medicines": matched_medicines,
        "is_greeting": False,
        "general_response": "",
        "safety_results": [],
        "has_blocks": False,
        "has_warnings": False,
        "safety_summary": "",
        "response_type": "chat",
        "response_message": "",
    }
    return agent_graph.invoke(initial)