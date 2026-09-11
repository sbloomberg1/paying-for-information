import http.client
import json
import queue
import socket
import threading
import time
from urllib.parse import urlsplit


class PlayerFault(Exception):
    pass


def reject(value):
    raise ValueError("invalid response")


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            reject(None)
        result[key] = value
    return result


class Client:
    def __init__(self, url):
        self.url = urlsplit(url)
        if self.url.scheme != "http" or not self.url.hostname or self.url.username:
            raise ValueError("invalid player URL")

    def request(self, path, body, seconds, expected):
        output = queue.Queue(maxsize=1)
        connection = http.client.HTTPConnection(self.url.hostname, self.url.port or 80, timeout=seconds)

        def run():
            try:
                data = json.dumps(body, separators=(",", ":"), allow_nan=False) if body is not None else None
                connection.request("POST" if body is not None else "GET", path, data,
                                   {"Content-Type": "application/json"})
                response = connection.getresponse()
                if response.status != expected:
                    raise ValueError("invalid response")
                raw = response.read(1_048_577)
                if len(raw) > 1_048_576:
                    raise ValueError("invalid response")
                value = json.loads(raw.decode("utf-8"), parse_constant=reject, object_pairs_hook=unique_pairs) if raw else {}
                if not isinstance(value, dict):
                    raise ValueError("invalid response")
                pending = [(value, 0)]
                while pending:
                    item, depth = pending.pop()
                    if depth > 12:
                        raise ValueError("invalid response")
                    if isinstance(item, dict):
                        pending.extend((v, depth + 1) for v in item.values())
                    elif isinstance(item, list):
                        pending.extend((v, depth + 1) for v in item)
                output.put((True, value))
            except (OSError, ValueError, RecursionError, http.client.HTTPException):
                output.put((False, None))
            finally:
                connection.close()

        threading.Thread(target=run, daemon=True).start()
        try:
            ok, value = output.get(timeout=seconds)
        except queue.Empty:
            try:
                if connection.sock:
                    connection.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()
            raise PlayerFault("player unavailable") from None
        if not ok:
            raise PlayerFault("player unavailable")
        return value

    def reset(self, config):
        end = time.monotonic() + 15
        while True:
            try:
                if self.request("/health", None, 0.5, 200).get("ready") is True:
                    break
            except PlayerFault:
                pass
            if time.monotonic() >= end:
                raise PlayerFault("player unavailable")
            time.sleep(0.1)
        self.request("/reset", {"match_id": "market", "player_index": 0, "seed": 0, "config": config}, 1, 204)

    def act(self, observation, deadline_ms):
        response = self.request("/act", {"observation": observation, "deadline_ms": deadline_ms},
                                deadline_ms / 1000, 200)
        if set(response) != {"action"}:
            raise PlayerFault("player unavailable")
        return response["action"]
