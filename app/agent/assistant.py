from ..agent.core.state_models import State
from ..agent.core.llm_manager import LLMManger

# def assistant(state:State):

#     llm = LLMManger()
#     if state["intent"] == "performance_node":
#         assistant_message = """
#        Create a vertical table with two columns (Field | Value). Start the table with User Name, User ID, and Date (fill these with placeholders if not provided). Below these, list the following fields in this exact order in the left column:
# AD HOC Orders | Unplanned Visits | Total Order Value | Non Productive Call | Productivity Call | Scheduled Call | Total Visits.

# Right column: Use values from the input data. If a field is missing, write no performance result.

# Format the table neatly. Do not add extra columns, rows, or explanations."

# Example Output for Your Input:

# Copy
# User Name: [Name]  
# User ID: [ID]  
# Date: [Date]  

# Field               | Value  
# --------------------|------  
# AD HOC Orders       | 0  
# Unplanned Visits    | 0  
# Total Order Value   | 0  
# Non Productive Call | 0  
# Productivity Call   | 0  
# Scheduled Call      | 80  
# Total Visits        | 80  

# If Total Order Value were missing:
# Field               | Value  
# --------------------|------  
# AD HOC Orders       | 0  
# Unplanned Visits    | 0  
# Total Order Value   | no performance result  
# ... (rest of the fields)  
#         """+ "Date :"+ state["date"]+ " User Name : "+ state["extracted_username"]+ " User ID : "+ state["resolved_user_id"]
        
        
        
        
        
#         print("Intent inside Assistant: ",state["intent"],state["date"])
#         print("User Count ", state["usernamecount"])
#         response = llm.invoke(assistant_message + state["response"])
#         print(response)
#         return {"messages":response}
    
#     if state["intent"] == "general":
#         assistant_prompt = "you are a helpful assistant who knows helps related general query and performance related query. other than that you are not allowed to answer any other question. if you are asked to answer any other question then you should respond with 'I am sorry, I am not allowed to answer that question.'"
#         response = llm.invoke(assistant_prompt + state["response"])
#         return {"messages": response}


def assistant(state):
    llm = LLMManger()
    if state["intent"] == "performance_node":
          if state["usernamecount"] ==0:
            assistant_message = "Tell the user that there is no user ID found for this name or maybe the user name is incorrect"
            print("User count inside Assistant : ", state["usernamecount"])
            response = llm.invoke(assistant_message + state["response"])
            print(response)
            return {"messages":response} 
          
          else:
            assistant_message = """
       Create a vertical table with two columns (Field | Value). Start the table with User Name, User ID, and Date (fill these with placeholders if not provided). Below these, list the following fields in this exact order in the left column:
AD HOC Orders | Unplanned Visits | Total Order Value | Non Productive Call | Productivity Call | Scheduled Call | Total Visits.

Right column: Use values from the input data. If a field is missing, write no performance result.

Format the table neatly. Do not add extra columns, rows, or explanations."

Example Output for Your Input:

Copy
User Name: [Name]  
User ID: [ID]  
Date: [Date]  

Field               | Value  
--------------------|------  
AD HOC Orders       | 0  
Unplanned Visits    | 0  
Total Order Value   | 0  
Non Productive Call | 0  
Productivity Call   | 0  
Scheduled Call      | 80  
Total Visits        | 80  

If Total Order Value were missing:
Field               | Value  
--------------------|------  
AD HOC Orders       | 0  
Unplanned Visits    | 0  
Total Order Value   | no performance result  
... (rest of the fields)  
        """+ "Date :"+ state["date"]+ " User Name : "+ state["extracted_username"]+ " User ID : "+ state["resolved_user_id"]
        
    
            print("User count inside Assistant : ", state["usernamecount"])
            print("Intent inside Assistant: ",state["intent"],state["date"])
            response = llm.invoke(assistant_message + state["response"])
            print(response)
            return {"messages":response}
    
    if state["intent"] == "general":
        assistant_prompt = "you are a helpful assistant who knows helps related general query and performance related query. other than that you are not allowed to answer any other question. if you are asked to answer any other question then you should respond with 'I am sorry, I am not allowed to answer that question.'"
        response = llm.invoke(assistant_prompt + state["response"])
        return {"messages": response}