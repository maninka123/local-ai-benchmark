"""Serve an exported GitHub Pages folder on loopback for review."""
import argparse
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--directory',required=True);parser.add_argument('--port',type=int,default=8777);args=parser.parse_args()
    root=Path(args.directory).resolve()
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*a,**kw):super().__init__(*a,directory=str(root),**kw)
        def translate_path(self,path):
            if path.startswith('/local-ai-benchmark/'):path=path[len('/local-ai-benchmark'):]
            return super().translate_path(path)
        def end_headers(self):self.send_header('Access-Control-Allow-Origin','*');super().end_headers()
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
if __name__=='__main__':main()
