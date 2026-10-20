#!/usr/bin/env python3
"""Replay checked-in evaluation results in the original Agent UI (stdlib only)."""

import argparse
import html
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "src/main/resources/static"
FIXTURES = ROOT / "docs/demo/recorded-responses.json"


def load_recordings():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def replay_banner(dataset_version):
    return (
        '<aside role="note" style="background:#fff8e6;border-bottom:1px solid #efd29b;'
        'color:#734c14;padding:12px 20px;text-align:center;font:14px/1.6 Arial,sans-serif">'
        '<strong>历史评测回放 / Recorded replay</strong> · '
        + html.escape(dataset_version)
        + ' · 使用仓库保存的回答与工具轨迹，无需模型或数据库。'
        '</aside>'
    )


class RecordedDemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, recordings, **kwargs):
        self.recordings = recordings
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def _respond(self, status, payload, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._respond(status, data, "application/json; charset=utf-8")

    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path in ("/", "/agent.html"):
            page = (STATIC / "agent.html").read_text(encoding="utf-8")
            page = page.replace("<body>", "<body>" + replay_banner(self.recordings["dataset_version"]), 1)
            # The original second example differs from the frozen benchmark.
            page = page.replace(
                "What is the mode of action of abamectin?",
                self.recordings["examples"][1]["question"],
            )
            self._respond(200, page.encode("utf-8"), "text/html; charset=utf-8")
        elif path.startswith("/ziyuan/"):
            # Serve bundled assets only; never expose repo config, .git or fixtures.
            candidate = (STATIC / path.lstrip("/")).resolve()
            if (STATIC / "ziyuan").resolve() not in candidate.parents or not candidate.is_file():
                self.send_error(404)
                return
            super().do_GET()
        else:
            self.send_error(404)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/agent/query":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 16384:
                raise ValueError("invalid request size")
            request = json.loads(self.rfile.read(length))
            question = request.get("question", "")
            if not isinstance(question, str):
                raise ValueError("invalid question")
            question = question.strip()
        except (ValueError, AttributeError, UnicodeError):
            self._json(400, {"error": "question must be a JSON string"})
            return
        for example in self.recordings["examples"]:
            if question == example["question"]:
                self._json(200, example["response"])
                return
        self._json(400, {"error": "历史回放仅支持页面中的三个示例问题，请点击示例后提交。"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    recordings = load_recordings()
    handler = partial(RecordedDemoHandler, recordings=recordings)
    # Intentionally local-only: this is a preview server, not a production API.
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Recorded replay: http://127.0.0.1:{args.port}/agent.html", flush=True)
    print("Uses saved evaluation outputs; no live LLM/database calls. Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
