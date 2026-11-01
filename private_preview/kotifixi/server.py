"""Unlisted Kotifixi visual concept preview, not customer production.

Read-only. No publishing to Kotifixi's real domain. No sensitive data or CMS.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
from urllib.parse import urlsplit

HERE=Path(__file__).resolve().parent
PORT=int(os.environ.get('PORT','10000'))
STATIC={
 '/':'index.html', '/index.html':'index.html',
 '/palvelut/':'palvelut/index.html', '/palvelut/index.html':'palvelut/index.html',
 '/meista/':'meista/index.html', '/meista/index.html':'meista/index.html',
 '/yhteys/':'yhteys/index.html', '/yhteys/index.html':'yhteys/index.html',
 '/assets/style.css':'assets/style.css', '/assets/app.js':'assets/app.js',
}
REDIRECTS={'/palvelut':'/palvelut/','/meista':'/meista/','/yhteys':'/yhteys/'}
TYPE={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'application/javascript; charset=utf-8'}

class SiteHandler(BaseHTTPRequestHandler):
 def _serve(self,head=False):
  requested=urlsplit(self.path).path
  headers=[]
  if requested=='/robots.txt':
   status=200;data=b'User-agent: *\nDisallow: /\n';mime='text/plain; charset=utf-8'
  elif requested=='/_health':
   status=200;data=b'ok';mime='text/plain; charset=utf-8'
  elif requested in REDIRECTS:
   status=308;data=b'';mime='text/plain; charset=utf-8';headers.append(('Location',REDIRECTS[requested]))
  elif requested in STATIC:
   target=(HERE/STATIC[requested]);mime=TYPE[target.suffix]
   if target.is_file():status=200;data=target.read_bytes()
   else:status=404;data=b'Page not found';mime='text/plain; charset=utf-8'
  else:status=404;data=b'Page not found';mime='text/plain; charset=utf-8'
  self.send_response(status)
  for key,val in [
   ('Content-Type',mime),('Content-Length',str(len(data))),
   ('Cache-Control','private, no-store, max-age=0'),
   ('X-Robots-Tag','noindex, nofollow, noarchive'),
   ('X-Content-Type-Options','nosniff'),('Referrer-Policy','strict-origin-when-cross-origin'),
   ('X-Frame-Options','DENY'),
   ('Content-Security-Policy',"default-src 'none'; img-src 'self' https://images.unsplash.com data:; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'none'")
  ]+headers:self.send_header(key,val)
  self.end_headers()
  if not head:self.wfile.write(data)
 def do_GET(self):self._serve()
 def do_HEAD(self):self._serve(True)

if __name__=='__main__':
 print('Kotifixi public-unlisted V3 visual demo: noindex, read-only, no customer domain changes.',flush=True)
 ThreadingHTTPServer(('0.0.0.0',PORT),SiteHandler).serve_forever()