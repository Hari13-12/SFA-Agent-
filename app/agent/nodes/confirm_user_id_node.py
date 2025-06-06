from ..core.state_models import State
from .extract_user_id import extract_user_id_with_llm

def confirmed_userid_node(state: State):
    #print("Previous interrupt value :", state["messages"][-2].content)
    # confirmed_userid = state["messages"][-1].content
    # final_id = extract_user_id_with_llm(state["messages"][-2].content, state["messages"][-1].content)
    final_id = extract_user_id_with_llm(state["user_search_results"], state["messages"][-1].content)
    #print("Extracted User ID : \n", final_id)
    state["resolved_user_id"] = final_id
    #print("Extracted User ID from State: \n", final_id)
    state["usernamecount"] = 1
    # #print("Confirmed ID after interrrupt :", state["resolved_user_id"])
    return state