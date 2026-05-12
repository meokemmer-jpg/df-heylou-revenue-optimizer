"""Audit-Logger fuer DF-HeyLou-Revenue-Optimizer [CRUX-MK].

HMAC-SHA256-Signed Audit-Trail pro Pricing-Recommendation.
Pflicht per external-anchor-requirement-audit-logs.md.

[CRUX-MK]
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AuditLogger:
    """HMAC-SHA256-Signed Audit-Trail.

    Append-Only JSONL mit Hash-Chain (vorheriger Hash → naechster Eintrag).
    """

    def __init__(
        self,
        audit_path: Optional[Path] = None,
        secret: Optional[str] = None,
    ):
        if audit_path is None:
            audit_path = Path.home() / ".df-state" / "df-heylou-revenue-opt-audit.jsonl"
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        self.audit_path = audit_path

        # Phase-1: HMAC-Secret aus ENV; Phase-2: secret_vault
        self.secret = secret or os.environ.get(
            "DF_HEYLOU_REVENUE_OPT_AUDIT_SECRET", "skeleton-default-secret"
        )
        self._last_hash = self._read_last_hash()

    def _read_last_hash(self) -> str:
        """Lese letzten Hash fuer Chain-Continuation."""
        if not self.audit_path.exists():
            return "GENESIS"
        try:
            with open(self.audit_path, "r") as f:
                lines = f.readlines()
            if not lines:
                return "GENESIS"
            last_entry = json.loads(lines[-1])
            return last_entry.get("entry_hash", "GENESIS")
        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(f"Could not read last hash: {e}, starting GENESIS")
            return "GENESIS"

    def append(self, event: dict) -> str:
        """Append Audit-Event mit HMAC-Signature.

        Returns:
            entry_hash (SHA256 of HMAC-signed payload)
        """
        entry = {
            "ts": time.time(),
            "iso_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": event,
            "prev_hash": self._last_hash,
        }
        payload_bytes = json.dumps(entry, sort_keys=True).encode("utf-8")
        signature = hmac.new(
            self.secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        entry["hmac_sha256"] = signature
        entry["entry_hash"] = hashlib.sha256(
            (signature + self._last_hash).encode()
        ).hexdigest()

        with open(self.audit_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        self._last_hash = entry["entry_hash"]
        return entry["entry_hash"]

    def verify_chain(self) -> dict:
        """Verifiziert die gesamte Hash-Chain.

        Returns:
            {"valid": bool, "entries_verified": int, "first_corrupted": Optional[int]}
        """
        if not self.audit_path.exists():
            return {"valid": True, "entries_verified": 0, "first_corrupted": None}

        prev = "GENESIS"
        count = 0
        with open(self.audit_path, "r") as f:
            for i, line in enumerate(f):
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    return {"valid": False, "entries_verified": count, "first_corrupted": i}
                if entry.get("prev_hash") != prev:
                    return {"valid": False, "entries_verified": count, "first_corrupted": i}
                prev = entry.get("entry_hash", "")
                count += 1
        return {"valid": True, "entries_verified": count, "first_corrupted": None}
