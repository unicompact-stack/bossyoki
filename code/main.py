"""BossYoki — выключен (только health check)."""
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.getenv('PORT', '10000'))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write('BossYoki off. Send empty commit to turn on.'.encode())
    def log_message(self, *a): pass

print(f'BossYoki OFF — health check on port {PORT}', flush=True)
HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
