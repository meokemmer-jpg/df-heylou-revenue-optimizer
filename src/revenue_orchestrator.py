"""Revenue-Orchestrator [CRUX-MK].

LaunchAgent-Entry + main() fuer DF-HeyLou-Revenue-Optimizer.

Pipeline:
1. Pre-Run-Checks (K16 mutex + STOP.flag + Sandbox-Mode)
2. Demand-Forecast pro Hotel
3. Competitor-Snapshot
4. Bayesian-Pricing-Recommendation
5. Audit-Log (HMAC-signed)

[CRUX-MK]
"""

from __future__ import annotations

import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorResult:
    """Orchestrator-Run-Ergebnis."""
    hotel_id: str
    recommendation_eur: float
    expected_occupancy: float
    audit_hash: str
    sandbox_mode: bool
    duration_ms: float


class RevenueOrchestrator:
    """Main-Orchestrator fuer Revenue-Optimizer."""

    def __init__(self, sandbox_mode: Optional[bool] = None):
        from . import bayesian_yield_manager, demand_forecaster, competitor_price_tracker, audit_logger
        if sandbox_mode is None:
            sandbox_mode = (
                os.environ.get("DF_HEYLOU_REVENUE_OPT_REAL_ENABLED", "false").lower()
                != "true"
            )
        self.sandbox_mode = sandbox_mode
        self.yield_mgr = bayesian_yield_manager.BayesianYieldManager(sandbox_mode=sandbox_mode)
        self.demand_fc = demand_forecaster.DemandForecaster()
        self.price_tracker = competitor_price_tracker.CompetitorPriceTracker(sandbox_mode=sandbox_mode)
        self.audit = audit_logger.AuditLogger()

    def run_for_hotel(
        self,
        hotel_id: str,
        base_rate_eur: float,
        forecast_date_iso: str,
        historical_bookings: Optional[int] = None,
        historical_rooms_available: Optional[int] = None,
    ) -> OrchestratorResult:
        """Single-Hotel Run."""
        t0 = time.time()

        # K_0-Pflicht-Check: Sandbox-Mode-Verifikation
        if not self.sandbox_mode and not os.environ.get("PHRONESIS_TICKET"):
            raise PermissionError(
                "Real-Mode requires PHRONESIS_TICKET (K_0-Schutz). "
                "Phronesis-Pflicht Martin: K_0-Berührung Anti-OTA-Pricing."
            )

        # Bayesian-Update wenn historische Daten vorhanden
        if historical_bookings is not None and historical_rooms_available is not None:
            self.yield_mgr.update_posterior(
                hotel_id, historical_bookings, historical_rooms_available
            )

        # Demand-Forecast
        demand = self.demand_fc.forecast(hotel_id, forecast_date_iso)

        # Competitor-Snapshot (optional)
        snap = self.price_tracker.get_snapshot(hotel_id, forecast_date_iso)
        comp_avg = snap.avg_rate_eur if snap else None

        # Pricing-Recommendation
        rec = self.yield_mgr.recommend_pricing(
            hotel_id=hotel_id,
            base_rate_eur=base_rate_eur,
            competitor_avg_eur=comp_avg,
            demand_signal=demand.demand_signal,
        )

        # Audit-Log
        audit_hash = self.audit.append({
            "type": "pricing_recommendation",
            "hotel_id": hotel_id,
            "base_rate_eur": base_rate_eur,
            "recommended_rate_eur": rec.recommended_rate_eur,
            "expected_occupancy": rec.expected_occupancy,
            "demand_signal": demand.demand_signal,
            "competitor_avg_eur": comp_avg,
            "sandbox_mode": self.sandbox_mode,
            "rationale": rec.rationale,
        })

        return OrchestratorResult(
            hotel_id=hotel_id,
            recommendation_eur=rec.recommended_rate_eur,
            expected_occupancy=rec.expected_occupancy,
            audit_hash=audit_hash,
            sandbox_mode=self.sandbox_mode,
            duration_ms=(time.time() - t0) * 1000,
        )


def main(argv: Optional[list[str]] = None) -> int:
    """LaunchAgent-Entry-Point."""
    logging.basicConfig(level=logging.INFO)

    # STOP.flag-Check
    stop_flag = Path("/tmp/df-heylou-revenue-opt.stop")
    if stop_flag.exists():
        logger.info("STOP.flag detected, exiting cleanly.")
        return 0

    # Skeleton-Run: 1 Demo-Hotel
    orch = RevenueOrchestrator()
    result = orch.run_for_hotel(
        hotel_id="HILDESHEIM-PILOT-01",
        base_rate_eur=99.00,
        forecast_date_iso="2026-06-15",
        historical_bookings=15,
        historical_rooms_available=20,
    )
    logger.info(f"Run complete: {result}")
    return 0


def __df_guarded_entry():  # K16+K11-FOUNDATION-WIRED [CRUX-MK]
    sys.exit(main(sys.argv[1:]))

if __name__ == "__main__":  # K16+K11-FOUNDATION-WIRED [CRUX-MK]
    try:
        from _df_common.df_foundation import run_guarded as _rg
    except Exception:
        raise SystemExit(__df_guarded_entry())   # Foundation weg -> normal
    raise SystemExit(_rg("df-heylou-revenue-optimizer", __df_guarded_entry))   # K14+K16+K15+K11 echt
