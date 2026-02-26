from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import timedelta

import asyncssh

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD, CONF_SSH_MODE,
    SSH_MODE_MODERN, SSH_MODE_LEGACY
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class RouterData:
    online: bool
    uptime_seconds: float | None
    cpu_load_1m: float | None
    mem_used_percent: float | None
    wan_if: str | None
    rx_mbps: float | None
    tx_mbps: float | None


class GenericRouterCoordinator(DataUpdateCoordinator[RouterData]):
    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry

        self.host: str = entry.data[CONF_HOST]
        self.port: int = int(entry.data[CONF_PORT])
        self.username: str = entry.data[CONF_USERNAME]
        self.password: str = entry.data[CONF_PASSWORD]
        self.ssh_mode: str = entry.data.get(CONF_SSH_MODE, SSH_MODE_MODERN)

        self._last_if_counters: dict[str, tuple[int, int]] = {}
        self._last_time: float | None = None
        self._wan_if: str | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"Generic Router Monitor ({self.host})",
            update_interval=timedelta(seconds=30),
        )

    async def _ping_online(self) -> bool:
        try:
            proc = await asyncio.create_subprocess_exec(
                "ping", "-c", "2", "-W", "1", self.host,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.communicate()
            return proc.returncode == 0
        except Exception:
            return False

    async def _ssh_cmd(self, cmd: str) -> str:
        try:
            if self.ssh_mode == SSH_MODE_LEGACY:
                conn = await asyncssh.connect(
                    self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    known_hosts=None,
                    login_timeout=10,
                    kex_algs=["diffie-hellman-group1-sha1", "diffie-hellman-group14-sha1"],
                    server_host_key_algs=["ssh-rsa"],
                    encryption_algs=["aes128-cbc", "aes256-cbc", "aes128-ctr"],
                )
            else:
                # Modern: do not override algorithms
                conn = await asyncssh.connect(
                    self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    known_hosts=None,
                    login_timeout=10,
                )

            async with conn:
                result = await conn.run(cmd, check=False)
                return (result.stdout or "").strip()
        except Exception as err:
            raise UpdateFailed(f"SSH error: {err}") from err

    @staticmethod
    def _parse_proc_net_dev(text: str) -> dict[str, tuple[int, int]]:
        out: dict[str, tuple[int, int]] = {}
        for ln in text.splitlines():
            if ":" not in ln:
                continue
            iface, rest = ln.split(":", 1)
            iface = iface.strip()
            parts = rest.split()
            if len(parts) < 16:
                continue
            rx_bytes = int(parts[0])
            tx_bytes = int(parts[8])
            out[iface] = (rx_bytes, tx_bytes)
        return out

    @staticmethod
    def _choose_wan_interface(prev: dict[str, tuple[int, int]], cur: dict[str, tuple[int, int]]) -> str | None:
        excluded_prefixes = ("lo", "br")
        best_if = None
        best_delta = -1
        for iface, (rx, tx) in cur.items():
            if iface.startswith(excluded_prefixes):
                continue
            if iface not in prev:
                continue
            prx, ptx = prev[iface]
            delta = max(0, rx - prx) + max(0, tx - ptx)
            if delta > best_delta:
                best_delta = delta
                best_if = iface
        return best_if

    @staticmethod
    def _parse_uptime(text: str) -> float | None:
        try:
            return float(text.split()[0])
        except Exception:
            return None

    @staticmethod
    def _parse_loadavg(text: str) -> float | None:
        try:
            return float(text.split()[0])
        except Exception:
            return None

    @staticmethod
    def _parse_free(text: str) -> float | None:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        mem_line = None
        for ln in lines:
            if ln.lower().startswith("mem:"):
                mem_line = ln
                break
        if not mem_line:
            return None
        parts = mem_line.split()
        if len(parts) < 3:
            return None
        try:
            total = float(parts[1])
            used = float(parts[2])
            if total <= 0:
                return None
            return (used / total) * 100.0
        except Exception:
            return None

    async def _async_update_data(self) -> RouterData:
        online = await self._ping_online()
        if not online:
            return RouterData(False, None, None, None, self._wan_if, None, None)

        # Single SSH run for minimal overhead
        cmd = "echo __UPTIME__; cat /proc/uptime; echo __LOAD__; cat /proc/loadavg; echo __FREE__; free; echo __NET__; cat /proc/net/dev"
        raw = await self._ssh_cmd(cmd)

        def section(name: str) -> str:
            start = raw.find(f"__{name}__")
            if start == -1:
                return ""
            start += len(f"__{name}__")
            next_pos = len(raw)
            for other in ["UPTIME", "LOAD", "FREE", "NET"]:
                if other == name:
                    continue
                p = raw.find(f"__{other}__", start)
                if p != -1 and p < next_pos:
                    next_pos = p
            return raw[start:next_pos].strip()

        uptime_s = self._parse_uptime(section("UPTIME"))
        load_1m = self._parse_loadavg(section("LOAD"))
        mem_pct = self._parse_free(section("FREE"))

        cur_if = self._parse_proc_net_dev(section("NET"))
        now = time.time()
        rx_mbps = None
        tx_mbps = None

        if self._last_time is not None and self._last_if_counters:
            chosen = self._choose_wan_interface(self._last_if_counters, cur_if)
            if chosen:
                self._wan_if = chosen

        if (
            self._wan_if
            and self._last_time is not None
            and self._wan_if in self._last_if_counters
            and self._wan_if in cur_if
        ):
            dt = max(0.001, now - self._last_time)
            prx, ptx = self._last_if_counters[self._wan_if]
            crx, ctx = cur_if[self._wan_if]
            rx_mbps = (max(0, crx - prx) * 8.0) / dt / 1_000_000.0
            tx_mbps = (max(0, ctx - ptx) * 8.0) / dt / 1_000_000.0

        self._last_if_counters = cur_if
        self._last_time = now

        return RouterData(True, uptime_s, load_1m, mem_pct, self._wan_if, rx_mbps, tx_mbps)
