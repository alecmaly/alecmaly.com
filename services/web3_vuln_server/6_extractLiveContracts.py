import pandas as pd
from datetime import date
import re

current_date = date.today()
formatted_date = current_date.strftime("%Y-%m-%d")


def read_csv(filepath):
    try:
        # Read the CSV file directly into a DataFrame
        df = pd.read_csv(filepath)

        # Convert the DataFrame to a list of dictionaries
        # Each dictionary represents a row, with column names as keys
        return df.to_dict(orient='records')
    except:
        return []
    
output_filepath = "./contract_monitoring/live_contracts.csv"
seen_live_contracts = read_csv(output_filepath)

seen_contracts_map = {}
for c in seen_live_contracts:
    seen_contracts_map[f"{c['chain']}-{c['address']}"] = True    

# load 


# Replace with your CSV file path
data = read_csv('immunefi_data.csv')
for row in data:
    # why blanks get read as floats is confusing, probably a pandas thing. Ignore them.
    if row['live_contract_urls'] and type(row['live_contract_urls']) != float:
        for live_contract_url in row['live_contract_urls'].split(';'):
            domain = live_contract_url.split("//")[1].split("/")[0]

            # Search for the Ethereum address in the URL
            # address = live_contract_url.split("/")[-1]
            try:
                address_pattern = r"0x[a-fA-F0-9]{40}"
                address = re.search(address_pattern, live_contract_url).group(0)
            except Exception as e:
                print(f"failed to get address for url {live_contract_url}", e)
                continue

            contract_key = f"{domain}-{address}"
            if seen_contracts_map.get(contract_key, None):
                continue

            # append to list the newly found contracts
            seen_live_contracts.append({
                'date': formatted_date,
                'project': row['id'],
                'chain': domain,
                'address': address
            })
            seen_contracts_map[f"{domain}-{address}"] = True


# output to file        
df = pd.DataFrame(seen_live_contracts)
df.to_csv(output_filepath, index=False)



#     print(index, row)

# # Display the first 5 rows of the DataFrame
# print(df.head())
