mkdir -p contract_monitoring

/usr/local/bin/python3 "1_collect-scopes.py"
#### .".\2_getGithubDates.ps1"   # may not need anymore
/app/powershell/pwsh -noprofile "3_getGithubRepoCommitDetails.ps1"
/app/powershell/pwsh -noprofile "4_converToHTML.ps1"
/usr/local/bin/python3 "6_extractLiveContracts.py"
/usr/local/bin/python3 "7_lookupProxies.py"
/usr/local/bin/python3 "8_updateContractsList.py"
# pwsh -noprofile "9_addPatchDiffDetails.ps1"

/app/powershell/pwsh -noprofile "11_generateHTMLReview.ps1"

cp web3contractreport.html public
cp web3repoupdates.html public