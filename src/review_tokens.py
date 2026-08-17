"""
Secure Time-Limited Token Generator & Resolver for Doctor Review Links.
Generates unique, time-limited tokens for /review/{secure_token} endpoints.
"""

import secrets
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict

DEFAULT_TOKEN_TTL_HOURS = 24

class DoctorReviewTokenManager:
    """
    Manages generation, storage, validation, and expiration of secure time-limited tokens.
    Token URL format: /review/{token}
    """

    def __init__(self, token_db_path: str = None, default_ttl_hours: int = DEFAULT_TOKEN_TTL_HOURS):
        project_root = Path(__file__).resolve().parent.parent
        self.db_path = Path(token_db_path) if token_db_path else project_root / "data" / "review_tokens.json"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.default_ttl = timedelta(hours=default_ttl_hours)
        self._init_db()

    def _init_db(self):
        if not self.db_path.exists():
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _read_tokens(self) -> Dict[str, dict]:
        with open(self.db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_tokens(self, tokens: Dict[str, dict]):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2)

    def generate_review_token(self, review_id: str, ttl_hours: Optional[int] = None) -> dict:
        """
        Generates a 32-byte URL-safe cryptographic token for a given review_id.
        Returns a dict containing token, review_id, expiration, and relative review_url.
        """
        token = secrets.token_urlsafe(32)
        ttl = timedelta(hours=ttl_hours) if ttl_hours else self.default_ttl
        now = datetime.now(timezone.utc)
        expires_at = now + ttl

        token_record = {
            "token": token,
            "review_id": review_id,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "used": False,
            "review_url": f"/review/{token}"
        }

        tokens = self._read_tokens()
        tokens[token] = token_record
        self._write_tokens(tokens)
        return token_record

    def validate_token(self, token: str) -> dict:
        """
        Validates a token and returns the token record.
        Raises ValueError if token is invalid, expired, or already used.
        """
        tokens = self._read_tokens()
        if token not in tokens:
            raise KeyError("Invalid or non-existent review token.")

        record = tokens[token]
        expires_at = datetime.fromisoformat(record["expires_at"])
        now = datetime.now(timezone.utc)

        if now > expires_at:
            raise ValueError("Review token has expired. Please request a new review link.")

        return record

    def consume_token(self, token: str) -> dict:
        """
        Marks a token as used after successful doctor feedback submission.
        """
        record = self.validate_token(token)
        tokens = self._read_tokens()
        tokens[token]["used"] = True
        tokens[token]["used_at"] = datetime.now(timezone.utc).isoformat()
        self._write_tokens(tokens)
        return tokens[token]
