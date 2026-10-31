"""Disposable, dependency-free HTTP target; no command execution or outbound calls."""
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'<!doctype html><html lang="en"><title>Pipeline demo</title><p>Healthy</p></html>'
        self.send_response(200 if self.path == '/' else 404)
        for name, value in {
            'Content-Type': 'text/html; charset=utf-8',
            'Content-Length': str(len(body)),
            'Content-Security-Policy': "default-src 'none'; frame-ancestors 'none'; form-action 'none'",
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'Cache-Control': 'no-store',
        }.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    HTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
