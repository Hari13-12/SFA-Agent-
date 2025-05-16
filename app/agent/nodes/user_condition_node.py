from ..core.state_models import State

def username_condition_node(state:State):
    # print("Inside Username Condition Node\n\n")
    if state["usernamecount"] == 0:
        # print("Usercount", state["usernamecount"])
        return {"next_node":"assistant_node"}
    if state["usernamecount"] == 1:
        # print("Usercount", state["usernamecount"])
        return {"next_node": "performance_report_node"}
    if state["usernamecount"] >1:
        # print("Usercount", state["usernamecount"])
        return {"next_node": "ask_user"}
    else:
        return {"next_node": "assistant_node"}