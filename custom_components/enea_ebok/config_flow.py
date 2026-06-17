import logging

import voluptuous as vol
from homeassistant import config_entries

from .api import EneaAuthError, EneaClient
from .const import CONF_EMAIL, CONF_PASSWORD, CONF_PPE, DOMAIN

_LOGGER = logging.getLogger(__name__)


class EneaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            client = EneaClient(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])
            try:
                ppe = await client.async_validate()
            except EneaAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Enea: unexpected error during setup")
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Enea ({user_input[CONF_EMAIL]})",
                    data={
                        CONF_EMAIL: user_input[CONF_EMAIL],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_PPE: ppe,
                    },
                )
            finally:
                await client.close()

        schema = vol.Schema(
            {vol.Required(CONF_EMAIL): str, vol.Required(CONF_PASSWORD): str}
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
