from ..core.state_models import State
from .. core.llm_manager import LLMManger
import json

def intent_classifier(state:State):
    prompt = """
Analyze the user query and determine the intent. If it's a valid business request, return structured data. If it's a greeting or an unrelated query, return an appropriate response.

Possible intents:
1. "performance_node" -> Requires "Account Name".
2. "general" → For greetings and small talk.
Output ONLY valid JSON without any extra text or explanations
Example Inputs and Outputs:

User Query: "Hi"
Output:
{
  "intent": "general",
  "response": "Hello! How can I assist you today?"
}

User Query: "What's the weather like?"
Output:
{
  "intent": "general",
  "response": "I'm here to help with performance or score cards, not weather updates."
}
User Query: "Get the performance or score card  of A for today"
Output:
{
  "intent": "performance_node",
  "username": "A"
}

User Query: ""
User Query:
"""

    llm = LLMManger()
    print("State at intent classifier", state)
    print(state["messages"][-1].content)
    response = llm.invoke(prompt+state["messages"][-1].content)
    print(response)
    response = response.content.replace("```json", "").replace("```", "")
    response = json.loads(response)
    state["intent"] = response.get("intent", "general")
    if response.get("intent", "general") == "general":
        state["response"] = response.get(
            "response",
            "I'm here to help with general inquiries, performance of users and score cards",
        )   
    if response.get("intent", "general") == "performance_node":
        state["extracted_username"] = response["username"]
    print("return state at intent classifier", state)
    return state