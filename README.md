# DF-HeyLou-Revenue-Optimizer [CRUX-MK]

**Welle-40 Foundation-DF: Profit-Layer #1**

RMS-aequivalent fuer 9OS-Hotels mit Bayesian-Yield-Management + Demand-Forecasting + Competitor-Price-Tracking.

## Status
- Version: 0.1.0-SKELETON
- Phase: PRE-PRODUCTION-CONDITIONAL
- K_0-Touch: TRUE (Anti-OTA-Strategie + Pricing-Decisions)

## Architektur

```
src/
├── bayesian_yield_manager.py    # Bayesian-Hierarchical-Model + Beta-Prior
├── demand_forecaster.py          # Time-Series + Saisonalitaet + Events
├── competitor_price_tracker.py   # Cross-OTA-Rate-Drift via W37
├── revenue_orchestrator.py       # LaunchAgent-Entry + main()
└── audit_logger.py               # HMAC-SHA256-Signed Audit-Trail
```

## Pflicht-Properties

- **Sandbox-Default:** `DF_HEYLOU_REVENUE_OPT_REAL_ENABLED=false`
- **Provenance-Envelope:** Jede Pricing-Recommendation
- **K11-K16 + LC1-LC5:** Vollstaendig in config.yaml
- **Cross-Adapter-Reuse:** Konsumiert W37 cross_ota_rate_sync

## rho-Gain Year-1 Pilot

+30-60k EUR/J durch optimierte Yield-Management bei Hildesheim-Pilot (1 Hotel).
Year-3 Skaling 5+ Hotels: +200-400k EUR/J.

## Phronesis-Pflicht Martin

Real-Pricing-Aktivierung erfordert PHRONESIS_TICKET (Anti-OTA-Strategie ist K_0-Risiko).

[CRUX-MK]
