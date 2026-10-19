
from flask import Flask, request, jsonify
import sqlite3
import os
from pathlib import Path

app = Flask(__name__)

# Lokasi database SQLite
DB_PATH = os.environ.get(
    "DB_PATH",
    str(Path(__file__).resolve().parent / "app.db")
)


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    # Pastikan folder database tersedia
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    conn = connect_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


# Membuat tabel saat aplikasi dijalankan
init_db()


@app.route('/')
def hello():
    return (
        "Halo dari Flask + Docker + Jenkins! "
        "Database SQLite aktif. "
        "Cek koneksi melalui /db-check."
    )


@app.route('/db-check')
def db_check():
    conn = connect_db()
    try:
        result = conn.execute(
            "SELECT sqlite_version()"
        ).fetchone()

        return jsonify({
            "database": "SQLite",
            "status": "connected",
            "version": result[0]
        })
    finally:
        conn.close()


@app.route('/messages', methods=['GET', 'POST'])
def messages():
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form
        message = (data.get('message') or '').strip()

        if not message:
            return jsonify({
                "error": "Pesan tidak boleh kosong"
            }), 400

        conn = connect_db()
        try:
            cursor = conn.execute(
                "INSERT INTO messages (message) VALUES (?)",
                (message,)
            )
            conn.commit()

            return jsonify({
                "id": cursor.lastrowid,
                "message": message,
                "status": "saved"
            }), 201
        finally:
            conn.close()

    conn = connect_db()
    try:
        rows = conn.execute(
            "SELECT id, message, created_at "
            "FROM messages ORDER BY id DESC"
        ).fetchall()

        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@app.route('/github-webhook', methods=['POST'])
def github_webhook():
    payload = request.get_json(silent=True)

    print("Webhook diterima dari GitHub")
    print(payload)

    return "Webhook received", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
