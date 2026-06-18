# Enea eBOK — Home Assistant integration

<p align="center"><img src="logo.png" alt="Enea" width="220"></p>

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
  the 4 hourly values into **recorder statistics carried on real sensor entities**
  (so any card — `statistics-graph`, etc. — can read them):
  - `sensor.enea_ebok_enea_pobor_przed_bilansowaniem` — pobrana, **przed** bilansowaniem (raw)
  - `sensor.enea_ebok_enea_oddanie_przed_bilansowaniem` — oddana, **przed** bilansowaniem
  - `sensor.enea_ebok_enea_pobor_po_bilansowaniu` — pobrana, **po** bilansowaniu (settlement)
  - `sensor.enea_ebok_enea_oddanie_po_bilansowaniu` — oddana, **po** bilansowaniu
- Summary sensors: last data date, last full day's import / export.
- Statistics are imported at the correct historical hour, so the entities
  deliberately carry **no `state_class`** (the recorder must not auto-generate
  stats from the 1–2 day-delayed live state).

---

## Options & backfill

Configurable in *Settings → Devices & Services → Enea eBOK → **Configure***:

- **Refresh interval** (hours) — how often to re-pull (default 6 h).
- **Backfill start date** — how far back to fetch full history (default
  `2023-05-01`, the earliest data eBOK exposes; it keeps ~3 years).
- **Catch-up days** — how many recent days to re-pull on every refresh (eBOK lags
  ~1–2 days).
- **Throttle (ms)** — pause between days during a full backfill (anti-rate-limit).

The **"Pull full history"** button fetches the entire history from the start date
(throttled) and does a **full statistics re-import** (cumulative sums rebuilt from
zero). Regular refreshes only re-pull the last few days (append).

> Hourly resolution is only available day-by-day (`duration=day`). eBOK's
> `month`/`year` bulk endpoints return daily/monthly aggregates, not hours.

---

## Przed vs po bilansowaniu
Two different things, easy to confuse:
- **Saldowanie międzyfazowe** (vector sum of phases) happens *continuously at the
  meter* — already baked into the raw per-hour import/export.
- **Bilansowanie godzinowe** (prosumer settlement) nets import vs export *within
  each hour*: `import_after = max(0, import − export)`, `export_after =
  max(0, export − import)`. That's the *przed/po* toggle. For verifying against
  physical measurements use **przed bilansowaniem**.

---

## Install

1. Copy `custom_components/enea_ebok` into your HA `config/custom_components/`
   (or add this repo to HACS as a custom repository).
2. Restart Home Assistant.
3. *Settings → Devices & Services → Add Integration → "Enea eBOK"* → e-mail +
   password. The delivery point (PPE) is auto-discovered.
4. Open *Configure* to set the refresh interval / backfill start, then press
   **Pull full history** once to load the archive.

Then add the statistics to any chart (e.g. a `statistics-graph` card with
`stat_types: [change]`, `period: day`) to compare with your own measurements.

---

## Notes / limitations
- eBOK is a session-cookie web app (no official API); this is a community reverse
  of the meter endpoints. Use at your own risk; respect Enea's terms.
- Data is delayed ~1–2 days — this is historical verification, not real-time.
- Tested with a bidirectional (two-way) electricity meter on a prosumer (PV) contract.

See **[CHANGELOG.md](CHANGELOG.md)**.
