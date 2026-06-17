# Enea eBOK — Home Assistant integration

> **🏠 Works with the latest Home Assistant (tested on 2026.6+).**

Custom Home Assistant integration for **Enea** (Polish electricity supplier).
It logs into [ebok.enea.pl](https://ebok.enea.pl), pulls the **hourly day-by-day
meter data** (import/export, before *and* after hourly netting — *przed/po
bilansowaniu*) and feeds it into Home Assistant **long-term statistics** so you can
overlay your utility meter on your own measurements (inverters, sub-meters, …).

Built for a **prosument** (PV + grid) setup: the meter reports both energy taken
from and given to the grid per hour.

---

## What it does

- Logs in to eBOK (CSRF token + `EBOK_SESSION` cookie).
- Pulls `POST /meter/summaryBalancingChart` (XHR → JSON) for each day and imports
  **4 external statistics** (kWh, hourly):
  - `enea_ebok:grid_import` — pobrana, **przed** bilansowaniem (raw, for comparison)
  - `enea_ebok:grid_export` — oddana, **przed** bilansowaniem
  - `enea_ebok:grid_import_settled` — pobrana, **po** bilansowaniu (settlement)
  - `enea_ebok:grid_export_settled` — oddana, **po** bilansowaniu
- Exposes summary sensors: last data date, last full day's import / export.
- Backfills ~30 days on first run, then re-pulls the last few days twice a day
  (eBOK data lags ~1–2 days).

### Przed vs po bilansowaniu
Two different things, easy to confuse:
- **Saldowanie międzyfazowe** (vector sum of phases) happens *continuously at the
  meter* — already baked into the raw per-hour import/export.
- **Bilansowanie godzinowe** (prosumer settlement) nets import vs export *within
  each hour*: `import_after = max(0, import − export)`, `export_after =
  max(0, export − import)`. That's the *przed/po* toggle. For verifying against
  physical measurements use **przed bilansowaniem**.

---

## Install

1. Copy `custom_components/enea_ebok` into your HA `config/custom_components/`.
2. Restart Home Assistant.
3. *Settings → Devices & Services → Add Integration → "Enea eBOK"* → e-mail +
   password. The delivery point (PPE) is auto-discovered.

Then add the statistics to any chart (e.g. a `statistics-graph` card with
`stat_types: [change]`, `period: day`) to compare with your inverters.

---

## Notes / limitations
- eBOK is a session-cookie web app (no official API); this is a community reverse
  of the meter endpoints. Use at your own risk; respect Enea's terms.
- Data is delayed ~1–2 days — this is historical verification, not real-time.
- Tested with an ASIN-AQUA-style bidirectional meter on a prosumer contract.

See **[CHANGELOG.md](CHANGELOG.md)**.
