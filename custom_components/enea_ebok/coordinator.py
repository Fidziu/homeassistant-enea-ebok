"""Fetch Enea hourly data. Statistics are imported by the sensor entities
(they own the statistic_id), so this coordinator only assembles the rows."""
from __future__ import annotations

import logging
import zoneinfo
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import EneaAuthError, EneaClient
from .const import BACKFILL_DAYS, CATCHUP_DAYS, SERIES, TZ, UPDATE_INTERVAL_HOURS

_LOGGER = logging.getLogger(__name__)


class EneaCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: EneaClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Enea eBOK",
            config_entry=entry,
            update_interval=timedelta(hours=UPDATE_INTERVAL_HOURS),
        )
        self.client = client
        self._first = True

    async def _async_update_data(self) -> dict:
        try:
            return await self._pull()
        except EneaAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Enea update failed: {err}") from err

    async def _pull(self) -> dict:
        tz = zoneinfo.ZoneInfo(TZ)
        today = dt_util.now().astimezone(tz).date()
        days = BACKFILL_DAYS if self._first else CATCHUP_DAYS
        self._first = False
        start = today - timedelta(days=days)

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
            day += timedelta(days=1)

        for rows in series.values():
            rows.sort(key=lambda x: x[0])

        return {
            "series": series,
            "last_date": last_date.isoformat() if last_date else None,
            "last_import": round(last_import, 3),
            "last_export": round(last_export, 3),
        }
