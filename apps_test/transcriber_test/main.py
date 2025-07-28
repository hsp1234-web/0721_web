import http.server
import socketserver
import os

PORT = int(os.getenv("PORT", 8002))

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/docs':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Transcriber test docs are here!")
        else:
            self.send_response(404)
            self.end_headers()

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Transcriber test server serving at port {PORT}")
    httpd.serve_forever()
