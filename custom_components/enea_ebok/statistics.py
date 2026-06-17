"""Inject Enea hourly meter data as recorder statistics for our own sensor
entities (so cards like apexcharts-card, which require a real `entity`, can read
them — external `domain:id` statistics are not usable there)."""
from __future__ import annotations

import logging

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import (
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
    hass: HomeAssistant, statistic_id: str, name: str, rows: list[tuple]
) -> float | None:
    """rows: sorted list of (start_dt_aware_utc, hourly_kwh). Returns the final
    cumulative sum (the sensor uses it as its state). statistic_id is an
    entity_id -> recorder-source statistics."""
    if not rows:
        return None
    total, last_ts = await async_last_sum(hass, statistic_id)
    data: list[StatisticData] = []
    for start_dt, value in rows:
        if last_ts is not None and start_dt.timestamp() <= last_ts:
            continue
        total += float(value or 0.0)
        data.append(StatisticData(start=start_dt, sum=total))
    if data:
        meta = StatisticMetaData(
            mean_type=StatisticMeanType.NONE,
            has_mean=False,
            has_sum=True,
            name=name,
            source="recorder",
            statistic_id=statistic_id,
            unit_of_measurement="kWh",
        )
        async_import_statistics(hass, meta, data)
        _LOGGER.debug("Enea: imported %d points into %s", len(data), statistic_id)
    return round(total, 3)
