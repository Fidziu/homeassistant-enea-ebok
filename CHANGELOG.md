# Changelog

## [0.1.0] — 2026-06-17

Initial release.

### Added
- eBOK login (CSRF token + session cookie) via a dedicated aiohttp session.
- Hourly meter pull (`/meter/summaryBalancingChart`, XHR JSON) with the 4 values
  per hour: `aec`/`eaec` (import/export before hourly netting) and
  `aecasb`/`eaecasb` (after netting).
- Import into HA long-term statistics: `enea_ebok:grid_import`,
  `:grid_export`, `:grid_import_settled`, `:grid_export_settled` (kWh, cumulative
  sums, continued across runs via `get_last_statistics`).
- ~30-day backfill on first run; twice-daily catch-up of the last few days
  (covers eBOK's 1–2 day lag). Today and not-yet-finalized (all-zero) days skipped.
- Summary sensors: last data date, last full day import / export.
- Config flow (e-mail + password); PPE auto-discovery.
- HA 2026.6 compatibility: `config_entry`-aware coordinator,
  `StatisticMeanType.NONE` in statistics metadata.

### Notes
- Built/tested against a prosumer (PV + grid) contract on a bidirectional meter.
- Companion setup (not part of the component): summed Deye grid import/export
  template sensors + an "Enea" dashboard overlaying Enea (przed bilansowaniem)
  against the inverters.
