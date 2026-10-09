#!/usr/bin/env python3
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

HEADSCALE_API = os.environ.get('HEADSCALE_API', '').strip()
LISTEN_HOST = os.environ.get('LISTEN_HOST', '0.0.0.0')
LISTEN_PORT = int(os.environ.get('LISTEN_PORT', '8091'))

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stdout.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), fmt % args))

    def _send_json(self, status, obj):
        data = json.dumps(obj).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if '/tailnet/-/devices' not in self.path:
            self._send_json(404, {'error': 'not found'})
            return
        auth = self.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            self._send_json(401, {'error': 'missing bearer token'})
            return
        token = auth.split(' ', 1)[1].strip()
        if not token:
            self._send_json(401, {'error': 'empty token'})
            return
        if not HEADSCALE_API:
            self._send_json(500, {'error': 'not_configured', 'detail': 'set HEADSCALE_API to your Headscale nodes endpoint, e.g. https://headscale.example.com/api/v1/node'})
            return
        req = Request(HEADSCALE_API, headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'User-Agent': 'hs2ts-adapter/1.0'})
        try:
            with urlopen(req, timeout=30) as resp:
                body = resp.read()
                hs = json.loads(body.decode('utf-8'))
        except HTTPError as e:
            try:
                err = e.read().decode('utf-8', errors='replace')
            except Exception:
                err = str(e)
            self._send_json(e.code, {'error': 'headscale_error', 'detail': err})
            return
        except URLError as e:
            self._send_json(502, {'error': 'upstream_unreachable', 'detail': str(e)})
            return
        except Exception as e:
            self._send_json(500, {'error': 'internal_error', 'detail': str(e)})
            return
        devices = []
        nodes = hs.get('nodes', []) if isinstance(hs, dict) else []
        for n in nodes:
            if not isinstance(n, dict):
                continue
            hostname = n.get('givenName') or n.get('name') or ''
            addresses = n.get('ipAddresses') or []
            if not isinstance(addresses, list):
                addresses = []
            devices.append({'id': n.get('id'), 'name': n.get('name') or hostname, 'hostname': hostname, 'addresses': addresses, 'os': '', 'lastSeen': n.get('lastSeen'), 'online': n.get('online')})
        self._send_json(200, {'devices': devices})

if __name__ == '__main__':
    server = HTTPServer((LISTEN_HOST, LISTEN_PORT), Handler)
    print(f'hs2ts-adapter listening on {LISTEN_HOST}:{LISTEN_PORT}', file=sys.stderr)
    server.serve_forever()
