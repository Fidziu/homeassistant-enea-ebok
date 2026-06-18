import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .api import EneaAuthError, EneaClient
from .const import (
    CONF_BACKFILL_START,
    CONF_CATCHUP_DAYS,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_PPE,
    CONF_THROTTLE_MS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_BACKFILL_START,
    DEFAULT_CATCHUP_DAYS,
    DEFAULT_THROTTLE_MS,
    DEFAULT_UPDATE_INTERVAL_HOURS,
    DOMAIN,
)

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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return EneaOptionsFlow(config_entry)


class EneaOptionsFlow(config_entries.OptionsFlow):
    """Regulacja: interwal odczytu, zakres backfillu, throttle."""

    def __init__(self, config_entry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        o = self._entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=o.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_HOURS),
                ): vol.All(vol.Coerce(float), vol.Range(min=0.5, max=48)),
                vol.Optional(
                    CONF_BACKFILL_START,
                    default=o.get(CONF_BACKFILL_START, DEFAULT_BACKFILL_START),
                ): str,
                vol.Optional(
                    CONF_CATCHUP_DAYS,
                    default=o.get(CONF_CATCHUP_DAYS, DEFAULT_CATCHUP_DAYS),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
                vol.Optional(
                    CONF_THROTTLE_MS,
                    default=o.get(CONF_THROTTLE_MS, DEFAULT_THROTTLE_MS),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=5000)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
