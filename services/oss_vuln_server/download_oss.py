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
TIME_THRESHOLD_YEARS = 3  # only keep vulnerabilities published in the last 3 years




# Function to process each ecosystem
def process_ecosystem(args, ecosystem):
    global total
    global unique_langs
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

                        has_good_ref = any([r for r in refs if "github" in r['url'] and "#L" in r['url']])

                        lang = ""
                        refs_w_line_num = [r for r in refs if "github" in r['url'] and "#L" in r['url']]
                        if len(refs_w_line_num) > 0:
                            # All file extensions from lines w/ line number + dedupe languages
                            langs = list(set([ref['url'].split('#')[0].split("?")[0].split("/")[-1].split('.')[-1][:5] for ref in refs_w_line_num]))
                            langs = [l for l in langs if l != "md"]  # Remove markdown files
                            for l in langs:
                                if l not in unique_langs:
                                    unique_langs.append(l)

                        if has_good_ref:
                            o = {
                                'ecosystem': ecosystem,
                                'id': data['id'],
                                'langs': langs,
                                'summary': data.get('summary', ""),
                                'details': data['details'],
                                'published': data['published'],
                                'has_good_ref': has_good_ref,
                                'references': refs,
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
        </head>
        <script src="mark.min.js"></script>

        <link rel="stylesheet" type="text/css" href="styles.css">
        <link rel="stylesheet" type="text/css" href="purecss.min.css">
    <body>"""

    # # add sticky search bar that hides rows that don't match the search
    html += """
    <div class="pure-form pure-g" style="position: sticky; top: 0; background-color: #fff; padding: 10px; z-index: 1000; border-bottom: 1px solid #ddd;">
        <div class="pure-u-1 pure-u-md-1-2">
            <input class="pure-input-1" type="text" id="search" onkeyup="debounce()" placeholder="Search for ecosystems..">
        </div>
        <div class="pure-u-1 pure-u-md-1-8">
            <select class="pure-input-1" id="ecosystem" onchange="buildTable()"></select>
        </div>
        <div class="pure-u-1 pure-u-md-1-8">
            <select class="pure-input-1" id="lang" onchange="buildTable()"></select>
        </div>
        <div class="pure-u-1 pure-u-md-1-8">
            <input class="pure-input-1" type="number" id="cvss-min" min="0" max="10" step="0.5" placeholder="CVSS min" onkeyup="debounce()">
        </div>
        <div class="pure-u-1 pure-u-md-1-8">
            <input class="pure-input-1" type="number" id="cvss-max" min="0" max="10" step="0.5" placeholder="CVSS max" onkeyup="debounce()">
        </div>
    </div>
    
    <h1>Data from: <a href='https://osv.dev/list' target='_blank'>https://osv.dev/list</a></h1>
    """



    def sanitize_xss(s):
        return s.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;").replace('"', "&quot;").replace("'", "&#x27;").replace("/", "&#x2F;")


    output = sorted(output, key=lambda x: x['published'], reverse=True)

    html_output = []
    for row in output:

        refs_html = "<ul>"
        for ref in row['references']:
            refs_html += f"<li>- <a target='_blank' href='{ref['url']}'>{ref['url']}</a></li>"
        refs_html += "</ul>"

        obj = {
            'ecosystem': sanitize_xss(row['ecosystem']),
            'id': f"<a href='https://osv.dev/vulnerability/{row['id']}' target='_blank'>{row['id']}</a>",
            'details': (f"<b>{sanitize_xss(row['summary'])}</b><br>" if 'summary' in row and row['summary'] != row['details'] else "") + sanitize_xss(row['details']),
            'published': row['published'],
            'severity': str(row['severity']),
            'langs': "\n".join(row['langs']),
            'references': refs_html,
        }

        html_output.append(obj)
        

    # handle xss that may occur in output
    json_output = json.dumps(html_output)
    html += """
        <script>
            var data = """ + json_output + """;
        </script>
    """
    html += "<table></table>"
    html += "<script src='main.js'></script>"
    html += "</body></html>"


    with open('report.html', 'w', encoding='utf-8') as file:
        file.write(html)
        

    print("[+] Done.")


if __name__ == "__main__":
    main()





## get all ecosystems
# url = "https://storage.googleapis.com/osv-vulnerabilities/ecosystems.txt"
# response = requests.get(url)
# print(response.text)
