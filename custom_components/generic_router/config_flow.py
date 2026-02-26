from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SSH_MODE,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    SSH_MODE_MODERN,
    SSH_MODE_LEGACY,
)


class GenericRouterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            await self.async_set_unique_id(host.lower())
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=host, data={
                CONF_HOST: host,
                CONF_PORT: int(user_input.get(CONF_PORT, DEFAULT_PORT)),
                CONF_USERNAME: user_input[CONF_USERNAME].strip(),
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_SSH_MODE: user_input.get(CONF_SSH_MODE, SSH_MODE_MODERN),
            })

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
            vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(CONF_SSH_MODE, default=SSH_MODE_MODERN): vol.In([SSH_MODE_MODERN, SSH_MODE_LEGACY]),
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
