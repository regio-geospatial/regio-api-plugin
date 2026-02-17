# -*- coding: utf-8 -*-
import json
from typing import Callable, Optional, Any, Dict

from qgis.PyQt.QtCore import QObject, QUrl, QUrlQuery, QTimer
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.core import QgsNetworkAccessManager

from .logger import PluginLogger


class ApiClient(QObject):
    BASE_URL = "https://api.regio.ee"

    def __init__(self, logger: PluginLogger, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._log = logger
        self._nam = QgsNetworkAccessManager.instance()

    def _build_url(self, path: str, params: Dict[str, Any]) -> QUrl:
        url = QUrl(f"{self.BASE_URL}{path}")
        q = QUrlQuery()
        for k, v in params.items():
            if v is None:
                continue
            q.addQueryItem(k, str(v))
        url.setQuery(q)
        return url

    def _safe_url_for_log(self, url: QUrl) -> str:
        safe_url = QUrl(url)
        q = QUrlQuery(safe_url)

        if q.hasQueryItem("apikey"):
            q.removeAllQueryItems("apikey")
            q.addQueryItem("apikey", "***")

        safe_url.setQuery(q)
        return safe_url.toString()

    def _get_json(
        self,
        url: QUrl,
        request_id: int,
        on_done: Callable[[int, bool, Optional[dict], Optional[str]], None],
        timeout_ms: int = 10000
    ) -> QNetworkReply:
        safe_url_str = self._safe_url_for_log(url)

        req = QNetworkRequest(url)
        req.setRawHeader(b"Accept", b"application/json")

        reply = self._nam.get(req)
        reply.setProperty("request_id", request_id)

        timeout = QTimer(reply)
        timeout.setSingleShot(True)

        def _on_timeout():
            if reply.isRunning():
                self._log.warning(f"Timeout: {safe_url_str}")
                reply.abort()

        timeout.timeout.connect(_on_timeout)
        timeout.start(timeout_ms)

        def _finished():
            timeout.stop()
            rid = int(reply.property("request_id") or -1)

            if reply.error() != QNetworkReply.NetworkError.NoError:
                err = reply.errorString()
                self._log.error(f"Network error ({rid}): {err} | {safe_url_str}")
                reply.deleteLater()
                on_done(rid, False, None, err)
                return

            raw = bytes(reply.readAll()).decode("utf-8", errors="replace")
            try:
                data = json.loads(raw) if raw else {}
            except Exception as e:
                err = f"JSON parse error: {e}"
                self._log.error(f"{err} | {safe_url_str} | raw={raw[:300]}")
                reply.deleteLater()
                on_done(rid, False, None, err)
                return

            reply.deleteLater()
            on_done(rid, True, data, None)

        reply.finished.connect(_finished)
        return reply

    def geocode(
        self,
        address: str,
        country: str,
        apikey: str,
        request_id: int,
        on_done: Callable[[int, bool, Optional[dict], Optional[str]], None],
        timeout_ms: int = 10000
    ) -> QNetworkReply:
        url = self._build_url("/geocode", {
            "address": address,
            "country": country,
            "limit": 10,
            "apikey": apikey
        })
        self._log.debug(f"GEOCODE URL: {self._safe_url_for_log(url)}")
        return self._get_json(url, request_id, on_done, timeout_ms=timeout_ms)
    
    def revgeocode(
        self,
        lng: float,
        lat: float,
        country: str,
        apikey: str,
        request_id: int,
        on_done: Callable[[int, bool, Optional[dict], Optional[str]], None],
        timeout_ms: int = 10000
    ) -> QNetworkReply:
        url = self._build_url("/revgeocode", {
            "lng": lng,
            "lat": lat,
            "country": country,
            "apikey": apikey
        })
        self._log.debug(f"REVGEOCODE URL: {self._safe_url_for_log(url)}")
        return self._get_json(url, request_id, on_done, timeout_ms=timeout_ms)

    def routing(
        self,
        coordinates: str,
        profile: str,
        apikey: str,
        request_id: int,
        on_done,
        overview: str = "full",
        geometries: str = "geojson",
        timeout_ms: int = 20000
    ) -> QNetworkReply:
        url = self._build_url("/routing", {
            "coordinates": coordinates,
            "profile": profile,
            "overview": overview,
            "geometries": geometries,
            "apikey": apikey
        })
        self._log.debug(f"ROUTING URL: {self._safe_url_for_log(url)}")
        return self._get_json(url, request_id, on_done, timeout_ms=timeout_ms)
    
    def optimize(
        self,
        coordinates: str,
        apikey: str,
        request_id: int,
        on_done,
        overview: str = "full",
        profile: str = "car",
        source: str = "first",
        destination: str = "last",
        roundtrip: str = "true",
        timeout_ms: int = 20000
    ) -> QNetworkReply:
        url = self._build_url("/routing", {
            "service": "optimize",
            "coordinates": coordinates,
            "overview": overview,
            "source": source,
            "profile": profile,
            "destination": destination,
            "roundtrip": roundtrip,
            "apikey": apikey
        })
        self._log.debug(f"OPTIMIZE URL: {self._safe_url_for_log(url)}")
        return self._get_json(url, request_id, on_done, timeout_ms=timeout_ms)
