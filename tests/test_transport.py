from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "referee"))
from transport import Client, PlayerFault


@pytest.mark.parametrize("body", [b'[]', b'{"action":NaN}', b'{"action":0,"action":1}',
                                   b'\xff', b'{', b'{"action":"' + b'x' * 1_100_000 + b'"}',
                                   b'{"action":' + b'[' * 1500 + b'0' + b']' * 1500 + b'}'], ids=['type','nan','duplicate','encoding','truncated','oversized','depth'])
def test_invalid_http_body(body):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except OSError:
                pass
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with pytest.raises(PlayerFault):
            Client(f"http://127.0.0.1:{server.server_port}").act({}, 100)
    finally:
        server.shutdown()
        server.server_close()


def test_trickle_response_has_total_deadline():
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.send_response(200)
            self.send_header("Content-Length", "500")
            self.end_headers()
            try:
                for _ in range(500):
                    self.wfile.write(b" ")
                    self.wfile.flush()
                    time.sleep(0.02)
            except OSError:
                pass
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    started = time.monotonic()
    try:
        with pytest.raises(PlayerFault):
            Client(f"http://127.0.0.1:{server.server_port}").act({}, 100)
        assert time.monotonic() - started < 0.4
    finally:
        server.shutdown()
        server.server_close()
