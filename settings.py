# -*- coding: utf-8 -*-
from qgis.core import QgsSettings

PLUGIN_NS = "RegioApiPlugin"

KEY_API_KEY = f"{PLUGIN_NS}/api_key"
KEY_COUNTRIES = f"{PLUGIN_NS}/countries"
KEY_LANGUAGE = f"{PLUGIN_NS}/language"
KEY_DEBUG_LOGGING = f"{PLUGIN_NS}/debug_logging"

DEFAULT_COUNTRIES = ["EE", "LV", "LT"]
DEFAULT_LANGUAGE = "en"
DEFAULT_DEBUG_LOGGING = False

_ALLOWED = {"EE", "LV", "LT"}


class PluginSettings:
    def __init__(self):
        self._s = QgsSettings()

    def api_key(self) -> str:
        return self._s.value(KEY_API_KEY, "", type=str)

    def set_api_key(self, key: str) -> None:
        self._s.setValue(KEY_API_KEY, (key or "").strip())

    def countries(self) -> list[str]:
        raw = self._s.value(KEY_COUNTRIES, "", type=str).strip()
        if not raw:
            return DEFAULT_COUNTRIES[:]
        vals = [c.strip().upper() for c in raw.split(",") if c.strip()]
        vals = [c for c in vals if c in _ALLOWED]
        return vals or DEFAULT_COUNTRIES[:]

    def set_countries(self, countries: list[str]) -> None:
        vals = [(c or "").strip().upper() for c in (countries or [])]
        vals = [c for c in vals if c in _ALLOWED]
        if not vals:
            vals = DEFAULT_COUNTRIES[:]
        self._s.setValue(KEY_COUNTRIES, ",".join(vals))

    def countries_param(self) -> str:
        return ",".join([c.lower() for c in self.countries()])

    def language(self) -> str:
        return self._s.value(KEY_LANGUAGE, DEFAULT_LANGUAGE, type=str)

    def set_language(self, lang: str) -> None:
        self._s.setValue(KEY_LANGUAGE, (lang or DEFAULT_LANGUAGE).strip().lower())

    def debug_logging(self) -> bool:
        return self._s.value(KEY_DEBUG_LOGGING, DEFAULT_DEBUG_LOGGING, type=bool)

    def set_debug_logging(self, enabled: bool) -> None:
        self._s.setValue(KEY_DEBUG_LOGGING, bool(enabled))
