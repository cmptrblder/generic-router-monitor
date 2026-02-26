from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_PASSWORD


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    data = dict(entry.data)
    if CONF_PASSWORD in data:
        data[CONF_PASSWORD] = "***REDACTED***"

    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    return {
        "entry": {
            "title": entry.title,
            "unique_id": entry.unique_id,
            "data": data,
        },
        "last_data": None if coordinator is None or coordinator.data is None else {
            "online": coordinator.data.online,
            "uptime_seconds": coordinator.data.uptime_seconds,
            "cpu_load_1m": coordinator.data.cpu_load_1m,
            "mem_used_percent": coordinator.data.mem_used_percent,
            "wan_if": coordinator.data.wan_if,
            "rx_mbps": coordinator.data.rx_mbps,
            "tx_mbps": coordinator.data.tx_mbps,
        },
    }
