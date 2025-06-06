from ..core.state_models import State
from datetime import date
from requests import  Session
from langchain_core.messages import HumanMessage,SystemMessage
from ..core.llm_manager import LLMManger

'''
def visit_details(state: State):
    llm = LLMManger()
    user_id = state["user_id"]
    start = user_id.find("_")
    user_id = user_id[0:start]
    # print("User_id in state:", user_id)
    state["response"] = "There is no visit details to display"
    s = Session()
    today = date.today()
    today = today.strftime("%Y-%m-%d")
    # print("Date: ",today)
    API_ENDPOINT = "https://appstrail-sfa-dev-ed.develop.my.salesforce.com/services/apexrest/APTLDataRequest"

    headers = {
        "Authorization": "Bearer " + state["access_token"],
        "Content-Type": "application/json",
        
    }
    body = {
        "keyword": "MarketVisit",
        "conditionName": "Planned_Date_Filter",
        "parameters": [
            {"name": "planneddate", "value": "2025-06-04"},
            {"name": "UserId", "value": user_id},
        
        ]
    }
    response = s.post(API_ENDPOINT, json=body, headers=headers)
    rec = response.json().get("records", [])
    # print(rec)
    # print("Input:",state["messages"][-1].content)
    accountid = []
    accountname = []
    for i in range(len(rec)):
        if rec[i]["parentRecord"]["Status"] == "Planned":
            accountid.append(rec[i]["parentRecord"]["AccountId"])
            accountname.append(rec[i]["parentRecord"]["AccountName"])
    # print(accountid,accountname)
    # print(len(accountid),len(accountname))

    system_prompt = SystemMessage(content= """
You are an assistant that extracts the number of future visits a user is asking for from natural language.
Your output should be a single integer, representing the number of visits requested.
If the user does not specify a number, assume they mean 1.
If the user explicitly asks for a number (e.g. "next 3 visits", "five places", "two trips"), extract and return that number.
Always return the result as a single integer (e.g., 3).
Do not return any explanation, text, or additional formatting — just the list.""")
    
    input_message = HumanMessage(content=state["messages"][-1].content)
    response = llm.invoke([system_prompt, input_message])
    number_of_visits = response.content
    # print("Number of Visits:",number_of_visits)
    visit_list = []
    for i in range(int(number_of_visits)):
        if int(number_of_visits) > len(accountname):
            visit_list = accountname
        else:
            visit_list.append(accountname[i])
    # print("Visit_list:", visit_list)
#     prompt = """
# You are a helpful and conversational AI assistant.
# Your task is to take:
# -> a user_query : {user_query}
# -> an answer : {visit_details}
# -> number of visits : {number_of_visits}
# -> available visits : {available_visits}
# -> and generate a natural, friendly chatbot-style reply.
                                  
# Respond in clear, concise, and polite natural language.
# Use the answer to directly address the user_query, without adding extra facts or changing the meaning.
# You may rephrase the answer to make it sound more human, but do not invent or assume additional information.

# Tone should be friendly, clear, and conversational.
# Do not repeat the user's question unless necessary.
# Always respond as if you're chatting with the user directly.             
#         """
#     prompt = prompt.format(user_query = state["messages"][-1].content,visit_details = visit_list, number_of_visits = number_of_visits, available_visits = len(accountname))
#     # print(prompt)
#     system_prompt = SystemMessage(content= prompt)
    
#     input_message = HumanMessage(content="Execute the mesage with provided details")
#     response = llm.invoke([system_prompt, input_message])



    prompt = """
You are a helpful and conversational AI assistant.
Your task is to generate a natural, friendly chatbot-style reply based on the following:
-> user_query: {user_query}
-> answer: {visit_details}
-> number of visits requested by the user: {number_of_visits}
-> total available visits: {available_visits}

Please follow these rules:
- If the user asks for more visits than are available, acknowledge this politely and provide only the available visits.
- Do not say the number of visits as requested if that many aren't available — be accurate.
- You can rephrase the answer to make it sound more natural, but never invent or assume additional information.
- Avoid repeating the user’s question unless needed.
- Keep the tone friendly, clear, and conversational.
- Be concise and polite in your language.

Example:
If the user asks for 3 visits, but only 1 visit is available, say something like:
"Today you have only 1 visit to [visit detail]"

Now, generate the correct response using the given inputs.
    """
    prompt = prompt.format(
        user_query=state["messages"][-1].content,
        visit_details=visit_list,
        number_of_visits=number_of_visits,
        available_visits=len(accountname)
    )
    system_prompt = SystemMessage(content=prompt)

    input_message = HumanMessage(content="Execute the message with provided details")
    response = llm.invoke([system_prompt, input_message])
    state["response"] = response.content
    return state  
'''

def visit_details(state: State):
    llm = LLMManger()
    user_id = state["user_id"]
    start = user_id.find("_")
    user_id = user_id[0:start]
    # print("User_id in state:", user_id)
    state["response"] = "There is no visit details to display"
    s = Session()
    today = date.today()
    today = today.strftime("%Y-%m-%d")
    # print("Date: ",today)
    API_ENDPOINT = "https://appstrail-sfa-dev-ed.develop.my.salesforce.com/services/apexrest/APTLDataRequest"

    headers = {
        "Authorization": "Bearer " + state["access_token"],
        "Content-Type": "application/json",
        
    }
    body = {
        "keyword": "MarketVisit",
        "conditionName": "Planned_Date_Filter",
        "parameters": [
            {"name": "planneddate", "value": "2025-06-04"},
            {"name": "UserId", "value": user_id},
        
        ]
    }
    response = s.post(API_ENDPOINT, json=body, headers=headers)
    rec = response.json().get("records", [])
    # print(rec)
    # print("Input:",state["messages"][-1].content)
    accountid = []
    accountname = []
    for i in range(len(rec)):
        if rec[i]["parentRecord"]["Status"] == "Planned":
            accountid.append(rec[i]["parentRecord"]["AccountId"])
            accountname.append(rec[i]["parentRecord"]["AccountName"])
    prompt = """
*You are a helpful assistant that manages my visit list, which contains the following shops I plan to visit next:
visit_list = {visits_list}

Your task is to answer any questions I have about this list, such as:
Respond to my questions in a friendly, conversational way, like a friend helping me plan my errands

"What is my next visit?" → Reply with the first item in the list.

"Where should I go next?" → Suggest the next pending visit (first item).

"Whats left on my visit list?" → List all remaining shops in order.

"Have I been to [X] yet?" → Check if [X] is visited (assume items are removed after visiting).

"How many places are left?" → Count and return the number of pending visits.

"Whats after [X]?" → Return the shop immediately after [X] in the list.

Assume the list is ordered and mutable (changes as I visit/update). Keep answers concise and action-oriented.
If the list is empty, say: "Your visit list is empty!"
"""
    prompt = prompt.format(visits_list = accountname )
    system_prompt = SystemMessage(content= prompt)
        
    input_message = HumanMessage(content=state["messages"][-1].content)
    response = llm.invoke([system_prompt, input_message])
    state["response"] = response.content
    return state
