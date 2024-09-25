$contracts = import-csv .\contract_monitoring\live_contracts.csv
$proxies = import-csv .\contract_monitoring\live_contract_proxies.csv
$repos = import-csv .\immunefi_github_repos.csv


$recent_contracts = $contracts | where-object { (get-date $_.date) -ge (get-date (get-date).adddays(-1)) }
$recent_proxies = $proxies | where-object { (get-date $_.date) -ge (get-date (get-date).adddays(-1)) }
$recent_repos = $repos | where-object { (get-date $_.lastUpdated) -ge (get-date (get-date).adddays(-1)) }

write-host "`nRecent Repos:"
$recent_repos | ft

write-host "`nRecent Contracts:"
$recent_contracts | ft

write-host "`nRecent Proxies:"
$recent_proxies | ft


