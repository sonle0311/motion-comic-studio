# -*- coding: utf-8 -*-
"""Mock tests for flow2api.py. No paid generation: a local fake server answers every request.
Run: python3 test_flow2api.py"""
import datetime, io, json, os, pathlib, sys, tempfile, threading, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import flow2api as F

PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000")


class Fake(BaseHTTPRequestHandler):
    mode = "sse"; last_body = None; last_auth = None
    jobs_enabled = True; jobs = {}; idem = {}; polls = 0; job_mode = "ok"; posts = 0; last_idem = None

    def log_message(self, *a):
        pass

    def _json(self, code, obj, headers=None):
        self.send_response(code); self.send_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers(); self.wfile.write(json.dumps(obj).encode())

    def do_DELETE(self):
        job = Fake.jobs.get(self.path.rsplit("/", 1)[-1])
        if not job:
            return self._json(404, {"error": {"message": "No job", "code": "job_not_found"}})
        job["status"] = "canceled"; self._json(200, {**job, "upstream_cancelled": False})

    def do_GET(self):
        if self.path.startswith("/v1/jobs/"):
            job = Fake.jobs.get(self.path.rsplit("/", 1)[-1])
            if not job:
                return self._json(404, {"error": {"message": "No job", "code": "job_not_found"}})
            Fake.polls += 1
            if job["status"] == "running" and Fake.polls >= 2:
                if Fake.job_mode == "fail":
                    job.update(status="failed", error={"message": "Generation failed", "type": "server_error", "code": "generation_failed", "status_code": 503})
                else:
                    job.update(status="succeeded", output_url="/files/j.png",
                               result={"choices": [{"message": {"content": "![image](/files/j.png)"}}]})
            return self._json(200, job, {"Retry-After": "5"} if job["status"] in ("queued", "running") else None)
        if self.path.startswith("/files/"):
            self.send_response(200); self.send_header("Content-Type", "image/png"); self.end_headers(); self.wfile.write(PNG); return
        if self.headers.get("Authorization") != "Bearer good":
            self.send_response(401); self.end_headers(); self.wfile.write(b'{"detail":"Invalid API key"}'); return
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps({"data": [{"id": "gemini-3.1-flash-image"}]}).encode())

    def do_POST(self):
        Fake.last_auth = self.headers.get("Authorization")
        Fake.last_body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/v1/jobs":
            if not Fake.jobs_enabled:
                return self._json(404, {"detail": "Not Found"})
            Fake.posts += 1; k = self.headers.get("Idempotency-Key"); Fake.last_idem = k
            if Fake.mode == "429":
                return self._json(429, {"error": {"message": "Service busy", "type": "rate_limit_error", "code": "server_busy", "retry_after": 2}}, {"Retry-After": "2"})
            if Fake.mode == "budget":
                return self._json(429, {"error": {"message": "Monthly credit budget spent", "type": "rate_limit_error", "code": "credit_budget_exceeded"}}, {"Retry-After": "86400"})
            if Fake.mode == "403":
                return self._json(403, {"error": {"message": "Model not allowed for this key", "type": "permission_error", "code": "model_not_allowed"}})
            if k and k in Fake.idem:
                return self._json(200, Fake.jobs[Fake.idem[k]], {"Idempotent-Replayed": "true", "Retry-After": "5"})
            jid = "job%d" % (len(Fake.jobs) + 1); Fake.jobs[jid] = {"id": jid, "object": "job", "status": "running", "model": Fake.last_body["model"]}
            if k:
                Fake.idem[k] = jid
            Fake.polls = 0
            return self._json(202, Fake.jobs[jid], {"Location": "/v1/jobs/" + jid, "Retry-After": "5"})
        m = Fake.mode
        if m == "401":
            self.send_response(401); self.end_headers(); self.wfile.write(b'{"detail":"Invalid API key"}'); return
        if m == "422":
            self.send_response(422); self.end_headers(); self.wfile.write(b'{"detail":"durationSeconds must be integer"}'); return
        self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.end_headers()
        if m == "sse_error":
            self.wfile.write(b'data: {"error":{"message":"Generation failed"}}\n\n'); return
        if m == "no_done":
            self.wfile.write(b'data: {"choices":[{"delta":{"reasoning_content":"working"}}]}\n\n'); return
        frames = [b'data: {"choices":[{"delta":{"reasoning_content":"\xe7\x94\x9f\xe6\x88\x90\xe4\xb8\xad"}}]}\r\n\r\n',
                  b'data: {"choices":[{"delta":{"content":"![img](/files/a.png)"}}]}\n\n', b"data: [DONE]"]
        if m == "video":
            frames[1] = b'data: {"choices":[{"delta":{"content":"```html\\n<video src=\\"/files/v.mp4\\" data-media-id=\\"MID123\\" controls></video>\\n```"}}]}\n\n'
        blob = b"".join(frames)
        for i in range(0, len(blob), 7):   # split frames and UTF-8 across chunks
            self.wfile.write(blob[i:i + 7]); self.wfile.flush()


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.root = "http://127.0.0.1:%d" % cls.srv.server_address[1]
        cls.tmp = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def test_config_strips_v1_and_reads_env(self):
        os.environ["FLOW2API_BASE_URL"] = "http://x:8000/proxy/v1/"; os.environ["FLOW2API_API_KEY"] = "k"
        try:
            self.assertEqual(F.load_config(), ("http://x:8000/proxy", "k"))
        finally:
            del os.environ["FLOW2API_BASE_URL"], os.environ["FLOW2API_API_KEY"]

    def test_config_plugin_option_priority(self):
        names = ("FLOW2API_BASE_URL", "FLOW2API_API_KEY")
        saved = {n: os.environ.pop(n, None) for n in names + tuple("CLAUDE_PLUGIN_OPTION_" + n for n in names)}
        conf = F.CONF_FILE; F.CONF_FILE = pathlib.Path(self.tmp) / "env"
        try:
            F.CONF_FILE.write_text("FLOW2API_BASE_URL=http://file:1\nFLOW2API_API_KEY=file-key\n", encoding="utf-8")
            self.assertEqual(F.load_config(), ("http://file:1", "file-key"))
            os.environ["CLAUDE_PLUGIN_OPTION_FLOW2API_BASE_URL"] = "http://plugin:2/v1"
            os.environ["CLAUDE_PLUGIN_OPTION_FLOW2API_API_KEY"] = "plugin-key"
            self.assertEqual(F.load_config(), ("http://plugin:2", "plugin-key"))
            os.environ["FLOW2API_BASE_URL"] = "http://env:3"; os.environ["FLOW2API_API_KEY"] = "env-key"
            self.assertEqual(F.load_config(), ("http://env:3", "env-key"))
            F.CONF_FILE.unlink()
            for n in list(os.environ):
                if n.endswith(names):
                    del os.environ[n]
            self.assertEqual(F.load_config(), (F.DEFAULT_ROOT, ""))
        finally:
            F.CONF_FILE = conf
            for n in saved:
                os.environ.pop(n, None)
                if saved[n] is not None:
                    os.environ[n] = saved[n]

    def test_validation(self):
        F.validate_image("gemini-3.1-flash-image", "9:16", "2K", [])
        with self.assertRaises(F.Flow2APIError):
            F.validate_image("gemini-3.1-flash-image", "21:9", "1K", [])
        self.assertEqual(F.validate_video("veo-3.1-fast", "i2v", "9:16", 6, 2, None), "i2v")
        D = datetime.date(2026, 11, 25)
        for bad in [("veo-3.1-quality", "r2v", "16:9", 8, 1, None), ("veo-3.1-fast", "i2v", "16:9", 8, 1, None),
                    ("veo-3.1-fast", "t2v", "16:9", 8, 1, None), ("omni-1.2-flash", "auto", "16:9", 16, 0, None),
                    ("veo-3.1-fast", "extend", "16:9", 8, 0, "M1"), ("omni-1.1-flash", "auto", "16:9", 8, 8, None),
                    ("omni-1.2-flash", "auto", "16:9", 8, 11, None), ("omni-1.2-flash", "extend", "16:9", 11, 0, "M1"),
                    ("omni-1.2-flash", "extend", "16:9", 8, 0, None), ("omni-1.2-flash", "edit", "16:9", 8, 1, "M1"),
                    ("omni-1.2-flash", "auto", "16:9", 8, 0, "M1"), ("omni-1.2-flash", "edit", "16:9", 8, 0, "https://x/v.mp4")]:
            with self.assertRaises(F.Flow2APIError, msg=str(bad)):
                F.validate_video(*bad, today=D)
        self.assertEqual(F.validate_video("omni-1.2-flash", "auto", "9:16", 15, 3, None, today=D), "auto")
        self.assertEqual(F.validate_video("omni-1.2-flash", "auto", "16:9", 15, 10, None, today=D), "auto")
        self.assertEqual(F.validate_video("omni-1.1-flash", "auto", "16:9", 10, 7, None, today=D), "auto")
        self.assertEqual(F.validate_video("omni-1.2-flash", "extend", "16:9", 10, 0, "M1", today=D), "extend")
        self.assertEqual(F.validate_video("omni-1.2-flash", "edit", "9:16", 15, 0, "M1?project=P2", today=D), "edit")

    def test_retirement(self):
        self.assertIn("2026-12-05", F.check_retirement("veo-3.1-fast", datetime.date(2026, 11, 25)))
        self.assertIsNone(F.check_retirement("veo-3.1-lite", datetime.date(2027, 1, 1)))
        with self.assertRaises(F.Flow2APIError):
            F.validate_video("omni-1.1-flash", "auto", "16:9", 8, 0, None, today=datetime.date(2026, 12, 5))
        self.assertEqual(F.validate_video("veo-3.1-lite", "t2v", "16:9", 8, 0, None, today=datetime.date(2026, 12, 5)), "t2v")
        self.assertEqual(F.job_video({"kind": "video", "prompt": "x"})[1]["model"], "omni-1.2-flash")

    def test_payload_types_and_refs(self):
        p = pathlib.Path(self.tmp) / "r.png"; p.write_bytes(PNG)
        k, body = F.job_video({"kind": "video", "prompt": "x", "model": "veo-3.1-lite", "mode": "i2v", "ref": [str(p)]})
        vc = body["generationConfig"]["videoConfig"]
        self.assertEqual((vc["durationSeconds"], vc["mode"], vc["aspectRatio"]), (4, "i2v", "16:9"))
        self.assertIsInstance(vc["durationSeconds"], int); self.assertNotIn("imageConfig", body["generationConfig"])
        self.assertTrue(body["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,"))
        k, body = F.job_video({"kind": "video", "prompt": "go on", "mode": "extend", "source": "MID123"})
        self.assertEqual(body["messages"][0]["content"][-1]["image_url"]["url"], "extend://MID123")
        self.assertEqual(body["generationConfig"]["videoConfig"], {"durationSeconds": 8, "aspectRatio": "16:9", "mode": "extend"})
        k, body = F.job_video({"kind": "video", "prompt": "orange", "mode": "edit", "duration": 4, "extend": "M9"})   # old field name
        self.assertEqual(body["messages"][0]["content"][-1]["image_url"]["url"], "extend://M9")
        k, body = F.job_image({"prompt": "x", "aspect": "9:16", "size": "2K"})
        self.assertEqual(body["generationConfig"], {"imageConfig": {"aspectRatio": "9:16", "imageSize": "2K"}})
        with self.assertRaises(F.Flow2APIError):
            F.build_body("image", "  ", "gemini-3.1-flash-image", [], {})

    def test_sse_split_crlf_and_last_frame(self):
        blob = 'data: {"choices":[{"delta":{"reasoning_content":"生成中"}}]}\r\n\r\ndata: {"choices":[{"delta":{"content":"A"}}]}\n\ndata: [DONE]'.encode()
        evs = list(F.parse_sse(blob[i:i + 3] for i in range(0, len(blob), 3)))
        self.assertEqual(evs, [("progress", "生成中"), ("content", "A"), ("done", None)])
        with self.assertRaises(F.Flow2APIError):
            list(F.parse_sse([b'data: {"error":{"message":"quota exceeded"}}\n\n']))

    def test_extract_and_safe_url(self):
        self.assertEqual(F.extract_media("![a](https://h/x.png)")[:2], ("image", "https://h/x.png"))
        k, u, mid = F.extract_media('```html\n<video src="/c/v.mp4" data-media-id="M1"></video>\n```')
        self.assertEqual((k, u, mid), ("video", "/c/v.mp4", "M1"))
        with self.assertRaises(F.Flow2APIError):
            F.safe_url("javascript:alert(1)", "http://h")
        with self.assertRaises(F.Flow2APIError):
            F.safe_url("data:text/html;base64,AAAA", "http://h")

    def test_jobs_poll_and_idempotent_rerun(self):
        Fake.mode = "sse"; Fake.jobs_enabled = True; Fake.job_mode = "ok"; Fake.jobs.clear(); Fake.idem.clear(); Fake.posts = 0
        slept = []
        j = {"kind": "image", "prompt": "a lake", "out": self.tmp, "name": "jobimg"}
        meta = F.run_one(dict(j), self.root, "good", quiet=True, sleep=slept.append)
        self.assertEqual(pathlib.Path(meta["file"]).read_bytes(), PNG); self.assertEqual(meta["job_id"], "job1")
        self.assertFalse(Fake.last_body["stream"]); self.assertTrue(Fake.last_idem.startswith("f2a-"))
        self.assertLessEqual(len(Fake.last_idem), 128); self.assertIn(5.0, slept)        # honours Retry-After
        self.assertTrue((pathlib.Path(self.tmp) / "jobimg.job.json").exists())
        first_key = Fake.last_idem
        meta2 = F.run_one(dict(j), self.root, "good", quiet=True, sleep=slept.append)    # same body: replayed, no new job
        self.assertEqual((meta2["job_id"], Fake.last_idem, len(Fake.jobs)), ("job1", first_key, 1))
        F.run_one(dict(j, new=True), self.root, "good", quiet=True, sleep=slept.append)  # --new: a fresh job
        self.assertEqual(len(Fake.jobs), 2)

    def test_job_failure_and_fallback_to_stream(self):
        Fake.jobs_enabled = True; Fake.job_mode = "fail"; Fake.mode = "sse"; Fake.jobs.clear(); Fake.idem.clear()
        with self.assertRaises(F.Flow2APIError) as c:
            F.run_one({"kind": "image", "prompt": "fails", "out": self.tmp}, self.root, "good", quiet=True, sleep=lambda s: None)
        self.assertIn("generation_failed", str(c.exception))
        Fake.job_mode = "ok"; Fake.jobs_enabled = False
        try:
            meta = F.run_one({"kind": "image", "prompt": "old server", "out": self.tmp, "name": "fb"}, self.root, "good", quiet=True)
            self.assertTrue(Fake.last_body["stream"]); self.assertEqual(pathlib.Path(meta["file"]).read_bytes(), PNG)
        finally:
            Fake.jobs_enabled = True

    def test_429_retry_after_budget_and_403(self):
        Fake.jobs_enabled = True; Fake.mode = "429"; Fake.posts = 0; slept = []
        with self.assertRaises(F.Flow2APIError) as c:
            F.run_one({"kind": "image", "prompt": "busy", "out": self.tmp}, self.root, "good", quiet=True, sleep=slept.append)
        self.assertEqual((Fake.posts, c.exception.code), (4, "server_busy"))
        self.assertTrue(all(2 <= d <= 4 for d in slept), slept)                         # waited Retry-After (+ jitter)
        for mode, code in (("budget", "credit_budget_exceeded"), ("403", "model_not_allowed")):
            Fake.mode = mode; Fake.posts = 0; slept = []
            with self.assertRaises(F.Flow2APIError) as c:
                F.run_one({"kind": "image", "prompt": "x", "out": self.tmp}, self.root, "secret-key", quiet=True, sleep=slept.append)
            self.assertEqual((Fake.posts, slept, c.exception.code), (1, [], code)); self.assertNotIn("secret-key", str(c.exception))
        Fake.mode = "sse"

    def test_sse_429_event_is_retryable(self):
        with self.assertRaises(F.Flow2APIError) as c:
            list(F.parse_sse([b'data: {"error":{"message":"queue wait expired","code":"server_busy","status_code":429,"retry_after":7}}\n\n']))
        self.assertTrue(c.exception.retryable); self.assertEqual(c.exception.retry_after, 7)

    def test_end_to_end_image_and_video(self):
        Fake.mode = "sse"
        meta = F.run_one({"kind": "image", "prompt": "a lake", "out": self.tmp, "name": "img", "transport": "stream"}, self.root, "good", quiet=True)
        self.assertEqual(pathlib.Path(meta["file"]).read_bytes(), PNG); self.assertEqual(Fake.last_auth, "Bearer good")
        self.assertTrue(Fake.last_body["stream"])
        Fake.mode = "video"
        meta = F.run_one({"kind": "video", "prompt": "pan", "out": self.tmp, "name": "vid", "transport": "stream"}, self.root, "good", quiet=True)
        self.assertEqual(meta["media_id"], "MID123"); self.assertTrue(meta["file"].endswith(".mp4"))

    def test_errors_do_not_leak_key(self):
        for mode, code in (("401", 401), ("422", 422)):
            Fake.mode = mode
            with self.assertRaises(F.Flow2APIError) as c:
                F.run_one({"kind": "image", "prompt": "x", "out": self.tmp, "transport": "stream"}, self.root, "secret-key", quiet=True)
            self.assertEqual(c.exception.status, code); self.assertNotIn("secret-key", str(c.exception))
        Fake.mode = "sse_error"
        with self.assertRaises(F.Flow2APIError):
            F.run_one({"kind": "image", "prompt": "x", "out": self.tmp, "transport": "stream"}, self.root, "good", quiet=True)
        Fake.mode = "no_done"
        with self.assertRaises(F.Flow2APIError) as c:
            F.run_one({"kind": "image", "prompt": "x", "out": self.tmp, "transport": "stream"}, self.root, "good", quiet=True)
        self.assertIn("[DONE]", str(c.exception))

    def test_retryable_classification(self):
        self.assertTrue(F._retryable(429, "")); self.assertTrue(F._retryable(None, "reCAPTCHA evaluation failed"))
        self.assertFalse(F._retryable(400, "bad mode")); self.assertFalse(F._retryable(401, "Invalid API key"))
        self.assertFalse(F._retryable(429, "", "credit_budget_exceeded")); self.assertFalse(F._retryable(403, "", "model_not_allowed"))

    def test_idempotency_key_is_stable_and_valid(self):
        import re as _re
        b = {"model": "m", "messages": [{"role": "user", "content": "x"}], "generationConfig": {"imageConfig": {"aspectRatio": "1:1", "imageSize": "1K"}}}
        k = F.idempotency_key(b)
        self.assertEqual(k, F.idempotency_key(json.loads(json.dumps(b))))
        self.assertNotEqual(k, F.idempotency_key(b, "nonce"))
        self.assertTrue(_re.fullmatch(r"[A-Za-z0-9._:\-]{1,128}", k))


if __name__ == "__main__":
    unittest.main(verbosity=1)
