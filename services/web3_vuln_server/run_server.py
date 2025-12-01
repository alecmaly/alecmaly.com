from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
from urllib.parse import unquote

def fully_unquote(path):
    prev = None
    while prev != path:
        prev = path
        path = unquote(path)
    return path

class PublicDirectoryHTTPRequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # 1. Fully decode double-encoded paths
        path = fully_unquote(path)

        public_dir = os.path.realpath(os.path.join(os.getcwd(), "public"))

        # 2. Reject explicit ".." anywhere
        if ".." in path:
            return os.path.join(public_dir, "index.html")

        # 3. Force everything to be under /public
        if not path.startswith("/public"):
            # Always serve index.html by default
            return os.path.join(public_dir, "index.html")

        # 4. Strip prefix only (/public)
        relative = path[len("/public"):]
        if relative.startswith("/"):
            relative = relative[1:]

        # 5. Build final path
        final = os.path.realpath(os.path.join(public_dir, relative))

        # 6. Prevent escaping public/ directory
        if not final.startswith(public_dir + os.sep):
            return os.path.join(public_dir, "index.html")

        # 7. If the file does not exist → return index.html
        if not os.path.exists(final):
            return os.path.join(public_dir, "index.html")

        return final


server_address = ("", 3000)
httpd = HTTPServer(server_address, PublicDirectoryHTTPRequestHandler)
print("Serving public/ on :3000 ...")
httpd.serve_forever()
