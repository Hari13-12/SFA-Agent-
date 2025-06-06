from ..core.state_models import State


def intent_condition_node(state: State):
    if state["intent"] == "general":
        return {"next_node":"assistant"}
    if state["intent"] == "performance_node":
        # #print("i am in performance_node")
        return {"next_node": "user_count_node"}
    if state["intent"] == "visit_details":
        return {"next_node": "visit_node"}