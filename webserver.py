import http.server
import socketserver
import re
import requests
from urllib.parse import urlparse
from urllib.parse import parse_qs

PORT = 8080

img_path_pattern = re.compile(r'\/img\/([0-9a-f]+)$')

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET_image(self, img_uid, img_url=None):
        if len(img_uid) != 32:
            return False
        try:
            if img_url is None:
                solr_response = requests.get(f'http://localhost:8983/solr/commonpool/get?id={img_uid}')
                img_url = solr_response.json()['doc']['Url'][0]
            response = requests.get(img_url)
        except Exception as e:
            print(e)
            self.send_response(404)
            self.end_headers()
            return False
        # print('Sending from URL: ', img_url)
        self.send_response(response.status_code)
        self.send_header('Content-type', response.headers.get("content-type"))
        self.end_headers()
        self.wfile.write(response.content)
        return False
    def do_GET(self):
        parsed_url = urlparse(self.path)
        self.path = parsed_url.path
        params = parse_qs(parsed_url.query)
        print(parsed_url, params)
        if self.path in ['/', '/search.html']:
            self.path = '/search.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        else:
            match = re.match(img_path_pattern, self.path)
            if match:
                img_uid = match.group(1)
                return self.do_GET_image(img_uid, img_url=params.get('src', [None])[0])
            self.send_response(404)
            self.end_headers()
            return False


socketserver.TCPServer.allow_reuse_address=True
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()