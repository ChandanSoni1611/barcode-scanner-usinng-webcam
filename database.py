import sqlite3
from config import DATABASE_PATH


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS scan_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode      TEXT    NOT NULL,
                name         TEXT,
                brand        TEXT,
                category     TEXT,
                price        TEXT,
                mfg_date     TEXT,
                exp_date     TEXT,
                hsn_code     TEXT,
                source       TEXT,
                scanned_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)


def save_scan(data: dict):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO scan_log
              (barcode, name, brand, category, price, mfg_date, exp_date, hsn_code, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("barcode"),
            data.get("name"),
            data.get("brand"),
            data.get("category"),
            data.get("price"),
            data.get("mfg_date"),
            data.get("exp_date"),
            data.get("hsn_code"),
            data.get("source"),
        ))


def get_all_scans():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM scan_log ORDER BY scanned_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def barcode_already_scanned(barcode: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM scan_log WHERE barcode = ? LIMIT 1", (barcode,)
        ).fetchone()
    return row is not None


def clear_scans():
    with get_connection() as conn:
        conn.execute("DELETE FROM scan_log")


def get_scan_count():
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM scan_log").fetchone()[0]