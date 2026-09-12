# -*- coding: utf-8 -*-
import os
import re
import json
import time
import email
import email.message
import email.utils
import datetime
import imaplib
import sqlite3
import urllib.request
import asyncio
import logging
from email.header import decode_header
from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel

logger = logging.getLogger("pulseos.mail")
logger.setLevel(logging.INFO)

DB_PATH = "/opt/pulseos/pulseos.db"
CONFIG_PATH = "/opt/pulseos/mail_otp_config.json"

router = APIRouter(prefix="/api/mail", tags=["Universal Mailbox Hub"])

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_mail_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute("""
        CREATE TABLE IF NOT EXISTS mail_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_email TEXT NOT NULL,
            folder TEXT NOT NULL,
            msg_uid TEXT NOT NULL,
            sender TEXT NOT NULL,
            sender_email TEXT,
            recipient TEXT,
            subject TEXT NOT NULL,
            snippet TEXT,
            body_text TEXT,
            body_html TEXT,
            date_str TEXT,
            timestamp INTEGER NOT NULL,
            is_read INTEGER DEFAULT 0,
            is_otp INTEGER DEFAULT 0,
            otp_code TEXT,
            ai_summary TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(account_email, folder, msg_uid)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_mail_account ON mail_messages (account_email);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_mail_folder ON mail_messages (folder);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_mail_timestamp ON mail_messages (timestamp DESC);")
    conn.commit()
    conn.close()

init_mail_db()

def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_deepseek_key() -> str:
    cfg = load_config()
    return cfg.get("deepseek_api_key") or os.environ.get("DEEPSEEK_API_KEY", "")

def decode_mime_words(s: Optional[str]) -> str:
    if not s:
        return ""
    try:
        words = decode_header(s)
        parts = []
        for word, enc in words:
            if isinstance(word, bytes):
                parts.append(word.decode(enc or "utf-8", errors="ignore"))
            else:
                parts.append(str(word))
        return "".join(parts)
    except Exception:
        return str(s)

def parse_sender_info(from_str: str):
    clean = decode_mime_words(from_str)
    m = re.search(r'<([^>]+)>', clean)
    if m:
        email_addr = m.group(1).strip()
        name = clean.replace(f"<{email_addr}>", "").strip(' "')
        return name or email_addr, email_addr
    return clean.strip(), clean.strip()

def extract_email_bodies(msg: email.message.Message):
    body_text = ""
    body_html = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="ignore")
            except Exception:
                decoded = payload.decode("utf-8", errors="ignore")
                
            if content_type == "text/plain" and not body_text:
                body_text = decoded
            elif content_type == "text/html" and not body_html:
                body_html = decoded
    else:
        content_type = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="ignore")
            except Exception:
                decoded = payload.decode("utf-8", errors="ignore")
            if content_type == "text/html":
                body_html = decoded
            else:
                body_text = decoded

    snippet_source = body_text or re.sub(r'<style[^>]*>[\s\S]*?</style>', ' ', body_html, flags=re.IGNORECASE)
    snippet_source = re.sub(r'<[^>]+>', ' ', snippet_source)
    snippet_source = re.sub(r'&[a-zA-Z0-9#]+;', ' ', snippet_source)
    clean_snippet = re.sub(r'\s+', ' ', snippet_source).strip()[:180]
    
    return body_text, body_html, clean_snippet

def extract_otp_candidate(subject: str, text: str) -> Optional[str]:
    combined = (subject or "") + "\n" + (text or "")
    
    # 1. Google G-XXXXXX format
    g_match = re.search(r'\b(G-[0-9]{6})\b', combined)
    if g_match:
        return g_match.group(1)

    # 2. Strict keyword + digits (4 to 8 digits)
    patterns = [
        r'(?:验证码|校验码|动态码|安全码|确认码|安全PIN|code|verification code)[\s:：是为is\-]{1,24}([0-9]{4,8})\b',
        r'([0-9]{4,8})[\s:：]{0,4}(?:为您的验证码|是您的验证码|is your verification code|为本次验证码|是本次验证码)',
        r'(?:您的|your\s+)?(?:Google|微信|QQ|GitHub|Telegram|OpenAI|Microsoft|Cloudflare|AWS|Apple)[\s\S]{0,30}?(?:验证码|code)[\s:：是为is\-]{1,20}([0-9]{4,8})\b',
        r'(?:验证码|code)[\s\S]{1,60}?\b([0-9]{6})\b'
    ]
    for p in patterns:
        matches = re.findall(p, combined, re.IGNORECASE)
        for c in matches:
            c = str(c).strip()
            if c.isdigit() and len(c) in (4, 5, 6, 8):
                return c
    return None

def sync_single_account(acc: Dict[str, Any], fetch_limit: int = 15) -> List[Dict[str, Any]]:
    results = []
    user = acc.get("email")
    auth = acc.get("auth_code", "").strip()
    host = acc.get("host")
    port = acc.get("port", 993)
    ssl_flag = acc.get("ssl", True)

    if not auth:
        return results

    mail = None
    try:
        mail = imaplib.IMAP4_SSL(host, port, timeout=12) if ssl_flag else imaplib.IMAP4(host, port, timeout=12)
        mail.login(user, auth)

        # 1. Resolve folder mapping
        folders = {"INBOX": "INBOX"}
        if "qq.com" in host:
            folders["TRASH"] = "Deleted Messages"
        else:
            trash_folder = "[Gmail]/Trash"
            st, flist = mail.list()
            for f in flist:
                line = f.decode("utf-8", errors="ignore")
                if "\\Trash" in line:
                    trash_folder = line.split(' "/" ')[-1].strip('"')
                    break
            folders["TRASH"] = trash_folder

        now_utc = datetime.datetime.now(datetime.timezone.utc).timestamp()
        conn = get_db()
        cursor = conn.cursor()

        for folder_type, remote_folder in folders.items():
            try:
                st, d = mail.select(f'"{remote_folder}"', readonly=True)
                total = int(d[0].decode()) if d and d[0] else 0
                if total <= 0:
                    continue

                start_seq = max(1, total - fetch_limit + 1)
                
                # Fast range fetch for all headers at once (~0.2s)
                seq_range = f"{start_seq}:{total}"
                st, hdata = mail.fetch(seq_range.encode(), "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM TO DATE MESSAGE-ID)])")
                if not hdata:
                    continue

                for item in hdata:
                    if not isinstance(item, tuple) or len(item) < 2:
                        continue
                    raw_hdr = item[1]
                    if not isinstance(raw_hdr, (bytes, bytearray)):
                        continue

                    hdr_msg = email.message_from_bytes(raw_hdr)
                    msg_id = hdr_msg.get("Message-ID", "").strip()
                    date_str = hdr_msg.get("Date", "").strip()
                    subject = decode_mime_words(hdr_msg.get("Subject", "无主题"))
                    from_hdr = hdr_msg.get("From", "")
                    sender_name, sender_email = parse_sender_info(from_hdr)
                    recipient = decode_mime_words(hdr_msg.get("To", user))
                    
                    seq_match = re.search(r'([0-9]+)', item[0].decode('utf-8', errors='ignore'))
                    seq_num = seq_match.group(1) if seq_match else str(total)
                    if not msg_id:
                        msg_id = f"{subject}_{date_str}_{seq_num}"

                    # Check if already cached in SQLite
                    cursor.execute("SELECT id FROM mail_messages WHERE account_email = ? AND folder = ? AND msg_uid = ?", (user, folder_type, msg_id))
                    if cursor.fetchone():
                        results.append({"account": user, "folder": folder_type, "subject": subject, "cached": True})
                        continue

                    # Only download RFC822 for NEW messages
                    try:
                        status, data = mail.fetch(seq_num.encode(), "(RFC822)")
                        if not data or not data[0] or not isinstance(data[0][1], (bytes, bytearray)):
                            continue

                        msg = email.message_from_bytes(data[0][1])
                        email_ts = int(now_utc * 1000)
                        try:
                            dt = email.utils.parsedate_to_datetime(date_str)
                            email_ts = int(dt.timestamp() * 1000)
                        except Exception:
                            pass

                        body_text, body_html, snippet = extract_email_bodies(msg)
                        combined_text = (snippet or "") + "\n" + (body_text or "")[:1500]
                        otp_code = extract_otp_candidate(subject, combined_text)
                        is_otp = 1 if otp_code else 0

                        if is_otp and otp_code:
                            try:
                                import otp_service
                                s_name = otp_service.detect_service_name(sender_name, subject)
                                t_email = otp_service.extract_target_account(combined_text, user)
                                otp_data = {
                                    "id": f"otp-{email_ts}-{otp_code}",
                                    "code": otp_code,
                                    "service": s_name,
                                    "target_email": t_email,
                                    "received_in": user,
                                    "subject": subject,
                                    "timestamp": email_ts,
                                    "expires_in_seconds": 600,
                                    "age_seconds": int(now_utc - email_ts / 1000)
                                }
                                otp_service.trigger_broadcast_sync(otp_data)
                                logger.info(f"⚡ [MAIL SYNC -> OTP] Broadcasted OTP {otp_code} from {s_name}")
                            except Exception as err:
                                logger.debug(f"Broadcast OTP from mail sync error: {err}")

                        cursor.execute("""
                            INSERT INTO mail_messages (
                                account_email, folder, msg_uid, sender, sender_email,
                                recipient, subject, snippet, body_text, body_html,
                                date_str, timestamp, is_read, is_otp, otp_code, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                            ON CONFLICT(account_email, folder, msg_uid) DO UPDATE SET
                                subject=excluded.subject,
                                snippet=excluded.snippet,
                                body_text=coalesce(excluded.body_text, mail_messages.body_text),
                                body_html=coalesce(excluded.body_html, mail_messages.body_html),
                                otp_code=excluded.otp_code,
                                is_otp=excluded.is_otp
                        """, (
                            user, folder_type, msg_id, sender_name, sender_email,
                            recipient, subject, snippet, body_text, body_html,
                            date_str, email_ts, is_otp, otp_code,
                            datetime.datetime.now().isoformat()
                        ))
                        results.append({"account": user, "folder": folder_type, "subject": subject, "cached": False})
                    except Exception as item_e:
                        logger.debug(f"Error fetching email {seq_num} for {user}: {item_e}")

            except Exception as fe:
                logger.debug(f"Error opening folder {remote_folder} for {user}: {fe}")

        conn.commit()
        conn.close()

    except Exception as e:
        logger.warning(f"Mail sync error for {user}: {e}")
    finally:
        if mail:
            try:
                mail.close()
                mail.logout()
            except Exception:
                pass
    return results

# ==============================================================================
# FASTAPI ENDPOINTS
# ==============================================================================

@router.get("/list")
async def get_mail_list(
    account: str = Query("all"),
    folder: str = Query("all"),
    is_otp: Optional[int] = Query(None),
    search: str = Query(""),
    page: int = Query(1, ge=1),
    limit: int = Query(30, ge=1, le=100)
):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT id, account_email, folder, msg_uid, sender, sender_email, recipient, subject, snippet, date_str, timestamp, is_read, is_otp, otp_code, ai_summary, created_at FROM mail_messages WHERE 1=1"
    params = []

    if account and account.lower() not in ("all", "", "none"):
        query += " AND account_email = ?"
        params.append(account)

    if folder and folder.lower() not in ("all", "", "none"):
        query += " AND UPPER(folder) = ?"
        params.append(folder.upper())

    if is_otp is not None and is_otp != "":
        try:
            query += " AND is_otp = ?"
            params.append(int(is_otp))
        except (ValueError, TypeError):
            pass

    if search and search.strip():
        query += " AND (subject LIKE ? OR sender LIKE ? OR snippet LIKE ?)"
        wildcard = f"%{search.strip()}%"
        params.extend([wildcard, wildcard, wildcard])

    count_q = "SELECT COUNT(*) FROM (" + query + ")"
    cursor.execute(count_q, params)
    total = cursor.fetchone()[0]

    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, (page - 1) * limit])
    cursor.execute(query, params)
    rows = cursor.fetchall()
    items = [dict(r) for r in rows]

    # Stats breakdown
    cursor.execute("SELECT folder, COUNT(*) as cnt FROM mail_messages GROUP BY folder")
    folder_counts = {r["folder"]: r["cnt"] for r in cursor.fetchall()}

    cursor.execute("SELECT account_email, COUNT(*) as cnt FROM mail_messages GROUP BY account_email")
    account_counts = {r["account_email"]: r["cnt"] for r in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) FROM mail_messages WHERE is_otp = 1")
    otp_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM mail_messages")
    total_all = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM mail_messages WHERE UPPER(folder) = 'INBOX'")
    total_inbox = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM mail_messages WHERE UPPER(folder) = 'TRASH'")
    total_trash = cursor.fetchone()[0]

    conn.close()

    return {
        "code": 200,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "folder_counts": folder_counts,
            "account_counts": account_counts,
            "otp_count": otp_count,
            "stats": {
                "total_all": total_all,
                "total_inbox": total_inbox,
                "total_trash": total_trash,
                "total_otp": otp_count
            }
        }
    }

@router.get("/detail/{mail_id}")
async def get_mail_detail(mail_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mail_messages WHERE id = ?", (mail_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return JSONResponse(status_code=404, content={"code": 404, "message": "Email not found"})
    return {
        "code": 200,
        "data": dict(row)
    }

@router.get("/raw_html/{mail_id}")
async def get_mail_raw_html(mail_id: int, theme: str = Query("auto")):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT body_html, body_text, subject FROM mail_messages WHERE id = ?", (mail_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return HTMLResponse("<html><body>邮件不存在</body></html>", status_code=404)
    
    raw_html = row["body_html"] or ""
    raw_text = row["body_text"] or ""

    if not raw_html:
        escaped = (raw_text or "（无邮件正文）").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
        content_html = f"<div class='mail-plain-wrapper' style='font-family:inherit; white-space:pre-wrap; font-size:14.5px;'>{escaped}</div>"
    else:
        content_html = raw_html

    style_block = """
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style id="mailThemeStyle">
    :root { color-scheme: light dark; }
    html, body {
      margin: 0;
      padding: 20px 24px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif !important;
      font-size: 14.5px;
      line-height: 1.65;
      word-break: break-word;
      transition: background-color 0.2s ease, color 0.2s ease;
    }
    img { max-width: 100% !important; height: auto !important; }
    table { max-width: 100% !important; }
    pre, code { white-space: pre-wrap; font-family: 'JetBrains Mono', Consolas, monospace; }

    /* === 1. 浅色原貌 (Daytime / Clean Paper White) === */
    html.theme-light, html.theme-light body {
      background-color: #ffffff !important;
      color: #0f172a !important;
      color-scheme: light !important;
    }
    html.theme-light a { color: #0284c7 !important; }

    /* === 2. 柔和护眼 (Warm Sepia / Parchment) === */
    html.theme-eyecare, html.theme-eyecare body {
      background-color: #faf6ee !important;
      color: #2d261e !important;
      color-scheme: light !important;
    }
    html.theme-eyecare a { color: #b45309 !important; }
    html.theme-eyecare hr { border-color: rgba(180, 83, 9, 0.15) !important; }
    html.theme-eyecare [bgcolor="#ffffff" i], html.theme-eyecare [bgcolor="#fff" i], html.theme-eyecare [bgcolor="white" i],
    html.theme-eyecare [bgcolor^="#f" i], html.theme-eyecare [bgcolor^="#e" i] {
      background-color: #f3ece0 !important;
    }
    html.theme-eyecare [style*="background" i][style*="#fff" i],
    html.theme-eyecare [style*="background" i][style*="#f" i],
    html.theme-eyecare [style*="background" i][style*="#e" i],
    html.theme-eyecare [style*="background" i][style*="white" i],
    html.theme-eyecare [style*="background" i][style*="rgb(255" i],
    html.theme-eyecare [style*="background" i][style*="rgb(250" i],
    html.theme-eyecare [style*="background" i][style*="rgb(24" i] {
      background-color: #f3ece0 !important;
    }
    html.theme-eyecare p, html.theme-eyecare span, html.theme-eyecare td, html.theme-eyecare th, 
    html.theme-eyecare div, html.theme-eyecare li, html.theme-eyecare font, html.theme-eyecare b, html.theme-eyecare strong {
      color: #2d261e !important;
    }

    /* === 3. 深色护眼 (Midnight Obsidian Night Mode) === */
    html.theme-dark, html.theme-dark body {
      background-color: #0b0f19 !important;
      color: #e2e8f0 !important;
      color-scheme: dark !important;
    }
    html.theme-dark a { color: #38bdf8 !important; }
    html.theme-dark hr { border-color: rgba(255, 255, 255, 0.12) !important; }
    html.theme-dark [bgcolor="#ffffff" i], html.theme-dark [bgcolor="#fff" i], html.theme-dark [bgcolor="white" i],
    html.theme-dark [bgcolor^="#f" i], html.theme-dark [bgcolor^="#e" i] {
      background-color: #151d2f !important;
    }
    html.theme-dark [style*="background" i][style*="#fff" i],
    html.theme-dark [style*="background" i][style*="#f" i],
    html.theme-dark [style*="background" i][style*="#e" i],
    html.theme-dark [style*="background" i][style*="white" i],
    html.theme-dark [style*="background" i][style*="rgb(255" i],
    html.theme-dark [style*="background" i][style*="rgb(250" i],
    html.theme-dark [style*="background" i][style*="rgb(24" i] {
      background-color: #151d2f !important;
    }
    html.theme-dark p, html.theme-dark span, html.theme-dark td, html.theme-dark th, 
    html.theme-dark div, html.theme-dark li, html.theme-dark font, html.theme-dark b, html.theme-dark strong {
      color: #cbd5e1 !important;
    }
    html.theme-dark h1, html.theme-dark h2, html.theme-dark h3, html.theme-dark h4, html.theme-dark h5, html.theme-dark h6 {
      color: #f8fafc !important;
    }
    html.theme-dark img {
      filter: brightness(0.94) contrast(1.04);
    }
  </style>
  <script>
    (function() {
      function normalizeMailLuminance(doc, theme) {
        if (!doc || !doc.body) return;
        if (theme === 'light') {
          var modified = doc.querySelectorAll('[data-mail-theme-overridden]');
          for (var i = 0; i < modified.length; i++) {
            var el = modified[i];
            el.style.backgroundColor = el.getAttribute('data-prev-bg') || '';
            el.style.color = el.getAttribute('data-prev-color') || '';
            el.removeAttribute('data-mail-theme-overridden');
          }
          return;
        }

        var targetBg = (theme === 'dark') ? '#151d2f' : '#f3ece0';
        var targetColor = (theme === 'dark') ? '#cbd5e1' : '#2d261e';

        var elements = doc.querySelectorAll('div, table, td, tr, section, article, main, p, span, h1, h2, h3, h4, font, b, strong, li');
        for (var j = 0; j < elements.length; j++) {
          var el = elements[j];
          var cs = window.getComputedStyle ? window.getComputedStyle(el) : null;
          if (!cs) continue;

          var bg = cs.backgroundColor;
          if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
            var rgb = bg.match(/\\d+/g);
            if (rgb && rgb.length >= 3) {
              var r = parseInt(rgb[0]), g = parseInt(rgb[1]), b = parseInt(rgb[2]);
              var lum = 0.299 * r + 0.587 * g + 0.114 * b;
              if (lum > 175) {
                if (!el.hasAttribute('data-mail-theme-overridden')) {
                  el.setAttribute('data-prev-bg', el.style.backgroundColor || '');
                  el.setAttribute('data-mail-theme-overridden', '1');
                }
                el.style.setProperty('background-color', targetBg, 'important');
              }
            }
          }

          var color = cs.color;
          if (color) {
            var rgbC = color.match(/\\d+/g);
            if (rgbC && rgbC.length >= 3) {
              var rc = parseInt(rgbC[0]), gc = parseInt(rgbC[1]), bc = parseInt(rgbC[2]);
              var lumC = 0.299 * rc + 0.587 * gc + 0.114 * bc;
              if (theme === 'dark' && lumC < 100) {
                if (!el.hasAttribute('data-mail-theme-overridden')) {
                  el.setAttribute('data-prev-color', el.style.color || '');
                  el.setAttribute('data-mail-theme-overridden', '1');
                }
                el.style.setProperty('color', targetColor, 'important');
              } else if (theme === 'eyecare' && lumC > 200) {
                if (!el.hasAttribute('data-mail-theme-overridden')) {
                  el.setAttribute('data-prev-color', el.style.color || '');
                  el.setAttribute('data-mail-theme-overridden', '1');
                }
                el.style.setProperty('color', targetColor, 'important');
              }
            }
          }
        }
      }

      function applyTheme(t) {
        var cls = 'theme-light';
        if (t === 'eyecare') {
          cls = 'theme-eyecare';
        } else if (t === 'dark') {
          cls = 'theme-dark';
        } else if (t === 'light') {
          cls = 'theme-light';
        } else {
          try {
            var isParentLight = window.parent && window.parent.document && window.parent.document.documentElement.classList.contains('theme-light');
            cls = isParentLight ? 'theme-light' : 'theme-dark';
          } catch(e) {
            cls = 'theme-light';
          }
        }
        document.documentElement.className = cls;
        document.documentElement.setAttribute('data-pulseos-theme', cls);
        var normTheme = (cls === 'theme-eyecare') ? 'eyecare' : ((cls === 'theme-dark') ? 'dark' : 'light');
        try {
          normalizeMailLuminance(document, normTheme);
        } catch(e) {}
      }

      window.setPulseosTheme = applyTheme;
      window.applyTheme = applyTheme;
      window.applyPulseosTheme = applyTheme;
      window.normalizeMailLuminance = normalizeMailLuminance;

      var p = new URLSearchParams(window.location.search);
      applyTheme(p.get('theme') || 'auto');

      window.addEventListener('message', function(e) {
        if (e.data && e.data.action === 'setTheme') {
          applyTheme(e.data.theme);
        }
      });
      document.addEventListener('DOMContentLoaded', function() {
        var curTheme = document.documentElement.getAttribute('data-pulseos-theme') || 'auto';
        applyTheme(curTheme.replace('theme-', ''));
      });
    })();
  </script>
"""

    if '<head>' in content_html.lower():
        head_pos = re.search(r'<head[^>]*>', content_html, re.IGNORECASE)
        if head_pos:
            end = head_pos.end()
            return HTMLResponse(content_html[:end] + '\n' + style_block + '\n' + content_html[end:])
    
    # Fragment without head
    wrapped = f"<!DOCTYPE html><html><head>{style_block}</head><body>{content_html}</body></html>"
    return HTMLResponse(wrapped)

@router.post("/sync")
async def trigger_mail_sync(limit: int = Query(15)):
    """
    Triggers concurrent synchronization across all 4 mailboxes for both INBOX and TRASH.
    """
    cfg = load_config()
    accounts = [a for a in cfg.get("accounts", []) if a.get("enabled", True) and a.get("auth_code")]

    start_t = time.time()
    tasks = [asyncio.to_thread(sync_single_account, acc, limit) for acc in accounts]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    synced_total = 0
    new_count = 0
    for res in results:
        if isinstance(res, list):
            synced_total += len(res)
            new_count += sum(1 for r in res if not r.get("cached", False))

    duration = round(time.time() - start_t, 2)
    logger.info(f"📬 Synced {synced_total} emails ({new_count} new) across {len(accounts)} accounts in {duration}s")

    return {
        "code": 200,
        "message": f"成功同步 4 大邮箱（总扫描 {synced_total} 封，新增/更新 {new_count} 封，耗时 {duration} 秒）",
        "synced_count": synced_total,
        "new_count": new_count,
        "duration": duration
    }

@router.get("/stats")
async def get_mail_stats():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM mail_messages")
    total_all = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM mail_messages WHERE UPPER(folder) = 'INBOX'")
    total_inbox = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM mail_messages WHERE UPPER(folder) = 'TRASH'")
    total_trash = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM mail_messages WHERE is_otp = 1")
    total_otp = cursor.fetchone()[0]

    cursor.execute("SELECT account_email, COUNT(*) as cnt FROM mail_messages GROUP BY account_email")
    accounts = {r["account_email"]: r["cnt"] for r in cursor.fetchall()}

    conn.close()

    return {
        "code": 200,
        "data": {
            "total_all": total_all,
            "total_inbox": total_inbox,
            "total_trash": total_trash,
            "total_otp": total_otp,
            "accounts": accounts
        }
    }

@router.post("/ai-summary/{mail_id}")
@router.post("/summarize/{mail_id}")
@router.get("/ai-summary/{mail_id}")
@router.get("/summarize/{mail_id}")
async def summarize_single_mail(mail_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mail_messages WHERE id = ?", (mail_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return JSONResponse(status_code=404, content={"code": 404, "message": "Email not found"})

    if row["ai_summary"]:
        conn.close()
        return {"code": 200, "summary": row["ai_summary"], "data": {"summary": row["ai_summary"]}}

    mail_dict = dict(row)
    conn.close()

    prompt = f"""
请以专业行政秘书的口吻，对这封邮件进行超高密度的中文提炼：
1. 用【一句话结论】说明这封邮件在讲什么；
2. 用 2~3 个 Bullet Points 提炼邮件的核心细节、金额、日期、业务主体；
3. 【行动项提醒】：明确指出用户是否需要回复、付款、授权、到期提醒或无需操作。

发件人: {mail_dict['sender']} ({mail_dict['sender_email']})
收件人: {mail_dict['recipient']} (目标邮箱: {mail_dict['account_email']})
主题: {mail_dict['subject']}
日期: {mail_dict['date_str']}
正文摘要:
{mail_dict['snippet']}
正文前1000字:
{(mail_dict['body_text'] or '')[:1000]}
"""

    api_key = get_deepseek_key()
    try:
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一位专业的双语商务与技术秘书，精通多语言邮件速读与核心行动项提炼。回复使用优美排版的 Markdown。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.2
            }).encode("utf-8")
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            summary = data["choices"][0]["message"]["content"]
            
            # Cache in SQLite
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE mail_messages SET ai_summary = ? WHERE id = ?", (summary, mail_id))
            conn.commit()
            conn.close()

            return {"code": 200, "summary": summary, "data": {"summary": summary}}
    except Exception as e:
        logger.error(f"Single mail AI summary error: {e}")
        return {"code": 500, "message": f"AI 摘要生成失败: {e}"}

@router.post("/ai-digest")
@router.post("/ai_digest")
@router.get("/ai-digest")
@router.get("/ai_digest")
async def generate_mail_digest(folder: str = Query("all")):
    """
    Generates a consolidated intelligence briefing of all recent emails across all 4 accounts.
    """
    conn = get_db()
    cursor = conn.cursor()
    if folder and folder.lower() not in ("all", "", "none"):
        cursor.execute("""
            SELECT account_email, folder, sender, subject, snippet, date_str, timestamp
            FROM mail_messages
            WHERE UPPER(folder) = ?
            ORDER BY timestamp DESC LIMIT 30
        """, (folder.upper(),))
    else:
        cursor.execute("""
            SELECT account_email, folder, sender, subject, snippet, date_str, timestamp
            FROM mail_messages
            ORDER BY timestamp DESC LIMIT 30
        """)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        empty_msg = "📬 暂无最近邮件记录，点击「⚡ 实时同步 4 大邮箱」即可瞬间聚合拉取最新邮件并生成简报。"
        return {
            "code": 200,
            "summary": empty_msg,
            "data": {"report": empty_msg, "summary": empty_msg}
        }

    mail_lines = []
    for r in rows:
        dt = datetime.datetime.fromtimestamp(r["timestamp"] / 1000).strftime("%m-%d %H:%M")
        mail_lines.append(f"[{dt}] [{r['account_email']}] 发件人: {r['sender']} | 主题: {r['subject']} | 摘要: {r['snippet']}")

    blob = "\n".join(mail_lines)
    prompt = f"""
你是一位顶级的数字私人秘书。以下是用户 4 个核心邮箱（QQ邮箱 3512473224@qq.com、日常Gmail ppday666@gmail.com、工作Gmail clevercccp@gmail.com、备用Gmail ppdayup@gmail.com）最近聚合收到的邮件流。
请为用户生成一份【全渠道邮件智能资产早报/晚报】：
1. 🚨 【紧急/关键待办】：需要用户近期关注、处理、授权或续费的重要事项；
2. 💼 【工作与技术订阅】：来自 GitHub、OpenAI、Cloudflare、AWS 等平台的开发动态；
3. 🔐 【安全与账号变动】：登录提醒、验证码与密码重置；
4. 🗑️ 【垃圾与营销快筛】：简要说明哪些是推销/广告（无需关注）；
5. 💡 【秘书今日建议】：给用户的一句话全局行动指引。

邮件流水如下：
{blob}
"""

    api_key = get_deepseek_key()
    try:
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一位精炼干练的高级个人助理，回复采用赏心悦目的 Markdown 格式，层级清晰。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1200,
                "temperature": 0.3
            }).encode("utf-8")
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            summary = data["choices"][0]["message"]["content"]
            return {
                "code": 200,
                "summary": summary,
                "data": {"report": summary, "summary": summary},
                "mail_count": len(rows)
            }
    except Exception as e:
        logger.error(f"Mail digest error: {e}")
        fallback_msg = f"✨ **4大邮箱邮件速报**（本地概览）：当前已聚合监控 {len(rows)} 封最近邮件。点击各邮件可查看全文及单篇 AI 深度解析。"
        return {
            "code": 200,
            "summary": fallback_msg,
            "data": {"report": fallback_msg, "summary": fallback_msg},
            "mail_count": len(rows),
            "error": str(e)
        }

@router.delete("/{mail_id}")
async def delete_mail_local(mail_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM mail_messages WHERE id = ?", (mail_id,))
    conn.commit()
    conn.close()
    return {"code": 200, "message": "Deleted from local hub"}
