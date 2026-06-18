"""Fetch Enea hourly data. Statistics are imported by the sensor entities
(they own the statistic_id), so this coordinator only assembles the rows.

Regular refresh re-pulls the last `catchup_days` (append). The backfill button
calls `async_backfill()` which pulls the whole history from `backfill_start`
with throttling and triggers a full re-import (full=True)."""
from __future__ import annotations

import asyncio
import logging
import zoneinfo
from datetime import date, datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import EneaAuthError, EneaClient
from .const import (
    CONF_BACKFILL_START,
    CONF_CATCHUP_DAYS,
    CONF_THROTTLE_MS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_BACKFILL_START,
    DEFAULT_CATCHUP_DAYS,
    DEFAULT_THROTTLE_MS,
    DEFAULT_UPDATE_INTERVAL_HOURS,
    SERIES,
    TZ,
)

_LOGGER = logging.getLogger(__name__)


class EneaCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: EneaClient) -> None:
        interval = float(entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_HOURS))
        super().__init__(
            hass,
            _LOGGER,
            name="Enea eBOK",
            config_entry=entry,
            update_interval=timedelta(hours=interval),
        )
        self.client = client
        self._entry = entry

    async def _async_update_data(self) -> dict:
        """Regular refresh: re-pull only the last `catchup_days` (append)."""
        try:
            days = int(self._entry.options.get(CONF_CATCHUP_DAYS, DEFAULT_CATCHUP_DAYS))
            tz = zoneinfo.ZoneInfo(TZ)
            today = dt_util.now().astimezone(tz).date()
            return await self._pull_window(today - timedelta(days=days), full=False)
        except EneaAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Enea update failed: {err}") from err

    async def async_backfill(self) -> None:
        """Full history from `backfill_start`, throttled, full re-import."""
        try:
            start = date.fromisoformat(
                self._entry.options.get(CONF_BACKFILL_START, DEFAULT_BACKFILL_START)
            )
        except ValueError:
            start = date.fromisoformat(DEFAULT_BACKFILL_START)
        _LOGGER.info("Enea: backfill od %s (w tle, z throttle)...", start)
        try:
            data = await self._pull_window(start, full=True)
            self.async_set_updated_data(data)
            _LOGGER.info("Enea: backfill zakonczony, ostatni dzien=%s", data.get("last_date"))
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Enea: backfill nie powiodl sie: %s", err)

    async def _pull_window(self, start: date, full: bool) -> dict:
        tz = zoneinfo.ZoneInfo(TZ)
        today = dt_util.now().astimezone(tz).date()
        throttle = int(self._entry.options.get(CONF_THROTTLE_MS, DEFAULT_THROTTLE_MS)) / 1000.0

        series: dict[str, list[tuple]] = {key: [] for key in SERIES}
        last_date = None
        last_import = last_export = 0.0

        day = start
        while day < today:  # skip today — data is incomplete / lagged
            try:
                rows = await self.client.async_get_day(day)
            except EneaAuthError:
                raise
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Enea: day %s failed: %s", day, err)
                rows = []
            if rows:
                day_import = day_export = 0.0
                for row in rows:
                    naive = datetime.fromisoformat(row["dateFrom"])
                    start_dt = dt_util.as_utc(naive.replace(tzinfo=tz))
                    for key, (field, _name) in SERIES.items():
                        series[key].append((start_dt, row.get(field) or 0))
                    day_import += row.get("aec") or 0
                    day_export += row.get("eaec") or 0
                if day_import > 0 or day_export > 0:
                    last_date = day
                    last_import = day_import
                    last_export = day_export
            # throttle only matters for the long backfill; catch-up is a few days
            if full and throttle:
                await asyncio.sleep(throttle)
            day += timedelta(days=1)

        for rows in series.values():
            rows.sort(key=lambda x: x[0])

        return {
            "series": series,
            "full": full,
            "last_date": last_date.isoformat() if last_date else None,
            "last_import": round(last_import, 3),
            "last_export": round(last_export, 3),
        }
