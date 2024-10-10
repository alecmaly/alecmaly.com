import pandas as pd
from datetime import date
from dateutil.parser import parse
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

seen_contracts_map = {}
output_filepath = "./contract_monitoring/live_contracts.csv"

## Load previously seen live contracts, this may not be necessary as I only want contracts in scope 
seen_live_contracts = read_csv(output_filepath)
for c in seen_live_contracts:
    seen_contracts_map[f"{c['chain']}-{c['address']}"] = c



# Replace with your CSV file path
data = read_csv('immunefi_data.csv')
addresses_in_scope = []
for row in data:
    # why blanks get read as floats is confusing, probably a pandas thing. Ignore them.
    if row['live_contract_urls'] and type(row['live_contract_urls']) != float:
        for addedAt_plus_url in row['live_contract_urls'].split(';'):
            added_at, live_contract_url = addedAt_plus_url.split('~')
            domain = live_contract_url.split("://")[-1].lstrip('/').split("/")[0]

            added_at = parse(added_at).strftime("%Y-%m-%d")

            # Search for the Ethereum address in the URL
            # address = live_contract_url.split("/")[-1]
            try:
                address_pattern = r"0x[a-fA-F0-9]{40}"
                address = re.search(address_pattern, live_contract_url).group(0)
            except Exception as e:
                print(f"failed to get address for url {live_contract_url}", e)
                continue

            if not domain:
                print("[!] Domain not found")
                continue
            
            addresses_in_scope.append(address)
            contract_key = f"{domain}-{address}"
            

            lookup_item = seen_contracts_map.get(contract_key, None)
            if lookup_item:
                lookup_item['date'] = added_at if added_at else formatted_date
            else:
                # append to list the newly found contracts
                o = {
                    'date': added_at if added_at else formatted_date,
                    'project': row['id'],
                    'chain': domain,
                    'address': address
                }
                seen_live_contracts.append(o)
                seen_contracts_map[f"{domain}-{address}"] = o

for c in seen_live_contracts:
    if c['address'] in addresses_in_scope:
        c['in_scope'] = True
    else:
        c['in_scope'] = False

# output to file        
df = pd.DataFrame(seen_live_contracts)
df.to_csv(output_filepath, index=False)



#     print(index, row)

# # Display the first 5 rows of the DataFrame
# print(df.head())
