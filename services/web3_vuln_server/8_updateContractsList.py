import pandas as pd
import os
from web3 import Web3
import requests
from datetime import datetime
import json

# additional targets
# in wiki: project "dforce": https://github.com/dforce-network/Immunefi/wiki?utm_source=immunefi

from dotenv import load_dotenv
import os

# load .env file
load_dotenv()


## CONSTANTS
INUFRA_KEY = os.getenv("INUFRA_KEY")

# TODO: create function to handle requests with rate limits
def requestWithRatelimit(url, rateLimit):
    return ""



TOKENS = {}
TOKENS["etherscan.io"] = os.getenv("ETHERSCAN_TOKEN")
TOKENS["bscscan.com"] = os.getenv("BSSCAN_TOKEN")
TOKENS["optimistic.etherscan.io"] = os.getenv("OPTIMISTIC_ETHERSCAN_TOKEN")
TOKENS["polygonscan.com"] = os.getenv("POLYSCAN_TOKEN")
TOKENS["basescan.org"] = os.getenv("BASESCAN_TOKEN")
TOKENS["arbiscan.io"] = os.getenv("ARBISCAN_TOKEN")
TOKENS["ftmscan.com"] = os.getenv("FTMSCAN_TOKEN")
TOKENS["cronoscan.com"] = os.getenv("CRONOSCAN_TOKEN")


DOMAIN_HOST_MAP = {}
DOMAIN_HOST_MAP["optimistic.etherscan.io"] = "api-optimistic.etherscan.io"




def GetSourceCode(address, DOMAIN, token, download=False, download_root_folder=None):
    if not download_root_folder:
        download_root_folder = address 
    HOST = DOMAIN_HOST_MAP.get(DOMAIN, f"api.{DOMAIN}")
    # pad address w/ zero's
    hex_part = address.replace("0x", "")
    address = "0x" + hex_part.zfill(40)
    action = "getsourcecode"
    uri = f"https://{HOST}/api?module=contract&action={action}&address={address}&apikey={token}"
    resp = requests.get(uri)  # NEET TO FIX HERE
    source_files = {}
    try:
        for ele in resp.json()['result']:
            try:
                try:
                    sources = json.loads(ele['SourceCode'][1:-1])['sources']
                except:
                    sources = json.loads(ele['SourceCode'])
                for source_file in sources:
                    source_files[source_file] = sources[source_file]['content']
            except:
                source_files['flattened'] = ele['SourceCode']
        # download
        if download:
            open('./called2.txt', 'w').write("called")
            for filepath in source_files.keys():
                source_code = source_files[filepath]
                os.makedirs(f"./{download_root_folder}/{'/'.join(filepath.split('/')[:-1])}", 777, exist_ok=True)
                open(f"./{download_root_folder}/{filepath}", "w", encoding="utf-8").write(source_code)
    except Exception as e:
        print("failed to get source files / download", e)
    return resp.json()['result']

# download files
# code = GetSourceCode(address, "etherscan.io", "4BVQ9MHEAKBH6KNB6VYWED6J79RP36IXMB", download=True)


def GetLastTransactionTime(address, DOMAIN, token):
    HOST = DOMAIN_HOST_MAP.get(DOMAIN, f"api.{DOMAIN}")
    uri = f"https://{HOST}/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=10&sort=desc&apikey={token}"
    resp = requests.get(uri)
    data = resp.json()
    timestamp = int(data['result'][0]['timeStamp'])
    date_time = datetime.fromtimestamp(timestamp)
    return date_time



# GetLastTransactionTime(address)


#### update
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
live_contracts = read_csv(output_filepath)

contracts_in_scope = []
i = 0
for row in live_contracts:
    i += 1
    if i % 20 == 0:
        print(f"Completed {i} / {len(live_contracts)}")

    if not row['in_scope']:
        continue

    contracts_in_scope.append(row['address'])

    token = TOKENS.get(row['chain'], None)
    try: 
        # check if ContractName is defined, if not - needs a lookup
        if any([type(row.get(p, None)) in [float, type(None)] for p in ['ContractName', 'CompilerVersion']]) and token:
        # if type(row.get('ContractName', None)) in [float, type(None)] and token:
            # if not updated
            code = GetSourceCode(row['address'], row['chain'], token, download=False)
            row['ContractName'] = code[0].get('ContractName', '<error>')
            row['impl_address'] = code[0].get('impl_address', '')
            row['CompilerVersion'] = code[0].get('CompilerVersion', '<error>')
    except Exception as e:
        print(f"Failed on {row['chain']} for {row['address']}", e)



# output to file        
df = pd.DataFrame(live_contracts)
df.to_csv(output_filepath, index=False)




###
## Update proxy details
###

output_filepath = "./contract_monitoring/live_contract_proxies.csv"
live_contract_proxies = read_csv(output_filepath)

i = 0
for row in live_contract_proxies:
    i += 1
    if i % 20 == 0:
        print(f"Completed {i} / {len(live_contract_proxies)}")

    if row['address'] not in contracts_in_scope:
        continue

    token = TOKENS.get(row['chain'], None)
    try: 
        # check if ContractName is defined, if not - needs a lookup
        if any([type(row.get(p, None)) in [float, type(None)] for p in ['ProxyContractName', 'ProxyCompilerVersion']]) and token:
        # if type(row.get('ProxyContractName', None)) in [float, type(None)] and token:
            # if not updated
            code = GetSourceCode(row['impl_address'], row['chain'], token, download=False)

            row['ProxyContractName'] = code[0].get('ContractName', '<error>')
            row['ProxyCompilerVersion'] = code[0].get('CompilerVersion', '<error>')
    except Exception as e:
        print(f"Failed on {row['chain']} for {row['impl_address']}", e)



# output to file        
df = pd.DataFrame(live_contract_proxies)
df.to_csv(output_filepath, index=False)

