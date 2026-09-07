"""Opt-in real CLI serialization probe. Only a loopback error stub; no inference.

CODE_STUDIOS_TEST_CODEX=/absolute/path/to/codex pytest -q tests/test_reasoning_effort_cli_wire.py
The production runner never receives these isolated test-only provider overrides.
"""
import http.server
import json
import os
from pathlib import Path
import subprocess
import threading

import pytest

from test_reasoning_effort import effort, task

CODEX = os.environ.get("CODE_STUDIOS_TEST_CODEX")
pytestmark = pytest.mark.skipif(not CODEX, reason="local CLI wire probe is explicitly opt-in")


@pytest.mark.parametrize("arm,explicit,expected", [
    ("medium", None, "medium"), ("high", None, "high"),
    ("auto", None, "low"), ("auto", "xhigh", "xhigh"),
])
def test_real_cli_serializes_fixed_model_and_selected_effort(tmp_path, arm, explicit, expected):
    received = []

    class Receiver(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"models":[]}')

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            # Capture the wire configuration, not the prompt, credentials or source code.
            received.append({"model": body.get("model"), "reasoning": body.get("reasoning")})
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":{"message":"LOCAL_PROBE_NO_INFERENCE","type":"invalid_request_error"}}')

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Receiver)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        sample = task(prompt="Reply probe", explicit_effort=explicit)
        choice = effort.select(sample, arm=arm)["selected_effort"]
        argv = effort.command(sample["model"], choice, tmp_path, CODEX)
        # Test only: no user/project config, plugins, real inference, or saved session.
        # The temporary empty root is identical for all arms; the model/prompt are fixed.
        provider = {"name": "Local probe", "base_url": f"http://127.0.0.1:{server.server_port}/v1",
                    "wire_api": "responses", "requires_openai_auth": False,
                    "request_max_retries": 0, "stream_max_retries": 0}
        inline = "{" + ",".join(f"{k}={json.dumps(v)}" for k, v in provider.items()) + "}"
        argv[2:2] = ["--ignore-user-config", "--skip-git-repo-check", "--ephemeral",
                     "-c", 'model_provider="effort_probe"',
                     "-c", "model_providers.effort_probe=" + inline,
                     "-c", "model_supports_reasoning=true"]
        completed = subprocess.run(argv, input=sample["prompt"], text=True, encoding="utf-8", capture_output=True,
                                   cwd=tmp_path, timeout=30)
        assert received, completed.stderr + completed.stdout
        assert all(r == {"model": "gpt-5.5", "reasoning": {"effort": expected}} for r in received)
        # Error is deliberate: the stub cannot run or honor model effort.
        assert completed.returncode != 0
        assert "LOCAL_PROBE_NO_INFERENCE" in completed.stdout
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
