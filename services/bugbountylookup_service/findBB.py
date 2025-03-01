# sourced from: https://github.com/System00-Security/findbbprograms

import requests
from urllib import parse as p
import json
from colorama import init, Fore
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, render_template_string
from werkzeug.utils import secure_filename
import os

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
headers = {'User-Agent': user_agent}

bootstrap_template = """
<!DOCTYPE html>
<html>
<head>
  <title>FindBB Program Search</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body class="container mt-5">
<center><pre>
  ___ _         _<font color="red"> ___ ___<font color="black"> ___                                 
 | __(_)_ _  __| <font color="red">| _ ) _ )<font color="black"> _ \_ _ ___  __ _ _ _ __ _ _ __  ___
 | _|| | ' \/ _` <font color="red">| _ \ _ \<font color="black">  _/ '_/ _ \/ _` | '_/ _` | '  \(_-<
 |_| |_|_||_\__,_<font color="red">|___/___/<font color="black">_| |_| \___/\__, |_| \__,_|_|_|_/__/
                       |___/ <font color="green">V2<font color="black">
 <font color="yellow">- ><font color="black"> Accidental Bug Happens find the program and report it
</pre></center><br/>
  <form method="post">
    <div class="mb-3">
      <label for="domain" class="form-label">Domain:</label>
      <input type="text" class="form-control" name="domain" id="domain" required>
    </div>
    <button type="submit" class="btn btn-primary">Search Single Domain</button>
  </form>
  <br>
  <form method="post" enctype="multipart/form-data">
    <div class="mb-3">
      <label for="file" class="form-label">Upload File:</label>
      <input type="file" class="form-control" name="file" id="file">
    </div>
    <button type="submit" class="btn btn-primary">Search Multiple Domains</button>
  </form>
  {% if results %}
    <div class="mt-4">
      <h2>Search Result</h2>
      <style>
      a {
        color: black;
        text-decoration: none;
      }
      </style>
      {% for result in results %}
      <div class='alert alert-success' role='alert'>
        <a href='{{ result["program_url"] }}'>{{ result["program_url"] }}</a><br>
        Result For: {{ result["search_link"] }}
      </div>
      {% endfor %}
    </div>
  {% endif %}
</body>
</html>
"""

app = Flask(__name__)

class FindBBProgram:
    def __init__(self):
        self.programs_data = []

    def fetch_data(self, url):
        try:
            with requests.get(url, headers=headers) as req:
                if req.status_code == 200:
                    return json.loads(req.text)
                return []
        except requests.ConnectionError:
            return []
        except Exception as e:
            print(e)
            return []

    def api1(self, domain):
        if not self.programs_data:
            self.programs_data = self.fetch_data("https://raw.githubusercontent.com/disclose/diodb/master/program-list.json")
        for i in self.programs_data:
            if i['program_name'] == domain:
                return {
                    "program_url": i['contact_url'],
                    "search_link": f"{p.quote(domain)}"
                }
        return None

    def api2(self, domain):
        if not self.programs_data:
            self.programs_data = self.fetch_data("https://raw.githubusercontent.com/projectdiscovery/public-bugbounty-programs/master/chaos-bugbounty-list.json")
        for i in self.programs_data['programs']:
            if domain in i['domains']:
                return {
                    "program_url": i['url'],
                    "search_link": f"{p.quote(domain)}"
                }
        return None

    def api3(self, domain):
        try:
            endpoint = "https://raw.githubusercontent.com/trickest/inventory/main/targets.json"
            with requests.get(endpoint, headers=headers) as req:
                if req.status_code == 200:
                    data = json.loads(req.text)
                    data = data['targets']
                    for i in data:
                        if domain in i['domains']:
                            return {
                                "program_url": i['url'],
                                "search_link": f"{p.quote(domain)}"
                            }
                return None
        except requests.ConnectionError:
            return None

    def search_program(self, domain):
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(api, domain) for api in (self.api1, self.api2, self.api3)]
            for future in futures:
                result = future.result()
                if result:
                    return result
        return None

    def engine(self, domain):
        print(f"{Fore.GREEN}[SRC]{Fore.RESET} Searching for {domain}")
        program_info = self.search_program(domain)
        return program_info

class CustomLogHandler(logging.StreamHandler):
    def emit(self, record):
        log_msg = self.format(record)
        if '127.0.0.1' in log_msg or 'localhost' in log_msg:
            log_msg = f"[WEB-UI] {log_msg}"
        else:
            level = record.levelname
            if level == 'INFO':
                log_msg = f"[INFO] {log_msg}"
            elif level == 'WARNING':
                log_msg = f"[WARN] {log_msg}"
        print(log_msg)

app.logger.addHandler(CustomLogHandler())

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "domain" in request.form:
            domain = request.form["domain"]
            result = FindBBProgram().engine(domain)
            if result:
                results = [result]
            else:
                results = []
            return render_template_string(bootstrap_template, results=results)

        elif "file" in request.files:
            file = request.files["file"]

            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join("uploads", filename)
                file.save(file_path)
                with open(file_path, "r") as f:
                    domains = f.read().splitlines()

                program_info_list = []
                for domain in domains:
                    result = FindBBProgram().engine(domain)
                    if result:
                        program_info_list.append(result)
                os.remove(file_path)

                return render_template_string(bootstrap_template, results=program_info_list)

    return render_template_string(bootstrap_template)

if __name__ == "__main__":
    init()
    print(f"""
  ___ _         _{Fore.RED} ___ ___{Fore.RESET} ___                                 
 | __(_)_ _  __| {Fore.RED}| _ ) _ ){Fore.RESET} _ \_ _ ___  __ _ _ _ __ _ _ __  ___
 | _|| | ' \/ _` {Fore.RED}| _ \ _ \{Fore.RESET}  _/ '_/ _ \/ _` | '_/ _` | '  \(_-<
 |_| |_|_||_\__,_{Fore.RED}|___/___/{Fore.RESET}_| |_| \___/\__, |_| \__,_|_|_|_/__/
                                      |___/ {Fore.GREEN}V2{Fore.RESET}
 {Fore.YELLOW}- >{Fore.RESET} Accidental Bug Happens find the program and report it
""")
    parser = argparse.ArgumentParser(description="FindBB Program Search")
    parser.add_argument("-web", action="store_true", help="Enable the web-based search UI")
    parser.add_argument("-d", "--domain", help="Domain to search")
    parser.add_argument("-f", "--file", help="File containing domains to search")
    args = parser.parse_args()

    if args.domain:
        if args.domain == "":
            app.logger.warning("Please provide a domain to search using -d option.")
        else:
            domain = args.domain
            result = FindBBProgram().engine(domain)
            if result:
                url = result["program_url"]
                print(f"{Fore.GREEN}[Program Link] {Fore.RESET}{url}")
            else:
                app.logger.warning("No Program Found")
    elif args.file:
        if args.file == "":
            app.logger.warning("Please provide a file containing domains to search using -f option.")
        else:
            with open(args.file, "r") as f:
                for domain in f.read().splitlines():
                    result = FindBBProgram().engine(domain)
                    if result:
                        url = result["program_url"]
                        print(f"{Fore.GREEN}[Program Link] {Fore.RESET}{url}")
                    else:
                        app.logger.warning(f"No Program Found for {domain}")
    elif args.web:
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
        app.run(host="0.0.0.0", port=5000, debug=False)
    else:
        parser.print_help()