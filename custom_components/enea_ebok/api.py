"""Client for Enea eBOK (ebok.enea.pl).

Classic session-cookie web app: GET /logowanie for a CSRF token, POST it with
e-mail+password to get an EBOK_SESSION cookie, then the hourly meter data is an
XHR POST that returns a JSON array.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import date

import aiohttp
import async_timeout

from .const import BASE_URL, DEFAULT_PPE, USER_AGENT

_LOGGER = logging.getLogger(__name__)
TIMEOUT = 30


class EneaAuthError(Exception):
    """Login rejected."""


class EneaClient:
    def __init__(self, email: str, password: str, ppe: str | None = None) -> None:
        self._email = email
        self._password = password
        self._ppe = ppe or DEFAULT_PPE
        self._session: aiohttp.ClientSession | None = None
        self._logged_in = False

    @property
    def ppe(self) -> str:
        return self._ppe

    def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": USER_AGENT},
                cookie_jar=aiohttp.CookieJar(),
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def login(self) -> None:
        session = self._ensure_session()
        async with async_timeout.timeout(TIMEOUT):
            async with session.get(f"{BASE_URL}/logowanie") as resp:
                html = await resp.text()
            match = re.search(r'name="token"[^>]*value="([^"]+)"', html)
            if not match:
                raise EneaAuthError("CSRF token not found on login page")
            data = {
                "email": self._email,
                "password": self._password,
                "token": match.group(1),
                "btnSubmit": "",
            }
            async with session.post(f"{BASE_URL}/logowanie", data=data) as resp:
                final_url = str(resp.url)
        if "logowanie" in final_url:
            raise EneaAuthError("invalid e-mail or password")
        self._logged_in = True
        try:
            await self._discover_ppe()
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Enea: PPE auto-discovery failed, using %s", self._ppe)

    async def _discover_ppe(self) -> None:
        async with async_timeout.timeout(TIMEOUT):
            async with self._session.get(f"{BASE_URL}/meter/summaryBalancingChart") as resp:
                html = await resp.text()
        match = re.search(
            r'pointOfDeliveryId"?\s*[:=]\s*"?'
            r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
            html,
            re.I,
        )
        if match:
            self._ppe = match.group(1)

    async def async_get_day(self, day: date) -> list[dict]:
        """Return the 24 hourly rows for `day` (re-login once on session loss)."""
        for attempt in range(2):
            if not self._logged_in:
                await self.login()
            data = {
                "duration": "day",
                "date": day.strftime("%d.%m.%Y"),
                "pointOfDeliveryId": self._ppe,
            }
            headers = {"X-Requested-With": "XMLHttpRequest"}
            async with async_timeout.timeout(TIMEOUT):
                async with self._session.post(
                    f"{BASE_URL}/meter/summaryBalancingChart", data=data, headers=headers
                ) as resp:
                    text = await resp.text()
            stripped = text.lstrip()
            if stripped.startswith("["):
                return json.loads(stripped)
            # Not JSON -> session likely expired; re-login and retry once.
            self._logged_in = False
            if attempt == 0:
                continue
            _LOGGER.warning("Enea: unexpected non-JSON response for %s", day)
            return []
        return []

    async def async_validate(self) -> str:
        """Login and return the (possibly discovered) PPE id. For config flow."""
        await self.login()
        return self._ppe
