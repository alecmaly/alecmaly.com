mkdir -p contract_monitoring

echo "Running 1_collect-scopes.py"
/usr/local/bin/python3 "1_collect-scopes.py"

#### .".\2_getGithubDates.ps1"   # may not need anymore


echo "Running 3_getGithubRepoCommitDetails.ps1"
/app/powershell/pwsh -noprofile "3_getGithubRepoCommitDetails.ps1"

echo "Running 4_converToHTML.ps1"
/app/powershell/pwsh -noprofile "4_converToHTML.ps1"

echo "Running 6_extractLiveContracts.py"
/usr/local/bin/python3 "6_extractLiveContracts.py"

echo "Running 7_lookupProxies.py"
/usr/local/bin/python3 "7_lookupProxies.py"

echo "Running 8_updateContractsList.py"
/usr/local/bin/python3 "8_updateContractsList.py"

echo "Running 9_addPatchDiffDetails.ps1"
/app/powershell/pwsh -noprofile "9_addPatchDiffDetails.ps1"

echo "Running 11_generateHTMLReview.ps1"
/app/powershell/pwsh -noprofile "11_generateHTMLReview.ps1"

cp web3contractreport.html public
cp web3repoupdates.html public
cp ./public/live_contracts.csv ./contract_monitoring/live_contracts.csv
cp ./public/live_contract_proxies.csv ./contract_monitoring/live_contract_proxies.csv