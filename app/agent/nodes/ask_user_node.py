from ..core.state_models import State
from ..core.llm_manager import LLMManger
from langchain_core.messages import AIMessage

def ask_user(state: State):
    print("Im inside ask_user node")

    prompt = """Analyze these user search results and generate a clear selection question for the user. 
Follow these steps:
1. Identify if there are multiple entries with similar names
2. List each unique entry with its ID and distinguishing features
3. Format as a numbered list with ID, Name, and unique identifier (username/email)
4. Ask user to specify which one they want by ID
Example Response Format for Multiple Results:
"I found multiple matches for 'Zanak Meshram'. Please specify which user you're referring to using their ID:
1. [ID: 005fK000001iIs0QAE] Zanak Meshram (zanak.meshram@appstrail.com.sfa)
2. [ID: 005fK000001lTSqQAM] Zanak Meshram (zanak.meshram@appstrail.comsfaapps)
Please respond with the corresponding ID number."
Example Single Result Format:
"I found 1 matching user: [ID: 005fK000001iIs0QAE] Zanak Meshram. Is this the correct user?"
Current Search Results:
{user_search_results}
 """
    llm = LLMManger()
    response = llm.invoke(prompt + state["user_search_results"])
    return {"messages" : AIMessage(content=response.content)}
