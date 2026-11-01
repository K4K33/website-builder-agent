"""Read-only unlisted Kotifixi design preview. Not a customer production website.

No CMS or tracking. Public only to people with link, no auth.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import os

HERE=Path(__file__).resolve().parent
PORT=int(os.environ.get('PORT','10000'))
PAGES={'/':'index.html','/index.html':'index.html','/palvelut/':'palvelut/index.html','/palvelut/index.html':'palvelut/index.html','/hinnasto/':'hinnasto/index.html','/hinnasto/index.html':'hinnasto/index.html','/meista/':'meista/index.html','/meista/index.html':'meista/index.html','/yhteys/':'yhteys/index.html','/yhteys/index.html':'yhteys/index.html','/assets/style.css':'assets/style.css','/assets/app.js':'assets/app.js'}
REDIRECTS={'/palvelut':'/palvelut/','/hinnasto':'/hinnasto/','/meista':'/meista/','/yhteys':'/yhteys/'}
TYPES={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'application/javascript; charset=utf-8'}
class Handler(BaseHTTPRequestHandler):
 def _respond(self,head=False):
  path=urlsplit(self.path).path
  extras=[]
  if path=='/robots.txt': code=200;body=b'User-agent: *\nDisallow: /\n';ctype='text/plain; charset=utf-8'
  elif path=='/_health': code=200;body=b'ok';ctype='text/plain; charset=utf-8'
  elif path in REDIRECTS: code=308;body=b'';ctype='text/plain; charset=utf-8';extras=[('Location',REDIRECTS[path])]
  elif path in PAGES:
   f=HERE/PAGES[path]
   if f.is_file():code=200;body=f.read_bytes();ctype=TYPES[f.suffix]
   else:code=404;body=b'Not found';ctype='text/plain; charset=utf-8'
  else:code=404;body=b'Not found';ctype='text/plain; charset=utf-8'
  self.send_response(code)
  for key,val in [
   ('Content-Type',ctype),('Content-Length',str(len(body))),('Cache-Control','public, max-age=60'),
   ('X-Robots-Tag','noindex, nofollow, noarchive'),('X-Content-Type-Options','nosniff'),
   ('Referrer-Policy','strict-origin-when-cross-origin'),('X-Frame-Options','DENY'),
   ('Content-Security-Policy',"default-src 'none'; img-src 'self' https://images.pexels.com data:; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'none'")
  ]+extras:self.send_header(key,val)
  self.end_headers()
  if not head:self.wfile.write(body)
 def do_GET(self):self._respond()
 def do_HEAD(self):self._respond(head=True)
if __name__=='__main__':
 print('Kotifixi read-only concept preview (noindex, link accessible).',flush=True)
 ThreadingHTTPServer(('0.0.0.0',PORT),Handler).serve_forever()