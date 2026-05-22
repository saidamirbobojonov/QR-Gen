"""
QR Code Generator – web backend.
Logic from qr_gui.py (URL mode) and qr-multi.py (vCard mode), no tkinter.

Run:  python server.py
Open: http://localhost:5000
"""

from flask import Flask, request, jsonify, send_from_directory, redirect, Response
import qrcode
from PIL import Image
import io, base64, secrets, json, os, html
from datetime import date

app = Flask(__name__)

STORE_FILE = "qr_store.json"


# ── store ──────────────────────────────────────────────────────────────────────

def load_store():
    if os.path.exists(STORE_FILE):
        with open(STORE_FILE) as f:
            return json.load(f)
    return {}


def save_store(store):
    with open(STORE_FILE, "w") as f:
        json.dump(store, f, indent=2)


# ── from qr-multi.py ───────────────────────────────────────────────────────────

def escape_vcard(text: str) -> str:
    return text.replace("\n", "\\n").replace(";", "\\;").replace(",", "\\,")


def build_vcard(name, phone, address, website):
    lines = ["BEGIN:VCARD", "VERSION:3.0"]
    if name:
        lines.append(f"FN:{escape_vcard(name)}")
    if phone:
        lines.append(f"TEL;TYPE=CELL:{escape_vcard(phone)}")
    if address:
        lines.append(f"ADR:;;{escape_vcard(address)};;;;")
    if website:
        lines.append(f"URL:{escape_vcard(website)}")
    lines.append("END:VCARD")
    return "\n".join(lines)


# ── shared QR render ───────────────────────────────────────────────────────────

def render_qr(text: str) -> str:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ── routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/asset/<path:path>")
def assets(path):
    return send_from_directory("asset", path)


@app.route("/go/<qr_id>")
def go(qr_id):
    store = load_store()
    entry = store.get(qr_id)
    if not entry:
        return _status_page("Not Found", "This QR code does not exist.", "#888"), 404

    expires = entry.get("expires")
    if expires and date.today() > date.fromisoformat(expires):
        return _status_page("QR Code Expired",
                            f"This QR code expired on {expires}.", "#ff6b6b"), 410

    if entry["type"] == "url":
        return redirect(entry["url"])

    if entry["type"] == "vcard":
        return _vcard_page(entry, qr_id)

    return "Unknown type.", 400


@app.route("/go/<qr_id>/vcf")
def download_vcf(qr_id):
    store = load_store()
    entry = store.get(qr_id)
    if not entry or entry["type"] != "vcard":
        return "Not found.", 404
    expires = entry.get("expires")
    if expires and date.today() > date.fromisoformat(expires):
        return _status_page("QR Code Expired",
                            f"This QR code expired on {expires}.", "#ff6b6b"), 410
    name = entry.get("name", "contact")
    return Response(
        entry["vcard"],
        mimetype="text/vcard",
        headers={"Content-Disposition": f'attachment; filename="{name}.vcf"'},
    )


@app.route("/api/generate", methods=["POST"])
def generate():
    body    = request.get_json(force=True) or {}
    mode    = body.get("mode", "")
    expires = body.get("expires", "").strip() or None

    if expires:
        try:
            exp_date = date.fromisoformat(expires)
            if exp_date <= date.today():
                return jsonify({"error": "Expiry date must be in the future"}), 400
        except ValueError:
            return jsonify({"error": "Invalid expiry date"}), 400

    store    = load_store()
    qr_id    = secrets.token_urlsafe(8)
    base_url = request.host_url.rstrip("/")
    link     = f"{base_url}/go/{qr_id}"
    exp_tag  = f"  ·  expires {expires}" if expires else ""

    # URL mode — qr_gui.py logic
    if mode == "url":
        url = body.get("url", "").strip()
        if not url:
            return jsonify({"error": "URL is required"}), 400
        store[qr_id] = {"type": "url", "url": url, "expires": expires}
        save_store(store)
        return jsonify({"image": render_qr(link), "display": url + exp_tag})

    # vCard mode — qr-multi.py logic
    if mode == "vcard":
        name    = body.get("name",    "").strip()
        phone   = body.get("phone",   "").strip()
        address = body.get("address", "").strip()
        website = body.get("website", "").strip()
        if not any([name, phone, address, website]):
            return jsonify({"error": "Fill in at least one field"}), 400
        vcard   = build_vcard(name, phone, address, website)
        parts   = [x for x in [name, phone, website] if x]
        display = ("vCard — " + " · ".join(parts) if parts else "vCard contact") + exp_tag
        store[qr_id] = {
            "type": "vcard", "vcard": vcard,
            "name": name, "phone": phone, "address": address,
            "website": website, "expires": expires,
        }
        save_store(store)
        return jsonify({"image": render_qr(link), "display": display})

    return jsonify({"error": "Invalid mode"}), 400


# ── HTML helpers ───────────────────────────────────────────────────────────────

def _status_page(title, message, color):
    t = html.escape(title)
    m = html.escape(message)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t}</title>
<style>
body{{background:#0a0a0a;color:#fff;font-family:sans-serif;
     display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}
.b{{text-align:center;padding:40px}}
h1{{color:{color};margin-bottom:12px;font-size:2rem}}
p{{color:rgba(255,255,255,.5);font-size:.9rem}}
</style></head>
<body><div class="b"><h1>{t}</h1><p>{m}</p></div></body></html>"""


def _vcard_page(e, qr_id):
    def row(label, val, href=None):
        v = html.escape(val)
        content = f'<a href="{html.escape(href)}">{v}</a>' if href else v
        return (f'<div class="row"><div class="lbl">{label}</div>'
                f'<div class="val">{content}</div></div>')

    rows = ""
    if e.get("phone"):
        rows += row("Phone", e["phone"], f'tel:{e["phone"]}')
    if e.get("address"):
        rows += row("Address", e["address"])
    if e.get("website"):
        rows += row("Website", e["website"], e["website"])

    name    = html.escape(e.get("name", "Contact"))
    expires = e.get("expires")
    exp_row = (f'<div class="exp">Expires {html.escape(expires)}</div>'
               if expires else "")

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name}</title>
<style>
body{{background:#0a0a0a;color:#fff;font-family:sans-serif;
     display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}
.card{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
       border-radius:16px;padding:32px 40px;max-width:360px;width:90%}}
h1{{font-size:1.5rem;margin:0 0 20px;font-weight:600}}
.row{{margin-bottom:14px}}
.lbl{{font-size:.7rem;text-transform:uppercase;letter-spacing:1px;
      color:rgba(255,255,255,.35);margin-bottom:3px}}
.val{{font-size:.9rem;color:rgba(255,255,255,.75)}}
a{{color:#fff;text-decoration:none}}
.exp{{font-size:.75rem;color:rgba(255,255,255,.3);margin-top:16px}}
.dl{{display:inline-block;margin-top:24px;border:1px solid rgba(255,255,255,.25);
     padding:10px 24px;border-radius:100px;font-size:.85rem;
     text-decoration:none;color:#fff}}
</style></head>
<body><div class="card">
<h1>{name}</h1>
{rows}
{exp_row}
<a class="dl" href="/go/{qr_id}/vcf">Download vCard</a>
</div></body></html>"""


if __name__ == "__main__":
    app.run(debug=True, port=5000)
