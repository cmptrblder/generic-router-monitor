from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GenericRouterCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: GenericRouterCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            RouterUptimeSensor(coordinator, entry),
            RouterCpuLoadSensor(coordinator, entry),
            RouterMemUsedSensor(coordinator, entry),
            RouterWanIfSensor(coordinator, entry),
            RouterRxSensor(coordinator, entry),
            RouterTxSensor(coordinator, entry),
        ]
    )


class _Base(CoordinatorEntity[GenericRouterCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: GenericRouterCoordinator, entry, suffix: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.unique_id}_{suffix}"
        self._attr_name = name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id)},
            "name": entry.title,
            "manufacturer": "Generic",
            "model": "Router Monitor (SSH)",
        }


class RouterUptimeSensor(_Base):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "s"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "uptime", "Uptime")

    @property
    def native_value(self):
        d = self.coordinator.data
        return None if not d else d.uptime_seconds


class RouterCpuLoadSensor(_Base):
    _attr_icon = "mdi:cpu-64-bit"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "cpu_load_1m", "CPU Load (1m)")

    @property
    def native_value(self):
        d = self.coordinator.data
        return None if not d else d.cpu_load_1m


class RouterMemUsedSensor(_Base):
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:memory"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "mem_used", "Memory Used")

    @property
    def native_value(self):
        d = self.coordinator.data
        if not d or d.mem_used_percent is None:
            return None
        return round(float(d.mem_used_percent), 1)


class RouterWanIfSensor(_Base):
    _attr_icon = "mdi:wan"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "wan_if", "WAN Interface")

    @property
    def native_value(self):
        d = self.coordinator.data
        return None if not d else d.wan_if


class RouterRxSensor(_Base):
    _attr_native_unit_of_measurement = "Mbps"
    _attr_icon = "mdi:download-network"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "rx_mbps", "WAN RX")

    @property
    def native_value(self):
        d = self.coordinator.data
        if not d or d.rx_mbps is None:
            return None
        return round(float(d.rx_mbps), 3)


class RouterTxSensor(_Base):
    _attr_native_unit_of_measurement = "Mbps"
    _attr_icon = "mdi:upload-network"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "tx_mbps", "WAN TX")

    @property
    def native_value(self):
        d = self.coordinator.data
        if not d or d.tx_mbps is None:
            return None
        return round(float(d.tx_mbps), 3)
