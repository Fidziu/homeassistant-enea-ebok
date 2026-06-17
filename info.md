# Enea eBOK

Home Assistant integration for **Enea** (Polish electricity supplier). Pulls the
**hourly meter data** from [ebok.enea.pl](https://ebok.enea.pl) (import/export,
before & after hourly netting) into HA long-term statistics — overlay your utility
meter on your inverters / sub-meters.

- 4 hourly statistics: `enea_ebok:grid_import` / `grid_export` /
  `grid_import_settled` / `grid_export_settled` (kWh).
- ~30-day backfill, twice-daily refresh (eBOK lags ~1–2 days).
- UI config: e-mail + password (PPE auto-discovered).

Works with the latest Home Assistant (2026.6+).
