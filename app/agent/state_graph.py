from langgraph.graph import StateGraph,END,START
from ..agent.core.state_models import State
from ..agent.nodes.extract_date_node import extract_date_from_query
from ..agent.nodes.intent_node import intent_classifier
from ..agent.nodes.intent_condition_node import intent_condition_node
from ..agent.nodes.user_count_node import username_count_node
from ..agent.nodes.user_condition_node import username_condition_node
from ..agent.nodes.performance_node import performance_generate_report
from ..agent.nodes.ask_user_node import ask_user
from ..agent.nodes.confirm_user_id_node import confirmed_userid_node
from ..agent.nodes.visits_node import visit_details
from .assistant import assistant

builder = StateGraph(State)

builder.add_node("date_node",extract_date_from_query)
builder.add_node("intent_node",intent_classifier)
builder.add_node("condition_for_intent",intent_condition_node)
builder.add_node("user_count_node",username_count_node)
builder.add_node("username_condition_node",username_condition_node)
builder.add_node("performance_node",performance_generate_report)
builder.add_node("ask_user_node", ask_user)
builder.add_node("confirmed_userid",confirmed_userid_node)
builder.add_node("visit_node",visit_details)
builder.add_node("assistant_node",assistant)


builder.add_edge(START, "date_node")
builder.add_edge("date_node", "intent_node")
builder.add_edge("intent_node", "condition_for_intent")
builder.add_conditional_edges(
    "condition_for_intent",
    lambda state:state["next_node"],{
        "assistant": "assistant_node",
        "user_count_node": "user_count_node",
        "visit_node" : "visit_node"
    }
)
builder.add_edge("visit_node","assistant_node")
builder.add_edge("user_count_node", "username_condition_node")

builder.add_conditional_edges(
    "username_condition_node",
    lambda state:state["next_node"],{
        "performance_report_node" : "performance_node",
        "assistant_node" : "assistant_node",
        "ask_user" : "ask_user_node"
       
    }
)
builder.add_edge("ask_user_node", "confirmed_userid")
builder.add_edge("confirmed_userid", "username_condition_node")
builder.add_edge("performance_node", "assistant_node")
builder.add_edge("assistant_node", END)



