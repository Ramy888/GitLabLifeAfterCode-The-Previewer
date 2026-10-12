"""The release email: subject, plain text and email-safe HTML (tables and inline styles only)."""

from __future__ import annotations

import json
import os
import urllib.request
from html import escape

from store_review.report import STORES

SEVERITY_ORDER = ("blocker", "warning", "info")
# Served by the Cloud Run deploy (deploy/cloudrun/brand); email clients don't render SVG.
LOGO_URL = "https://time-tracker-web-57342278583.us-central1.run.app/brand/logo-96.png"
MAX_FINDINGS = 5

INK = "#111827"
MUTED = "#6B7280"
LINE = "#E5E7EB"
BRAND = "#3730A3"
GREEN = "#15803D"
GREEN_BG = "#DCFCE7"
RED = "#B91C1C"
RED_BG = "#FEE2E2"
AMBER = "#B45309"
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"


def _ready(doc: dict) -> bool:
    return all(s["status"] == "ready" for s in doc["scores"].values())


def _count(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def subject_line(doc: dict) -> str:
    app, s = doc["app"], doc["scores"]
    state = "is ready to submit" if _ready(doc) else "needs work"
    return f"{app['name']} v{app['version']} {state} · iOS {s['ios']['readiness']} · Android {s['android']['readiness']}"


def render_text(doc: dict, release_url: str) -> str:
    app = doc["app"]
    lines = [f"The Previewer finished the store review for {app['name']} v{app['version']}.", ""]
    for store, label in STORES.items():
        s = doc["scores"][store]
        lines.append(f"{label}: {s['status']}, readiness {s['readiness']} ({s['low']}–{s['high']}), "
                     f"{_count(s['blockers'], 'blocker')}, {_count(s['warnings'], 'warning')}")
    lines += ["", f"Release (report, store packages, signed app bundle): {release_url}", "",
              "Nothing was uploaded to any store. Submitting is your call."]
    return "\n".join(lines) + "\n"


def _store_card(label: str, s: dict) -> str:
    ready = s["status"] == "ready"
    colour, bg = (GREEN, GREEN_BG) if ready else (RED, RED_BG)
    pill = "Ready" if ready else "Blocked"
    width = max(2, min(100, int(s["readiness"])))
    return f"""<td width="50%" valign="top" style="padding:0 6px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid {LINE};border-radius:12px;">
    <tr><td style="padding:16px 18px 6px;font:600 14px {FONT};color:{INK};">{escape(label)}
      <span style="float:right;background:{bg};color:{colour};font:600 11px {FONT};padding:3px 9px;border-radius:999px;">{pill}</span></td></tr>
    <tr><td style="padding:2px 18px 0;font:700 40px {FONT};color:{INK};line-height:1.1;">{s['readiness']}<span style="font:400 14px {FONT};color:{MUTED};"> / 100</span></td></tr>
    <tr><td style="padding:10px 18px 4px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{LINE};border-radius:4px;"><tr>
        <td width="{width}%" style="background:{colour};height:6px;line-height:6px;font-size:0;border-radius:4px;">&nbsp;</td>
        <td style="height:6px;line-height:6px;font-size:0;">&nbsp;</td></tr></table></td></tr>
    <tr><td style="padding:6px 18px 16px;font:400 12px {FONT};color:{MUTED};">Range {s['low']}–{s['high']} ·
      {_count(s['blockers'], 'blocker')} · {_count(s['warnings'], 'warning')}</td></tr>
  </table></td>"""


def _findings_rows(doc: dict) -> str:
    findings = sorted(doc["findings"], key=lambda f: SEVERITY_ORDER.index(f["severity"]))
    shown, rest = findings[:MAX_FINDINGS], len(findings) - MAX_FINDINGS
    if not shown:
        return ""
    colour = {"blocker": RED, "warning": AMBER, "info": MUTED}
    rows = "".join(
        f"""<tr><td style="padding:9px 0;border-top:1px solid {LINE};font:400 13px {FONT};color:{INK};">
      <span style="color:{colour[f['severity']]};font-weight:600;">{escape(f['severity'].capitalize())}</span>
      <span style="color:{MUTED};"> · {escape(STORES.get(f['store'], 'Both stores'))} · {escape(f['id'])}</span><br>{escape(f['title'])}</td></tr>"""
        for f in shown)
    more = (f"""<tr><td style="padding:9px 0;border-top:1px solid {LINE};font:400 13px {FONT};color:{MUTED};">
      and {rest} more in the report</td></tr>""" if rest > 0 else "")
    return f"""<tr><td style="padding:24px 32px 0;font:600 13px {FONT};color:{INK};text-transform:uppercase;letter-spacing:.04em;">What the reviewers flagged</td></tr>
  <tr><td style="padding:6px 32px 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}{more}</table></td></tr>"""


def render_html(doc: dict, release_url: str) -> str:
    app = doc["app"]
    ready = _ready(doc)
    headline = "Ready to submit" if ready else "Needs work before you submit"
    sub = ("Both stores passed the rehearsal. Review the release, then submit when you're ready."
           if ready else "At least one store is blocked. The report lists what to fix.")
    bench = doc.get("benchmark")
    bench_line = (f"Rules benchmark: precision {bench['precision']:.2f}, recall {bench['recall']:.2f} on {bench['cases']} seeded cases."
                  if bench else "")
    url = escape(release_url, quote=True)
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(subject_line(doc))}</title></head><body style="margin:0;padding:0;background:#F3F4F6;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F3F4F6;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#FFFFFF;border-radius:16px;overflow:hidden;">
  <tr><td style="background:{BRAND};padding:18px 32px;">
    <table role="presentation" cellpadding="0" cellspacing="0"><tr>
      <td valign="middle"><img src="{LOGO_URL}" width="40" height="40" alt="The Previewer"
        style="display:block;border:0;border-radius:10px;"></td>
      <td valign="middle" style="padding-left:12px;font:700 17px {FONT};color:#FFFFFF;">The Previewer<br>
        <span style="font:400 12px {FONT};color:#C7D2FE;">iOS and Android store review rehearsal</span></td>
    </tr></table></td></tr>
  <tr><td style="padding:28px 32px 4px;font:400 13px {FONT};color:{MUTED};">{escape(app['name'])} · v{escape(str(app['version']))}</td></tr>
  <tr><td style="padding:0 32px;font:700 26px {FONT};color:{INK};">{headline}</td></tr>
  <tr><td style="padding:8px 32px 20px;font:400 15px {FONT};color:{MUTED};line-height:1.5;">{sub}</td></tr>
  <tr><td style="padding:0 26px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
    {_store_card(STORES['ios'], doc['scores']['ios'])}
    {_store_card(STORES['android'], doc['scores']['android'])}
  </tr></table></td></tr>
  <tr><td style="padding:24px 32px 0;">
    <a href="{url}" style="display:inline-block;background:{BRAND};color:#FFFFFF;font:600 15px {FONT};text-decoration:none;padding:12px 22px;border-radius:10px;">Open release v{escape(str(app['version']))}</a>
    <span style="font:400 13px {FONT};color:{MUTED};padding-left:10px;">report · store packages · signed app bundle</span></td></tr>
  {_findings_rows(doc)}
  <tr><td style="padding:28px 32px 28px;font:400 12px {FONT};color:{MUTED};line-height:1.6;border-top:1px solid {LINE};">
    Nothing was uploaded to any store. Submitting is your call.<br>{bench_line}<br>
    Sent by The Previewer · <a href="mailto:support@thepreviwer.dev" style="color:{MUTED};">support@thepreviwer.dev</a></td></tr>
</table></td></tr></table></body></html>
"""


def render_release_email(doc: dict, release_url: str) -> tuple[str, str, str]:
    return subject_line(doc), render_text(doc, release_url), render_html(doc, release_url)


def send(subject: str, text: str, html: str, to: str, sender: str) -> dict:
    """Send through Cloudflare Email Sending (REST). Needs CLOUDFLARE_EMAIL_TOKEN and CLOUDFLARE_ACCOUNT_ID."""
    account = os.environ["CLOUDFLARE_ACCOUNT_ID"]
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{account}/email/sending/send",
        data=json.dumps({"to": to, "from": sender, "subject": subject, "text": text, "html": html}).encode(),
        method="POST",
        headers={"Authorization": f"Bearer {os.environ['CLOUDFLARE_EMAIL_TOKEN']}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310 (fixed Cloudflare API host)
        return json.load(resp)
