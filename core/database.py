"""
Database Access Module (SQLite)
================================
Stores certificate fingerprints, preprocessed images, quality metrics,
and unique Certificate IDs (e.g. CERT-8F31A2).
"""

import sqlite3
import json
import uuid
import datetime
from config import DB_PATH


class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes SQLite tables if they do not exist."""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS certificates (
                    cert_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    original_filename TEXT,
                    original_image_path TEXT NOT NULL,
                    preprocessed_image_path TEXT NOT NULL,
                    phash TEXT NOT NULL,
                    dhash TEXT NOT NULL,
                    ahash TEXT NOT NULL,
                    whash TEXT NOT NULL,
                    region_hashes TEXT,
                    quality_report TEXT,
                    metadata TEXT
                );
            """)
            conn.commit()

    @staticmethod
    def generate_cert_id():
        """Generates a clean, unique certificate ID, e.g. CERT-8F31A2"""
        short_hex = uuid.uuid4().hex[:6].upper()
        return f"CERT-{short_hex}"

    def save_certificate(
        self,
        cert_id,
        original_filename,
        original_image_path,
        preprocessed_image_path,
        hashes,
        region_hashes=None,
        quality_report=None,
        metadata=None
    ):
        """Inserts a new issuer certificate fingerprint record."""
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO certificates (
                    cert_id, created_at, original_filename,
                    original_image_path, preprocessed_image_path,
                    phash, dhash, ahash, whash,
                    region_hashes, quality_report, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cert_id,
                    created_at,
                    original_filename,
                    original_image_path,
                    preprocessed_image_path,
                    hashes["phash"],
                    hashes["dhash"],
                    hashes["ahash"],
                    hashes.get("whash", hashes["phash"]),
                    json.dumps(region_hashes or {}),
                    json.dumps(quality_report or {}),
                    json.dumps(metadata or {})
                )
            )
            conn.commit()
        return cert_id

    def get_certificate(self, cert_id):
        """Retrieves a certificate record by ID."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM certificates WHERE cert_id = ? COLLATE NOCASE",
                (cert_id.strip(),)
            ).fetchone()
            if not row:
                return None
            return {
                "cert_id": row["cert_id"],
                "created_at": row["created_at"],
                "original_filename": row["original_filename"],
                "original_image_path": row["original_image_path"],
                "preprocessed_image_path": row["preprocessed_image_path"],
                "phash": row["phash"],
                "dhash": row["dhash"],
                "ahash": row["ahash"],
                "whash": row["whash"],
                "region_hashes": json.loads(row["region_hashes"]) if row["region_hashes"] else {},
                "quality_report": json.loads(row["quality_report"]) if row["quality_report"] else {},
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            }

    def list_certificates(self, limit=20):
        """Lists recent certificates."""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT cert_id, created_at, original_filename, original_image_path, preprocessed_image_path, metadata FROM certificates ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [
                {
                    "cert_id": r["cert_id"],
                    "created_at": r["created_at"],
                    "original_filename": r["original_filename"],
                    "original_image_path": r["original_image_path"],
                    "preprocessed_image_path": r["preprocessed_image_path"],
                    "metadata": json.loads(r["metadata"]) if r["metadata"] else {}
                }
                for r in rows
            ]
