from ..core.state_models import State
from ..core.llm_manager import LLMManger
from langchain_core.messages import AIMessage

def ask_user(state: State):
    # print("Im inside ask_user node")

    prompt = """Analyze these user search results and generate a clear selection question for the user. 
Follow these steps:
1. Identify if there are multiple entries with similar names
2. List each unique entry with its ID and distinguishing features
3. Format as a numbered list with ID, Name, and unique identifier (username/email)
4. Ask user to specify which one they want by ID
Example Response Format for Multiple Results:
"I found multiple matches for your search. Please specify which user you're referring to using their ID:
1. <em>(zanak.meshram@appstrail.com.sfa)</em>
2. <em>(zanak.meshram@appstrail.comsfaapps)</em>
Please reply for choosing the correct user."

Current Search Results:
{user_display_results}
 """  
    # prompt = prompt.format(user_name = state["extracted_username"])
    # print("IN ASK USER NODE\n\n", state["extracted_username"])
#     prompt = """
#     Example Response Format for Multiple Results:
# "I found multiple matches for 'Zanak Meshram'. Please specify which user you're referring to using their ID:
# 1. ID: **005fK000001iIs0QAE** Zanak Meshram (zanak.meshram@appstrail.com.sfa)
# 2. ID: **005fK000001lTSqQAM** Zanak Meshram (zanak.meshram@appstrail.comsfaapps)
# Please answer to choose the ID."
# Current Search Results:
# {user_search_results}
# """

#     prompt = """
# Analyze these user search results and generate a clear selection question for the user. 
# Follow these steps:
# 1. Identify if there are multiple entries with similar names.
# 2. List each unique entry with its ID and distinguishing features.
# 3. Format as a numbered list with ID (bolded using <b> tags), Name, and unique identifier (username/email).
# 4. Ask the user to specify which one they want by ID.

# **Rules:**
# - Preserve the <b> tags for IDs (do **not** convert them to Markdown or other formats).
# - If only one result exists, confirm it directly.
# - For multiple results, list them with IDs in bold.

# **Example Response (Multiple Results):**
# "I found multiple matches. Please specify which user you're referring to using their ID:
# 1. ID: <b>005fK000001iIs0QAE</b> - zanak.meshram@appstrail.com.sfa
# 2. ID: <b>005fK000001lTSqQAM</b> - zanak.meshram@appstrail.comsfaapps
# Please respond with the corresponding ID number."

# **Example Response (Single Result):**
# "I found 1 matching user: ID: <b>005fK000001iIs0QAE</b> - Zanak Meshram. Is this the correct user?"

# **Current Search Results:**
# {user_search_results}
# """
    llm = LLMManger()
    response = llm.invoke(prompt + state["extracted_username"] + state["user_display_results"]) 
    # print("\n\nResponse in ASK USER NODE\n\n", response.content)
    return {"messages" : AIMessage(content=response.content)}
