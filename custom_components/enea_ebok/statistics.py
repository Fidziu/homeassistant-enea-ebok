"""Inject Enea hourly meter data as long-term statistics.

We use EXTERNAL statistics (statistic_id "enea_ebok:<key>", source="enea_ebok")
rather than recorder statistics under an entity_id. External statistics are
decoupled from any entity's `state_class`, so HA never raises the
`state_class_removed` repair — yet energy-custom-graph-card and the Energy
dashboard read them by statistic_id exactly the same way."""
from __future__ import annotations

import logging

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    async_import_statistics,
    get_last_statistics,
)
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_last_sum(hass: HomeAssistant, statistic_id: str):
    last = await get_instance(hass).async_add_executor_job(
        get_last_statistics, hass, 1, statistic_id, True, {"sum"}
    )
    if not last.get(statistic_id):
        return 0.0, None
    rec = last[statistic_id][0]
    total = float(rec.get("sum") or 0.0)
    start = rec.get("start")
    last_ts = start if isinstance(start, (int, float)) else start.timestamp()
    return total, last_ts


async def async_import_series(
    hass: HomeAssistant, statistic_id: str, name: str, rows: list[tuple],
    reset: bool = False,
) -> float | None:
    """rows: sorted list of (start_dt_aware_utc, hourly_kwh). Returns the final
    cumulative sum. statistic_id "enea_ebok:<key>" -> external statistics;
    a bare entity_id -> legacy recorder statistics (kept for back-compat).

    reset=False (default): append only the rows newer than the last stored point
    (normal catch-up). reset=True: rebuild the whole series from zero, overwriting
    existing statistics (full historical backfill — rows must be the COMPLETE,
    chronologically sorted history)."""
    if not rows:
        return None
    if reset:
        total, last_ts = 0.0, None
    else:
        total, last_ts = await async_last_sum(hass, statistic_id)
    data: list[StatisticData] = []
    for start_dt, value in rows:
        if last_ts is not None and start_dt.timestamp() <= last_ts:
            continue
        total += float(value or 0.0)
        data.append(StatisticData(start=start_dt, sum=total))
    if data:
        external = ":" in statistic_id
        meta = StatisticMetaData(
            mean_type=StatisticMeanType.NONE,
            has_mean=False,
            has_sum=True,
            name=name,
            # external stats: source must equal the statistic_id prefix
            # ("enea_ebok"); legacy recorder stats (entity_id) keep "recorder".
            source=statistic_id.split(":")[0] if external else "recorder",
            statistic_id=statistic_id,
            unit_of_measurement="kWh",
        )
        if external:
            async_add_external_statistics(hass, meta, data)
        else:
            async_import_statistics(hass, meta, data)
        _LOGGER.debug("Enea: imported %d points into %s (reset=%s)", len(data), statistic_id, reset)
    return round(total, 3)
