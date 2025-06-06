# from ..core.llm_manager import LLMManager
from ..core.llm_manager import LLMManger

def extract_user_id_with_llm(user_response: str, user_options: str) -> str:
    llm = LLMManger()

    prompt = f"""
    Given the following user options: {user_options},
    determine the most likely user ID based on the user's response: "{user_response}".
    Return only the user ID, without any extra text.
    """

    llm_response = llm.invoke(prompt)
    # #print(llm_response.content)
    # Ensure the response is a valid user ID
    if llm_response.content:
        return llm_response.content
    # else:
    #     return None  # If LLM fails to match, return None
    

# # resolve_user_id_with_llm("/I found multiple matches. Please specify which user you're referring to using their ID:\n\n1. [ID: 005fK000001iIs0QAE] zanak.meshram@appstrail.com.sfa\n2. [ID: 005fK000001iS01QAE] hari.prasad@appstrail.com.sfa\n3. [ID: 005fK000001jQ7RQAU] shishira@yopmail.com\n4. [ID: 005fK000001jQdiQAE] shishira1@yopmail.com\n5. [ID: 005fK000001lTSqQAM] zanak.meshram@appstrail.comsfaapps\n\nPlease respond with the corresponding ID number.", "use the fourth ID")


# def extract_user_id_with_llm(user_response: str, user_options: str) -> str:
#     prompt = f"""
#     Given the following user options: {user_options},
#     determine the most likely user ID based on the user's response: "{user_response}".
    
#     The user ID should be extracted exactly as it appears in the options, without any modifications.
#     Return only the exact user ID string, without any extra text, characters, or explanations.
    
#     Sample user_options:
#     For example, if the options are:
#     1. [ID: 005fK000001iIs0QAE] zanak.meshram@appstrail.com.sfa
#     2. [ID: 005fK000001lTSqQAM] zanak.meshram@appstrail.comsfaapps
    
#     Sample user_response:
#     Use the first one
    
#     Output:
#     you should return exactly: 005fK000001iIs0QAE
#     """
#     llm = LLMManger()
#     llm_response = llm.invoke(prompt)
#     #print("Extracted ID in LLM:\n\n", llm_response.content)
#     if llm_response:
#         return llm_response.content
#     # if llm_response.content:
#     #     # Add additional validation to ensure the ID matches the expected format
#     #     extracted_id = llm_response.content.strip()
#     #     if any(extracted_id in option for option in user_options.split('\n')):
#     #         return extracted_id
#     return None
    


