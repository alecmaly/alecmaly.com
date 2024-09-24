from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class PublicDirectoryHTTPRequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Define the public directory as the only accessible directory
        root_directory = os.path.join(os.getcwd(), 'public')  # Root is the /public directory

        # Check if the requested path starts with '/public'
        if not path.startswith('/public'):
            # Redirect to /public if the path is not inside /public
            self.send_response(302)
            self.send_header('Location', '/public')
            self.end_headers()
            return None

        # Translate the path as normal, ensuring it's inside /public
        return os.path.join(root_directory, path.lstrip('/public'))

# Define the server address and port
server_address = ('', 3000)  # '' means all available interfaces, 3000 is the port

# Create the HTTP server with the custom request handler
httpd = HTTPServer(server_address, PublicDirectoryHTTPRequestHandler)

print("Serving on port 3000, redirecting all requests to /public...")
httpd.serve_forever()
