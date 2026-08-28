#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ÉHON 営業コックピット（ローカル実行版）

ブラウザのフォーム → claude -p "/shodan ..." をこのMacで実行 → 進捗を逐次表示。

  python3 cockpit/server.py
  → http://127.0.0.1:8765

127.0.0.1 にのみバインドする。外部からは接続できない。
シェルを介さず argv で渡すのでコマンドインジェクションは起きない。
"""
import json, os, queue, re, shutil, subprocess, threading, time, uuid, html
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(ROOT, "cockpit")
OUTPUT = os.path.join(ROOT, "output")
# 0.0.0.0 で待ち受けるが、下の許可リストで自分と Tailscale 以外を弾く。
# こうすると iMac 上の localhost と、Tailscale の自分の端末の両方から使える。
HOST, PORT = "0.0.0.0", 8765

def tailscale_ip():
    """Tailscale が割り当てた 100.x.x.x を取る（未接続なら None）"""
    import subprocess
    for exe in ("/Applications/Tailscale.app/Contents/MacOS/Tailscale", "tailscale"):
        try:
            out = subprocess.run([exe, "ip", "-4"], capture_output=True, text=True, timeout=5).stdout.strip()
            if out.startswith("100."):
                return out.splitlines()[0].strip()
        except Exception:
            continue
    return None


def allowed_client(ip):
    """自分自身か、Tailscale のアドレス帯（100.64.0.0/10）だけ許可する。
    同じWi-Fiの他人や、万一ルーターが開いていてもインターネットからは弾く。"""
    if ip in ("127.0.0.1", "::1"):
        return True
    try:
        a, b = ip.split(".")[:2]
        return int(a) == 100 and 64 <= int(b) <= 127
    except Exception:
        return False


# /shodan が使うツールだけを許可する（対話セッションの権限設定には触れない）
ALLOWED = [
    "Read", "Write", "Edit", "Glob", "Grep", "WebSearch", "WebFetch",
    "Bash(python3:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(mkdir:*)", "Bash(pip3 install:*)",
    "mcp__notion-eigyo__API-query-data-source",
    "mcp__notion-eigyo__API-retrieve-a-database",
    "mcp__notion-eigyo__API-retrieve-a-page",
    "mcp__notion-eigyo__API-post-search",
    "mcp__notion-eigyo__API-post-page",
    "mcp__notion-eigyo__API-patch-page",
]



# ============ Google Drive への書き出し ============
# Drive for Desktop がローカル同期しているフォルダに、生成物をコピーする。
# API を使わないので認証設定が不要。同期がまだ来ていない場合は output/ に残すだけで、処理は止めない。
DRIVE_FOLDER = "営業コックピット提案書"
DRIVE_TEST_SUB = "テスト"
_drive_cache = {"at": 0, "path": None}


def drive_dir():
    """同期済みの「営業コックピット提案書」を全アカウントのマウントから探す。
    見つからなければ None（＝Driveへは出さず output/ のみ）。"""
    now = time.time()
    if _drive_cache["path"] and now - _drive_cache["at"] < 120:
        return _drive_cache["path"]
    base = os.path.expanduser("~/Library/CloudStorage")
    found = None
    if os.path.isdir(base):
        for mount in sorted(os.listdir(base)):
            if not mount.startswith("GoogleDrive-"):
                continue
            for sub in ("マイドライブ", "共有ドライブ"):
                root = os.path.join(base, mount, sub)
                if not os.path.isdir(root):
                    continue
                # 直下と、その1階層下まで見る
                cand = os.path.join(root, DRIVE_FOLDER)
                if os.path.isdir(cand):
                    found = cand
                    break
                try:
                    for d in os.listdir(root):
                        c2 = os.path.join(root, d, DRIVE_FOLDER)
                        if os.path.isdir(c2):
                            found = c2
                            break
                except OSError:
                    pass
            if found:
                break
    _drive_cache["at"], _drive_cache["path"] = now, found
    return found


def copy_to_drive(filenames, is_test):
    """生成物を Drive にコピー。(成功したファイル名, 保存先の説明) を返す"""
    dest_root = drive_dir()
    if not dest_root:
        return [], None
    dest = os.path.join(dest_root, DRIVE_TEST_SUB) if is_test else dest_root
    try:
        os.makedirs(dest, exist_ok=True)
    except OSError as e:
        return [], f"Driveフォルダを作成できません（{e}）"
    ok = []
    for name in filenames:
        src = os.path.join(OUTPUT, name)
        if not os.path.exists(src):
            continue
        try:
            shutil.copy2(src, os.path.join(dest, name))
            ok.append(name)
        except OSError:
            pass
    return ok, dest


# ============ Notion 読み取り ============
# 営業基盤は「えほんインク」ワークスペース側。ユーザー設定の token を使う。
# 公開APIの入れ子構造を、ダッシュボードが期待する平坦な形に変換する。
import urllib.request

DBS = {
    "props":   "0fa0b424-afbe-4869-be6c-dfe0bc459101",   # 提案トラッキング
    "clients": "dd401e3d-1706-4428-b713-48515ea0e916",   # クライアントマスタ
    "exts":    "63731955-9869-4be4-b0f8-ce3f15710e48",   # 拡張案件
    "prices":  "6401f9c9-8db8-4638-9e22-eb20e417813b",   # 印刷単価マスタ
}
_CACHE = {}
CACHE_TTL = 180


def _notion_token():
    for path in (os.path.expanduser("~/.claude/mcp.json"), os.path.join(ROOT, ".mcp.json")):
        try:
            cfg = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        for name in ("notion-eigyo", "notion"):
            env = (cfg.get("mcpServers", {}).get(name) or {}).get("env") or {}
            tok = env.get("NOTION_TOKEN") or env.get("NOTION_API_KEY")
            if tok and path.endswith("mcp.json") and (name == "notion-eigyo" or "\\.claude" in path or "/.claude/" in path):
                return tok
    return None


def _page_url(pid):
    return "https://app.notion.com/p/" + str(pid).replace("-", "")


def _flatten(page):
    """Notion公開APIのページを、ビュー実行モードと同じ平坦な辞書に直す"""
    out = {"url": _page_url(page.get("id", ""))}
    for name, v in (page.get("properties") or {}).items():
        t = v.get("type")
        if t == "title":
            out[name] = "".join(x.get("plain_text", "") for x in v.get("title") or [])
        elif t == "rich_text":
            out[name] = "".join(x.get("plain_text", "") for x in v.get("rich_text") or [])
        elif t == "select":
            out[name] = (v.get("select") or {}).get("name", "")
        elif t == "multi_select":
            out[name] = json.dumps([o.get("name") for o in v.get("multi_select") or []], ensure_ascii=False)
        elif t == "number":
            out[name] = v.get("number")
        elif t == "checkbox":
            out[name] = v.get("checkbox")
        elif t == "url":
            out[name] = v.get("url") or ""
        elif t == "date":
            d = v.get("date") or {}
            out[f"date:{name}:start"] = d.get("start")
            out[f"date:{name}:end"] = d.get("end")
            out[f"date:{name}:is_datetime"] = 1 if (d.get("start") or "").find("T") > 0 else 0
        elif t == "relation":
            out[name] = json.dumps([_page_url(r.get("id")) for r in v.get("relation") or []], ensure_ascii=False)
        elif t == "formula":
            f = v.get("formula") or {}
            out[name] = f.get(f.get("type"))
    return out


def notion_query(db_id, token):
    rows, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        req = urllib.request.Request(
            f"https://api.notion.com/v1/databases/{db_id}/query",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28",
                     "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read())
        rows += [_flatten(p) for p in d.get("results", [])]
        if not d.get("has_more"):
            break
        cursor = d.get("next_cursor")
    return rows


def notion_all(force=False):
    now = time.time()
    if not force and _CACHE.get("at") and now - _CACHE["at"] < CACHE_TTL:
        return _CACHE["data"]
    token = _notion_token()
    if not token:
        return {"error": "Notionトークンが見つかりません（~/.claude/mcp.json を確認）"}
    data = {"at": now}
    for key, db in DBS.items():
        try:
            data[key] = notion_query(db, token)
        except Exception as e:
            data[key] = []
            data.setdefault("errors", {})[key] = str(e)[:200]
    _CACHE["at"], _CACHE["data"] = now, data
    return data


JOBS = {}          # id -> {"q": Queue, "state": str, "started": float, "label": str, "files": [], "log": []}
LOCK = threading.Lock()


def snapshot_outputs():
    """名前だけでなく更新時刻も見る。同名ファイルの上書きを取りこぼさないため。"""
    try:
        return {(f, os.path.getmtime(os.path.join(OUTPUT, f))) for f in os.listdir(OUTPUT)}
    except FileNotFoundError:
        return set()


def pick_command(company):
    """クライアントマスタに居れば既存顧客 → /teian、居なければ新規 → /shodan"""
    try:
        data = notion_all()
        names = [(c.get("企業名") or "") for c in data.get("clients", [])]
    except Exception:
        return "shodan"
    q = company.strip()
    for n in names:
        if not n:
            continue
        a, b = n.replace(" ", ""), q.replace(" ", "")
        if a == b or (len(b) >= 3 and b in a) or (len(a) >= 3 and a in b):
            return "teian"
    return "shodan"


def run_job(job_id, company, context, skip_notion):
    job = JOBS[job_id]
    before = snapshot_outputs()

    cmd_name = pick_command(company)
    prompt = f"/{cmd_name} {company}"
    if context.strip():
        prompt += " " + context.strip()
    if skip_notion:
        prompt += " ※STEP 6のNotion登録はスキップして"

    cmd = ["claude", "-p", prompt,
           "--output-format", "stream-json", "--include-partial-messages", "--verbose"]
    for t in ALLOWED:
        cmd += ["--allowedTools", t]

    def emit(kind, text):
        job["log"].append((kind, text))
        job["q"].put({"kind": kind, "text": text})

    emit("meta", f"実行: {prompt}")
    emit("meta", "既存顧客のため /teian を使います" if cmd_name == "teian" else "新規企業のため /shodan を使います")
    try:
        p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, bufsize=1, env={**os.environ, "CLAUDE_CODE_ENTRYPOINT": "cockpit"})
    except FileNotFoundError:
        job["state"] = "失敗"; emit("error", "claude コマンドが見つかりません"); job["q"].put(None); return

    last_text = ""
    for line in p.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "assistant":
            for blk in (ev.get("message") or {}).get("content", []):
                if blk.get("type") == "text" and blk.get("text", "").strip():
                    txt = blk["text"].strip()
                    if txt != last_text:
                        last_text = txt
                        emit("text", txt)
                elif blk.get("type") == "tool_use":
                    name = blk.get("name", "")
                    inp = blk.get("input") or {}
                    detail = inp.get("command") or inp.get("query") or inp.get("file_path") or ""
                    emit("tool", f"{name}  {str(detail)[:90]}")
        elif t == "result":
            job["state"] = "完了" if not ev.get("is_error") else "失敗"
            cost = ev.get("total_cost_usd")
            dur = ev.get("duration_ms", 0) / 1000
            emit("meta", f"終了（{dur:.0f}秒" + (f" / ${cost:.2f}" if cost else "") + "）")
    p.wait()
    if job["state"] not in ("完了", "失敗"):
        job["state"] = "完了" if p.returncode == 0 else "失敗"

    new_files = sorted({f for f, _ in (snapshot_outputs() - before)})
    job["files"] = new_files
    for f in new_files:
        emit("file", f)

    # Google Drive へ書き出す（試験実行は「テスト」サブフォルダへ）
    if new_files:
        copied, dest = copy_to_drive(new_files, is_test=skip_notion)
        if copied and dest:
            where = "Drive ／ 営業コックピット提案書" + ("／テスト" if skip_notion else "")
            emit("meta", f"{where} に {len(copied)}件コピーしました")
        elif dest is None:
            emit("meta", "Driveフォルダが未同期のため、output/ にのみ保存しました")
        else:
            emit("error", str(dest))
    job["q"].put(None)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _guard(self):
        ip = self.client_address[0]
        if allowed_client(ip):
            return True
        self._send(403, "text/plain; charset=utf-8",
                   "このコックピットは、この Mac 自身と Tailscale で接続した自分の端末からのみ利用できます。")
        return False

    def _send(self, code, ctype, body):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        # 画面のファイルはキャッシュさせない。iPhone の Safari が古い版を握り続けるため
        if "html" in ctype or "javascript" in ctype:
            self.send_header("Cache-Control", "no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self._guard():
            return
        u = urlparse(self.path)
        if u.path == "/":
            with open(os.path.join(HERE, "index.html"), encoding="utf-8") as f:
                return self._send(200, "text/html; charset=utf-8", f.read())
        if u.path == "/app.js":
            with open(os.path.join(HERE, "app.js"), encoding="utf-8") as f:
                return self._send(200, "application/javascript; charset=utf-8", f.read())
        if u.path == "/api/drive":
            d = drive_dir()
            return self._send(200, "application/json",
                              json.dumps({"path": d, "ok": bool(d)}, ensure_ascii=False))
        if u.path == "/api/which":
            q = parse_qs(u.query)
            name = (q.get("c") or [""])[0]
            return self._send(200, "application/json",
                              json.dumps({"cmd": pick_command(name) if name.strip() else ""}))
        if u.path == "/api/notion":
            force = "force" in parse_qs(u.query)
            return self._send(200, "application/json",
                              json.dumps(notion_all(force), ensure_ascii=False))
        if u.path == "/jobs":
            with LOCK:
                data = [{"id": k, "label": v["label"], "state": v["state"],
                         "started": v["started"], "files": v["files"]}
                        for k, v in sorted(JOBS.items(), key=lambda x: -x[1]["started"])]
            return self._send(200, "application/json", json.dumps(data, ensure_ascii=False))
        if u.path.startswith("/stream/"):
            job_id = u.path.split("/")[-1]
            job = JOBS.get(job_id)
            if not job:
                return self._send(404, "text/plain", "no such job")
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            for kind, text in list(job["log"]):
                self._push({"kind": kind, "text": text})
            if job["state"] in ("完了", "失敗"):
                self._push({"kind": "end", "text": job["state"]}); return
            while True:
                item = job["q"].get()
                if item is None:
                    self._push({"kind": "end", "text": job["state"]}); return
                if not self._push(item):
                    return
        if u.path.startswith("/file/"):
            name = unquote(u.path.split("/", 2)[-1])
            path = os.path.join(OUTPUT, name)
            if not os.path.abspath(path).startswith(os.path.abspath(OUTPUT)) or not os.path.exists(path):
                return self._send(404, "text/plain", "not found")
            with open(path, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{name}"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if u.path == "/reveal":
            q = parse_qs(u.query)
            name = (q.get("f") or [""])[0]
            path = os.path.join(OUTPUT, name)
            if os.path.exists(path):
                subprocess.run(["open", "-R", path])
            return self._send(200, "text/plain", "ok")
        return self._send(404, "text/plain", "not found")

    def _push(self, obj):
        try:
            self.wfile.write(f"data: {json.dumps(obj, ensure_ascii=False)}\n\n".encode("utf-8"))
            self.wfile.flush()
            return True
        except (BrokenPipeError, ConnectionResetError):
            return False

    def do_POST(self):
        if not self._guard():
            return
        u = urlparse(self.path)
        if u.path != "/run":
            return self._send(404, "text/plain", "not found")
        n = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(n) or b"{}")
        company = (payload.get("company") or "").strip()
        context = (payload.get("context") or "").strip()
        skip = bool(payload.get("skip_notion"))
        if not company:
            return self._send(400, "application/json", json.dumps({"error": "企業名が空です"}))
        job_id = uuid.uuid4().hex[:12]
        with LOCK:
            JOBS[job_id] = {"q": queue.Queue(), "state": "実行中", "started": time.time(),
                            "label": company, "files": [], "log": []}
        threading.Thread(target=run_job, args=(job_id, company, context, skip), daemon=True).start()
        return self._send(200, "application/json", json.dumps({"id": job_id}))


class ThreadedServer(HTTPServer):
    daemon_threads = True
    def process_request(self, request, client_address):
        threading.Thread(target=self._h, args=(request, client_address), daemon=True).start()
    def _h(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            pass
        finally:
            self.shutdown_request(request)


if __name__ == "__main__":
    os.makedirs(OUTPUT, exist_ok=True)
    ts = tailscale_ip()
    print("─" * 56)
    print("  ÉHON 営業コックピット")
    print("─" * 56)
    print(f"  このMacから      http://127.0.0.1:{PORT}")
    if ts:
        print(f"  他の自分の端末から http://{ts}:{PORT}")
        print(f"                    http://imac.tail387f82.ts.net:{PORT}")
    else:
        print("  Tailscale 未接続のため、この Mac からのみ利用できます")
    dd_ = drive_dir()
    print(f"  Drive書き出し先   {dd_ if dd_ else '未同期（output/ にのみ保存）'}")
    print(f"  作業ディレクトリ  {ROOT}")
    print("─" * 56)
    ThreadedServer((HOST, PORT), Handler).serve_forever()
