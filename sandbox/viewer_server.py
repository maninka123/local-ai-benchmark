import http.server,os
os.chdir('/site')
class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Content-Security-Policy',"default-src 'self' data: blob:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'none'; frame-src 'none'; form-action 'none'")
        self.send_header('X-Content-Type-Options','nosniff')
        super().end_headers()
http.server.ThreadingHTTPServer(('0.0.0.0',8000),Handler).serve_forever()
