function converToBase64($string) {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($string)
    $encoded = [System.Convert]::ToBase64String($bytes)
    return $encoded
}

# Define file paths
$liveContactsPath = "./contract_monitoring/live_contracts.csv"
$liveContactProxiesPath = "./contract_monitoring/live_contract_proxies.csv"

$programs = Import-Csv "./immunefi_data.csv"
$programs_map = @{}
foreach ($program in $programs) {
    $programs_map[$program.id] = $program.maximum_reward
}

# Read CSV files and filter by date
$DAYS = 5
$liveContacts = Import-Csv -Path $liveContactsPath | Where-Object { (Get-Date $_.date) -ge (Get-Date).AddDays(-$DAYS) }
$liveContactProxies = Import-Csv -Path $liveContactProxiesPath | Where-Object { (Get-Date $_.date) -ge (Get-Date).AddDays(-$DAYS) }

# Define a function to convert a CSV to an HTML table with checkboxes
function ConvertTo-HtmlTableWithCheckboxes {
    param($csvData, $classCheckbox)
    if (!$csvData) {
        return ""
    }

    $columns = $csvData | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name |? { $_ -notin @("patches", "prevVersionCount") }
    $table = "<table>`n<thead><tr><th>Select</th>"
    foreach ($column in $columns) {
        $table += "<th>$column</th>"
    }
    $table += "<th>max bounty</th>"
    $table += "<th>prevVersionCount</th>"
    $table += "</tr></thead>`n<tbody>"

    foreach ($row in $csvData) {
        $table += "<tr data-patches='$(converToBase64 -string $row.patches)'><td><input type='checkbox' class='$classCheckbox' onchange='generateScript()'></td>"
        foreach ($column in $columns) {
            $table += "<td>$($row.$column)</td>"
        }
        $table += "<td><a target='_blank' href='https://immunefi.com/bounty/$($row.project)/'>$('{0:N0}' -f [int]$programs_map[$row.project])</a></td>" # max bounty
        $dates = $row.patches.date -join ', '
        $table += "<td>$($row.prevVersionCount) - $(($row.patches | convertfrom-json).date -join ', ')</td>" # prevVersionCount
        $table += "</tr>`n"
    }
    $table += "</tbody></table>"
    return $table
}

# Convert CSV files to HTML tables with checkboxes
$liveContactsTable = ConvertTo-HtmlTableWithCheckboxes $liveContacts "contactRow"
$liveContactProxiesTable = ConvertTo-HtmlTableWithCheckboxes $liveContactProxies "proxyRow"

# Define the CSS for the HTML file
$css = @"
<style>
body {
    font-family: Arial, sans-serif;
}
table {
    border-collapse: collapse;
    width: 100%;
}
th, td {
    border: 1px solid black;
    padding: 8px;
    text-align: left;
}
th {
    background-color: #f2f2f2;
}
textarea {
    width: 100%;
    height: 400px;
}
</style>
"@

# Define the HTML structure and include JavaScript for interactivity
$htmlContent = @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSV Tables</title>
    $css
</head>
<body>
    <h2>Live Contracts</h2>
    <select id="liveContractsSelection" onchange="generateScript()">
        <option value="address">Address</option>
        <option value="implementation">Implementation</option>
    </select>
    $liveContactsTable
    <h2>Proxies</h2>
    <select id="proxiesSelection" onchange="generateScript()">
        <option value="address">Address</option>
        <option value="impl_address" selected="selected">Implementation Address</option>
    </select>
    $liveContactProxiesTable
    <h2>Generated Shell Script</h2>
    <input type='text' id='output_dir' value='source_code' onkeyup="generateScript()" />
    <textarea id="shellScript" readonly></textarea>

    <script>

    function generateScript() {
        var scriptLines = [];
        var selectedContractsDetail = [];
        var selectedProxiesDetail = [];
        var chain = ""; // last selected chain
        var version = "";   // last selected version
        var liveContractsSelection = document.getElementById('liveContractsSelection').value;
        var proxiesSelection = document.getElementById('proxiesSelection').value;
        var output_dir = document.querySelector('#output_dir').value
        var output_dir_param = output_dir ? ``-f `${output_dir}`` : ""

        var complexScriptPrefix = ``
cp ~/Desktop/slither-custom-tooling/tools/solidity/_downloadLiveContracts.py .
``

var complexScriptTemplatePostfix = ``
cd `${output_dir}
cpslither
init_web3_fuzz
code .
        ``
        // contracts
        document.querySelectorAll('.contactRow:checked').forEach(function(cb) {
            var row = cb.closest('tr');
            let patches = row.getAttribute('data-patches') ? JSON.parse(atob(row.getAttribute('data-patches'))) : []
            
            chain = row.cells[2].textContent
            version = row.cells[3].textContent
            let date = row.cells[5].textContent

            var columnIndex = liveContractsSelection === 'address' ? 1 : 6; // Adjust index based on selection and CSV structure
            var domain = row.cells[2].textContent;
            var value = row.cells[columnIndex].textContent;
            scriptLines.push(``python3 _downloadLiveContracts.py `${domain} `${value} `${output_dir_param}``);
            
            let contractName = row.cells[4].textContent
            let address = row.cells[1].textContent
            selectedContractsDetail.push(```${contractName} = `${address} # `${contractName} `${date}``)
            for (let patch of patches) {
                selectedContractsDetail.push(```tpython3 _downloadLiveContracts.py `${patch.chain} `${patch.address} -f diff_`${patch.ContractName}_`${patch.date.replaceAll("/", "_")}``);
                selectedContractsDetail.push(```tmeld `${output_dir} diff_`${patch.ContractName}_`${patch.date.replaceAll("/", "_")}``);
                selectedContractsDetail.push("")
            }
        });

        // proxies
        document.querySelectorAll('.proxyRow:checked').forEach(function(cb) {
            var row = cb.closest('tr');
            let patches = row.getAttribute('data-patches') ? JSON.parse(atob(row.getAttribute('data-patches'))) : []

            chain = row.cells[2].textContent
            version = row.cells[6].textContent
            let date = row.cells[3].textContent

            var columnIndex = proxiesSelection === 'address' ? 1 : 4; // Adjust index based on selection and CSV structure
            var domain = row.cells[2].textContent;
            var value = row.cells[columnIndex].textContent;
            scriptLines.push(``python3 _downloadLiveContracts.py `${domain} `${value} `${output_dir_param}``);

            let contractName = row.cells[7].textContent
            let address = row.cells[4].textContent
            let proxy_addr = row.cells[1].textContent

            selectedProxiesDetail.push(```${contractName} = `${address} (proxy: `${proxy_addr}) # `${contractName} `${date}``)
            for (let patch of patches) {
                selectedProxiesDetail.push(```tpython3 _downloadLiveContracts.py `${patch.chain} `${patch.impl_address} -f diff_`${patch.ProxyContractName}_`${patch.date.replaceAll("/", "_")}``);
                selectedProxiesDetail.push(```tmeld `${output_dir} diff_`${patch.ProxyContractName}_`${patch.date.replaceAll("/", "_")}``);
                selectedProxiesDetail.push("")
            }

        });
        version = version.split('+')[0].replace('v', '')

        var complexScript = complexScriptPrefix 
            + ``\nsolc-select install `${version}\n`` 
            + ``solc-select use `${version}\n\n`` 
            + scriptLines.join('\n')
            + complexScriptTemplatePostfix
            + ``\ncat << EOF > _contract_info.txt\n`${chain}\n\n`` + selectedContractsDetail.join('\n') + selectedProxiesDetail.join('\n') + '\nEOF\n'

        document.getElementById('shellScript').value = complexScript;
    }
    </script>
</body>
</html>
"@

# Save the HTML content to a file
$htmlContent | Out-File -FilePath "web3contractreport.html" -Encoding UTF8

# Output the path to the HTML file
Write-Host "HTML file generated at web3contractreport.html"
