"""Backfill button — pulls the full eBOK history (from `backfill_start`) on demand."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import EneaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: EneaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EneaBackfillButton(coordinator, entry)])


class EneaBackfillButton(ButtonEntity):
    _attr_has_entity_name = False
    _attr_name = "Enea pobierz pełną historię"
    _attr_icon = "mdi:history"

    def __init__(self, coordinator: EneaCoordinator, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_backfill"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Enea eBOK",
            manufacturer="Enea",
            model="eBOK",
        )

    async def async_press(self) -> None:
        self.hass.async_create_background_task(
            self._coordinator.async_backfill(), "enea_backfill"
        )
