from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from datetime import datetime

import config
import database as db
import product_lookup

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
 

def handle_scan(barcode: str) -> dict:
    # Real-time lookup from public APIs
    info = product_lookup.lookup(barcode)
    info["scanned_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.save_scan(info)
    return info


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.get_json(force=True)
    barcode = (data.get("barcode") or "").strip()
    if not barcode:
        return jsonify({"success": False, "message": "No barcode provided"}), 400

    if db.barcode_already_scanned(barcode):
        return jsonify({"success": False, "duplicate": True, "barcode": barcode})

    result = handle_scan(barcode)
    socketio.emit("scan_result", result)
    return jsonify(result)


@app.route("/api/products", methods=["GET"])
def api_products():
    return jsonify(db.get_all_scans())


@app.route("/api/clear", methods=["POST"])
def api_clear():
    db.clear_scans()
    return jsonify({"success": True})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    db.init_db()
    socketio.run(app, host=config.HOST, port=config.PORT, debug=config.DEBUG)