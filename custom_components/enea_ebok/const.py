DOMAIN = "enea_ebok"
PLATFORMS = ["sensor", "button"]

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_PPE = "point_of_delivery_id"

BASE_URL = "https://ebok.enea.pl"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
)

# eBOK data lags ~1-2 days; refresh and re-pull a window.
UPDATE_INTERVAL_HOURS = 12
BACKFILL_DAYS = 30          # legacy fallback
CATCHUP_DAYS = 5            # days re-pulled on every run (covers the lag)

# --- Opcje regulowane w UI (OptionsFlow) ---
CONF_UPDATE_INTERVAL = "update_interval_hours"   # co ile godzin odpytywac eBOK
CONF_BACKFILL_START = "backfill_start"           # "YYYY-MM-DD" - od kiedy ciagnac historie
CONF_CATCHUP_DAYS = "catchup_days"               # ile ostatnich dni odswiezac przy kazdym pull
CONF_THROTTLE_MS = "throttle_ms"                 # pauza miedzy dniami przy backfillu (anty-rate-limit)

DEFAULT_UPDATE_INTERVAL_HOURS = 6
DEFAULT_BACKFILL_START = "2023-05-01"            # najwczesniejsze dane w eBOK (sprawdzone 2026-06-18)
DEFAULT_CATCHUP_DAYS = 5
DEFAULT_THROTTLE_MS = 400

# Fallback delivery-point id (auto-discovered at config time when possible).
DEFAULT_PPE = "c0355c0f-3b08-e911-80de-005056b326a5"

TZ = "Europe/Warsaw"

# series_key -> (eBOK JSON field, display name). Each becomes an energy sensor
# whose recorder statistics are back-filled from eBOK.
#   aec/eaec       = pobrana/oddana PRZED bilansowaniem godzinowym (raw)
#   aecasb/eaecasb = po bilansowaniu (settlement)
SERIES: dict[str, tuple[str, str]] = {
    "grid_import": ("aec", "Enea pobór (przed bilansowaniem)"),
    "grid_export": ("eaec", "Enea oddanie (przed bilansowaniem)"),
    "grid_import_settled": ("aecasb", "Enea pobór (po bilansowaniu)"),
    "grid_export_settled": ("eaecasb", "Enea oddanie (po bilansowaniu)"),
}
