# -*- coding: utf-8 -*-
from collections import OrderedDict
from typing import Optional, Dict, Any, List, Tuple

from qgis.PyQt.QtCore import QObject, QTimer, QCoreApplication

from qgis.PyQt import sip

from ..api_client import ApiClient
from ..settings import PluginSettings
from ..logger import PluginLogger
from ..ui.widgets import GeocodeAutocompleteWidget

def tr(text: str) -> str:
    return QCoreApplication.translate("RegioApiPlugin", text)


class GeocodeAutocompleteController(QObject):
    def __init__(
        self,
        widget: GeocodeAutocompleteWidget,
        api: ApiClient,
        settings: PluginSettings,
        logger: PluginLogger,
        min_chars: int = 2,
        debounce_ms: int = 300,
        cache_size: int = 50,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self._w = widget
        self._api = api
        self._settings = settings
        self._log = logger

        self._min_chars = int(min_chars)
        self._debounce_ms = int(debounce_ms)
        self._cache_size = int(cache_size)

        self._cache: "OrderedDict[Tuple[str, str], List[Dict[str, Any]]]" = OrderedDict()

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._do_request)

        self._req_id = 0
        self._active_reply = None
        self._pending_text = ""

        self._w.textEdited.connect(self._on_text_edited)
        self._w.cleared.connect(self._on_cleared)

    # -------- reply helpers --------

    def _reply_active(self) -> bool:
        if self._active_reply is None:
            return False
        try:
            return not sip.isdeleted(self._active_reply)
        except Exception:
            return False

    def _abort_active_reply(self) -> None:
        if not self._reply_active():
            self._active_reply = None
            return
        try:
            self._active_reply.abort()
        except Exception:
            pass
        finally:
            self._active_reply = None

    # -------- UI signals --------

    def _on_cleared(self):
        self._timer.stop()
        self._abort_active_reply()

    def _on_text_edited(self, text: str) -> None:
        self._pending_text = (text or "").strip()
        self._timer.start(self._debounce_ms)

    # -------- cache helpers --------

    def _cache_get(self, query: str, country: str):
        key = (query, country)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def _cache_put(self, query: str, country: str, results: List[Dict[str, Any]]):
        key = (query, country)
        self._cache[key] = results
        self._cache.move_to_end(key)
        while len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

    # -------- request logic --------

    def _do_request(self) -> None:
        query = self._pending_text

        if len(query) < self._min_chars:
            self._w.set_hint("")
            self._w.clear_suggestions()
            return

        apikey = self._settings.api_key()
        if not apikey:
            self._w.set_hint(tr("API key not set. Open Settings."))
            self._w.clear_suggestions()
            return
        self._w.set_hint("")

        country = self._settings.countries_param()

        cached = self._cache_get(query, country)
        if cached is not None:
            self._w.set_suggestions(cached)
            return

        self._req_id += 1
        rid = self._req_id

        self._abort_active_reply()

        def _done(req_id: int, ok: bool, payload: Optional[dict], err: Optional[str]) -> None:
            self._active_reply = None

            if req_id != rid:
                return
            if self._w.text().strip() != query:
                return

            if not ok:
                self._log.warning(f"Geocode failed for '{query}': {err}")
                self._w.clear_suggestions()
                return

            data = (payload or {}).get("data") or []
            if not isinstance(data, list):
                self._w.clear_suggestions()
                return

            self._cache_put(query, country, data)
            self._w.set_suggestions(data)

        self._active_reply = self._api.geocode(
            address=query,
            country=country,
            apikey=apikey,
            request_id=rid,
            on_done=_done,
            timeout_ms=10000
        )
