from typing_extensions import Annotated,TypedDict,List
from langgraph.graph.message import add_messages

class State(TypedDict):
    intent:str
    messages: Annotated[List,add_messages]  # Full chat history
    date:str
    access_token: str  
    extracted_username: str
    resolved_user_id: str
    usernamecount:int
    performance_data: str
    response:str
    user_search_results:str
    api_endpoint: str = "https://appstrail-sfa-dev-ed.develop.my.salesforce.com/services/apexrest/APTLDataRequest"
    session_id:str
    map_cr: str
    user_display_results: str
    user_id: str