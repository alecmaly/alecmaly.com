import pandas as pd
from datetime import date
from web3 import Web3
from dotenv import load_dotenv
import os

# pip install python-dotenv


## CONSTANTS
INUFRA_KEY = os.getenv("INUFRA_KEY")

BLOCKCHAIN_INFURA_AUTH_MAP = {}
BLOCKCHAIN_INFURA_AUTH_MAP['etherscan.io'] = f"https://mainnet.infura.io/v3/{INUFRA_KEY}"
BLOCKCHAIN_INFURA_AUTH_MAP['sepolia.etherscan.io'] = f"https://sepolia.infura.io/v3/{INUFRA_KEY}"
BLOCKCHAIN_INFURA_AUTH_MAP['optimistic.etherscan.io'] = f"https://optimism-mainnet.infura.io/v3/{INUFRA_KEY}"
BLOCKCHAIN_INFURA_AUTH_MAP['polygonscan.com'] = f"https://polygon-mainnet.infura.io/v3/{INUFRA_KEY}"
BLOCKCHAIN_INFURA_AUTH_MAP['basescan.org'] = f"https://base-mainnet.infura.io/v3/{INUFRA_KEY}"
BLOCKCHAIN_INFURA_AUTH_MAP['goreli.basescan.org'] = f"https://base-goerli.infura.io/v3/{INUFRA_KEY}"
BLOCKCHAIN_INFURA_AUTH_MAP['cronoscan.com'] = f""
BLOCKCHAIN_INFURA_AUTH_MAP['moonbean.moonscan.io'] = f""
BLOCKCHAIN_INFURA_AUTH_MAP['arbiscan.io'] = f"https://arbitrum-mainnet.infura.io/v3/{INUFRA_KEY}"
BLOCKCHAIN_INFURA_AUTH_MAP['aurorascan.dev'] = f"https://aurora-mainnet.infura.io/v3/{INUFRA_KEY}"
BLOCKCHAIN_INFURA_AUTH_MAP['www.bscscan.com'] = f"https://bnbsmartchain-mainnet.infura.io/v3/{INUFRA_KEY}"
BLOCKCHAIN_INFURA_AUTH_MAP['bscscan.com'] = f"https://bnbsmartchain-mainnet.infura.io/v3/{INUFRA_KEY}"
BLOCKCHAIN_INFURA_AUTH_MAP['evm.confluxscan.io'] = f""
BLOCKCHAIN_INFURA_AUTH_MAP['ftmscan.com'] = f""

CURRENT_DATE = date.today()
FORMATTED_DATE = CURRENT_DATE.strftime("%Y-%m-%d")



def showDataInChunks(result_bytes):
    chunk_size = 32

    # Iterate over the byte string in chunks
    for i in range(0, len(result_bytes), chunk_size):
        chunk = result_bytes[i:i + chunk_size]
        print(f"Chunk {i // chunk_size + 1} ({hex(i)}): {chunk}")
    



def getProxyAddress(conn_url, contract_address):
    contract_address = Web3.to_checksum_address(contract_address)

    # also try looking at facets() function?
    try:
        web3 = Web3(Web3.HTTPProvider(conn_url))  # need different for each network
        impl_contract = Web3.to_hex(
            web3.eth.get_storage_at(
                contract_address,
                "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
            )
        )

        # TODO: make recursive?

        impl_contract_unpadded = "0x" + impl_contract.lstrip("0x").lstrip("0")
        return impl_contract_unpadded
    except:
        return None


def getDiamondFacetAddresses(conn_url, contract_address):
    contract_address = Web3.to_checksum_address(contract_address)

    try:
        # from Diamond standard
        contract_abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "facets",
                "outputs": [
                    {
                        "components": [
                            {"name": "facetAddress", "type": "address"},
                            {"name": "functionSelectors", "type": "bytes4[]"}
                        ],
                        "name": "facets_",
                        "type": "tuple[]"
                    }
                ],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }
        ]

        web3 = Web3(Web3.HTTPProvider(conn_url)) 

        # Load the contract ABI

        # Create a contract instance
        contract = web3.eth.contract(address=contract_address, abi=contract_abi)

        # Call a contract function (e.g., facets())
        facets = contract.functions.facets().call()
        facet_addresses = [facet[0] for facet in facets]  # extract addresses

        return facet_addresses
    except:
        return []



# conn_url=BLOCKCHAIN_INFURA_AUTH_MAP['etherscan.io']
# contract_address= "0xC1E088fC1323b20BCBee9bd1B9fC9546db5624C5" # beanstalk diamond
# contract_address= "0xe7145d06ca5c769ff1d6db0be0bf7f53a32e10b6" #  diamonds | 0xe7145d06ca5c769ff1d6db0be0bf7f53a32e10b6 | 0x21dd761cac8461a68344f40d2f12e172a18a297f

# contract_address = Web3.to_checksum_address(contract_address)

# web3 = Web3(Web3.HTTPProvider(conn_url)) 
# function_signature = 'facets()'
# function_selector = web3.keccak(text=function_signature)[:4]

# # Prepare the call data
# call_data = function_selector.hex()

# # Make the call
# result = web3.eth.call({'to': contract_address, 'data': call_data})




# getDiamondFacetAddresses(conn_url, contract_address)








def read_csv(filepath):
    try:
        # Read the CSV file directly into a DataFrame
        df = pd.read_csv(filepath)

        # Convert the DataFrame to a list of dictionaries
        # Each dictionary represents a row, with column names as keys
        return df.to_dict(orient='records')
    except Exception as e:
        print("Error reading file", e)
        return []


output_filepath = "./contract_monitoring/live_contract_proxies.csv"
live_contracts_filepath = "./contract_monitoring/live_contacts.csv"
seen_live_contract_proxies = read_csv(output_filepath)

seen_contract_proxies_map = {}
for c in seen_live_contract_proxies:
    seen_contract_proxies_map[f"{c['chain']}-{c['address']}-{c['impl_address']}"] = True    

# load 


def processImplAddress(impl_addr, s_type):
    # skip logging zero address
    if impl_addr == "0x" or impl_addr == "0x0000000000000000000000000000000000000000000000000000000000000000":
        return

    impl_addr_id = f"{row['chain']}-{row['address']}-{impl_addr}"
    if impl_addr and not seen_contract_proxies_map.get(impl_addr_id, None):
        # add
        seen_live_contract_proxies.append({
            'date': FORMATTED_DATE,
            'project': row['project'],
            'chain': row['chain'],
            'address': row['address'],
            'type': s_type,
            'impl_address': impl_addr
        })
        seen_contract_proxies_map[impl_addr_id] = True

# Replace with your CSV file path
live_contracts = read_csv(live_contracts_filepath)
i = 0

row = [r for r in live_contracts if r['project'] == 'beanstalk' and r['address'] == '0xC1E088fC1323b20BCBee9bd1B9fC9546db5624C5'][0]

for row in live_contracts:
    # why blanks get read as floats is confusing, probably a pandas thing. Ignore them.
    try:
        impl_addr = getProxyAddress(conn_url=BLOCKCHAIN_INFURA_AUTH_MAP[row['chain']], contract_address=row['address'])
        processImplAddress(impl_addr, 'impl_proxy')

        impl_addresses = getDiamondFacetAddresses(conn_url=BLOCKCHAIN_INFURA_AUTH_MAP[row['chain']], contract_address=row['address'])
        for impl_addr in impl_addresses:
            processImplAddress(impl_addr, 'diamond_facet')
    except Exception as e:
        print("Err", e)

    i += 1
    if (i % 50 == 0):
        print(f"Completed: {i} / {len(live_contracts)}")


# output to file        
df = pd.DataFrame(seen_live_contract_proxies)
df.to_csv(output_filepath, index=False)



#     print(index, row)

# # Display the first 5 rows of the DataFrame
# print(df.head())
