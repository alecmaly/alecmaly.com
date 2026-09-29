#!/usr/local/bin/python

# pip install cvss requests
from cvss import CVSS2, CVSS3, CVSS4
import argparse
import requests
import zipfile
import json
import datetime
import os
import gc
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Global set for references (managed carefully)
global all_references
all_references = set()

CURRENT_YEAR = datetime.datetime.now().year
TIME_THRESHOLD_YEARS = 3  # Kept your comment's logic (3 years)

def download_ecosystem(ecosystem):
    filename = ecosystem + ".zip"
    zip_filepath = os.path.join('data', filename)

    # mkdir if does not exist
    if not os.path.exists('data'):
        os.makedirs('data')

    url = "https://storage.googleapis.com/osv-vulnerabilities/" + ecosystem + "/all.zip"

    print(f"[+] Downloading {ecosystem}...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(zip_filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def is_good_link(url):
    links_to_exclude = [
        "mattermost.com", "nodejs.org", "npmjs.com", "nvd.nist.gov",
        "wpscan.com", "github.com", "grafana.com", "bugzilla.redhat.com",
        "apache.org", "debian.org", "openwall.com", "thewatch.centreon.com",
        "openstack.org", "cve.org", "crates.io", "pkg.go.dev",
        "ycombinator.com", "typo3.org"
    ]

    url_lower = url.lower()

    # 1. Check exclusions
    if any(exclude in url_lower for exclude in links_to_exclude):
        # 2. Check exceptions to the exclusions (Github specific)
        if "github.com" in url_lower:
            if any(x in url_lower for x in ["#", "/security/advisories/", "/issues/", "/commit/"]):
                return True
        return False

    return True

def filtered_filepath(ecosystem):
    # One JSONL file per ecosystem holding only the already-filtered
    # records for that ecosystem. Used as the on-disk backing store so
    # main() never has to hold every ecosystem's records in memory at
    # once (see process_ecosystem's docstring below for why).
    return os.path.join('data', ecosystem + '.filtered.jsonl')

def process_ecosystem(args, ecosystem):
    # Previously this returned a Python list of every filtered record
    # for the ecosystem, which main() then concatenated across all 22
    # ecosystems into one big in-memory list before sorting/writing.
    # That aggregate list - not the raw zip parsing - was what pushed
    # past the container's memory limit and caused the recurring OOM
    # kills, since it held full 'details'/'summary'/'references' text
    # for every matching vulnerability across every ecosystem at once,
    # for the whole duration of the run.
    #
    # Instead, each matching record is written straight to a per-
    # ecosystem JSONL file on disk as soon as it's built, and this
    # function only returns a lightweight index (published date +
    # byte offset) so main() can sort and stream the records back out
    # later without ever holding more than one record in memory.
    index_entries = []  # (published, ecosystem, byte_offset)
    zip_filepath = os.path.join('data', ecosystem + '.zip')

    # Check download requirements
    now = datetime.datetime.now().timestamp()
    if args.force_download or not os.path.exists(zip_filepath) or os.path.getmtime(zip_filepath) < now - 86400:
        download_ecosystem(ecosystem)
    else:
        print(f"Skipping download for {ecosystem} (fresh enough)")

    print(f"[+] Processing {ecosystem}...")

    local_refs = set() # Collect refs locally to avoid threading lock contention
    files_processed = 0

    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref, \
             open(filtered_filepath(ecosystem), 'w', encoding='utf-8') as out_f:
            for file_name in zip_ref.namelist():
                files_processed += 1

                # Read content
                content = zip_ref.read(file_name)
                data = json.loads(content)
                del content # Free memory immediately

                if data.get('summary', "").startswith('Malicious code in '):
                    continue

                if 'references' in data:
                    # Filter references
                    refs = [ref for ref in data['references'] if ref.get('type') not in ['ADVISORY', 'FIX'] and 'url' in ref]

                    # Store URLs for global list
                    for r in refs:
                        local_refs.add(r['url'])

                    # Time check
                    years_since_published = 99
                    if 'published' in data:
                        try:
                            pub_year = int(data['published'].split('-')[0])
                            years_since_published = CURRENT_YEAR - pub_year
                        except:
                            pass

                    if len(refs) > 0 and years_since_published <= TIME_THRESHOLD_YEARS:
                        # Calculate Severity
                        severity = 0.0
                        if 'severity' in data:
                            try:
                                sev_entry = data['severity'][0]
                                t = sev_entry['type']
                                if t == 'CVSS_V3':
                                    severity = CVSS3(sev_entry['score']).scores()[0]
                                elif t == 'CVSS_V4':
                                    severity = CVSS4(sev_entry['score']).base_score
                            except:
                                pass # formatting error or unsupported version

                        has_good_ref = any(is_good_link(r['url']) for r in refs)

                        if not has_good_ref:
                            continue

                        bad_ref_urls = [r['url'] for r in refs if not is_good_link(r['url'])]

                        # Extract Languages
                        langs = set()
                        refs_w_line_num = [r for r in refs if "github" in r['url'] and "#L" in r['url']]
                        for r in refs_w_line_num:
                            try:
                                # Safe extraction
                                ext = r['url'].split('#')[0].split("?")[0].split("/")[-1].split('.')[-1][:5]
                                if ext != "md":
                                    langs.add(ext)
                            except:
                                pass

                        # --- CRITICAL MEMORY OPTIMIZATION ---
                        # Do NOT store 'data': data. Only store what is needed.
                        o = {
                            'ecosystem': ecosystem,
                            'id': data['id'],
                            'langs': list(langs),
                            'summary': data.get('summary', ""),
                            'details': data.get('details', ""),
                            'published': data.get('published', ""),
                            'references': refs,
                            'bad_ref_urls': bad_ref_urls,
                            'severity': severity
                        }

                        offset = out_f.tell()
                        json.dump(o, out_f)
                        out_f.write("\n")
                        index_entries.append((o['published'], ecosystem, offset))

                # Help GC inside loop
                del data

    except zipfile.BadZipFile:
        print(f"Error: Bad zip file for {ecosystem}")
    except Exception as e:
        print(f"Error processing {ecosystem}: {e}")

    # Explicit GC after heavy processing
    gc.collect()
    return index_entries, local_refs, files_processed

def sanitize_xss(s):
    if not s: return ""
    return s.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;").replace('"', "&quot;").replace("'", "&#x27;").replace("/", "&#x2F;")

def build_data_obj(row):
    # Build references HTML
    refs_html_parts = ["<ul>"]
    for ref in row['references']:
        style = "style='color:red'" if ref['url'] in row['bad_ref_urls'] else ""
        tag = "s" if ref['url'] in row['bad_ref_urls'] else "span"
        # Check for XSS in URLs just in case
        safe_url = sanitize_xss(ref['url'])
        refs_html_parts.append(f"<li>- <{tag} {style}><a target='_blank' href='{safe_url}'>{safe_url}</a></{tag}></li>")
    refs_html_parts.append("</ul>")

    # Combine details
    summary_part = f"<b>{sanitize_xss(row['summary'])}</b><br>" if row['summary'] and row['summary'] != row['details'] else ""
    full_details = summary_part + sanitize_xss(row['details'])

    return {
        'ecosystem': sanitize_xss(row['ecosystem']),
        'id': row['id'],
        'details': full_details,
        'published': row['published'],
        'severity': str(row['severity']),
        'langs': "\n".join(row['langs']),
        'references': "".join(refs_html_parts),
    }

def main():
    parser = argparse.ArgumentParser(description='Download and process OSV data')
    parser.add_argument('--force-download', action='store_true', help='Force download of zip files')
    args = parser.parse_args()

    total_files = 0
    global all_references

    ecosystems = ['GIT', 'OSS-Fuzz', 'npm', 'PyPI', 'NuGet', 'JavaScript', 'Linux', 'Go', 'GitHub Actions', 'GSD', 'Hex', 'Maven', 'DWF', 'Chainguard', 'CRAN', 'Bitnami', 'UVI', 'Wolfi', 'RubyGems', 'SwiftURL', 'Pub', 'Packagist']

    if not os.path.exists('data'):
        os.makedirs('data')

    # Only (published, ecosystem, byte_offset) tuples are held in memory
    # across ecosystems - the actual record content stays on disk in each
    # ecosystem's *.filtered.jsonl file until the streaming write phase below.
    all_index = []

    # max_workers=1: keeps at most one ecosystem's raw zip decompressed in
    # memory at a time (npm/GSD/Linux are large). Combined with the
    # disk-backed index above, this is what keeps peak memory bounded
    # regardless of how many total records match across all 22 ecosystems -
    # previously that aggregate was held in memory whole, which is what
    # caused the recurring OOM kills.
    with ThreadPoolExecutor(max_workers=1) as executor:
        future_to_eco = {executor.submit(process_ecosystem, args, eco): eco for eco in ecosystems}

        for future in as_completed(future_to_eco):
            eco = future_to_eco[future]
            try:
                index_entries, eco_refs, count = future.result()

                # Aggregate results
                all_index.extend(index_entries)
                all_references.update(eco_refs)
                total_files += count

                print(f"[+] Finished {eco}. Total records so far: {len(all_index)}")

                del index_entries
                del eco_refs
                gc.collect()

            except Exception as exc:
                print(f"Error processing {eco}: {exc}")

    print(f"Total files processed: {total_files}")
    print(f"Filtered vulnerabilities count: {len(all_index)}")

    # Sort by published date (Newest first) - Replacing the double sort
    # (Sorting by severity first then date overwrites the severity sort effectively, usually you want one primary)
    # I will stick to your final logic: Published Date
    print("[+] Sorting data...")
    all_index.sort(key=lambda x: x[0], reverse=True)

    print("[+] Generating HTML...")

    # STREAM WRITING HTML TO DISK
    # We do NOT build a huge string 'html = ...' in memory.

    with open('report.html', 'w', encoding='utf-8') as f:
        # Header
        f.write("""
        <html>
        <head>
            <title>Open Source Vulnerabilities</title>
            <meta property="og:title" content="open source vulnerabilities" />
            <meta property="og:type" content="website" />
            <meta property="og:description" content="Filtered list of //osv.dev for enhanced searching" />
            <script src="mark.min.js"></script>
            <link rel="stylesheet" type="text/css" href="purecss.min.css">
            <link rel="stylesheet" type="text/css" href="styles.css">
            <script type="text/javascript">
                var hostname = window.location.hostname;
                var parts = hostname.split('.');
                while (parts.length > 2) { parts.shift(); }
                var mainDomain = parts.join('.');
                var link = document.createElement('link');
                link.rel = 'icon';
                link.href = 'https://' + mainDomain + '/favicon.ico';
                link.type = 'image/x-icon';
                document.head.appendChild(link);
            </script>
        </head>
        <body>
        <button id="top-btn" class='pure-button' onclick="topFunction()">Top</button>
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
            <p>
                web3 reports can be found at <a href='https://solodit.xyz'>solodit.xyz</a> and <a href='https://code4rena.com/reports'>code4rena.com/reports</a><br>
                web2 reports sources:  <a href='https://github.com/reddelexc/hackerone-reports'>hackerone reports by tag</a>, <a href='https://pentester.land/writeups/'>pentester.land/writeups</a>
            </p>
            <p>
                Note: This list to filter for only vulns that have a github link to source code (//github.com/path/to/file#Lline_num) or potential writeup.<br>
            </p>
        </div>
        """)

        # Stream data.js and collect the RSS top-500 in the same pass, by
        # seeking into each ecosystem's on-disk JSONL file using the
        # sorted index built above. One record is ever in memory at a
        # time; the per-ecosystem file handles are opened lazily and
        # reused across the pass instead of reopening per record.
        print("[+] Generating data.js...")
        rss_rows = []
        open_files = {}
        try:
            with open('data.js', 'w') as jf:
                jf.write("var data = [")
                for i, (published, ecosystem, offset) in enumerate(all_index):
                    ef = open_files.get(ecosystem)
                    if ef is None:
                        ef = open(filtered_filepath(ecosystem), 'r', encoding='utf-8')
                        open_files[ecosystem] = ef
                    ef.seek(offset)
                    row = json.loads(ef.readline())

                    if i < 500:
                        rss_rows.append(row)

                    obj = build_data_obj(row)
                    if i > 0:
                        jf.write(",")
                    json.dump(obj, jf)
                jf.write("];")
        finally:
            for ef in open_files.values():
                ef.close()

        # Finish HTML
        f.write("""
        <script src="data.js"></script>
        <div class='table-container'>
            <table></table>
        </div>
        <script src='main.js'></script>
        </body>
        </html>
        """)

    # Write References
    with open('all_references.txt', 'w', encoding='utf-8') as file:
        file.write("\n".join(all_references))

    # Generate RSS
    print("[+] Generating RSS...")
    with open('rss.xml', 'w', encoding='utf-8') as f:
        f.write("""<?xml version="1.0" encoding="UTF-8" ?>
        <rss version="2.0">
            <channel>
                <title>Open Source Vulnerabilities</title>
                <link>https://oss-vulns.alecmaly.com</link>
                <description>Filtered list of //osv.dev for enhanced searching</description>
        """)

        # Take top 500 (already collected in sorted order above)
        for row in rss_rows:
            # Simple sanitization for XML
            title = sanitize_xss(row['details'].split("<br>")[0] if row['details'] else row['id'])
            # Ensure we don't break XML with special chars in title

            # Build description CDATA content
            desc_content = f"""
                    Source: <a href='https://osv.dev/vulnerability/{row['id']}'>https://osv.dev/vulnerability/{row['id']}</a><br>
                    <b>Published:</b> {row['published']}<br>
                    <b>Severity:</b> {row['severity']}<br>
                    <b>Langs:</b> {", ".join(row['langs'])}<br>
                    <b>Details:</b> {sanitize_xss(row['details'])}
            """

            f.write(f"""
                <item>
                    <title>{row['id']}: {row['severity']} | {title}</title>
                    <link>https://oss-vulns.alecmaly.com/report.html#{row['id']}</link>
                    <pubDate>{row['published']}</pubDate>
                    <description><![CDATA[{desc_content}]]></description>
                </item>
            """)

        f.write("""
            </channel>
        </rss>
        """)

    print("[+] Done.")

if __name__ == "__main__":
    main()
