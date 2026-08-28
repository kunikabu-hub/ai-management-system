#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
毎朝8時のリマインドを LINE に送る。

  予定 ＋ 期日 ＋ 宿題 の3つだけ。長くすると読まれない。

  python3 cockpit/morning.py          送信
  python3 cockpit/morning.py --dry    送らずに本文だけ表示
"""
import datetime, json, os, sys, urllib.parse, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GDIR = os.path.expanduser("~/.config/claude-code/gdrive/")
IDLE_STALE = 30          # 宿題がこれ以上前の議事録なら「滞留」と付ける

DBS = {
    "props":   "0fa0b424-afbe-4869-be6c-dfe0bc459101",
    "exts":    "63731955-9869-4be4-b0f8-ce3f15710e48",
    "minutes": "dbc20914-71cb-45e0-8cc0-faf467fae73d",
}
JP_WD = ["月", "火", "水", "木", "金", "土", "日"]


def secret(key):
    for p in (os.path.join(ROOT, ".mcp.json"), os.path.expanduser("~/.claude/mcp.json")):
        try:
            cfg = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        v = (cfg.get("_env") or {}).get(key)
        if v:
            return v
        for name in ("notion-eigyo", "notion"):
            env = (cfg.get("mcpServers", {}).get(name) or {}).get("env") or {}
            v = env.get(key)
            if v and p.endswith(".claude/mcp.json"):
                return v
    return None


# ---------- Google ----------
_gtok = {}


def google_token():
    if _gtok.get("v"):
        return _gtok["v"]
    t = json.load(open(GDIR + "token.json"))
    c = json.load(open(GDIR + "credentials.json"))
    c = c.get("installed") or c.get("web") or c
    d = urllib.parse.urlencode({"client_id": c["client_id"], "client_secret": c["client_secret"],
                                "refresh_token": t["refresh_token"], "grant_type": "refresh_token"}).encode()
    _gtok["v"] = json.load(urllib.request.urlopen(
        "https://oauth2.googleapis.com/token", data=d, timeout=20))["access_token"]
    return _gtok["v"]


def gget(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(
        url, headers={"Authorization": f"Bearer {google_token()}"}), timeout=25))


def calendar_today(today):
    try:
        at = google_token()
        tz = datetime.datetime.now().astimezone().tzinfo
        s = datetime.datetime.combine(today, datetime.time(0, 0), tz).isoformat()
        e = datetime.datetime.combine(today, datetime.time(23, 59, 59), tz).isoformat()
        q = urllib.parse.urlencode({"timeMin": s, "timeMax": e, "singleEvents": "true",
                                    "orderBy": "startTime", "maxResults": 30})
        r = gget(f"https://www.googleapis.com/calendar/v3/calendars/primary/events?{q}")
        out = []
        for ev in r.get("items", []):
            if ev.get("status") == "cancelled":
                continue
            st = ev["start"].get("dateTime") or ev["start"].get("date")
            out.append((st[11:16] if "T" in st else "終日", ev.get("summary", "(無題)")))
        return out, None
    except Exception as e:
        return [], f"カレンダー取得エラー（{type(e).__name__}）"


def name_of(frm):
    """差出人の表示名。MIMEエンコードと余計な引用符・バックスラッシュを落とす"""
    import email.header
    n = frm.split("<")[0].strip()
    try:
        n = "".join(t.decode(enc or "utf-8", "replace") if isinstance(t, bytes) else t
                    for t, enc in email.header.decode_header(n))
    except Exception:
        pass
    n = n.replace("\\", "").strip().strip('"').strip()
    return n or frm.split("<")[-1].rstrip(">")


def unreplied_mail(limit=6, days=10, scan=60):
    """受信トレイのうち、最後が相手からのまま返していないスレッド。

    Gmail に「未返信」の検索条件はないので、スレッドごとに最後の差出人を見る。
    そのままだとメルマガと自動通知で埋まるので、次を除外する。
      - List-Unsubscribe ヘッダを持つもの（＝配信停止できる＝メルマガ）
      - noreply / no-reply / donotreply などの差出人
      - 通知系のドメイン（自動送信で返信の必要がない）
      - Gmail のカテゴリ（promotions / social / updates / forums）
    """
    NOREPLY = ("noreply", "no-reply", "donotreply", "do-not-reply", "notifications@",
               "mailer-daemon", "postmaster", "info@", "support@", "news@", "magazine@",
               "mail@", "webmaster@", "system@", "admin@")
    # 件名で落とす（自動通知・カレンダーの出欠返信・配信物）
    SUBJ_NG = ("承諾:", "辞退:", "仮承諾:", "招待:", "更新:", "キャンセル:",
               "が登録されました", "ウェビナー", "セミナーのご案内", "ニュースレター",
               "newsletter", "自動返信", "Automatic reply", "配信停止")
    AUTO_DOMAINS = ("circleback.ai", "owler.com", "google.com", "notion.so", "slack.com",
                    "github.com", "linkedin.com", "facebookmail.com", "stripe.com",
                    "docusign.net", "calendly.com", "timerex.net")
    try:
        me = gget("https://www.googleapis.com/gmail/v1/users/me/profile")["emailAddress"].lower()
        q = urllib.parse.quote(
            f"in:inbox -in:chats newer_than:{days}d -from:me "
            "-category:promotions -category:social -category:updates -category:forums")
        lst = gget(f"https://www.googleapis.com/gmail/v1/users/me/threads?q={q}&maxResults={scan}")
        out = []
        for th in lst.get("threads", []):
            d = gget("https://www.googleapis.com/gmail/v1/users/me/threads/"
                     f"{th['id']}?format=metadata&metadataHeaders=From&metadataHeaders=Subject"
                     "&metadataHeaders=Date&metadataHeaders=List-Unsubscribe&metadataHeaders=Precedence")
            msgs = d.get("messages") or []
            if not msgs:
                continue
            last = msgs[-1]
            h = {x["name"].lower(): x["value"] for x in last["payload"].get("headers", [])}
            frm = h.get("from", "")
            low = frm.lower()
            if me in low:
                continue                                   # 最後が自分＝返信済み
            if "list-unsubscribe" in h:
                continue                                   # 配信停止できる＝メルマガ
            if (h.get("precedence", "").lower() in ("bulk", "list", "auto_reply")):
                continue
            if any(k in low for k in NOREPLY):
                continue
            if any(dm in low for dm in AUTO_DOMAINS):
                continue
            subj = h.get("subject", "(件名なし)")
            if any(k in subj for k in SUBJ_NG):
                continue
            # 自分の名前で届く通知（カレンダーの出欠など）は除外
            if "国則" in name_of(frm) and me not in low:
                continue
            ts = int(last.get("internalDate", 0)) / 1000
            age = (datetime.datetime.now() - datetime.datetime.fromtimestamp(ts)).days
            out.append((age, name_of(frm), subj))
        out.sort(key=lambda x: -x[0])
        return out[:limit], len(out), None
    except Exception as e:
        return [], 0, f"メール取得エラー（{type(e).__name__}）"


# ---------- Notion ----------
def notion(db, token):
    rows, cur = [], None
    while True:
        body = {"page_size": 100}
        if cur:
            body["start_cursor"] = cur
        req = urllib.request.Request(f"https://api.notion.com/v1/databases/{db}/query",
                                     data=json.dumps(body).encode(), method="POST",
                                     headers={"Authorization": f"Bearer {token}",
                                              "Notion-Version": "2022-06-28",
                                              "Content-Type": "application/json"})
        d = json.load(urllib.request.urlopen(req, timeout=30))
        rows += d.get("results", [])
        if not d.get("has_more"):
            return rows
        cur = d.get("next_cursor")


def txt(p, name):
    v = (p.get("properties") or {}).get(name) or {}
    t = v.get("type")
    if t == "title":
        return "".join(x.get("plain_text", "") for x in v.get("title") or [])
    if t == "rich_text":
        return "".join(x.get("plain_text", "") for x in v.get("rich_text") or [])
    if t == "select":
        return (v.get("select") or {}).get("name", "")
    if t == "number":
        return v.get("number")
    if t == "date":
        return (v.get("date") or {}).get("start")
    return ""


def yen(n):
    return f"¥{int(n):,}" if isinstance(n, (int, float)) and n else ""


def build(today, hour=None):
    """hour で挨拶と予定の対象日を変える。
    朝(〜11時)＝今日の予定 / 昼(〜17時)＝今日の残り / 夜(18時〜)＝明日の予定"""
    h = datetime.datetime.now().hour if hour is None else hour
    if h < 11:
        greet, cal_day, cal_label = "おはようございます", today, "今日の予定"
    elif h < 18:
        greet, cal_day, cal_label = "お疲れさまです", today, "今日の残りの予定"
    else:
        greet, cal_day, cal_label = "お疲れさまでした", today + datetime.timedelta(days=1), "明日の予定"

    L = [f"{greet}。{today:%-m/%-d}（{JP_WD[today.weekday()]}）"]
    notes = []

    # 1. 予定
    events, err = calendar_today(cal_day)
    if h >= 11 and h < 18:
        now_hm = f"{datetime.datetime.now():%H:%M}"
        events = [(t_, s_) for t_, s_ in events if t_ == "終日" or t_ >= now_hm]
    L.append(f"\n▍{cal_label}")
    if err:
        L.append(f"  {err}")
    elif events:
        for t_, s in events:
            L.append(f"  {t_}  {s}")
    else:
        L.append("  なし")

    tok = secret("NOTION_API_KEY") or secret("NOTION_TOKEN")
    if not tok:
        L.append("\n▍期日・宿題\n  Notionトークンが見つかりません")
        return "\n".join(L)

    # 2. 期日（提案トラッキング＋拡張案件）
    due = []
    try:
        for p in notion(DBS["props"], tok):
            st = txt(p, "ステージ")
            if st in ("受注", "失注", "保留") or not st:
                continue
            d = txt(p, "次アクション期日")
            if not d:
                continue
            n = (datetime.date.fromisoformat(d[:10]) - today).days
            if n <= 3:
                due.append((n, txt(p, "提案名"), txt(p, "クライアント"), txt(p, "金額")))
        for e in notion(DBS["exts"], tok):
            if txt(e, "ステータス") in ("受注", "見送り"):
                continue
            d = txt(e, "期日")
            if not d:
                continue
            n = (datetime.date.fromisoformat(d[:10]) - today).days
            if n <= 3:
                due.append((n, txt(e, "案件名"), "拡張案件", txt(e, "想定金額")))
    except Exception as ex:
        notes.append(f"期日の取得に失敗（{type(ex).__name__}）")
    due.sort()
    L.append("\n▍期日")
    if due:
        for n, name, client, amt in due:
            tag = f"{-n}日超過" if n < 0 else ("今日" if n == 0 else f"あと{n}日")
            a = f" {yen(amt)}" if yen(amt) else ""
            L.append(f"  [{tag}] {name}")
            L.append(f"      {client}{a}")
    else:
        L.append("  期限が近いものはありません")

    # 3. 宿題（議事録の 宿題_自社）
    todos = []
    try:
        for m in notion(DBS["minutes"], tok):
            h = txt(m, "宿題_自社")
            if not h.strip():
                continue
            d = txt(m, "日付")
            age = (today - datetime.date.fromisoformat(d[:10])).days if d else None
            title = txt(m, "タイトル").replace("（自動生成）", "")
            for line in h.replace("<br>", "\n").split("\n"):
                line = line.strip("・ ").strip()
                if line:
                    todos.append((age if age is not None else 999, line, title))
    except Exception as ex:
        notes.append(f"宿題の取得に失敗（{type(ex).__name__}）")
    todos.sort(key=lambda x: -x[0])
    L.append("\n▍こちらの宿題")
    if todos:
        for age, line, title in todos[:8]:
            stale = f"（{age}日前・{title}）" if age >= IDLE_STALE else f"（{title}）"
            L.append(f"  ・{line}")
            L.append(f"      {stale}")
        if len(todos) > 8:
            L.append(f"  ほか{len(todos)-8}件")
    else:
        L.append("  なし")

    # 4. 未返信メール
    mails, total, merr = unreplied_mail()
    L.append("\n▍未返信のメール")
    if merr:
        L.append(f"  {merr}")
    elif mails:
        for age, name, subj in mails:
            L.append(f"  ・{name}（{age}日前）")
            L.append(f"      {subj[:44]}")
        if total > len(mails):
            L.append(f"  ほか{total-len(mails)}件")
    else:
        L.append("  なし")

    if notes:
        L.append("\n※ " + " / ".join(notes))
    return "\n".join(L)


def send(text):
    tok = secret("LINE_CHANNEL_ACCESS_TOKEN")
    if not tok:
        print("LINEトークンが見つかりません", file=sys.stderr)
        return 1
    body = json.dumps({"messages": [{"type": "text", "text": text[:4900]}]}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(
            "https://api.line.me/v2/bot/message/broadcast", data=body, method="POST",
            headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}), timeout=25)
        return 0
    except urllib.error.HTTPError as e:
        print("LINE送信失敗:", e.code, e.read().decode()[:300], file=sys.stderr)
        return 1


if __name__ == "__main__":
    body = build(datetime.date.today())
    if "--dry" in sys.argv:
        print(body)
    else:
        sys.exit(send(body))
