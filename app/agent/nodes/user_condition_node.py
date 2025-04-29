from ..core.state_models import State

def username_condition_node(state:State):
    if state['usernamecount'] == 0:
        return {"next_node":"assistant_node"}
    if state["usernamecount"] == 1:
        return {"next_node": "performance_report_node"}
    if state["usernamecount"] >1:
        return {"next_node": "ask_user"}
    else:
        return {"next_node": "assistant_node"}