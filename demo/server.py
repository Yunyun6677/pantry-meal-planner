import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .engine import PantryAgent

def make_server(db_path, port=8765):
    agent = PantryAgent(db_path)
    class Handler(BaseHTTPRequestHandler):
        def respond(self, code, value, html=False):
            raw=value if html else json.dumps(value,ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header('Content-Type','text/html; charset=utf-8' if html else 'application/json; charset=utf-8')
            self.send_header('Content-Length',str(len(raw)))
            self.send_header('Cache-Control','no-store')
            self.end_headers()
            self.wfile.write(raw)
        def do_GET(self):
            if self.path=='/': self.respond(200,Path(__file__).with_name('index.html').read_bytes(),True)
            elif self.path=='/api/state': self.respond(200,agent.state())
            else: self.respond(404,{'error':'路径不存在'})
        def do_POST(self):
            hosts=[f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}']
            if self.headers.get('Host') not in hosts or (self.headers.get('Origin') and self.headers['Origin'] not in ['http://'+h for h in hosts]):
                self.respond(403,{'error':'不允许跨站写入'}); return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=16000 or self.headers.get('Content-Type','').split(';')[0]!='application/json': raise ValueError('需要不超过16KB的JSON')
                data=json.loads(self.rfile.read(size))
                routes={'/api/chat':lambda:agent.chat(data['text']),'/api/preview':lambda:agent.preview(data['text'],data['mode']),'/api/apply':lambda:agent.apply(data['id']),'/api/recommend':lambda:agent.recommend(data.get('people')),'/api/cook':lambda:agent.consume(data['id'])}
                if self.path not in routes: self.respond(404,{'error':'路径不存在'}); return
                self.respond(200,routes[self.path]())
            except (ValueError,KeyError,TypeError,AttributeError) as e: self.respond(400,{'error':str(e)})
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--port',type=int,default=8765)
    p.add_argument('--db',type=Path,default=Path(__file__).resolve().parents[1]/'data'/'pantry.sqlite3')
    a=p.parse_args(); server=make_server(a.db,a.port)
    print(f'http://127.0.0.1:{server.server_port}',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__=='__main__': main()
