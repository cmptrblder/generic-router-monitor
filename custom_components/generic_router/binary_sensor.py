from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GenericRouterCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: GenericRouterCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RouterOnlineBinarySensor(coordinator, entry)])


class RouterOnlineBinarySensor(CoordinatorEntity[GenericRouterCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: GenericRouterCoordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.unique_id}_online"
        self._attr_name = "Online"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id)},
            "name": entry.title,
            "manufacturer": "Generic",
            "model": "Router Monitor (SSH)",
        }

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.online)
