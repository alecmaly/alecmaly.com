# DEPENDENCIES:
    # - ConvertTo-Yaml

## get commit details
# i.e. interesting commits (commits to .sol / other interesting file extensions)



# Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/user/repos" -Credential $cred -Proxy "http://localhost:8080"

# Invoke-RestMethod -Headers @{Authorization=("Basic {0}" -f $base64AuthInfo)} -Uri "https://api.github.com/repos/$($github_project)/commits?page=1&per_page=1" -Proxy "http://localhost:8080"
        

# check rate limit
# $resp = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/rate_limit" -Proxy "http://localhost:8080"

# load .env file
Get-Content .env -ErrorAction SilentlyContinue | foreach {
    $name, $value = $_.split('=')
    if ([string]::IsNullOrWhiteSpace($name) -or $name.Contains('#')) {
        return
    }
    write-host $name $value
    $name = $name.Trim()
    $value = $value.Trim()
    Set-Content env:\$name $value
}


$output_file = 'immunefi_github_repos.csv'
Remove-Item -Force $output_file -ErrorAction SilentlyContinue
If (Test-Path $output_file) {
    $completed = (Import-Csv ".\$output_file").in_scope_repo_urls
} else {
    $completed = @()
}

$scriptblock = {
    Param (
        [PSCustomObject] $row
    )

    function ConvertTo-PercentageHTML {
        param (
            [Parameter(Mandatory=$true)]
            [PSCustomObject] $repo_languages
        )
    
        # Calculating the total count
        $totalCount = ($repo_languages.PSObject.Properties).Value | Measure-Object -Sum | Select-Object -ExpandProperty Sum
    
        # Creating an array to hold objects with language and percentage
        $percentageArray = @()
    
        # Calculating percentage for each language
        foreach ($property in $repo_languages.PSObject.Properties) {
            $percentage = ($property.Value / $totalCount) * 100
            $percentageObject = New-Object PSObject -Property @{
                Language = $property.Name
                Percentage = [math]::Round($percentage, 2)
            }
    
            $percentageArray += $percentageObject
        }
    
        $languages_sorted = $percentageArray | Sort-Object -Property Percentage -Descending

        $output_arr = $languages_sorted |% { return " $($_.Percentage) - $($_.Language)" }

        # Sort the array by percentage in descending order and return
        return $output_arr -join "<br>"
    }

    $COMMIT_THRESHOLD_DAYS = 3
    $exclude_paths = @(
        'test', 'mock'
        'dev/',  'interfaces/', 'lib/', 'libraries/', 'cache/', 'script/', 'scripts/', 'misc/', 'deployments/', 'artifacts/', 
        '.t.sol', '.s.sol',
        '.pdf', '.md', '.lock', '.png', '.svg'
        # '.pdf', '.md', '.lock', '.png', '.ts', '.js', '.tsx', '.json', '.sql', '.svg'
        )

    function Invoke-GitHubAPIGETRequest($headers, $uri) {
        # $uri = "https://api.github.com/repos//commits?page=1"
        # $uri = "https://api.github.com/repos/crytic/slither/commits?page=1"
        do {
            $err = $null
            try {
                $resp = Invoke-RestMethod -Headers $headers -Uri $uri -PreserveAuthorizationOnRedirect # -Proxy http://localhost:8080
            } catch {
                # Dig into the exception to get the Response details.
                # Note that value__ is not a typo.
                $err = $_
                Write-Host "StatusCode:" $_.Exception.Response.StatusCode.value__
                Write-Host "StatusDescription:" $_.Exception.Response.StatusDescription
                If ($_.Exception.Response.StatusCode.value__ -eq 403) {
                    Start-Sleep 5
                }
            }
        } while ($err.Exception.Response.StatusCode.value__ -eq 403)
        
        return $resp
    }

    function Get-ReadmeSlitherText($github_project) {
        $resp = Invoke-RestMethod -Method Get "https://raw.githubusercontent.com/$($github_project)/master/README.md" # -Proxy http://localhost:8080
        $slither_comments = ($resp | Select-String -Pattern ".*slither.*" -CaseSensitive:$false -All).matches.Value -join "`n" 
        return $slither_comments
    }


    # Authentication - for GitHub Rate Limiting
    $clientid = $env:GITHUB_CLIENTID
    $secret = $env:GITHUB_SECRET
    $base64AuthInfo = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(("{0}:{1}" -f $clientid,$secret)))
    $headers = @{Authorization=("Basic {0}" -f $base64AuthInfo)}


    $github_urls = $row.in_scope_repo_urls -split ';'

    $output = @()
    foreach ($github_url in $github_urls) {
        If ($github_url -in $completed) {
            write-host "[!] Skipping: $github_url"
            continue
        }
        
        $github_project = $github_url.replace('github.com/', '')
        if (!$github_project -or $github_project.split('/').length -ne 2) {
            continue
        }

        $repo_base = $null
        $repo_base = Invoke-GitHubAPIGETRequest -Headers $headers -Uri "https://api.github.com/repos/$($github_project)"  # -PreserveAuthorizationOnRedirect #  -Proxy "http://localhost:8080"
        # Extract the repository links from the matches

        $repo_languages = $null
        $repo_languages = Invoke-GitHubAPIGETRequest -Headers $headers -Uri "https://api.github.com/repos/$($github_project)/languages" # -PreserveAuthorizationOnRedirect #  -Proxy "http://localhost:8080"
        # Extract the repository links from the matches


        $resp = $null
        $commits = Invoke-GitHubAPIGETRequest -Headers $headers -Uri "https://api.github.com/repos/$($github_project)/commits?page=1" # -PreserveAuthorizationOnRedirect #  -Proxy "http://localhost:8080"
        # Extract the repository links from the matches

        # get last updated date
        try {
            $lastUpdated = $null
            # $lastUpdated = Get-Date $matches.Matches[0].Value.Split(">")[1].Split("<")[0] -f "yyyy-MM-dd"
            $lastUpdated = get-date $commits[0].commit.committer.date -f "yyyy-MM-dd"
        } catch {
            Write-Warning -Message "[!] Failed on $($github_url)"
            continue
        }

        $extensions = @{}
        $filepaths = @{}
        $commits_details = @()
        # get file types modified
        foreach ($commit in $commits) {
            $date = [DateTime]::Parse($commit.commit.committer.date)
        
            if ($date -ge (Get-Date).AddDays(-$COMMIT_THRESHOLD_DAYS)) {
                Write-Host "The date ($date) is within the last $COMMIT_THRESHOLD_DAYS days."
                
                # get commit details + add extensions
                $commit_resp = Invoke-GitHubAPIGETRequest -Headers $headers -Uri $commit.url

                $commits_details += "
                    <a target='_target' href='$($commit.html_url)'>$($commit.sha)</a>
                    
                    $($commit.commit.message)
                "




                foreach ($file in $commit_resp.files) {
                    $filepath = $file.filename
                    if ($filepath.indexOf('.') -eq -1) {
                        continue
                    }
                    
                    $ext = $filepath.split('.') | select -last 1

                    $match_found = $false
                    foreach ($exclude_path in $exclude_paths) {
                        if ($filepath -like "*$exclude_path*") { $match_found = $true; break }
                    }

                    If (!$match_found) {
                        $extensions[$ext] = if($extensions[$ext]) { $extensions[$ext] + 1 } else { 1  }
                        # $filepaths[$filepath] = $true
                        # TODO: add additionals and deletions
                        
                        if(!$filepaths[$filepath]) {
                            $filepaths[$filepath] = @{'add'= 0; 'del' = 0; 'commits' = @()}
                        }

                        $filepaths[$filepath].add += $file.additions
                        $filepaths[$filepath].del += $file.deletions
                        $commit_str = "$($commit.html_url)~$(get-date $date -f 'yyyy-MM-dd')"
                        if (!$filepaths[$filepath].commits.Contains($commit_str)) {
                            $filepaths[$filepath].commits += $commit_str
                        }
                    }
                }
            } else {
                Write-Host "The date ($date) is not within the last $COMMIT_THRESHOLD_DAYS days."
            }
        }

        

        $file_detail_output = @()
        $PADDING = 4
        foreach ($filename in ($filepaths.GetEnumerator().Name | sort)) {

            $file_commit_html = @()
            foreach ($commit in $filepaths[$filename].commits) {
                $c_url = $commit.split("~")[0]
                $c_date = $commit.split("~")[1]

                $commit_hash = $($c_url.split("/") | select -last 1)
                $file_commit_html += "($($commit_hash.substring(0, 4)))<a target='_blank' href='$($c_url)?scroll_to=$filename'>$c_date</a>"
            }

            $str = "+ $($filepaths[$filename].add.toString().padLeft($PADDING, ' ')) | - $($filepaths[$filename].del.toString().padLeft($PADDING, ' ')) | $($filename) | $($file_commit_html -join ', ')"
            $file_detail_output += $str
        }

        

        # $file_commits_output = @()
        # foreach ($commit in $filepaths[$filename].commits) {
        #     $c_url = $commit.split("~")[0]
        #     $c_date = $commit.split("~")[1]
            
        #     $commit_hash = $($c_url.split('/') | select -Last 1)
        #     $file_commits_output += "COMMIT: <a target='_blank' href='$($c_url)'>$($c_date)</a>"
        # }

        

        $obj = [PSCustomObject] @{
            id = $row.id
            project = $row.project
            date = $row.date
            maximum_reward = $row.maximum_reward
            bounty_url = "https://immunefi.com/bounty/$($row.id)"
            lastUpdated = $lastUpdated
            github_history_url = $github_url + '/commits'
            default_branch = $repo_base.default_branch
            "extensions_modified_$($COMMIT_THRESHOLD_DAYS)_days" = $extensions | ConvertTo-Json -Compress
            files = if ($filepaths.Count -ne 0) {  "<pre>" + ($file_detail_output -join "<br>")  + "</pre>" } else { "" }
            silther_comments = (Get-ReadmeSlitherText -github_project $github_project) -join "`n"
            github_url = $github_url
            commit_messages = "<pre>" + ($commits_details -join "<br>") + "</pre>"
            languages = (ConvertTo-PercentageHTML -repo_languages $repo_languages)
        }

        # $obj | Export-Csv $output_file -NoTypeInformation -Append
        $output += $obj
    }
    return $output
}


# $data = Import-Csv .\immunifi_github.csv
$data = Import-Csv immunefi_data.csv

$jobs = @()
# $data = $data | select -first 3 | select -last 2
foreach ($row in $data) {
    $jobs += Start-ThreadJob -ScriptBlock $scriptblock -ArgumentList $row -ThrottleLimit 40
}


do {
    $running_jobs = $jobs | where State -ne Completed
    If ($running_jobs) {
        Write-Host "[+] $($running_jobs.Count) running jobs"
        Start-Sleep -Seconds 5
    }
} while ($running_jobs)


$output = $jobs | Receive-Job
$output | Export-Csv $output_file -NoTypeInformation










## TESTSING

# $row = $data | where github_in_scope_urls -like "*github.com/smartcontractkit/chainlink*"
# $github_url = "github.com/smartcontractkit/chainlink"