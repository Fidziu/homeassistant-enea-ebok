# Changelog

## [0.3.0] — 2026-06-24

### Fixed
- **Statistics back to external** (`enea_ebok:grid_import` / `:grid_export` /
  `:grid_import_settled` / `:grid_export_settled`). 0.2.0 inadvertently switched to
  recorder statistics carried on the sensor entities; because those entities
  (correctly) have no `state_class`, Home Assistant raised a recurring
  **"entity no longer has a state class" (`state_class_removed`) repair** on every
  import. External statistics are decoupled from entity `state_class`, so the repair
  is gone — while charts / the Energy dashboard still read the data by `statistic_id`.

### Upgrading from 0.2.0
- After updating, press **"Pull full history"** once — it rebuilds the external
  statistics from eBOK.
- The old per-entity statistics (`sensor.enea_ebok_enea_*`) left by 0.2.0 are now
  redundant; remove them via *Developer Tools → Statistics* (the repair's **Delete**
  button is safe **after** the backfill, since the data lives in `enea_ebok:*`).
- Fresh installs and upgrades from 0.1.0 (already external) need no action.

## [0.2.0] — 2026-06-18

### Added
- Options flow (UI): configurable **refresh interval**, **backfill start date**,
  **catch-up days** and per-day **throttle**.
- **"Pull full history" button** — on-demand full backfill from `backfill_start`
  (default `2023-05-01`, the earliest data eBOK exposes), throttled, with a full
  statistics re-import (cumulative sums rebuilt from zero).
- `reset` mode in the statistics importer for the historical re-import.

### Changed
- Default refresh interval 12 h → 6 h; backfill is date-based (from
  `backfill_start`) instead of a fixed day count.
- Integration reloads automatically when options change.

### Notes
- eBOK retains ~3 years of data; hourly resolution only via `duration=day`
  (day-by-day). `duration=month`/`year` return daily/monthly aggregates.

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
- Built/tested against a prosumer (PV + grid) contract on a two-way electricity meter.
- Companion setup (not part of the component): summed Deye grid import/export
  template sensors + an "Enea" dashboard overlaying Enea (przed bilansowaniem)
  against the inverters.
