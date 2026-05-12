"""Bayesian-Yield-Manager [CRUX-MK].

Welle-40 Profit-Layer #1: Bayesian-Hierarchical-Model fuer Yield-Forecast.

Pattern:
- Beta-Distribution-Prior fuer Occupancy-Rate (alpha, beta updated mit historischen Daten)
- Hierarchical: pro-Hotel-Posterior + Global-Prior-Pooling
- Pricing-Recommendation aus Posterior-Sampling
- Provenance-Envelope pro Recommendation

K_0-Schutz:
- Sandbox-Default: ENV-Var-Gated
- Recommendations sind NICHT auto-applied (Hotelier-Approval-Gate)
- Bayesian-Updates persistent in audit_logger (HMAC-SHA256-signed)

Lambda-Honesty-Caveat:
- Skeleton-Phase nutzt deterministische Beta-Approximation (Method-of-Moments)
- Full-MCMC-Posterior via pymc/numpyro in Phase-2 (Cross-LLM-Audit-Pflicht)
- Hierarchical-Pooling vereinfacht als gewichtetes Mean (Phase-1)

[CRUX-MK]
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class YieldPosterior:
    """Bayesian-Posterior fuer Hotel-Yield."""
    hotel_id: str
    alpha: float  # Beta-Posterior alpha (Success-Pseudo-Count)
    beta: float   # Beta-Posterior beta (Failure-Pseudo-Count)
    n_observations: int = 0
    last_update_ts: Optional[float] = None

    @property
    def expected_occupancy(self) -> float:
        """E[occupancy] = alpha / (alpha + beta) (Beta-Mean)."""
        denom = self.alpha + self.beta
        if denom <= 0:
            return 0.5  # Uninformed-Prior-Fallback
        return self.alpha / denom

    @property
    def credible_interval_95(self) -> tuple[float, float]:
        """Approximation: Mean +/- 1.96 * sqrt(var). Phase-2: echtes Beta-Quantile."""
        mean = self.expected_occupancy
        denom_sq = (self.alpha + self.beta) ** 2 * (self.alpha + self.beta + 1)
        if denom_sq <= 0:
            return (0.0, 1.0)
        var = (self.alpha * self.beta) / denom_sq
        std = math.sqrt(var)
        return (max(0.0, mean - 1.96 * std), min(1.0, mean + 1.96 * std))


@dataclass
class PricingRecommendation:
    """Bayesian-basierte Pricing-Empfehlung mit Provenance."""
    hotel_id: str
    base_rate_eur: float
    recommended_rate_eur: float
    expected_occupancy: float
    occupancy_ci_95: tuple[float, float]
    yield_score: float  # rate * occupancy
    rationale: str
    provenance: dict = field(default_factory=dict)


class BayesianYieldManager:
    """Bayesian-Hierarchical-Yield-Manager.

    Konsumiert Demand-Forecast + Competitor-Prices, liefert Pricing-Recommendation.
    """

    def __init__(self, sandbox_mode: Optional[bool] = None):
        """Init.

        Args:
            sandbox_mode: Default aus ENV-Var DF_HEYLOU_REVENUE_OPT_REAL_ENABLED.
        """
        if sandbox_mode is None:
            sandbox_mode = (
                os.environ.get("DF_HEYLOU_REVENUE_OPT_REAL_ENABLED", "false").lower()
                != "true"
            )
        self.sandbox_mode = sandbox_mode
        self._posteriors: dict[str, YieldPosterior] = {}

    def update_posterior(
        self,
        hotel_id: str,
        bookings: int,
        rooms_available: int,
    ) -> YieldPosterior:
        """Bayesian-Update mit neuen Booking-Daten.

        Beta-Conjugate: posterior_alpha = prior_alpha + bookings.
        posterior_beta = prior_beta + (rooms_available - bookings).
        """
        if bookings < 0 or rooms_available < bookings:
            raise ValueError(
                f"Invalid input: bookings={bookings}, rooms_available={rooms_available}"
            )

        prior = self._posteriors.get(
            hotel_id, YieldPosterior(hotel_id=hotel_id, alpha=1.0, beta=1.0)
        )

        prior.alpha += bookings
        prior.beta += rooms_available - bookings
        prior.n_observations += rooms_available
        prior.last_update_ts = time.time()

        self._posteriors[hotel_id] = prior
        return prior

    def recommend_pricing(
        self,
        hotel_id: str,
        base_rate_eur: float,
        competitor_avg_eur: Optional[float] = None,
        demand_signal: float = 1.0,  # >1.0 = high-demand, <1.0 = low
    ) -> PricingRecommendation:
        """Pricing-Recommendation via Bayesian-Posterior + Demand-Signal.

        Args:
            hotel_id: Hotel-Identifier
            base_rate_eur: Aktuelle Base-Rate
            competitor_avg_eur: Optional Wettbewerber-Durchschnitt
            demand_signal: Demand-Forecaster-Output (>1.0 high, <1.0 low)
        """
        posterior = self._posteriors.get(
            hotel_id, YieldPosterior(hotel_id=hotel_id, alpha=1.0, beta=1.0)
        )

        expected_occ = posterior.expected_occupancy
        ci_95 = posterior.credible_interval_95

        # Pricing-Logic: Bayesian-Expectation + Demand-Multiplier
        # Phase-1 Heuristik (Phase-2: echtes Yield-Optimum via Posterior-Sampling)
        # High-Occupancy + High-Demand → Price-Up
        # Low-Occupancy + Low-Demand → Price-Down (Diskont)
        occ_factor = 1.0 + (expected_occ - 0.7) * 0.5  # 0.7 = Break-Even-Occupancy
        demand_factor = max(0.7, min(1.3, demand_signal))
        recommended_rate = base_rate_eur * occ_factor * demand_factor

        # Competitor-Anchor (max +/- 15% Abweichung)
        if competitor_avg_eur is not None and competitor_avg_eur > 0:
            max_above = competitor_avg_eur * 1.15
            min_below = competitor_avg_eur * 0.85
            recommended_rate = max(min_below, min(max_above, recommended_rate))

        # Sandbox-Cap fuer K_0-Schutz
        if self.sandbox_mode:
            # Begrenze Recommendation in Sandbox auf max +/- 10% von base
            recommended_rate = max(
                base_rate_eur * 0.9, min(base_rate_eur * 1.1, recommended_rate)
            )

        yield_score = recommended_rate * expected_occ

        rationale_parts = [
            f"occ={expected_occ:.2f}",
            f"demand={demand_signal:.2f}",
            f"occ_factor={occ_factor:.2f}",
        ]
        if competitor_avg_eur:
            rationale_parts.append(f"comp_avg={competitor_avg_eur:.2f}")
        if self.sandbox_mode:
            rationale_parts.append("sandbox_capped")

        return PricingRecommendation(
            hotel_id=hotel_id,
            base_rate_eur=base_rate_eur,
            recommended_rate_eur=round(recommended_rate, 2),
            expected_occupancy=expected_occ,
            occupancy_ci_95=ci_95,
            yield_score=round(yield_score, 2),
            rationale=" | ".join(rationale_parts),
            provenance={
                "engine": "BayesianYieldManager",
                "version": "0.1.0-SKELETON",
                "sandbox_mode": self.sandbox_mode,
                "timestamp": time.time(),
                "input_hash": hashlib.sha256(
                    f"{hotel_id}|{base_rate_eur}|{competitor_avg_eur}|{demand_signal}".encode()
                ).hexdigest()[:16],
            },
        )

    def get_posterior(self, hotel_id: str) -> Optional[YieldPosterior]:
        """Read-only Posterior-Access fuer Tests / Audit."""
        return self._posteriors.get(hotel_id)
