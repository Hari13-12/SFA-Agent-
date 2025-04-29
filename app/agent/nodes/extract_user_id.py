# from ..core.llm_manager import LLMManager
from ..core.llm_manager import LLMManger

def extract_user_id_with_llm(user_response: str, user_options: str) -> str:
    prompt = f"""
    Given the following user options: {user_options},
    determine the most likely user ID based on the user's response: "{user_response}".
    Return only the user ID, without any extra text.
    """
    llm = LLMManger()
    llm_response = llm.invoke(prompt)
    if llm_response.content:
        return llm_response.content
    else:
        return None  
    # return None
    


