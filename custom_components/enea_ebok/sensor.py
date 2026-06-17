"""Enea sensors.

`EneaStatSensor` are real entities whose recorder statistics are back-filled from
eBOK (so apexcharts-card & friends, which need a real `entity`, can chart them).
They deliberately have NO state_class so the recorder does not auto-generate
statistics for the (1-2 day delayed) state — all statistics come from the import,
placed at the correct historical hour."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SERIES
from .coordinator import EneaCoordinator
from .statistics import async_import_series


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: EneaCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        EneaStatSensor(coordinator, entry, key, name) for key, (_f, name) in SERIES.items()
    ]
    entities += [
        EneaDateSensor(coordinator, entry),
        EneaEnergySensor(coordinator, entry, "last_import",
                         "Enea ostatni dzień – pobrana", "mdi:transmission-tower-export"),
        EneaEnergySensor(coordinator, entry, "last_export",
                         "Enea ostatni dzień – oddana", "mdi:transmission-tower-import"),
    ]
    async_add_entities(entities)


class _Base(CoordinatorEntity[EneaCoordinator]):
    _attr_has_entity_name = False

    def __init__(self, coordinator, entry, key) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Enea eBOK",
            manufacturer="Enea",
            model="eBOK",
        )


class EneaStatSensor(_Base, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_icon = "mdi:transmission-tower"

    def __init__(self, coordinator, entry, key, name) -> None:
        super().__init__(coordinator, entry, key)
        self._key = key
        self._attr_name = name
        self._total = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        await self._import()

    @callback
    def _handle_coordinator_update(self) -> None:
        self.hass.async_create_task(self._import())

    async def _import(self) -> None:
        data = self.coordinator.data or {}
        rows = (data.get("series") or {}).get(self._key, [])
        total = await async_import_series(self.hass, self.entity_id, self._attr_name, rows)
        if total is not None:
            self._total = total
            self.async_write_ha_state()

    @property
    def native_value(self):
        return self._total


class EneaDateSensor(_Base, SensorEntity):
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "last_date")
        self._attr_name = "Enea ostatnie dane"

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get("last_date")


class EneaEnergySensor(_Base, SensorEntity):
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry, key, name, icon) -> None:
        super().__init__(coordinator, entry, key)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get(self._key)
