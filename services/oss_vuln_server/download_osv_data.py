#!/usr/local/bin/python

# public database: https://osv.dev/list


# docs : https://google.github.io/osv.dev/data/#data-dumps



# pip install cvss
from cvss import CVSS2, CVSS3, CVSS4

import argparse
import requests
import zipfile
import json
import datetime
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

global all_references
all_references = set()

def download_ecosystem(ecosystem):
    filename = ecosystem + ".zip"
    print("[+] Downloading the zip file for " + ecosystem + " ...")
    url = "https://storage.googleapis.com/osv-vulnerabilities/" + ecosystem + "/all.zip"
    response = requests.get(url)

    # mkdir if does not exist
    if not os.path.exists('data'):
        os.makedirs('data')

    with open(os.path.join('data', filename), 'wb') as file:
        file.write(response.content)


CURRENT_YEAR = datetime.datetime.now().year
TIME_THRESHOLD_YEARS = 99  # only keep vulnerabilities published in the last 3 years


def is_good_link(url):
    # has a link that does not match any in links_to_exclude
    
    # has_good_ref = any([url for url in ref_urls_lowercase if 
    #                     ("github.com" in url and "#l" in url) or
    #                     "hackerone.com" in url or
    #                     "huntr.dev" in url or
    #                     "huntr.com" in url or
    #                     "notion.site" in url or
    #                     "medium.com" in url or
    #                     "report" in url or
    #                     "writeup" in url or 
    #                     ("nodejs.org" not in url and "blog" in url) or
    #                     ".pdf" in url or
    #                     ".md" in url or

    #                     # "/commit/" in url or
    #                     ("github.com" and "/security/advisories/" in url) or
    #                     ("github.com" and "/issues/" in url)
    #                 ])
    
    
    links_to_exclude = [
        "mattermost.com",
        "nodejs.org",
        "npmjs.com",
        "nvd.nist.gov",
        "wpscan.com",
        "github.com",
        "grafana.com",
        "bugzilla.redhat.com",
        "apache.org",
        "debian.org",
        "openwall.com",
        "thewatch.centreon.com",
        "openstack.org"
        "cve.org",
        "crates.io",
        "pkg.go.dev",
        "ycombinator.com",
        "typo3.org"
        # github regex, github without /issues/ or /security/advisories/
        
    ]
    url = url.lower()
    is_good_ref = not any(exclude in url for exclude in links_to_exclude)

    if not is_good_ref:
        # github exceptions that are good refs
        is_good_ref = (
            ("github.com" in url and "#" in url) or 
            ("github.com" in url and "/security/advisories/" in url) or
            ("github.com" in url and "/issues/" in url) or
            ("github.com" in url and "/commit/" in url) # maybe remove?
        )
    return is_good_ref



# Function to process each ecosystem
def process_ecosystem(args, ecosystem):
    global total
    global unique_langs
    global all_references
    output = []
    zip_filepath = os.path.join('data', ecosystem + '.zip')

    # if created time is not today
    now = datetime.datetime.now().timestamp()
    
    if args.force_download or not os.path.exists(zip_filepath) or os.path.getmtime(zip_filepath) < now - 86400:  # 24 hours
        download_ecosystem(ecosystem)
    else:
        print(f"Skipping download for {ecosystem} as it was downloaded today")

    print(f"[+] Extracting the zip file for {ecosystem} ...")
    
    try:
        # Extract the zip file
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            num_files = len(zip_ref.namelist())
            # Evaluate each file in zip before extracting
            for file in zip_ref.namelist():
                total += 1
                # Get content
                content = zip_ref.read(file, pwd=None)

                data = json.loads(content)

                if 'references' in data:
                    refs = [ref for ref in data['references'] if ref['type'] not in ['ADVISORY', 'FIX'] and 'url' in ref]
                    all_references.update([ref['url'] for ref in refs])

                    # Time since published
                    years_since_published = 99
                    if 'published' in data:
                        years_since_published = CURRENT_YEAR - int(data['published'].split('-')[0])

                    if len(refs) > 0 and years_since_published <= TIME_THRESHOLD_YEARS:
                        severity = 0
                        if 'severity' in data:
                            t = data['severity'][0]['type']
                            if t == 'CVSS_V3':
                                c = CVSS3(data['severity'][0]['score'])
                                severity = c.scores()[0]
                            elif t == 'CVSS_V4':
                                c = CVSS4(data['severity'][0]['score'])
                                severity = c.base_score
                            else:
                                raise Exception("CVSS version not supported")
                        
                        has_good_ref = any(r for r in refs if is_good_link(r['url']))
                        if not has_good_ref:
                            continue
                        
                        bad_ref_urls = [r['url'] for r in refs if not is_good_link(r['url'])]
                        
                        
                        langs = ""
                        refs_w_line_num = [r for r in refs if "github" in r['url'] and "#L" in r['url']]
                        if len(refs_w_line_num) > 0:
                            # All file extensions from lines w/ line number + dedupe languages
                            langs = list(set([ref['url'].split('#')[0].split("?")[0].split("/")[-1].split('.')[-1][:5] for ref in refs_w_line_num]))
                            langs = [l for l in langs if l != "md"]  # Remove markdown files
                            for l in langs:
                                if l not in unique_langs:
                                    unique_langs.append(l)

                        o = {
                            'ecosystem': ecosystem,
                            'id': data['id'],
                            'langs': langs,
                            'summary': data.get('summary', ""),
                            'details': data['details'],
                            'published': data['published'],
                            'has_good_ref': has_good_ref,
                            'references': refs,
                            'bad_ref_urls': bad_ref_urls,
                            'severity': severity,
                            'data': data
                        }
                        output.append(o)
        print(f"[+] Done w/ ecosystem: {ecosystem}")
    except zipfile.BadZipFile:
        print(f"Error: Bad zip file for {ecosystem}")
    return output





# Main parallel execution
def main():

    parser = argparse.ArgumentParser(description='Download and process OSV data')
    parser.add_argument('--force-download', action='store_true', help='Force download of zip files')

    args = parser.parse_args()

    global total
    global unique_langs
    total = 0
    unique_langs = []

    ecosystems_complete = 0
    output = []
    # 'creates.io'
    ecosystems = ['GIT', 'OSS-Fuzz', 'npm', 'PyPI', 'NuGet', 'JavaScript', 'Linux', 'Go', 'GitHub Actions', 'GSD', 'Hex', 'Maven', 'DWF', 'Chainguard', 'CRAN', 'Bitnami', 'UVI', 'Wolfi', 'RubyGems', 'SwiftURL', 'Pub', 'Packagist']


    with ThreadPoolExecutor(max_workers=6) as executor:  # Adjust max_workers as needed
        future_to_ecosystem = {executor.submit(process_ecosystem, args, ecosystem): ecosystem for ecosystem in ecosystems}
        
        for future in as_completed(future_to_ecosystem):
            ecosystem = future_to_ecosystem[future]
            try:
                result = future.result()
                output.extend(result)
                ecosystems_complete += 1
                print(f"[+] Ecosystems complete: {ecosystems_complete}/{len(ecosystems)}")
            except Exception as exc:
                print(f"Error processing {ecosystem}: {exc}")

    print(f"Total files processed: {total}")

    # Use the output after processing
    # Example: Save output to a file, analyze results, etc.
    print(f"Processed data count: {len(output)}")
    # Example of using the output:
        
        
    # sort by sevierity
    output = sorted(output, key=lambda x: x['severity'], reverse=True)


    html = """
    <html>
        <head>
            <title>Open Source Vulnerabilities</title>

            <meta property="og:title" content="open source vulnerabilities" />
            <meta property="og:type" content="website" />
            <meta property="og:url" content="https://oss-vulns.alecmaly.com" />
            <meta property="og:image" content="https://alecmaly.com/assets/images/tech-thumbnail.jpg" />
            <meta property="og:description" content="Filtered list of //osv.dev for enhanced searching" />
            
            <script src="mark.min.js"></script>

            <link rel="stylesheet" type="text/css" href="purecss.min.css">
            <link rel="stylesheet" type="text/css" href="styles.css">

            
            <!-- Favicon - dynamically look at parent domain -->
            <script type="text/javascript">
                // Get the current hostname
                var hostname = window.location.hostname;

                // Check if it's a subdomain
                var parts = hostname.split('.');
                while (parts.length > 2) {
                    // Strip off the subdomain to get the main domain
                    parts.shift(); // Removes the subdomain part
                }
                var mainDomain = parts.join('.');

                // Create a link element for the favicon
                var link = document.createElement('link');
                link.rel = 'icon';
                link.href = 'https://' + mainDomain + '/favicon.ico';
                link.type = 'image/x-icon';

                // Append the favicon link to the head of the document
                document.head.appendChild(link);
            </script>
        </head>
    <body>
    
    <button id="top-btn" class='pure-button' onclick="topFunction()">Top</button>
    """

    # # add sticky search bar that hides rows that don't match the search
    html += """
    <div class="pure-form pure-g" style="position: sticky; top: 0; background-color: #fff; padding: 10px; z-index: 1000; border-bottom: 1px solid #ddd;">
        <select class="pure-u-1-4 pure-u-sm-1-5" id="common-search" onchange="searchCommon()"></select>
        <input class="pure-u-3-4 pure-u-sm-1-5" type="text" id="search" onkeyup="debounceBuildTable()" placeholder="Search regex..">
        <select class="pure-u-1-4 pure-u-sm-1-7" id="ecosystem" onchange="debounceBuildTable()"></select>
        <select class="pure-u-1-4 pure-u-sm-1-7" id="lang" onchange="debounceBuildTable()"></select>
        <input class="pure-u-1-6 pure-u-sm-1-10" type="number" id="cvss-min" min="0" max="10" step="0.5" placeholder="CVSS min" onkeyup="debounceBuildTable()">
        <input class="pure-u-1-6 pure-u-sm-1-10" type="number" id="cvss-max" min="0" max="10" step="0.5" placeholder="CVSS max" onkeyup="debounceBuildTable()">
        <button class="button-secondary pure-u-1-6 pure-u-sm-1-10" id="reset-btn" onclick="resetFilters()">Reset Filters</button>
    </div>
    
    <div class='container'>
        <h1>Data from: <a href='https://osv.dev/list' target='_blank'>https://osv.dev/list</a></h1>
        <p>web3 reports can be found at <a href='https://solodit.xyz'>solodit.xyz</a> and <a href='https://code4rena.com/reports'>code4rena.com/reports</a></p>
        <p>
            Note: This list to filter for only vulns that have a github link to source code (//github.com/path/to/file#L<line_num>) or potential writeup.<br>
        </p>            
    </div>
    """

    def sanitize_xss(s):
        return s.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;").replace('"', "&quot;").replace("'", "&#x27;").replace("/", "&#x2F;")

    output = sorted(output, key=lambda x: x['published'], reverse=True)

    html_output = []
    for row in output:

        refs_html = "<ul>"
        for ref in row['references']:
            ref_html = f"<li>- <a target='_blank' href='{ref['url']}'>{ref['url']}</a></li>"
            if ref['url'] in row['bad_ref_urls']:
                ref_html = f"<s style='color:red'>{ref_html}</s>"
            refs_html += ref_html
        refs_html += "</ul>"

        obj = {
            'ecosystem': sanitize_xss(row['ecosystem']),
            'id': row['id'],
            'details': (f"<b>{sanitize_xss(row['summary'])}</b><br>" if 'summary' in row and row['summary'] != row['details'] else "") + sanitize_xss(row['details']),
            'published': row['published'],
            'severity': str(row['severity']),
            'langs': "\n".join(row['langs']),
            'references': refs_html,
        }

        html_output.append(obj)
        

    # handle xss that may occur in output
    json_output = json.dumps(html_output)
    open('data.js', 'w').write("""
        var data = """ + json_output + """;
    """)

    html += """
        <script src="data.js"></script>

        <div class='table-container'>
            <table></table>
        </div>

        <script src='main.js'></script>
    </body>
</html>
    """
    

    with open('report.html', 'w', encoding='utf-8') as file:
        file.write(html)
    
    global all_references
    with open('all_references.txt', 'w', encoding='utf-8') as file:
        file.write("\n".join(all_references))



    # build rss feed
    def build_rss_xml():
        xml = """<?xml version="1.0" encoding="UTF-8" ?>
        <rss version="2.0">
            <channel>   
                <title>Open Source Vulnerabilities</title>
                <link>https://oss-vulns.alecmaly.com</link>
                <description>Filtered list of //osv.dev for enhanced searching</description>
        """

        for row in html_output[:500]:
            title = row['details'].split("<br>")[0]
            xml += f"""
                <item>
                    <title>{row['id']}: {str(row['severity'])} | {title}</title>
                    <link>https://oss-vulns.alecmaly.com/report.html#{row['id']}</link>
                    <pubDate>{row['published']}</pubDate>
                    <description>
                        <![CDATA[
                            Source: <a href='https://osv.dev/vulnerability/{row['id']}'>https://osv.dev/vulnerability/{row['id']}</a><br>
                            <b>Published:</b> {row['published']}<br>
                            <b>Severity:</b> {row['severity']}<br>
                            <b>Langs:</b> {row['langs']}<br>
                            <b>References:</b> {row['references']}<br>
                            <b>Details:</b> {row['details']}
                        ]]>
                    </description>
                </item>
            """

        xml += """
            </channel>
        </rss>
        """

        with open('rss.xml', 'w', encoding='utf-8') as file:
            file.write(xml)
    build_rss_xml()

    print("[+] Done.")


if __name__ == "__main__":
    main()





## get all ecosystems
# url = "https://storage.googleapis.com/osv-vulnerabilities/ecosystems.txt"
# response = requests.get(url)
# print(response.text)
