import os
import pandas as pd
from phoenix import Client
from phoenix.trace.dsl import SpanQuery
from datetime import datetime
from phoenix.evals import TOOL_CALLING_PROMPT_TEMPLATE
import re

print(TOOL_CALLING_PROMPT_TEMPLATE)
 
os.environ["PHOENIX_CLIENT_HEADERS"] = "api_key=20781f216b8287a201c:855650c"
os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "https://app.phoenix.arize.com"
 
 
client = Client(
    endpoint="https://app.phoenix.arize.com",  
    api_key="20781f216b8287a201c:855650c",  
    warn_if_server_not_running=False          
)
 
query = SpanQuery()
 
try:
    spans_df = client.query_spans(query)
   
    # Display results
    if spans_df is not None and not spans_df.empty:
        # print(f"Successfully retrieved {len(spans_df)} spans from Phoenix Cloud!")
        # print("Columns:", spans_df.columns.tolist())
        # print("Sample data:")
        print(spans_df.head())
 
        columns_to_keep = ['context.span_id', 'name', 'start_time', 'end_time','attributes.llm.output_messages','attributes.llm.input_messages']
        # Filter the DataFrame
        df = spans_df[columns_to_keep]
        event_series = spans_df['attributes.event']
        rows_to_drop = []
# Iterate over rows
        for index, row in df.iterrows():
            input_val = row['attributes.llm.input_messages']
            output_val = row['attributes.llm.output_messages']
           
            if (pd.isna(input_val) or str(input_val).strip() == '') and \
            (pd.isna(output_val) or str(output_val).strip() == ''):
                print(f"Row {index} has empty 'input' and 'output' columns.")
                rows_to_drop.append(index)
        df = df.drop(index=rows_to_drop)
        # df.to_csv('final_phoenix_altered_4.csv', index=False)
 
        # # df2 = df
        # df = pd.read_csv("final_phoenix_altered_4.csv")
        # Save to CSV for further analysis
        final_df = pd.DataFrame(columns=['input', 'output', 'duration'])
        input_list = []
        output_list = []
        start_time_list = []
        end_time_list = []
        duration_list = []
 
        for index, row in df.iterrows():
            input_val = row['attributes.llm.input_messages']
            output_val = row['attributes.llm.output_messages']
            start_time_val = row['start_time']
            end_time_val = row['end_time']
 
            # # Add non-empty input
            if pd.notna(input_val) and str(input_val).strip() != '':
                input_list.append(input_val)
                start_time_list.append(start_time_val)
 
            if pd.notna(output_val) and str(output_val).strip() != '':
                output_list.append(output_val)
                end_time_list.append(end_time_val)
        print("\n\n\n")
        print(input_list)
        print(output_list)
        print(start_time_list)
        print(end_time_list)

 
        # for i,j in zip(start_time_list,end_time_list):
        #     start_time = datetime.fromisoformat(i)
        #     end_time = datetime.fromisoformat(j)
 
        #     # Calculate the difference
        #     time_difference = end_time - start_time
        #     print("\n\n")
        #     print(time_difference)
        #     duration_list.append(time_difference.total_seconds())

        for start, end in zip(start_time_list, end_time_list):
            diff = end - start
            print(f"Duration: {diff} ({diff.total_seconds()} seconds)")
            duration_list.append(diff.total_seconds())
 
        for i, j, k in zip(input_list, output_list, duration_list):
            final_df.loc[len(final_df)] = {'input': i, 'output': j, 'duration':k}
 
    

        input_tokens = []
        output_tokens = []
        total_tokens = []
        price_list = []
        # Loop through all rows
        for i in range(len(event_series)):
            df_0 = event_series[i]

            # Properly check for NaN
            if isinstance(df_0, str) and "input_tokens" in df_0:

                # Extract relevant substring
                start = df_0.find("input_tokens")
                end = df_0.find("input_token_details")
                token_str = df_0[start:end-3]

                # Extract tokens with regex
                token_pairs = re.findall(r"'?(\w+_tokens)'?:\s*(\d+)", token_str)
                token_dict = {key: int(value) for key, value in token_pairs}

                # Print output
                print(f"Row {i}")
                print("Token dict:", token_dict)
                print("Input tokens:", token_dict.get("input_tokens"))
                print("Output tokens:", token_dict.get("output_tokens"))
                print("Total tokens:", token_dict.get("total_tokens"))
                print("-" * 40)
                if len(input_tokens) == 0:
                    input_tokens.append(token_dict.get("input_tokens"))
                    output_tokens.append(token_dict.get("output_tokens"))
                    total_tokens.append(token_dict.get("total_tokens"))
                try: 
                    if input_tokens[-1]!= token_dict.get("input_tokens") and output_tokens[-1]!= token_dict.get("output_tokens") and total_tokens[-1]!= token_dict.get("total_tokens"):
                        input_tokens.append(token_dict.get("input_tokens"))
                        output_tokens.append(token_dict.get("output_tokens"))
                        total_tokens.append(token_dict.get("total_tokens"))
                except Exception as e:
                    print(f"Error processing row {i}: {e}")
                    continue

            else:
                continue
        for i in range(len(input_tokens)):
            price = input_tokens[i] * 0.00000005 + output_tokens[i] * 0.00000008
            formatted_price = format(price, ".8f")  # Always 8 decimal places
            price_list.append(formatted_price)
            # price_list.append(input_tokens[i]*0.00000005 + output_tokens[i]*0.00000008)
        print("\nTokens")
        print(input_tokens)
        print(output_tokens)
        print(total_tokens)
        print(price_list)
        data ={
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "price": price_list
        }

        data_df = pd.DataFrame(data)
        combined_df = pd.concat([final_df, data_df], axis=1)
        # final_df.to_csv('final_df_8.csv', index=False)
        output_file = "evaluation_traces_19_05_1.csv"
        combined_df.to_csv(output_file)
        print(f"Saved traces to {output_file}")
        print(duration_list)
    else:
        print("No spans found or empty dataframe returned")
       
 
except Exception as e:
    print(f"Error retrieving traces from Phoenix Cloud: {e}")
   
    # Try to list projects and experiment with different parameters
    try:
        print("\nTrying to list projects...")
        try:
            # Check if there's a method to list projects
            if hasattr(client, 'get_projects'):
                projects = client.get_projects()
                print(f"Projects: {projects}")
            elif hasattr(client, 'projects'):
                if hasattr(client.projects, 'list'):
                    projects = client.projects.list()
                    print(f"Projects: {projects}")
        except Exception as proj_e:
            print(f"Error listing projects: {proj_e}")
       
        # Try to get traces with different parameters
        print("\nTrying with different parameters...")
       
        # Try with project name
        try:
            spans_df = client.get_spans_dataframe(project_name="default")
            if spans_df is not None and not spans_df.empty:
                print(f"Successfully retrieved {len(spans_df)} spans with project_name!")
        except Exception as p_e:
            print(f"Error with project_name: {p_e}")
           
        # Try with limit only
        try:
            spans_df = client.get_spans_dataframe(limit=100)
            if spans_df is not None and not spans_df.empty:
                print(f"Successfully retrieved {len(spans_df)} spans with limit!")
        except Exception as l_e:
            print(f"Error with limit: {l_e}")
   
    except Exception as debug_e:
        print(f"Error during debugging: {debug_e}")
 

 
 
 