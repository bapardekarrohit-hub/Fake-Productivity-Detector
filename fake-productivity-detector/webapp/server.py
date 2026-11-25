#!/usr/bin/env python3
"""Fake Productivity Detector - web app server (Python standard library + the trained ML model).

Run:  python webapp/server.py            ->  http://127.0.0.1:8000
Demo login (auto-created on first run):  demo / demo12345

Local project server: passwords are hashed (PBKDF2) and sessions use HttpOnly cookies, but there is
no HTTPS or rate limiting, so do not expose it to the public internet as-is.
"""
import csv
import hashlib
import io
import json
import mimetypes
import secrets
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import joblib
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
import app_model as am  # noqa: E402

DB_PATH = HERE / "fpd.sqlite3"
STATIC = HERE / "static"
MODEL = joblib.load(ROOT / "models" / "productivity_model.joblib")["model"]
METRICS = json.loads((ROOT / "reports" / "app_metrics.json").read_text())
LIMITS = {"task_hours": 24, "idle_hours": 24, "social_hours": 24, "break_frequency": 50, "tasks_completed": 200}


# ----------------------------------------------------------------------------- database
def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def hash_pw(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000).hex()


def now_iso(dt=None) -> str:
    return (dt or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")


def init_db():
    fresh = not DB_PATH.exists()
    con = db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, salt TEXT, pw_hash TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id INTEGER, created_at TEXT);
    CREATE TABLE IF NOT EXISTS analyses(id INTEGER PRIMARY KEY, user_id INTEGER, created_at TEXT, source TEXT,
        row_label TEXT, task_hours REAL, idle_hours REAL, social_hours REAL, break_frequency REAL,
        tasks_completed REAL, score REAL, category TEXT);
    """)
    if fresh:
        uid = create_user(con, "demo", "demo12345")
        seed_demo(con, uid)
    con.commit()
    con.close()


def create_user(con, username, password) -> int:
    salt = secrets.token_bytes(16)
    cur = con.execute("INSERT INTO users(username,salt,pw_hash,created_at) VALUES(?,?,?,?)",
                      (username, salt.hex(), hash_pw(password, salt), now_iso()))
    return cur.lastrowid


def seed_demo(con, uid, n=40):
    """Give the demo account some realistic history so every page has content."""
    sample = am.generate(n, seed=7)
    scores = score_rows(sample)
    rng = np.random.default_rng(7)
    for k, (_, r) in enumerate(sample.iterrows()):
        when = datetime.now(timezone.utc) - timedelta(days=int((n - k) * 14 / n), hours=int(rng.integers(0, 8)))
        save_analysis(con, uid, "manual", "", r, scores[k], when)


# ----------------------------------------------------------------------------- model helpers
def score_rows(df: pd.DataFrame) -> np.ndarray:
    return np.clip(MODEL.predict(am.featurize(df)), 0, 100).round(0)


def score_one(row: dict) -> float:
    return float(score_rows(pd.DataFrame([row]))[0])


def save_analysis(con, uid, source, label, row, score, when=None):
    con.execute(
        "INSERT INTO analyses(user_id,created_at,source,row_label,task_hours,idle_hours,social_hours,"
        "break_frequency,tasks_completed,score,category) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (uid, now_iso(when), source, label, float(row["task_hours"]), float(row["idle_hours"]),
         float(row["social_hours"]), float(row["break_frequency"]), float(row["tasks_completed"]),
         float(score), am.category(score)))


def suggestions(row: dict, score: float) -> list:
    """What-if analysis: ask the trained model how much each realistic change would help."""
    tips = []
    tph = row["tasks_completed"] / (row["task_hours"] + 0.5)
    if row["task_hours"] >= 6 and tph < 0.4:
        tips.append("Pattern of fake productivity: many logged task hours but few completed tasks. "
                    "Track finished output, not hours.")
    scenarios = []
    if row["social_hours"] >= 1:
        shift = min(1.0, row["social_hours"])
        scenarios.append((f"Shift {shift:g}h from social media to focused work",
                          {**row, "social_hours": row["social_hours"] - shift, "task_hours": row["task_hours"] + shift}))
    if row["idle_hours"] >= 1:
        shift = min(1.0, row["idle_hours"])
        scenarios.append((f"Turn {shift:g}h of idle time into focused work",
                          {**row, "idle_hours": row["idle_hours"] - shift, "task_hours": row["task_hours"] + shift}))
    scenarios.append(("Complete 2 more tasks in the same time", {**row, "tasks_completed": row["tasks_completed"] + 2}))
    if row["break_frequency"] > 6:
        scenarios.append(("Take fewer, longer breaks (about 4 a day)", {**row, "break_frequency": 4}))
    gains = []
    for text, new_row in scenarios:
        gain = score_one(new_row) - score
        if gain >= 1:
            gains.append((gain, text))
    for gain, text in sorted(gains, reverse=True)[:3]:
        tips.append(f"{text} (model estimate: +{gain:.0f} points)")
    if not tips:
        tips.append("Great balance of focus and output. Keep it up.")
    return tips


def parse_row(obj: dict):
    """Validate one input row. Returns (row, error)."""
    row = {}
    for key, hi in LIMITS.items():
        try:
            v = float(obj.get(key))
        except (TypeError, ValueError):
            return None, f"{key.replace('_', ' ')} must be a number"
        if not np.isfinite(v) or v < 0 or v > hi:
            return None, f"{key.replace('_', ' ')} must be between 0 and {hi}"
        row[key] = v
    return row, None


def result_payload(row, score):
    return {"score": int(score), "category": am.category(score), "breakdown": {
        "Productive": row["task_hours"], "Idle": row["idle_hours"], "Social Media": row["social_hours"],
        "Breaks": row["break_frequency"]}, "suggestions": suggestions(row, score)}


# ----------------------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = "FPD/1.0"

    def log_message(self, fmt, *args):  # quieter console
        sys.stderr.write("%s %s\n" % (self.command, self.path))

    # --- helpers
    def send_json(self, obj, status=200, set_cookie=None):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if set_cookie:
            self.send_header("Set-Cookie", set_cookie)
        self.end_headers()
        self.wfile.write(body)

    def body_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 2_000_000:
            return {}
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return {}

    def current_user(self, con):
        raw = self.headers.get("Cookie")
        if not raw:
            return None
        jar = cookies.SimpleCookie(raw)
        if "fpd_session" not in jar:
            return None
        return con.execute("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=?",
                           (jar["fpd_session"].value,)).fetchone()

    def session_cookie(self, token, clear=False):
        return f"fpd_session={'' if clear else token}; Path=/; HttpOnly; SameSite=Lax" + \
               ("; Max-Age=0" if clear else "; Max-Age=2592000")

    # --- routing
    def do_GET(self):
        path = urlparse(self.path).path
        if not path.startswith("/api/"):
            return self.serve_static(path)
        con = db()
        try:
            user = self.current_user(con)
            if path == "/api/me":
                if not user:
                    return self.send_json({"user": None})
                return self.send_json({"user": {"username": user["username"], "created_at": user["created_at"]}})
            if not user:
                return self.send_json({"error": "Not signed in"}, 401)
            if path == "/api/history":
                rows = con.execute("SELECT * FROM analyses WHERE user_id=? ORDER BY created_at DESC, id DESC",
                                   (user["id"],)).fetchall()
                return self.send_json({"analyses": [dict(r) for r in rows]})
            if path == "/api/model":
                return self.send_json(METRICS)
            return self.send_json({"error": "Not found"}, 404)
        finally:
            con.close()

    def do_POST(self):
        path = urlparse(self.path).path
        data = self.body_json()
        con = db()
        try:
            if path in ("/api/login", "/api/register"):
                username = str(data.get("username", "")).strip()[:60]
                password = str(data.get("password", ""))
                if not username or not password:
                    return self.send_json({"error": "Enter a username and password"}, 400)
                if path == "/api/register":
                    if len(password) < 8:
                        return self.send_json({"error": "Password must be at least 8 characters"}, 400)
                    try:
                        uid = create_user(con, username, password)
                    except sqlite3.IntegrityError:
                        return self.send_json({"error": "That username is taken"}, 409)
                else:
                    u = con.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
                    if not u or not secrets.compare_digest(hash_pw(password, bytes.fromhex(u["salt"])), u["pw_hash"]):
                        return self.send_json({"error": "Wrong username or password"}, 401)
                    uid = u["id"]
                token = secrets.token_urlsafe(32)
                con.execute("INSERT INTO sessions VALUES(?,?,?)", (token, uid, now_iso()))
                con.commit()
                return self.send_json({"ok": True, "username": username}, set_cookie=self.session_cookie(token))

            user = self.current_user(con)
            if path == "/api/logout":
                raw = self.headers.get("Cookie")
                if raw:
                    jar = cookies.SimpleCookie(raw)
                    if "fpd_session" in jar:
                        con.execute("DELETE FROM sessions WHERE token=?", (jar["fpd_session"].value,))
                        con.commit()
                return self.send_json({"ok": True}, set_cookie=self.session_cookie("", clear=True))
            if not user:
                return self.send_json({"error": "Not signed in"}, 401)

            if path == "/api/analyze":
                row, err = parse_row(data)
                if err:
                    return self.send_json({"error": err}, 400)
                score = score_one(row)
                save_analysis(con, user["id"], "manual", "", row, score)
                con.commit()
                return self.send_json(result_payload(row, score))

            if path == "/api/analyze_csv":
                return self.analyze_csv(con, user, str(data.get("csv", "")))
            return self.send_json({"error": "Not found"}, 404)
        finally:
            con.close()

    def do_DELETE(self):
        if urlparse(self.path).path != "/api/history":
            return self.send_json({"error": "Not found"}, 404)
        con = db()
        try:
            user = self.current_user(con)
            if not user:
                return self.send_json({"error": "Not signed in"}, 401)
            con.execute("DELETE FROM analyses WHERE user_id=?", (user["id"],))
            con.commit()
            return self.send_json({"ok": True})
        finally:
            con.close()

    def analyze_csv(self, con, user, text):
        reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
        header = {h.strip().lower(): h for h in (reader.fieldnames or [])}
        missing = [c for c in am.CSV_COLUMNS if c.lower() not in header]
        if missing:
            return self.send_json({"error": "Missing columns: " + ", ".join(missing) +
                                   ". Download the template for the expected format."}, 400)
        rows, results, errors = [], [], []
        for i, rec in enumerate(reader, start=2):               # row 1 is the header
            obj = {am.CSV_TO_RAW[c]: rec.get(header[c.lower()]) for c in am.CSV_COLUMNS}
            row, err = parse_row(obj)
            if err:
                errors.append({"row": i, "error": err})
            else:
                rows.append((i, row))
            if len(rows) + len(errors) >= 2000:
                break
        if not rows:
            return self.send_json({"error": "No valid rows found", "errors": errors[:10]}, 400)
        scores = score_rows(pd.DataFrame([r for _, r in rows]))
        for (i, row), score in zip(rows, scores):
            save_analysis(con, user["id"], "csv", f"Row {i}", row, score)
            results.append({"row": i, "score": int(score), "category": am.category(score), **row})
        con.commit()
        return self.send_json({"results": results, "errors": errors[:10]})

    def serve_static(self, path):
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        target = (STATIC / rel).resolve()
        if STATIC.resolve() not in target.parents or not target.is_file():
            self.send_error(404)
            return
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main(port=8000):
    init_db()
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Fake Productivity Detector running at http://127.0.0.1:{port}  (demo login: demo / demo12345)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8000)
