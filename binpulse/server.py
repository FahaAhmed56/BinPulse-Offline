import argparse
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .core import connect, initialize, snapshot, record, pending, simulate, mark_synced

WEB=Path(__file__).resolve().parent.parent/'web'/'index.html'

class Handler(BaseHTTPRequestHandler):
    db_path='data/binpulse.sqlite3'
    def _json(self,payload,status=200):
        body=json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.end_headers();self.wfile.write(body)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/':
            body=WEB.read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
        with connect(self.db_path) as db:
            if path=='/api/bins':return self._json({'bins':snapshot(db)})
            if path=='/api/pending':return self._json({'count':len(pending(db)),'readings':pending(db)})
        return self._json({'error':'Not found'},404)
    def do_POST(self):
        path=urlparse(self.path).path
        if path not in ('/api/readings','/api/simulate','/api/sync'): return self._json({'error':'Not found'},404)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length>10000 or length<0: return self._json({'error':'Payload too large'},413)
            payload=json.loads(self.rfile.read(length) or b'{}')
            if not isinstance(payload,dict):raise ValueError('JSON object required')
            with connect(self.db_path) as db:
                if path=='/api/readings':
                    result={'id':record(db,payload['bin_id'],payload['fill_pct'],payload.get('battery_pct',100))}
                elif path=='/api/simulate':result={'readings':simulate(db)}
                else:
                    # Local demonstration of acknowledgement; no remote server contacted.
                    ids=[r['id'] for r in pending(db)]
                    mark_synced(db,ids)
                    result={'acknowledged_locally':len(ids),'note':'Demo only: no network upload occurs'}
            self._json(result,201 if path=='/api/readings' else 200)
        except (ValueError,KeyError,TypeError,json.JSONDecodeError) as e:self._json({'error':str(e)},400)
        except sqlite3.Error:self._json({'error':'Database error'},500)

def main():
    parser=argparse.ArgumentParser(description='Run local BinPulse monitoring dashboard')
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8080)
    parser.add_argument('--db',default='data/binpulse.sqlite3')
    args=parser.parse_args()
    Handler.db_path=args.db
    with connect(args.db) as db:initialize(db)
    server=ThreadingHTTPServer((args.host,args.port),Handler)
    print(f'BinPulse ready at http://{args.host}:{args.port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
