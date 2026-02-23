import os
import uuid
from abc import ABC, abstractmethod
from io import BytesIO
from functools import lru_cache

import pymysql
from flask import Flask, request, send_file, jsonify, abort
from werkzeug.utils import secure_filename

# =============================
# Storage Interface
# =============================
class ObjectStorage(ABC):
    @abstractmethod
    def upload(self, key, file, content_type, filename):
        pass

    @abstractmethod
    def download(self, key):
        pass


# =============================
# MySQL Storage
# =============================
class MYSQLStorage(ObjectStorage):
    def __init__(self):
        self.conn = pymysql.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            autocommit=True,
            connect_timeout=5,
            read_timeout=30,
            write_timeout=30,
        )

    def upload(self, key, file, content_type, filename):
        data = file.read()

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO images (id, filename, content_type, data)
                VALUES (%s, %s, %s, %s)
                """,
                (key, filename, content_type, data),
            )

    def download(self, key):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT data, content_type, filename FROM images WHERE id = %s",
                (key,),
            )
            row = cur.fetchone()

        if not row:
            raise FileNotFoundError()

        data, content_type, filename = row
        return BytesIO(data), content_type, filename


# =============================
# Storage Factory
# =============================
def get_storage():
    provider = (os.getenv("STORAGE_PROVIDER") or "").lower()
    if provider == "mysql":
        return MYSQLStorage()
    raise RuntimeError("Invalid STORAGE_PROVIDER. Use: mysql")


@lru_cache(maxsize=1)
def storage_client():
    return get_storage()


# =============================
# Flask App
# =============================
app = Flask(__name__)

ALLOWED = {"png", "jpg", "jpeg", "gif"}


def allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED


# =============================
# Health Check
# =============================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# =============================
# Upload API
# =============================
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")

    if not file or not file.filename:
        return jsonify({"error": "No file provided"}), 400

    filename = secure_filename(file.filename)

    if not allowed(filename):
        return jsonify({"error": "Invalid file type"}), 400

    image_id = str(uuid.uuid4())

    storage_client().upload(
        image_id,
        file,
        file.content_type,
        filename
    )

    return jsonify({
        "image_id": image_id,
        "message": "Upload successful"
    }), 201


# =============================
# View Image (inline)
# =============================
@app.route("/images/<image_id>", methods=["GET"])
def show_image(image_id):
    try:
        file, mime, filename = storage_client().download(image_id)
    except Exception:
        abort(404)

    return send_file(
        file,
        mimetype=mime or "application/octet-stream",
        download_name=filename
    )


# =============================
# Download Image (attachment)
# =============================
@app.route("/download/<image_id>", methods=["GET"])
def download_image(image_id):
    try:
        file, mime, filename = storage_client().download(image_id)
    except Exception:
        abort(404)

    return send_file(
        file,
        mimetype=mime or "application/octet-stream",
        download_name=filename,
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)