$contracts_filepath = "./contract_monitoring/live_contracts.csv"
$proxies_filepath = "./contract_monitoring/live_contract_proxies.csv"

$contracts = import-csv $contracts_filepath
$proxies = import-csv $proxies_filepath

Write-Host "[+] Evaluating diffs for $($contracts.Count) contracts and $($proxies.Count) proxies."
## Contracts

$contract_updates_map = @{}
foreach ($line in $contracts) {
    $key = "$($line.chain)-$($line.ContractName)-$($line.address)"
    If (!$contract_updates_map[$key]) {
        $contract_updates_map[$key] = @()
    }
    $contract_updates_map[$key] += $line.PSObject.Copy() | select -ExcludeProperty patches
}


foreach ($line in $contracts) {
    $key = "$($line.chain)-$($line.ContractName)-$($line.address)"
    $previous_versions = $contract_updates_map[$key] | where { ($_ | convertto-json) -ne ($line | convertto-json) -and (get-date $_.date) -lt (get-date $line.date) }
    If ($line.PSObject.Properties.Name.contains("patches")) {
        $line.patches = $previous_versions | ConvertTo-Json -Depth 1 -AsArray
    } else {
        $line | Add-Member NoteProperty -Name "patches" -Value $previous_versions -ErrorAction SilentlyContinue # don't need to do again in future as we already have the patches for previous verions
    }

    If ($line.PSObject.Properties.Name.contains("prevVersions")) {
        $line.prevVersions = ([Array]$previous_versions).Count
    } else {
        $line | Add-Member NoteProperty -Name "prevVersions" -Value $previous_versions -ErrorAction SilentlyContinue # don't need to do again in future as we already have the patches for previous verions
    }
}



## Proxies

$proxy_updates_map = @{}
foreach ($line in $proxies) {
    $key = "$($line.chain)-$($line.address)-$($line.ProxyContractName)"
    If (!$proxy_updates_map[$key]) {
        $proxy_updates_map[$key] = @()
    }
    $proxy_updates_map[$key] += $line.PSObject.Copy() | select -ExcludeProperty patches
}


foreach ($line in $proxies) {
    $key = "$($line.chain)-$($line.address)-$($line.ProxyContractName)"
    $previous_versions = $proxy_updates_map[$key] | where { ($_ | convertto-json) -ne ($line | convertto-json) -and (get-date $_.date) -lt (get-date $line.date) } 
    If ($line.PSObject.Properties.Name.contains("patches")) {
        $line.patches = $previous_versions | ConvertTo-Json -Depth 1 -AsArray
    } else {
        $line | Add-Member NoteProperty -Name "patches" -Value $previous_versions -ErrorAction SilentlyContinue # don't need to do again in future as we already have the patches for previous verions
    }

    If ($line.PSObject.Properties.Name.contains("prevVersions")) {
        $line.prevVersions = ([Array]$previous_versions).Count
    } else {
        $line | Add-Member NoteProperty -Name "prevVersions" -Value $previous_versions -ErrorAction SilentlyContinue # don't need to do again in future as we already have the patches for previous verions
    }
}


# $proxy_updates_map["etherscan.io-0x229047fed2591dbec1eF1118d64F7aF3dB9EB290"] | ft
# $proxy_updates_map["etherscan.io-0x00d950A41a0d277ed91bF9fD366a5523FEF0371e"] | ft


# $proxy_updates_map["etherscan.io-0xC1E088fC1323b20BCBee9bd1B9fC9546db5624C5"] | ft


$contracts | Export-Csv $contracts_filepath -NoTypeInformation
$proxies | Export-Csv $proxies_filepath -NoTypeInformation