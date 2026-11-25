#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Flow2API client: generate images and videos from the command line. Python 3.9+, standard library only.

  flow2api.py check                         GET /v1/models, /v1/models/aliases, /v1beta/models (free, read-only)
  flow2api.py models                        print the registered model table (local)
  flow2api.py image  "prompt" [--ref a.png ...] [--model M] [--aspect 9:16] [--size 2K] [--out DIR] [--name N]
  flow2api.py video  "prompt" [--mode t2v|i2v|r2v|auto|extend|edit] [--ref first.png [last.png]] [--source MEDIA_ID]
                     [--model M] [--aspect 16:9] [--duration 8] [--out DIR] [--name N]
  flow2api.py batch  jobs.jsonl [--parallel N]   one JSON job per line: {"kind":"image","prompt":...,"ref":[...],...}
  flow2api.py jobs   list | get ID | fetch ID --out DIR --name N | cancel ID

Transport: generations go through the job API by default (POST /v1/jobs with an Idempotency-Key made from the
request body, then GET /v1/jobs/{id}). Running the same command again after a timeout or an interrupted run
returns the original job instead of paying twice (jobs are kept 7 days); --new forces a fresh generation.
Job results carry no Flow media ID, so use --transport stream for a video you plan to extend or edit later.
Servers without /v1/jobs fall back to the streaming chat route automatically.

Config (never printed): FLOW2API_BASE_URL (default http://localhost:8000, no /v1) and FLOW2API_API_KEY.
Each value is looked up in this order: the environment variable, then CLAUDE_PLUGIN_OPTION_<NAME> (set by a
Claude Code plugin's userConfig, optional), then ~/.config/flow2api/env (KEY=value lines, chmod 600).
Every image/video call is a paid generation: run it only when the user asked for it. POSTs are never retried
automatically except on HTTP 429 / quota / reCAPTCHA errors (Retry-After when given, else 5, 15, 45 s); a spent
monthly credit budget (credit_budget_exceeded) and a model outside the key's allow-list (403) are never retried.
"""
import argparse, base64, datetime, hashlib, json, mimetypes, os, pathlib, random, re, sys, threading, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

DEFAULT_ROOT = "http://localhost:8000"
CONF_FILE = pathlib.Path.home() / ".config" / "flow2api" / "env"

IMAGE_MODELS = {m: {"aspect": ["16:9", "9:16", "1:1", "4:3", "3:4"], "size": ["1K", "2K", "4K"]}
                for m in ("gemini-3.0-pro-image", "gemini-3.1-flash-image", "gemini-3.1-flash-lite-image")}
# video: model -> mode -> (aspects, durations, (min_refs, max_refs), default_duration). Rows copied from the server's
# model_parameters registry; only combinations inside one row are registered.
_AR = ["16:9", "9:16"]
_VEO = {"t2v": (_AR, [4, 6, 8], (0, 0), 8), "i2v": (_AR, [4, 6], (1, 2), 4), "r2v": (_AR, [8], (1, 3), 8)}
VIDEO_MODELS = {
    "veo-3.1-fast": dict(_VEO), "veo-3.1-lite": dict(_VEO),
    "veo-3.1-quality": {k: v for k, v in _VEO.items() if k != "r2v"},
    "omni-1.1-flash": {"auto": (_AR, [4, 6, 8, 10], (0, 7), 8)},
    "omni-1.2-flash": {"auto": (_AR, list(range(3, 16)), (0, 10), 8),
                       "extend": (_AR, list(range(3, 11)), (0, 0), 8),    # appends durationSeconds to a kept source
                       "edit": (_AR, list(range(3, 16)), (0, 0), 8)},     # durationSeconds = source length
}
SOURCE_MODES = ("extend", "edit")         # need a Flow media ID from an earlier streamed result
DEFAULT_VIDEO_MODEL = "omni-1.2-flash"    # keeps working after the 2026-12-05 retirements
RETIRES = {"veo-3.1-fast": "2026-12-05", "veo-3.1-quality": "2026-12-05", "omni-1.1-flash": "2026-12-05"}
OMNI12_PLUS_FROM = 11    # omni-1.2-flash 11–15 s needs a Google AI Plus/Pro/Ultra plan on the server account
MAX_PAR = {"image": int(os.environ.get("FLOW2API_MAX_PARALLEL_IMAGE", 9)), "video": int(os.environ.get("FLOW2API_MAX_PARALLEL_VIDEO", 6))}
_SEM = {k: threading.Semaphore(v) for k, v in MAX_PAR.items()}
MAX_REF_BYTES = 20 * 1024 * 1024


class Flow2APIError(Exception):
    def __init__(self, msg, status=None, retryable=False, retry_after=None, code=None):
        super().__init__(msg); self.status = status; self.retryable = retryable; self.retry_after = retry_after; self.code = code


# ---------------- config ----------------
def load_config():
    vals = {}
    if CONF_FILE.exists():
        for line in CONF_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); vals[k.strip()] = v.strip().strip('"').strip("'")

    def pick(name):   # plain env var > plugin userConfig option > config file
        return os.environ.get(name) or os.environ.get("CLAUDE_PLUGIN_OPTION_" + name) or vals.get(name) or ""
    root = pick("FLOW2API_BASE_URL") or DEFAULT_ROOT
    key = pick("FLOW2API_API_KEY")
    root = root.rstrip("/")
    if root.endswith("/v1"):
        root = root[:-3]
    return root, key


def redact(text, key):
    return text.replace(key, "***") if key else text


# ---------------- validation ----------------
def validate_image(model, aspect, size, refs):
    if model not in IMAGE_MODELS:
        raise Flow2APIError("Unknown image model %r. Choose one of: %s" % (model, ", ".join(IMAGE_MODELS)))
    spec = IMAGE_MODELS[model]
    if aspect not in spec["aspect"]:
        raise Flow2APIError("aspect %s not registered for %s (allowed %s)" % (aspect, model, spec["aspect"]))
    if size not in spec["size"]:
        raise Flow2APIError("size %s not registered for %s (allowed %s)" % (size, model, spec["size"]))


def check_retirement(model, today=None):
    """Retired models answer HTTP 400 on the server; fail early and warn while the date is near."""
    day = RETIRES.get(model)
    if not day:
        return None
    today = today or datetime.datetime.now(datetime.timezone.utc).date()
    if today >= datetime.date.fromisoformat(day):
        raise Flow2APIError("%s was retired by Flow on %s. Use %s or veo-3.1-lite." % (model, day, DEFAULT_VIDEO_MODEL))
    return "%s retires on %s; prefer %s or veo-3.1-lite." % (model, day, DEFAULT_VIDEO_MODEL)


def video_defaults(model, mode):
    if model not in VIDEO_MODELS:
        raise Flow2APIError("Unknown video model %r. Choose one of: %s" % (model, ", ".join(VIDEO_MODELS)))
    modes = VIDEO_MODELS[model]
    mode = mode or ("auto" if "auto" in modes else "t2v")
    if mode not in modes:
        raise Flow2APIError("mode %s not registered for %s (allowed %s)" % (mode, model, list(modes)))
    return mode, modes[mode][3]


def validate_video(model, mode, aspect, duration, nrefs, source_id, today=None):
    check_retirement(model, today)
    mode, _ = video_defaults(model, mode)
    aspects, durations, (lo, hi), _ = VIDEO_MODELS[model][mode]
    if aspect not in aspects:
        raise Flow2APIError("aspect %s not registered for %s/%s (allowed %s)" % (aspect, model, mode, aspects))
    if duration not in durations:
        raise Flow2APIError("duration %s s not registered for %s/%s/%s (allowed %s)" % (duration, model, mode, aspect, durations))
    if not (lo <= nrefs <= hi):
        raise Flow2APIError("%s/%s takes %d–%d images, got %d" % (model, mode, lo, hi, nrefs))
    if mode in SOURCE_MODES and not re.fullmatch(r"[A-Za-z0-9_\-:.]+(\?project=[A-Za-z0-9_\-:.]+)?", source_id or ""):
        raise Flow2APIError("%s needs --source <data-media-id> kept from an earlier streamed result "
                            "(MEDIA_ID?project=PROJECT_ID for a video made elsewhere); not a chat id, URL or file" % mode)
    if mode not in SOURCE_MODES and source_id:
        raise Flow2APIError("--source only works with --mode extend or edit")
    return mode


# ---------------- request building ----------------
def image_part(ref):
    if re.match(r"^https://", ref):
        return {"type": "image_url", "image_url": {"url": ref}}
    p = pathlib.Path(ref).expanduser()
    if not p.is_file():
        raise Flow2APIError("reference image not found: %s" % ref)
    mime = mimetypes.guess_type(p.name)[0] or ""
    if mime not in ("image/png", "image/jpeg", "image/webp", "image/gif"):
        raise Flow2APIError("reference must be PNG/JPEG/WebP/GIF: %s" % ref)
    data = p.read_bytes()
    if len(data) > MAX_REF_BYTES:
        raise Flow2APIError("reference too large (%d MB > 20 MB): %s" % (len(data) >> 20, ref))
    return {"type": "image_url", "image_url": {"url": "data:%s;base64,%s" % (mime, base64.b64encode(data).decode("ascii"))}}


def build_body(kind, prompt, model, refs, cfg, source_id=None, stream=True):
    if not (prompt or "").strip():
        raise Flow2APIError("prompt is empty")
    parts = [image_part(r) for r in refs]
    if source_id:
        parts.append({"type": "image_url", "image_url": {"url": "extend://" + source_id}})
    content = prompt if not parts else [{"type": "text", "text": prompt}] + parts
    gc = {"imageConfig": cfg} if kind == "image" else {"videoConfig": cfg}
    return {"model": model, "messages": [{"role": "user", "content": content}], "stream": stream, "generationConfig": gc}


# ---------------- HTTP + SSE ----------------
def _error_fields(raw):
    """(message, code, retry_after) from {detail}, an OpenAI error envelope or a Gemini error."""
    try:
        j = json.loads(raw)
        if isinstance(j, dict):
            if "detail" in j:
                return str(j["detail"]), None, None
            e = j.get("error")
            if isinstance(e, dict):
                code = e.get("code") if isinstance(e.get("code"), str) else e.get("status")
                return str(e.get("message") or e), code, e.get("retry_after")
            if e:
                return str(e), None, None
    except Exception:
        pass
    return raw[:500], None, None


def _error_message(status, raw):
    return _error_fields(raw)[0]


HINT = {401: "Check FLOW2API_API_KEY (generation key).", 403: "The account, the key or the model is not permitted.",
        400: "Invalid model/mode/image combination, a retired model, or the prompt is missing.", 422: "A field in the body has the wrong type.",
        409: "This Idempotency-Key was already used with a different body; pass --new.",
        429: "Rate limited or the server queue is full.", 502: "Upstream error.", 503: "The server is out of tokens or not ready.", 504: "Upstream timed out."}
CODE_HINT = {"model_not_allowed": "This API key is not allowed to use this model; ask the server admin or pick a model listed by `check`.",
             "credit_budget_exceeded": "This key's monthly credit budget is spent; it resets on the 1st (UTC). Not retrying.",
             "server_busy": "Every Flow account is busy and the server queue is full.",
             "too_many_jobs": "The server is already running its maximum number of jobs."}
NEVER_RETRY = {"credit_budget_exceeded", "model_not_allowed", "PERMISSION_DENIED", "idempotency_key_reused"}


def _retryable(status, msg, code=None):
    if code in NEVER_RETRY:
        return False
    return status == 429 or bool(re.search(r"recaptcha evaluation failed|quota|rate limit", msg or "", re.I))


def _http_error(e, key):
    """Flow2APIError from a urllib HTTPError: message, code, hint, Retry-After; the key is redacted."""
    raw = redact(e.read().decode("utf-8", "replace"), key); msg, code, ra = _error_fields(raw)
    try:
        ra = float(e.headers.get("Retry-After") or ra) if (e.headers.get("Retry-After") or ra) is not None else None
    except (TypeError, ValueError):
        ra = None
    hint = CODE_HINT.get(code) or HINT.get(e.code, "")
    return Flow2APIError("HTTP %d%s: %s %s" % (e.code, " " + code if code else "", msg, hint), e.code,
                         _retryable(e.code, msg, code), ra, code)


def parse_sse(chunks):
    """Yield ('progress', text) | ('content', text) | ('media_id', id) | ('done', None) from byte chunks.
    Handles frames split across chunks, CRLF, a last frame without a trailing blank line, and errors inside a 200 stream."""
    buf = ""; dec = __import__("codecs").getincrementaldecoder("utf-8")()
    done = False

    def frame(block):
        nonlocal done
        data = "\n".join(l[5:].lstrip(" ") if l.startswith("data:") else "" for l in re.split(r"\r?\n", block) if l.startswith("data:"))
        if not data:
            return []
        if data.strip() == "[DONE]":
            done = True; return [("done", None)]
        ev = json.loads(data)
        if ev.get("error"):
            e = ev["error"]; m = e.get("message") if isinstance(e, dict) else str(e)
            st = e.get("status_code") if isinstance(e, dict) else None; code = e.get("code") if isinstance(e, dict) else None
            raise Flow2APIError("error inside the stream: %s" % m, st, _retryable(st, m, code),
                                e.get("retry_after") if isinstance(e, dict) else None, code)
        out = []
        for ch in ev.get("choices") or []:
            d = ch.get("delta") or {}
            if isinstance(d.get("reasoning_content"), str) and d["reasoning_content"]:
                out.append(("progress", d["reasoning_content"]))
            if isinstance(d.get("content"), str) and d["content"]:
                out.append(("content", d["content"]))
                for mid in re.findall(r'data-media-id\s*=\s*["\']([^"\']+)', d["content"]):
                    out.append(("media_id", mid))
        return out

    for chunk in chunks:
        buf += dec.decode(chunk)
        while True:
            m = re.search(r"\r?\n\r?\n", buf)
            if not m:
                break
            block, buf = buf[:m.start()], buf[m.end():]
            for ev in frame(block):
                yield ev
            if done:
                return
    buf += dec.decode(b"", final=True)
    if buf.strip():
        for ev in frame(buf):
            yield ev


def extract_media(content):
    """Return (kind, url, media_id) from final content: Markdown image or <video src> (maybe in a code fence)."""
    mid = None
    m = re.search(r'data-media-id\s*=\s*["\']([^"\']+)', content)
    if m:
        mid = m.group(1)
    m = re.search(r"!\[[^\]]*\]\(([^\s)]+)\)", content)
    if m:
        return "image", m.group(1), mid
    m = re.search(r"<video\b[^>]*\bsrc\s*=\s*(['\"])(.*?)\1", content, re.I | re.S)
    if m:
        return "video", m.group(2), mid
    raise Flow2APIError("no media found in the result: %s" % content[:300])


def safe_url(url, root):
    if url.startswith("data:"):
        if not re.match(r"^data:image/(png|jpeg|webp|gif);base64,[A-Za-z0-9+/=]+$", url) or len(url) > 30_000_000:
            raise Flow2APIError("invalid data URI")
        return url
    full = urllib.parse.urljoin(root + "/", url)
    p = urllib.parse.urlparse(full)
    if p.scheme not in ("http", "https"):
        raise Flow2APIError("URL scheme not allowed: %s" % p.scheme)
    return full


def download(url, dest, key, root):
    url = safe_url(url, root)
    if url.startswith("data:"):
        dest.write_bytes(base64.b64decode(url.split(",", 1)[1])); return dest
    req = urllib.request.Request(url)
    if urllib.parse.urlparse(url).netloc == urllib.parse.urlparse(root).netloc:
        req.add_header("Authorization", "Bearer " + key)
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "wb") as f:
        while True:
            b = r.read(1 << 16)
            if not b:
                break
            f.write(b)
    return dest


def post_stream(root, key, body, on_progress, timeout=3600, opener=None):
    req = urllib.request.Request(root + "/v1/chat/completions", data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json", "Accept": "text/event-stream"})
    try:
        resp = (opener or urllib.request.urlopen)(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        raise _http_error(e, key)
    ctype = resp.headers.get("Content-Type", "")
    if "text/event-stream" not in ctype:   # server answered without streaming
        j = json.loads(resp.read().decode("utf-8"))
        if j.get("error"):
            raise Flow2APIError(_error_message(200, json.dumps(j)), retryable=_retryable(None, str(j["error"])))
        return j["choices"][0]["message"]["content"], None
    content, mid, saw_done = "", None, False
    for kind, val in parse_sse(iter(lambda: resp.read1(8192) if hasattr(resp, "read1") else resp.read(8192), b"")):
        if kind == "progress":
            on_progress(val)
        elif kind == "content":
            content += val
        elif kind == "media_id":
            mid = val
        elif kind == "done":
            saw_done = True
    if not saw_done:
        raise Flow2APIError("stream ended before [DONE]; check the result on the server before sending again")
    if not content.strip():
        raise Flow2APIError("no final media content")
    return content, mid


class NoJobAPI(Exception):
    """The server has no /v1/jobs route (older Flow2API); use the streaming route instead."""


def idempotency_key(body, nonce=""):
    """Same request body -> same key, so a re-run replays the original job instead of paying again."""
    h = hashlib.sha256((json.dumps(body, sort_keys=True, ensure_ascii=False) + nonce).encode("utf-8")).hexdigest()
    return "f2a-" + h[:60]


def _json_request(method, url, key, body=None, headers=None, timeout=60, opener=None):
    h = {"Authorization": "Bearer " + key, "Accept": "application/json"}
    if body is not None:
        h["Content-Type"] = "application/json"
    h.update(headers or {})
    req = urllib.request.Request(url, data=None if body is None else json.dumps(body).encode("utf-8"), method=method, headers=h)
    try:
        with (opener or urllib.request.urlopen)(req, timeout=timeout) as r:
            return r.status, dict(r.headers), json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        if e.code in (404, 405) and method == "POST" and url.endswith("/v1/jobs"):
            raise NoJobAPI()
        raise _http_error(e, key)


def job_error(job):
    e = job.get("error") or {}
    msg = e.get("message") if isinstance(e, dict) else str(e)
    code = e.get("code") if isinstance(e, dict) else None
    st = e.get("status_code") if isinstance(e, dict) else None
    return Flow2APIError("job %s %s%s: %s" % (job.get("id"), job.get("status"), " " + code if code else "", msg or "no detail"),
                         st, _retryable(st, msg or "", code) or code == "server_restarted", e.get("retry_after") if isinstance(e, dict) else None, code)


def run_job(root, key, body, on_progress, record=None, nonce="", timeout=3600, poll=5, opener=None, sleep=time.sleep):
    """POST /v1/jobs with an Idempotency-Key, then poll until it ends. Returns (content, output_url, job)."""
    status, headers, job = _json_request("POST", root + "/v1/jobs", key, {**body, "stream": False},
                                         {"Idempotency-Key": idempotency_key(body, nonce)}, opener=opener)
    if record:
        record.write_text(json.dumps({"job_id": job.get("id"), "model": body.get("model"), "submitted": time.strftime("%Y-%m-%dT%H:%M:%S")}), encoding="utf-8")
    on_progress("job %s %s%s" % (job.get("id"), job.get("status"), " (replayed: no new charge)" if headers.get("Idempotent-Replayed") == "true" else ""))
    t0, last = time.time(), job.get("status")
    while job.get("status") in ("queued", "running"):
        if time.time() - t0 > timeout:
            raise Flow2APIError("job %s still %s after %d s; fetch it later with `jobs fetch %s` (not cancelled)" % (job.get("id"), job.get("status"), timeout, job.get("id")))
        try:
            wait = float(headers.get("Retry-After") or poll)
        except ValueError:
            wait = poll
        sleep(max(1.0, wait))
        status, headers, job = _json_request("GET", root + "/v1/jobs/" + urllib.parse.quote(job["id"]), key, opener=opener)
        if job.get("status") != last:
            last = job.get("status"); on_progress("job %s %s" % (job.get("id"), last))
    if job.get("status") != "succeeded":
        raise job_error(job)
    res = job.get("result") or {}
    content = ((res.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    return content, job.get("output_url"), job


def generate(kind, body, out_dir, name, root, key, quiet=False, transport="jobs", nonce="", sleep=time.sleep):
    """Run one paid generation with the per-kind concurrency limit and 429 backoff. Returns metadata dict."""
    out_dir = pathlib.Path(out_dir).expanduser(); out_dir.mkdir(parents=True, exist_ok=True)
    log = (lambda s: None) if quiet else (lambda s: print("  … " + s.strip()[:160], file=sys.stderr, flush=True))
    stem = name or time.strftime("%Y%m%d-%H%M%S") + "-" + kind
    delays = [5, 15, 45]; job = None; content = ""; mid = None; out_url = None
    with _SEM[kind]:
        for attempt in range(len(delays) + 1):
            try:
                if transport == "jobs":
                    try:
                        content, out_url, job = run_job(root, key, body, log, out_dir / (stem + ".job.json"), nonce, sleep=sleep)
                        break
                    except NoJobAPI:
                        log("server has no /v1/jobs; using the streaming route"); transport = "stream"
                content, mid = post_stream(root, key, body, log)
                break
            except Flow2APIError as e:
                if e.retryable and attempt < len(delays):
                    d = (float(e.retry_after) + random.uniform(0, 2)) if e.retry_after else delays[attempt] * random.uniform(0.8, 1.3)
                    print("  rate limit/quota, retrying in %.0f s (%s)" % (d, e), file=sys.stderr); sleep(d); continue
                raise
    return save_result(kind, body, content, out_url, mid, out_dir, stem, root, key, job)


def save_result(kind, body, content, out_url, mid, out_dir, stem, root, key, job=None):
    try:
        mkind, url, mid2 = extract_media(content or "")
    except Flow2APIError:
        if not out_url:
            raise Flow2APIError("no final media content: %s" % (content or "")[:300])
        mkind, url, mid2 = ("video" if re.search(r"\.mp4|/video", out_url, re.I) else kind), out_url, None
    mid = mid or mid2
    body = body or {"model": (job or {}).get("model"), "generationConfig": None, "messages": [{"content": ""}]}
    ext = ".mp4" if mkind == "video" else (".png" if ".png" in url.lower() or url.startswith("data:image/png") else ".jpg" if re.search(r"\.jpe?g|image/jpeg", url, re.I) else ".png")
    dest = download(url, out_dir / (stem + ext), key, root)
    head = dest.read_bytes()[:12]   # trust the bytes, not the URL: CDN links have no extension
    real = ".jpg" if head[:3] == b"\xff\xd8\xff" else ".png" if head[:8] == b"\x89PNG\r\n\x1a\n" else ".webp" if head[8:12] == b"WEBP" else ".gif" if head[:4] == b"GIF8" else ext
    if mkind == "image" and real != dest.suffix:
        dest = dest.rename(dest.with_suffix(real))
    meta = {"file": str(dest), "kind": mkind, "model": body["model"], "generationConfig": body["generationConfig"],
            "prompt": body["messages"][0]["content"] if isinstance(body["messages"][0]["content"], str) else body["messages"][0]["content"][0]["text"],
            "media_id": mid, "job_id": (job or {}).get("id"), "source_url": url if not url.startswith("data:") else "data-uri",
            "time": time.strftime("%Y-%m-%dT%H:%M:%S")}
    (out_dir / (stem + ".json")).write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return meta


# ---------------- commands ----------------
def cmd_check(a):
    root, key = load_config()
    print("root:", root, "| key:", "set" if key else "NOT SET")
    if not key:
        print("Set FLOW2API_API_KEY in the environment or in %s, then run this again." % CONF_FILE); return 2
    listed = {}
    for path, hdr in (("/v1/models", {"Authorization": "Bearer " + key}), ("/v1/models/aliases", {"Authorization": "Bearer " + key}),
                      ("/v1beta/models", {"x-goog-api-key": key})):
        req = urllib.request.Request(root + path, headers=hdr)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    j = json.loads(r.read().decode("utf-8"))
                items = (j.get("data") or j.get("models") or []) if isinstance(j, dict) else []
                ids = [(m.get("id") or m.get("name", "").split("/")[-1]) for m in items]
                for m in items:
                    listed[m.get("id") or m.get("name", "").split("/")[-1]] = str(m.get("description") or m.get("displayName") or "")
                print("%s: OK, %d entries%s" % (path, len(ids), (": " + ", ".join(ids[:12]) + (" …" if len(ids) > 12 else "")) if ids else ""))
                break
            except urllib.error.HTTPError as e:
                print("%s: HTTP %d %s" % (path, e.code, redact(_error_message(e.code, e.read().decode("utf-8", "replace")), key))); break
            except Exception as e:
                if attempt == 2:
                    print("%s: connection error: %s" % (path, e))
                time.sleep(1 + attempt)
    if listed:   # which of the short families this key can see (a per-client key may be limited to some models)
        fams = list(IMAGE_MODELS) + list(VIDEO_MODELS)
        print("families visible to this key: " + ", ".join(f for f in fams if f in listed))
        missing = [f for f in fams if f not in listed]
        if missing:
            print("not listed (no access, retired or unknown to this server): " + ", ".join(missing))
        for f in fams:
            m = re.search(r"\(retires ([0-9-]+)\)", listed.get(f, ""))
            if m:
                print("  %s retires %s" % (f, m.group(1)))
    req = urllib.request.Request(root + "/v1/jobs?limit=1", headers={"Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=20):
            print("/v1/jobs: available (generations use the job API with idempotent retries)")
    except urllib.error.HTTPError as e:
        print("/v1/jobs: HTTP %d, generations will use the streaming route" % e.code)
    except Exception as e:
        print("/v1/jobs: connection error: %s" % e)
    return 0


def cmd_models(a):
    print("IMAGE (aspect × size; reference images: 0 or more):")
    for m, s in IMAGE_MODELS.items():
        print("  %-28s aspect %s | size %s" % (m, ",".join(s["aspect"]), ",".join(s["size"])))
    print("VIDEO (mode: aspect | seconds | number of images):")
    for m, modes in VIDEO_MODELS.items():
        for mode, (asp, dur, (lo, hi), dflt) in modes.items():
            extra = " (needs --source)" if mode in SOURCE_MODES else ""
            ret = " | retires %s" % RETIRES[m] if m in RETIRES else ""
            print("  %-16s %-6s %s | %s s | %d–%d images%s | default %d s%s" % (m, mode, ",".join(asp), ",".join(map(str, dur)), lo, hi, extra, dflt, ret))
    print("omni-1.2-flash 11–15 s needs a Google AI Plus/Pro/Ultra plan. Default video model: %s." % DEFAULT_VIDEO_MODEL)
    print("Parallel limit: image %d, video %d (FLOW2API_MAX_PARALLEL_IMAGE/VIDEO)" % (MAX_PAR["image"], MAX_PAR["video"]))
    return 0


def job_image(j):
    model = j.get("model") or "gemini-3.1-flash-image"; aspect = j.get("aspect") or "16:9"; size = j.get("size") or "1K"
    refs = j.get("ref") or []
    validate_image(model, aspect, size, refs)
    return "image", build_body("image", j["prompt"], model, refs, {"aspectRatio": aspect, "imageSize": size})


def job_video(j):
    model = j.get("model") or DEFAULT_VIDEO_MODEL
    mode, dflt = video_defaults(model, j.get("mode"))
    aspect = j.get("aspect") or "16:9"; duration = int(j.get("duration") or dflt); refs = j.get("ref") or []
    source = j.get("source") or j.get("extend")     # "extend" is the old name of the same field
    mode = validate_video(model, mode, aspect, duration, len(refs), source)
    return "video", build_body("video", j["prompt"], model, refs, {"durationSeconds": duration, "aspectRatio": aspect, "mode": mode}, source)


def job_notes(j):
    """Warnings shown before sending: retirement dates, Omni 1.2 long clips, jobs without a media ID."""
    notes = []
    if j.get("kind") == "video":
        model = j.get("model") or DEFAULT_VIDEO_MODEL
        w = check_retirement(model)
        if w:
            notes.append(w)
        if model == "omni-1.2-flash" and int(j.get("duration") or 8) >= OMNI12_PLUS_FROM:
            notes.append("omni-1.2-flash 11–15 s needs a Google AI Plus/Pro/Ultra plan on the server account.")
        if (j.get("transport") or "jobs") == "jobs":
            notes.append("job results carry no Flow media ID; use --transport stream if you will extend or edit this video.")
    return notes


def run_one(j, root, key, quiet=False, sleep=time.sleep):
    kind, body = (job_image if j.get("kind", "image") == "image" else job_video)(j)
    if not quiet:
        for n in job_notes(j):
            print("  note: " + n, file=sys.stderr)
    return generate(kind, body, j.get("out") or "flow2api-out", j.get("name"), root, key, quiet,
                    j.get("transport") or "jobs", "%f" % time.time() if j.get("new") else "", sleep)


def cmd_gen(a, kind):
    root, key = load_config()
    if not key:
        print("FLOW2API_API_KEY is missing (environment or %s)." % CONF_FILE, file=sys.stderr); return 2
    j = {"kind": kind, "prompt": a.prompt, "model": a.model, "aspect": a.aspect, "ref": a.ref or [], "out": a.out, "name": a.name}
    if kind == "image":
        j["size"] = a.size
    else:
        j.update(mode=a.mode, duration=a.duration, source=a.source)
    j.update(transport=a.transport, new=a.new)
    if a.prompt_file:
        j["prompt"] = pathlib.Path(a.prompt_file).read_text(encoding="utf-8")
    try:
        meta = run_one(j, root, key)
    except Flow2APIError as e:
        print("ERROR: " + redact(str(e), key), file=sys.stderr); return 1
    print(json.dumps(meta, ensure_ascii=False, indent=1)); return 0


def cmd_jobs(a):
    root, key = load_config()
    if not key:
        print("FLOW2API_API_KEY is missing.", file=sys.stderr); return 2
    try:
        if a.action == "list":
            _, _, j = _json_request("GET", root + "/v1/jobs?limit=%d" % a.limit, key)
            for job in j.get("data", []):
                err = job.get("error"); detail = job.get("output_url") or (err.get("message", "") if isinstance(err, dict) else err or "")
                print("%s  %-9s %-28s %s %s" % (job.get("id"), job.get("status"), job.get("model"), job.get("created"), detail))
            return 0
        if not a.id:
            print("jobs %s needs a job id" % a.action, file=sys.stderr); return 2
        path = root + "/v1/jobs/" + urllib.parse.quote(a.id)
        if a.action == "cancel":
            _, _, job = _json_request("DELETE", path, key)
            print("job %s: %s. Work already sent to Flow cannot be recalled and may still be charged." % (a.id, job.get("status"))); return 0
        _, _, job = _json_request("GET", path, key)
        if a.action == "get":
            print(json.dumps({k: v for k, v in job.items() if k != "result"}, ensure_ascii=False, indent=1)); return 0
        if job.get("status") != "succeeded":   # fetch
            print("job %s is %s; nothing to download yet" % (a.id, job.get("status")), file=sys.stderr); return 1
        res = job.get("result") or {}
        content = ((res.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        out = pathlib.Path(a.out).expanduser(); out.mkdir(parents=True, exist_ok=True)
        meta = save_result("image", None, content, job.get("output_url"), None, out, a.name or a.id, root, key, job)
        print(json.dumps(meta, ensure_ascii=False, indent=1)); return 0
    except Flow2APIError as e:
        print("ERROR: " + redact(str(e), key), file=sys.stderr); return 1


def cmd_batch(a):
    root, key = load_config()
    if not key:
        print("FLOW2API_API_KEY is missing.", file=sys.stderr); return 2
    jobs = [json.loads(l) for l in pathlib.Path(a.jobs).read_text(encoding="utf-8").splitlines() if l.strip()]
    for j in jobs:   # validate everything before sending anything
        j.setdefault("transport", a.transport)
        (job_image if j.get("kind", "image") == "image" else job_video)(j)
    for n in sorted({n for j in jobs for n in job_notes(j)}):
        print("note: " + n, file=sys.stderr)
    results = [None] * len(jobs)

    def work(i):
        time.sleep(0.4 * i)   # stagger submissions
        try:
            results[i] = run_one(jobs[i], root, key, quiet=True); print("[%d/%d] done: %s" % (i + 1, len(jobs), results[i]["file"]), flush=True)
        except Exception as e:
            results[i] = {"error": redact(str(e), key)}; print("[%d/%d] error: %s" % (i + 1, len(jobs), results[i]["error"]), flush=True)
    with ThreadPoolExecutor(max_workers=max(1, min(a.parallel, MAX_PAR["image"] + MAX_PAR["video"]))) as ex:
        list(ex.map(work, range(len(jobs))))
    ok = sum(1 for r in results if r and "error" not in r)
    print("Finished %d/%d." % (ok, len(jobs)))
    return 0 if ok == len(jobs) else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Flow2API: generate images and videos (every image/video command is one paid generation)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check"); sub.add_parser("models")
    for kind in ("image", "video"):
        p = sub.add_parser(kind)
        p.add_argument("prompt", nargs="?", default="")
        p.add_argument("--prompt-file"); p.add_argument("--model"); p.add_argument("--aspect")
        p.add_argument("--ref", action="append", help="reference image (local file or https URL); repeat the flag, order matters")
        p.add_argument("--out", default="flow2api-out"); p.add_argument("--name")
        p.add_argument("--transport", choices=["jobs", "stream"], default="jobs",
                       help="jobs (default): idempotent job API, safe to re-run; stream: keeps the Flow media ID for extend/edit")
        p.add_argument("--new", action="store_true", help="generate again even if the same request already has a job")
        if kind == "image":
            p.add_argument("--size")
        else:
            p.add_argument("--mode", choices=["t2v", "i2v", "r2v", "auto", "extend", "edit"]); p.add_argument("--duration", type=int)
            p.add_argument("--source", "--extend", dest="source", help="data-media-id of an earlier streamed video (extend/edit)")
    p = sub.add_parser("batch"); p.add_argument("jobs"); p.add_argument("--parallel", type=int, default=3)
    p.add_argument("--transport", choices=["jobs", "stream"], default="jobs")
    p = sub.add_parser("jobs", help="list, inspect, download or cancel server-side jobs")
    p.add_argument("action", choices=["list", "get", "fetch", "cancel"]); p.add_argument("id", nargs="?")
    p.add_argument("--out", default="flow2api-out"); p.add_argument("--name"); p.add_argument("--limit", type=int, default=20)
    a = ap.parse_args(argv)
    if a.cmd == "check":
        return cmd_check(a)
    if a.cmd == "models":
        return cmd_models(a)
    if a.cmd == "batch":
        return cmd_batch(a)
    if a.cmd == "jobs":
        return cmd_jobs(a)
    return cmd_gen(a, a.cmd)


if __name__ == "__main__":
    sys.exit(main())
