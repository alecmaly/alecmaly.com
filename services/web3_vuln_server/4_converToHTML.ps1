

$repos = Import-Csv .\immunefi_github_repos.csv | Sort-Object lastUpdated -Descending


# Start of HTML with style
$html = @"
<style>
table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  border: 1px solid black;
  padding: 8px;
}

th {
  background-color: #f2f2f2;
}

a {
  color: blue;
}

.text-center {
    text-align: center;
}
</style>
"@


# TODO: update to extract commits




$html += @"
<table>
    <tr>
        <th>Repo Details</th>
        <th>Last Updated</th>
        <th>Default Branch & Languages</th>
        <th>Extensions Modified 3 Days</th>
        <th>Files</th>
        <th>Commit Commits</th>
    </tr>
"@

$counter = 1
foreach ($repo in $repos) {

    $details_html = "
    <div id='$counter'>
        <button style='position: absolute; top: 10' class='toggle-btn'>Show Details</button>

        #: $(($counter++))<br><br>
        id: $($repo.id)<br>
        project: $($repo.project)<br>
        Date: $($repo.date)<br>
        Max Reward: $($repo.maximum_reward)<br>
        Bounty Url: <a href='$($repo.bounty_url)'>$($repo.bounty_url)</a><br>
        <br>
        GitHub Url: <a href='https://$($repo.github_url)'>$($repo.github_url)</a><br>
        GitHub History Url: <a href='https://$($repo.github_history_url)'>$($repo.github_history_url)</a>
    </div>
    "

        
    $jsonObject = $repo.extensions_modified_3_days | ConvertFrom-Json
    $file_extensions_html = ""
    foreach ($property in $jsonObject.PSObject.Properties) {
        $file_extensions_html += "$($property.Name): $($property.Value)<br>"
    }


    $html += "<tr>"
    $html += "<td style='position: relative'>$($details_html)</td>"

    # $html += "<td>$($repo.id)</td>"
    # $html += "<td>$($repo.project)</td>"
    # $html += "<td><a href='https://$($repo.github_url)'>$($repo.github_url)</a></td>"
    # $html += "<td>$($repo.date)</td>"
    # $html += "<td>$($repo.maximum_reward)</td>"
    # $html += "<td><a href='$($repo.bounty_url)'>$($repo.bounty_url)</a></td>"
    $html += "<td style='width: 5em'>$($repo.lastUpdated)</td>"
    # $html += "<td><a href='https://$($repo.github_history_url)'>$($repo.github_history_url)</a></td>"
    $html += "<td>$($repo.default_branch)<br><br>$($repo.languages.replace("`n", '<br>'))</td>"
    $html += "<td>$($file_extensions_html )</td>"
    $html += "<td style='width: 20vw'><span class='toggleable'>$($repo.files)</a></td>"
    $html += "<td style='width: 20vw'><span class='toggleable'>$($repo.commit_messages)</span></td>"
    # $html += "<td>$($repo.silther_comments)</td>"
    $html += "</tr>"
}

$html += "</table>"



$html += @"
<script>
    document.addEventListener('DOMContentLoaded', function() {
        var rows = document.querySelectorAll('tr');
        rows.forEach(function(row) {
            row.addEventListener('click', function(evt) {
                if (evt.target.tagName === 'A') { return; }

                let eles = this.querySelectorAll('.toggleable');
                if (eles) {
                    let new_display = eles[0].style.display === 'block' ? 'none' : 'block';
                    
                    eles.forEach(ele => { ele.style.display = new_display });
                    /* this.innerText = new_display === 'block' ? 'Hide Elements' : 'Show Elements' */
                }

            });
        });
    });

    document.querySelectorAll('.toggleable').forEach(ele => { ele.style.display = 'none' })
</script>
"@

Set-Content web3repoupdates.html -Value $html
