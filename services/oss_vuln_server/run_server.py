from http.server import HTTPServer, SimpleHTTPRequestHandler

class NoListingHTTPRequestHandler(SimpleHTTPRequestHandler):
    def list_directory(self, path):
        # Override to disable directory listing
        self.send_error(403, "Directory listing not allowed")
        return None

# Define the server address and port
server_address = ('', 3000)  # '' means all available interfaces, 3000 is the port

# Create the HTTP server with the custom request handler
httpd = HTTPServer(server_address, NoListingHTTPRequestHandler)

print("Serving on port 3000...")
httpd.serve_forever()
