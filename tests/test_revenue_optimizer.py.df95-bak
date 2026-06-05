
# K12+K13+K16 Trinity-CONTRARIAN 2026-05-17 (Cross-LLM-validated)
def k12_provenance(payload: bytes, key: bytes = b"df-trinity-contrarian-v1") -> dict:
    import hashlib, hmac
    return {
        "payload_hash": hashlib.sha256(payload).hexdigest(),
        "hmac_sha256": hmac.new(key, payload, hashlib.sha256).hexdigest(),
    }

def k13_anchor(payload_hash: str) -> dict:
    from datetime import datetime, timezone
    return {
        "anchor_type": "rfc3161-mock",
        "iso_ts": datetime.now(timezone.utc).isoformat(),
        "payload_hash": payload_hash,
    }

def k16_lock_or_exit(df_name: str):
    import fcntl, os, sys
    lock_path = f"/tmp/df-trinity-{df_name}.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_WRONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except BlockingIOError:
        sys.exit(3)

"""Tests fuer DF-HeyLou-Revenue-Optimizer [CRUX-MK].

>=18 Tests Pflicht. Decken Bayesian-Yield + Demand-Forecast +
Competitor-Tracking + Audit-Chain + Orchestrator + K_0-Schutz.

[CRUX-MK]
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bayesian_yield_manager import (
    BayesianYieldManager,
    YieldPosterior,
)
from src.demand_forecaster import DemandForecaster
from src.competitor_price_tracker import CompetitorPriceTracker
from src.audit_logger import AuditLogger
from src.revenue_orchestrator import RevenueOrchestrator


# ============== Bayesian-Yield-Manager Tests ==============

def test_yield_manager_default_sandbox():
    """Test 1: Default-Mode ist Sandbox (K_0-Schutz)."""
    mgr = BayesianYieldManager()
    assert mgr.sandbox_mode is True


def test_yield_posterior_init_uniform_prior():
    """Test 2: Uniformer Beta(1,1)-Prior fuer unbekanntes Hotel."""
    mgr = BayesianYieldManager()
    rec = mgr.recommend_pricing("UNKNOWN-HOTEL", base_rate_eur=100.0)
    assert rec.expected_occupancy == 0.5  # Beta(1,1).mean = 0.5


def test_bayesian_update_increments_alpha_beta():
    """Test 3: Bayesian-Update inkrementiert alpha, beta korrekt."""
    mgr = BayesianYieldManager()
    p = mgr.update_posterior("H1", bookings=8, rooms_available=10)
    assert p.alpha == 1.0 + 8
    assert p.beta == 1.0 + 2  # 10 - 8 = 2 failures
    assert p.expected_occupancy == pytest.approx(9.0 / 12.0)


def test_bayesian_update_invalid_input_raises():
    """Test 4: bookings > rooms_available raises ValueError."""
    mgr = BayesianYieldManager()
    with pytest.raises(ValueError):
        mgr.update_posterior("H1", bookings=15, rooms_available=10)


def test_recommend_pricing_sandbox_cap_10pct():
    """Test 5: Sandbox-Cap begrenzt Recommendation auf +/- 10% von Base."""
    mgr = BayesianYieldManager(sandbox_mode=True)
    mgr.update_posterior("H1", bookings=20, rooms_available=20)  # 100% occ
    rec = mgr.recommend_pricing("H1", base_rate_eur=100.0, demand_signal=2.0)
    assert rec.recommended_rate_eur <= 110.0  # cap at +10%


def test_credible_interval_bounded_unit():
    """Test 6: CI bleibt in [0, 1] (Probability-Bounds)."""
    mgr = BayesianYieldManager()
    mgr.update_posterior("H1", bookings=1, rooms_available=1)
    p = mgr.get_posterior("H1")
    low, high = p.credible_interval_95
    assert 0.0 <= low <= high <= 1.0


def test_recommendation_has_provenance():
    """Test 7: Provenance-Envelope Pflicht (K12)."""
    mgr = BayesianYieldManager()
    rec = mgr.recommend_pricing("H1", base_rate_eur=100.0)
    assert "engine" in rec.provenance
    assert "version" in rec.provenance
    assert "timestamp" in rec.provenance
    assert "input_hash" in rec.provenance


# ============== Demand-Forecaster Tests ==============

def test_demand_forecast_seasonal_summer():
    """Test 8: Sommer (Juli) hat hoeheren Demand als Winter (Januar)."""
    fc = DemandForecaster()
    july = fc.forecast("H1", "2026-07-15")  # Mittwoch
    jan = fc.forecast("H1", "2026-01-14")  # Mittwoch
    assert july.demand_signal > jan.demand_signal


def test_demand_forecast_weekday_friday():
    """Test 9: Freitag-Demand > Sonntag-Demand."""
    fc = DemandForecaster()
    fri = fc.forecast("H1", "2026-06-12")  # Freitag
    sun = fc.forecast("H1", "2026-06-14")  # Sonntag
    assert fri.demand_signal > sun.demand_signal


def test_demand_forecast_event_boost():
    """Test 10: Event-Boost multipliziert Demand."""
    fc = DemandForecaster()
    fc.register_event("H1", "2026-09-26", 1.5, "Oktoberfest")
    f = fc.forecast("H1", "2026-09-26")
    assert f.event_boost == 1.5
    assert "Oktoberfest" in f.notes[0]


def test_event_boost_invalid_range_raises():
    """Test 11: Event-Boost out of range raises."""
    fc = DemandForecaster()
    with pytest.raises(ValueError):
        fc.register_event("H1", "2026-06-15", 5.0, "TooHigh")


# ============== Competitor-Price-Tracker Tests ==============

def test_competitor_snapshot_in_sandbox():
    """Test 12: Mock-Snapshot in Sandbox-Mode funktioniert."""
    t = CompetitorPriceTracker(sandbox_mode=True)
    t.register_mock_rates("H1", "2026-06-15", {"booking.com": 100.0, "expedia": 95.0})
    snap = t.get_snapshot("H1", "2026-06-15")
    assert snap is not None
    assert snap.avg_rate_eur == 97.5
    assert snap.source == "mock"


def test_competitor_real_mode_raises_without_phronesis():
    """Test 13: Real-Mode raises NotImplementedError (Phase-2 pending)."""
    t = CompetitorPriceTracker(sandbox_mode=False)
    with pytest.raises(NotImplementedError):
        t.get_snapshot("H1", "2026-06-15")


def test_competitor_drift_detection():
    """Test 14: Drift-Detection erkennt >5% Aenderung."""
    t = CompetitorPriceTracker(sandbox_mode=True)
    t.register_mock_rates("H1", "2026-06-15", {"c1": 100.0, "c2": 100.0})
    t.register_mock_rates("H1", "2026-06-16", {"c1": 110.0, "c2": 110.0})
    s0 = t.get_snapshot("H1", "2026-06-15")
    s1 = t.get_snapshot("H1", "2026-06-16")
    d = t.detect_drift(s0, s1, threshold_pct=5.0)
    assert d["drift_detected"] is True
    assert d["delta_pct"] == 10.0


# ============== Audit-Logger Tests ==============

def test_audit_log_hash_chain(tmp_path):
    """Test 15: Hash-Chain ist deterministisch + verifizierbar."""
    a = AuditLogger(audit_path=tmp_path / "audit.jsonl", secret="test-secret")
    h1 = a.append({"type": "event1", "data": "x"})
    h2 = a.append({"type": "event2", "data": "y"})
    assert h1 != h2
    result = a.verify_chain()
    assert result["valid"] is True
    assert result["entries_verified"] == 2


def test_audit_chain_genesis_first_entry(tmp_path):
    """Test 16: Erster Entry hat prev_hash=GENESIS."""
    a = AuditLogger(audit_path=tmp_path / "audit.jsonl", secret="s")
    a.append({"t": "1"})
    # Re-load and verify
    import json
    lines = (tmp_path / "audit.jsonl").read_text().splitlines()
    entry = json.loads(lines[0])
    assert entry["prev_hash"] == "GENESIS"


# ============== Orchestrator + K_0-Schutz Tests ==============

def test_orchestrator_default_sandbox():
    """Test 17: Orchestrator default sandbox-mode."""
    orch = RevenueOrchestrator()
    assert orch.sandbox_mode is True


def test_orchestrator_real_mode_requires_phronesis():
    """Test 18: K_0-Schutz - Real-Mode erfordert PHRONESIS_TICKET."""
    with patch.dict(os.environ, {"DF_HEYLOU_REVENUE_OPT_REAL_ENABLED": "true"}, clear=False):
        # Ensure PHRONESIS_TICKET not set
        if "PHRONESIS_TICKET" in os.environ:
            del os.environ["PHRONESIS_TICKET"]
        orch = RevenueOrchestrator(sandbox_mode=False)
        with pytest.raises(PermissionError, match="PHRONESIS_TICKET"):
            orch.run_for_hotel("H1", 100.0, "2026-06-15")


def test_orchestrator_run_returns_recommendation():
    """Test 19: End-to-End-Run liefert valid Recommendation."""
    orch = RevenueOrchestrator(sandbox_mode=True)
    result = orch.run_for_hotel(
        hotel_id="H1",
        base_rate_eur=100.0,
        forecast_date_iso="2026-06-15",
        historical_bookings=8,
        historical_rooms_available=10,
    )
    assert result.hotel_id == "H1"
    assert result.recommendation_eur > 0
    assert 0 <= result.expected_occupancy <= 1
    assert result.audit_hash != ""
    assert result.sandbox_mode is True


def test_competitor_anchor_caps_recommendation():
    """Test 20: Competitor-Anchor begrenzt Recommendation auf +/- 15% von Comp-Avg."""
    mgr = BayesianYieldManager(sandbox_mode=False)  # disable sandbox cap
    mgr.update_posterior("H1", bookings=20, rooms_available=20)  # max occ
    # base=100, demand=2.0 ohne Competitor → ~150 (occ_factor 1.15 * demand 1.3)
    # mit Competitor-Avg 100 → cap auf max 115 (1.15)
    rec = mgr.recommend_pricing("H1", 100.0, competitor_avg_eur=100.0, demand_signal=2.0)
    assert rec.recommended_rate_eur <= 115.0
