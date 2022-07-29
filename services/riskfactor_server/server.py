from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, quote
import requests
import json

# test url
# http://localhost:8000/riskfactor_redirect?q=Yadkinville%2cNC&type=flood

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if (self.path == '' or self.path == '/' or self.path == '/favicon.ico' or self.path == '/fire_flood_riskfactor_redirect'):
            self.send_response(200)

            self.send_header('Content-type', 'text/html')
            self.end_headers()

            self.wfile.write(bytes("Alive: url should look like this http://alecmaly.com/riskfactor_redirect?q=Yadkinville%2cNC&type=flood", "utf8"))
            return
        

        query = urlparse(self.path).query
        print(self.path)
        query_components = dict(qc.split("=") for qc in query.split("&"))
        print(query)
        search_query = quote(query_components["q"])
        floodORfire = query_components["type"]

        # malformed request
        if (not search_query or not floodORfire) or (floodORfire != "flood" and floodORfire != "fire"):
            self.send_response(400)
            return

        resp = requests.get(f"https://riskfactor.com/api/autocomplete/{search_query}")
        data = json.loads(resp.text)
        fsid= data[0]['fsid']
        entity = data[0]['entity']

        redirect_location = f'https://riskfactor.com/{entity}/{search_query}/{fsid}_fsid/{floodORfire}'

        self.send_response(302)
        self.send_header('Content-Type', "text/html")
        self.send_header('Location', redirect_location)
        self.end_headers()


with HTTPServer(('', 8000), handler) as server:
    server.serve_forever()
    