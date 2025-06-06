from ..agent.core.state_models import State
from ..agent.core.llm_manager import LLMManger
from langchain_core.messages import AIMessage


def assistant(state):
    llm = LLMManger()
    if state["intent"] == "visit_details":
      #  assistant_message = "Say about the visit details"
      #  response = llm.invoke(assistant_message + state["response"])
      #  print(response)
      #  return {"messages":response,"map_cr":None}
       return {"messages" : AIMessage(content=state["response"]),"map_cr":None}
    if state["intent"] == "performance_node":
          if state["usernamecount"] ==0:
            assistant_message = "Tell the user that there is no user ID found for this name or maybe the user name is incorrect"
            #print("User count inside Assistant : ", state["usernamecount"])
            response = llm.invoke(assistant_message + state["response"])
            #print(response)
            return {"messages":response,"map_cr":None}
    
          
          else:
            #print("Confirmed User ID in assistant : \n\n", state["resolved_user_id"])
        
            #print("Intent inside Assistant: ",state["intent"],state["date"])
            #print("In assistant state response :\n\n", state["response"])
            #print(state['map_cr'])
            if state['map_cr'] is not None:
              #print("In assistant state response :\n\n", state["map_cr"])

              assistant_message = """
              Return performance metrics and location map (if available) in EXACTLY this format:

              Name: <b>{user_name}</b><br>
              Id: <b>{user_id}</b><br>
              Date: <b>{date}</b><br>

              <table>
                <tr>
                  <th>Metric Name</th>
                  <th>Values</th>
                </tr>
                <tr>
                  <td>AD HOC Orders</td>
                  <td><b>N/A</b></td>
                </tr>
                <tr>
                  <td>Unplanned Visits</td>
                  <td><b>N/A</b></td>
                </tr>
                <tr>
                  <td>Total Order Value</td>
                  <td><b>N/A</b></td>
                </tr>
                <tr>
                  <td>Non-Productive Calls</td>
                  <td><b>N/A</b></td>
                </tr>
                <tr>
                  <td>Productive Calls</td>
                  <td><b>N/A</b></td>
                </tr>
                <tr>
                  <td>Scheduled Calls</td>
                  <td><b>N/A</b></td>
                </tr>
              </table>

            Rules:
            1. Use the EXACT performance metrics HTML structure provided above
            2. Include the map HTML exactly as provided if available
            3. Empty metric values should show <b>N/A</b>
            4. Never modify the map HTML code in any way
            5. If ALL metric values are empty, return: "No performance details available"
            6. Never include code examples or explanations
            7. Preserve all HTML tags exactly as provided
            8. The map code must appear exactly as provided after the performance metrics
              """
              assistant_message = assistant_message.format(user_name=state["extracted_username"], user_id=state["resolved_user_id"],date=state["date"])
              # response = llm.invoke(assistant_message + state["response"] + "Map code:\n" + state["map_cr"])
              #print("FINAL RESPONSE IN ASSISTANT\n\n", response)
              response = llm.invoke(assistant_message + state["response"])
              return {"messages" : response,"map_cr":state["map_cr"]}
              
            else:
              assistant_message = """
              Return performance metrics in EXACTLY this HTML table format (do NOT return Python code or Markdown):

              Name: <b>{user_name}</b><br>
              Id: <b>{user_id}</b><br>
              Date: <b>{date}</b><br>

              <table>
                <tr>
                  <th>Metric Name</th>
                  <th>Values</th>
                </tr>
                <tr>
                  <td>AD HOC Orders</td>
                  <td><b>N/A</b></td>
                </tr>
                <tr>
                  <td>Unplanned Visits</td>
                  <td><b>N/A</b></td>
                </tr>
                <tr>
                  <td>Total Order Value</td>
                  <td><b>N/A</b></td>
                </tr>
                <tr>
                  <td>Non-Productive Calls</td>
                  <td><b>N/A</b></td>
                </tr>
                <tr>
                  <td>Productive Calls</td>
                  <td><b>N/A</b></td>
                </tr>
                <tr>
                  <td>Scheduled Calls</td>
                  <td><b>N/A</b></td>
                </tr>
              </table>

              Rules:
              1. Use EXACTLY this HTML structure - do not modify table tags
              2. Empty values should show <b>N/A</b> (no content between tags)
              3. Replace N/A with empty <b>N/A</b> tags
              4. If ALL values are empty, return: "No performance details available"
              5. Never include code examples or explanations
              6. Preserve all HTML tags exactly as shown
              """
              assistant_message = assistant_message.format(user_name=state["extracted_username"], user_id=state["resolved_user_id"],date=state["date"])
              response = llm.invoke(assistant_message + state["response"])
              #print("FINAL RESPONSE IN ASSISTANT\n\n", response)
              return {"messages" : response,"map_cr":None}
    
    if state["intent"] == "general":
        assistant_prompt = '''
You are a Performance Assistant. Your sole function is to deliver structured daily performance data for a specific user on a specific date.
 
**Strict Rules:**
 
1. **Greetings:**  
   If the user sends greetings (e.g., "Hi", "Hello", "Thanks"), reply politely and briefly (e.g., "Hello! How can I help with performance data?").
 
2. **Role/Functionality Queries:**  
   If the user asks about your capabilities, purpose, or who you are (e.g., "What can you do?", "Who are you?", "What is your function?"), reply:  
   `"I am a Performance Assistant. My sole function is to provide daily performance metrics for a specific user when given their name and a date."`
 
3. **Out-of-Scope Requests:**  
   If the user asks anything unrelated to performance data (e.g., biography ,celebrities,recipes, news, opinions, random text),strictly  reply:  
   `"I specialize only in performance metrics. Please provide a user and date to proceed."`
 
**Critical Enforcement:**  
- Never answer, acknowledge, or engage with off-topic queries-even partially.  
- Never generate creative or default replies.  
- Only respond according to the rules above.
-Strictly Never answer, acknowledge, or engage with out-of-scope queries-even partially. Never generate creative or default replies.
 
**Instruction:**  
Strictly follow these rules for every user message. Do not deviate or improvise. Only respond as specified.
        '''
        response = llm.invoke(assistant_prompt + state["response"])
        return {"messages": response,"map_cr":None}
  