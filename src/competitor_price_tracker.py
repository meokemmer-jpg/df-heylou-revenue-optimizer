"""Competitor-Price-Tracker [CRUX-MK].

Cross-OTA-Rate-Drift-Detection via Welle-37 cross_ota_rate_sync (Skeleton-Import).

Phase-1 Skeleton: Mock-Snapshots aus festen Test-Daten.
Phase-2: Live-Integration via _df_common.cross_ota_rate_sync + Real-OTA-APIs.

Pflicht-Properties (per env-var-gated-real-integration-default.md):
- Default: Mock-Mode
- Real-Mode via DF_HEYLOU_REVENUE_OPT_REAL_ENABLED + PHRONESIS_TICKET

[CRUX-MK]
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from statistics import mean, stdev
from typing import Optional


@dataclass
class CompetitorPriceSnapshot:
    """OTA-Snapshot fuer Hotel + Datum."""
    hotel_id: str
    snapshot_date: str
    competitor_rates_eur: dict[str, float]  # competitor_id -> rate
    avg_rate_eur: float
    median_rate_eur: float
    drift_stdev: float
    snapshot_ts: float
    source: str  # "mock" | "w37-cross-ota-sync" | "live-api"


class CompetitorPriceTracker:
    """Tracker fuer Cross-OTA-Rate-Drift.

    Konsumiert in Phase-2: _df_common.cross_ota_rate_sync.RateSnapshot.
    """

    def __init__(self, sandbox_mode: Optional[bool] = None):
        if sandbox_mode is None:
            sandbox_mode = (
                os.environ.get("DF_HEYLOU_REVENUE_OPT_REAL_ENABLED", "false").lower()
                != "true"
            )
        self.sandbox_mode = sandbox_mode
        self._mock_db: dict[tuple[str, str], dict[str, float]] = {}

    def register_mock_rates(
        self,
        hotel_id: str,
        snapshot_date: str,
        rates_by_competitor: dict[str, float],
    ) -> None:
        """Fuer Tests: Mock-Daten injizieren."""
        if not self.sandbox_mode:
            raise RuntimeError("Mock-Inject nur in Sandbox-Mode erlaubt")
        self._mock_db[(hotel_id, snapshot_date)] = dict(rates_by_competitor)

    def get_snapshot(
        self,
        hotel_id: str,
        snapshot_date: str,
    ) -> Optional[CompetitorPriceSnapshot]:
        """Snapshot abrufen (Mock oder Real via W37).

        Phase-1: aus _mock_db
        Phase-2: dispatch via _df_common.cross_ota_rate_sync
        """
        if self.sandbox_mode:
            rates = self._mock_db.get((hotel_id, snapshot_date))
            if not rates:
                return None
            source = "mock"
        else:
            # Phase-2: Echte W37-Integration
            # from _df_common.cross_ota_rate_sync import fetch_cross_ota_snapshot
            # rates = fetch_cross_ota_snapshot(hotel_id, snapshot_date)
            # source = "w37-cross-ota-sync"
            raise NotImplementedError(
                "Real-Mode pending W37 cross_ota_rate_sync Phase-2 + PHRONESIS_TICKET"
            )

        if not rates:
            return None

        vals = list(rates.values())
        avg = mean(vals) if vals else 0.0
        med = sorted(vals)[len(vals) // 2] if vals else 0.0
        drift = stdev(vals) if len(vals) > 1 else 0.0

        return CompetitorPriceSnapshot(
            hotel_id=hotel_id,
            snapshot_date=snapshot_date,
            competitor_rates_eur=dict(rates),
            avg_rate_eur=round(avg, 2),
            median_rate_eur=round(med, 2),
            drift_stdev=round(drift, 2),
            snapshot_ts=time.time(),
            source=source,
        )

    def detect_drift(
        self,
        snapshot_t0: CompetitorPriceSnapshot,
        snapshot_t1: CompetitorPriceSnapshot,
        threshold_pct: float = 5.0,
    ) -> dict:
        """Drift zwischen 2 Snapshots.

        Returns:
            {"drift_detected": bool, "delta_pct": float, "details": ...}
        """
        if snapshot_t0.avg_rate_eur == 0:
            return {"drift_detected": False, "delta_pct": 0.0, "details": "no-baseline"}
        delta = snapshot_t1.avg_rate_eur - snapshot_t0.avg_rate_eur
        delta_pct = (delta / snapshot_t0.avg_rate_eur) * 100
        return {
            "drift_detected": abs(delta_pct) >= threshold_pct,
            "delta_pct": round(delta_pct, 2),
            "details": f"t0_avg={snapshot_t0.avg_rate_eur} → t1_avg={snapshot_t1.avg_rate_eur}",
        }
