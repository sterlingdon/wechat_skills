#!/usr/bin/env python3
import http.server
import socketserver


class UTF8Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Content-Type", "text/html; charset=utf-8")
        super().end_headers()


PORT = 8080
with socketserver.TCPServer(("0.0.0.0", PORT), UTF8Handler) as httpd:
    print(f"Server running at http://localhost:{PORT}")
    httpd.serve_forever()
