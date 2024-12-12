import requests
import json
import re
import csv
from concurrent.futures import ThreadPoolExecutor

# # Get NEXT_DATA in JSON format
NEXT_DATA_BOUNTIES = json.loads(re.search(r'<script id="__NEXT_DATA__" type="application/json".*>(.*)</script>', requests.get("https://immunefi.com/bug-bounty/").text).group(1))
NEXT_DATA_BOOSTS = json.loads(re.search(r'<script id="__NEXT_DATA__" type="application/json".*>(.*)</script>', requests.get("https://immunefi.com/boost/").text).group(1))


# # Get bounties in a variable
projects = NEXT_DATA_BOUNTIES['props']['pageProps']['bounties']
# # Get boosts in a variable
boosts = NEXT_DATA_BOOSTS['props']['pageProps']['bounties']

# # Let's see if new projects were added or paused
# cat ./projects.json | jq -r '.[].project' | sort >prev_projects_name.txt
# live_contracts = open('./contract_monitoringlive_contracts.csv', 'r').readlines()

# echo "$projects" | jq -r '.[].project' | sort >current_projects_name.txt

# # Let's see if new boosts were added or removed
# cat ./boosts.json | jq -r '.[].project' | sort >prev_boosts_name.txt
# echo "$boosts" | jq -r '.[].project' | sort >current_boosts_name.txt


# # Paused or Removed
# paused_programs=$(comm -23 ./prev_projects_name.txt ./current_projects_name.txt | sed 's/^/#/' | sed -r 's/\s+//g' | xargs)
# # Added or Unpaused
# added_programs=$(comm -13 ./prev_projects_name.txt ./current_projects_name.txt | sed 's/^/#/' | sed -r 's/\s+//g' | xargs)

# # Paused or Removed
# paused_boosts=$(comm -23 ./prev_boosts_name.txt ./current_boosts_name.txt | sed 's/^/#/' | sed -r 's/\s+//g' | xargs)
# # Added or Unpaused
# added_boosts=$(comm -13 ./prev_boosts_name.txt ./current_boosts_name.txt | sed 's/^/#/' | sed -r 's/\s+//g' | xargs)

# # Clean temporal files
# rm ./prev_projects_name.txt
# rm ./current_projects_name.txt

# # Clean temporal files
# rm ./prev_boosts_name.txt
# rm ./current_boosts_name.txt

# # Save current bounties
# echo "$boosts" >boosts.json

# # Save current bounties
# echo "$projects" >projects.json

# # Get buildId
# buildId=$(echo "$NEXT_DATA_BOUNTIES" | jq -r '.buildId')

# # Get how many bounties are
# bounties_length=$(echo "$projects" | jq length)


def process_project(project):
    blockchain_url_domains = ['etherscan.io', 'sepolia.etherscan.io', 'optimistic.etherscan.io', 'polygonscan.com', 'basescan.org', 'goreli.basescan.org', 'cronoscan.com', 'moonbean.moonscan.io', 'arbiscan.io', 'aurorascan.dev', 'bscscan.com', 'evm.confluxscan.io', 'ftmscan.com']
    
    project_id = project['id']
    project_data = requests.get(f"https://immunefi.com/_next/data/{NEXT_DATA_BOUNTIES['buildId']}/bug-bounty/{project_id}/scope.json").json()
    scope_data = project_data.pop('pageProps')
    
    rewards = ""
    for row in scope_data['bounty']['rewards']:
        max_amount = row.get('maxReward', row.get('fixedReward', None))
        if not max_amount:
            all_amounts = re.findall(r'[0-9,]+', row['payout'])
            max_amount = max(all_amounts, key=lambda x: int(x.replace(',', '')))
        data = f"{row.get('level', row.get('severity', ''))} - {max_amount}\n"
        if data not in rewards:
            rewards += data

    github_repos = []
    github_urls = []
    contract_urls = []
    for asset in scope_data['bounty']['assets']:
        url = asset['url']
        url = url.split("?")[0].split("#")[0]  # strip hashes + params from urls
        # Process contract addresses
        if any([blockchain_domain in url for blockchain_domain in blockchain_url_domains]):
            contract_urls.append(f"{asset['addedAt']}~{url}")
        # process GitHub
        if "github.com" in url and 'github.com/immunefi-team/Web3-Security-Library' not in url:
            if url not in github_urls:
                github_urls.append(url)
            repo_url = "/".join(url.replace("https://", '').replace("http://", "").split("/")[0:3])  
            if repo_url not in github_repos:
                github_repos.append(repo_url)
    
    project['github_in_scope_urls'] = ";".join(github_urls)
    project['in_scope_repo_urls'] = ";".join(github_repos)
    project['live_contract_urls'] = ";".join(contract_urls)
    project['rewards'] = rewards.strip()
    
    return project

# Set the number of worker threads
max_workers = 10  # Adjust this number based on your system's capabilities

# Process projects in parallel
total_projects = len(projects)
print(f"Starting to process {total_projects} projects...")

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    results = list(executor.map(process_project, projects))

print("All projects processed")


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



# Here you can add code to save the data to a file or process it further
# For example:
# with open('immunefi_data.csv', 'w', newline='', encoding='utf-8') as file:
#     writer = csv.writer(file)
#     
#     if results:
#         headers = list(results[0].keys())
#         writer.writerow(headers)
#
#         for program in results:
#             writer.writerow([program[key] for key in headers])
#     else:
#         print("No results to write to CSV.")

# ... rest of your code ...