import requests
import csv
import json
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import threading
import re
import time

## NOTE:
## - Does not get github repos associated with etherscan addresses

# Shared counter and lock
counter = 0
lock = threading.Lock()

# Function to process each program
def process_program(program):
    global counter
    blockchain_url_domains = ['etherscan.io', 'sepolia.etherscan.io', 'optimistic.etherscan.io', 'polygonscan.com', 'basescan.org', 'goreli.basescan.org', 'cronoscan.com', 'moonbean.moonscan.io', 'arbiscan.io', 'aurorascan.dev', 'bscscan.com', 'evm.confluxscan.io', 'ftmscan.com']
    
    try:
        while True:
            # resp = requests.get(f"https://immunefi.com/bounty/{program['id']}/", allow_redirects=True, verify=False, proxies={'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'} )
            resp = requests.get(f"https://immunefi.com/bug-bounty/{program['id']}/scope", allow_redirects=True)
            
            if resp.status_code == 200:
                break

            retry_after = resp.headers.get('Retry-After', 2)
            time.sleep(int(retry_after))


        soup = BeautifulSoup(resp.text, 'html.parser')

        # extract only content with scope block
        # start_tag = soup.find('span', text='Assets in Scope')
        scope_table_rows = []
        scope_tables = soup.find_all('tbody')
        for table in scope_tables:
            scope_table_rows += table.find_all('tr')
            

        github_repos = []
        github_urls = []
        contract_urls = []
        for row in scope_table_rows:
            text = row.find('td').text.strip()
            text = text.split("?")[0].split("#")[0]  # strip hashes + params from urls

            # clean up text in cell
            if text.endswith("Target"):
                text = text[:-6]

            # Process contract addresses
            if any([blockchain_domain in text for blockchain_domain in blockchain_url_domains]):
                contract_urls.append(text)

            # process GitHub

            if "github.com" in text and text != "github.com/immunefi-team/Web3-Security-Library":
                if text not in github_urls:
                    github_urls.append(text)

                repo_url = "/".join(text.replace("https://", '').replace("http://", "").split("/")[0:3])  
                if repo_url not in github_repos:
                    github_repos.append(repo_url)

        program['github_in_scope_urls'] = ";".join(github_urls)
        program['in_scope_repo_urls'] = ";".join(github_repos)
        program['live_contract_urls'] = ";".join(contract_urls)
    except Exception as e:
        print(f"Error processing {program['id']}: {e}")

    # Thread-safe increment of the counter and print progress
    with lock:
        counter += 1
        print(f"Completed {counter} / {len(programs)}")


    return program

# get JSON from https://immunefi.com/explore/
resp = requests.get('https://immunefi.com/explore')
soup = BeautifulSoup(resp.text, 'html.parser')

scripts = soup.find_all("script")

# last script on page contains all bounty programs
data = json.loads(scripts[-1].string)

programs = data['props']['pageProps']['bounties']

# Use ThreadPoolExecutor to run the loop in parallel
with ThreadPoolExecutor(max_workers=1) as executor:
    results = list(executor.map(process_program, programs))


with open('immunefi_data.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    
    # Check if there are any results to write
    if results:
        # Extract headers from the keys of the first result
        headers = list(results[0].keys())
        writer.writerow(headers)

        # Write each program as a row
        for program in results:
            writer.writerow([program[key] for key in headers])
    else:
        print("No results to write to CSV.")


print("Completed")
