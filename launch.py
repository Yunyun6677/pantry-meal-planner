"""Start/reuse the local demo, verify readiness, and optionally open a browser."""
import argparse
import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def healthy(url):
    try:
        with urllib.request.urlopen(url + '/api/health', timeout=1) as response:
            return json.load(response).get('app') == 'pantry-meal-planner'
    except (OSError, ValueError):
        return False


def start(port=8765, open_browser=True):
    url = f'http://127.0.0.1:{port}'
    if not healthy(url):
        with socket.socket() as probe:
            if probe.connect_ex(('127.0.0.1', port)) == 0:
                raise RuntimeError(f'Port {port} is occupied by another service or an older demo. Use --port 8766.')
        logs = ROOT / 'data'
        logs.mkdir(exist_ok=True)
        with (logs / 'server.log').open('ab') as log:
            process = subprocess.Popen(
                [sys.executable, '-u', '-m', 'demo.server', '--port', str(port)],
                cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                start_new_session=sys.platform != 'win32',
            )
        for _ in range(40):
            if healthy(url):
                break
            if process.poll() is not None:
                raise RuntimeError('Server exited. See data/server.log for details.')
            time.sleep(.25)
        else:
            raise RuntimeError('Server not ready. See data/server.log; retry the launcher.')
    if open_browser:
        webbrowser.open(url)
    return url


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-open', action='store_true')
    args = parser.parse_args()
    try:
        print(start(args.port, not args.no_open))
    except (OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
