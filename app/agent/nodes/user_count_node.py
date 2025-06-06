from ..core.state_models import State
from requests import  Session

def username_count_node(state: State):

    #print("Im in username_count_node\n")
    s = Session()
    try:
        API_ENDPOINT = "https://appstrail-sfa-dev-ed.develop.my.salesforce.com/services/apexrest/APTLDataRequest"

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + state["access_token"],
            "Cookie": "BrowserId=GSlXreH9Ee-ZFAW_KW_xKQ; CookieConsentPolicy=0:1; LSKey-c$CookieConsentPolicy=0:1",
        }
        #print(state["extracted_username"])
        body = {
            "keyword": "User",
            "conditionName": "Name_Filter",
            "parameters": [{"name": "Name", "value": state["extracted_username"]}],
        }
        response = s.post(API_ENDPOINT, json=body, headers=headers)
        data = response.json()
        #print("Data from user_count_node")
        #print(len(data.get("records", [])))
        state["usernamecount"] = len(data.get("records", []))

        

        if len(data.get("records", [])) == 0:
            # state["response"] = "User not found"
            state["response"] = "User not found!!! Please provide the correct name."
            #print("User Count in State ", state["usernamecount"])    ##### usercount state
            return state

        if len(data.get("records", [])) > 1:
            # user_details = []
            # for user in data.get("records", []):
            #     user_details.append({"Name":user.get("parentRecord", {}).get("Name"),"UserName":user.get("parentRecord", {}).get("Username"), "ID": user.get("parentRecord",{}).get("Id")})

            user_details = {}
            for index, user in enumerate(data.get("records", []), start=1):
                parent = user.get("parentRecord", {})
                key = f"ID : {index}"
                user_details[key] = {
                    # "Name": f"**{parent.get("Name")}**",
                    "UserName": f"<em>{parent.get("Username")}<em>",
                    "ID": f"<b>{parent.get("Id")}<b>"
                }
            formatted_output = []
            count = 1
        
            for key, value in user_details.items():
                    # formatted_output.append(
                    #     f"<br>**ID - {count}:**<br>"
                    # )
                    for field_key, field_value in value.items():
                        if isinstance(field_value, dict):
                            formatted_output.append(
                                f"  {field_key}:"
                            )
                            for sub_key, sub_value in field_value.items():
                                formatted_output.append(
                                    f"    {sub_key}: {sub_value}"
                                )
                        else:
                            formatted_output.append(f"  {field_key}: {field_value}")
                    count += 1

            
            user_details_1 = {}
            for index, user in enumerate(data.get("records", []), start=1):
                parent = user.get("parentRecord", {})
                key = f"ID : {index}"
                user_details_1[key] = {
                    # "Name": f"**{parent.get("Name")}**",
                    "UserName": f"<em>{parent.get("Username")}<em>",
                    # "ID": f"<b>{parent.get("Id")}<b>"
                }
            formatted_output_1 = []
            count = 1
        
            for key, value in user_details_1.items():
                    # formatted_output.append(
                    #     f"<br>**ID - {count}:**<br>"
                    # )
                    for field_key, field_value in value.items():
                        if isinstance(field_value, dict):
                            formatted_output_1.append(
                                f"  {field_key}:"
                            )
                            for sub_key, sub_value in field_value.items():
                                formatted_output_1.append(
                                    f"    {sub_key}: {sub_value}"
                                )
                        else:
                            formatted_output_1.append(f"  {field_key}: {field_value}")
                    count += 1
            
            state["user_search_results"] = "\n".join(formatted_output)
            state["user_display_results"] = "\n".join(formatted_output_1)
            # state["response"] = "Multiple users found. Please provide the correct name."
            # state["usernamecount"] = 2
            #print("State Multiple ID's : ", state["user_search_results"])
            #print("User Count in State ", state["usernamecount"])    ##### usercount state
            #print("User display results\n\n",state["user_display_results"])
            return state
            
        if len(data.get("records", [])) == 1:
            for user in data.get("records", []):
                #print("User in user_count_node:",user)
                if user.get("parentRecord", {}).get("Name") == state["extracted_username"]:
                    user_id = user["parentRecord"].get("Id")
                    state["resolved_user_id"] = user_id
                    #print("\nFor single User\n")
                    #print("User Count in State ", state["usernamecount"])    ##### usercount state
                    #print("State in resolve id",state)
                    return state
                else:
                    state["response"] = "User not found!!! Please provide the correct name."
                    state["usernamecount"] = 0
                    #print("User Count in State ", state["usernamecount"])    ##### usercount state
                    return state
        # if user_id is None:
        #     state["response"] = "User not found!!! Please provide the correct name."
        # return state

    except Exception as e:
        print(f"Error: {e}")