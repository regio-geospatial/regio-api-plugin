# -*- coding: utf-8 -*-
from __future__ import annotations

from qgis.PyQt import sip
import xml.etree.ElementTree as ET
from typing import Optional, Set

from qgis.PyQt.QtCore import QObject, QUrl, QUrlQuery, QTimer, QCoreApplication
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsSettings,
    QgsNetworkAccessManager,
)

from ..logger import PluginLogger
from ..settings import PluginSettings

def tr(text: str) -> str:
    return QCoreApplication.translate("RegioApiPlugin", text)


class BasemapController(QObject):

    CONN_NAME = "Regio API Plugin"
    LAYER_KEY = "RegioApiPlugin/basemap_id"
    BASEMAP_ID = "regio_wms_default"
    MAP_FILE = "/map/balti_wms.map"

    def __init__(self, iface, dock, settings: PluginSettings, logger: PluginLogger):
        super().__init__(dock)
        self._iface = iface
        self._dock = dock
        self._settings = settings
        self._log = logger

        self._nam = QgsNetworkAccessManager.instance()
        self._reply: Optional[QNetworkReply] = None
        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.timeout.connect(self._on_timeout)

        self._dock.btn_basemap_add.clicked.connect(self.add_basemap)

    # ---------- public ----------

    def add_basemap(self) -> None:
        apikey = (self._settings.api_key() or "").strip()
        if not apikey:
            self._iface.messageBar().pushWarning("Regio API Plugin", tr("API key not set. Open Settings."))
            return

        if self._find_existing_layer() is not None:
            self._iface.messageBar().pushInfo("Regio API Plugin", tr("Basemap already added."))
            return

        base_url = f"https://api.regio.ee/wms?map={self.MAP_FILE}&apikey={apikey}"
        self._ensure_wms_connection(base_url)

        self._fetch_capabilities_and_add(base_url)

    # ---------- WMS connection in QGIS settings ----------

    def _ensure_wms_connection(self, url: str) -> None:
        """
        Adds/updates a WMS connection so it shows up in QGIS WMS connections.
        """
        s = QgsSettings()
        base = f"/Qgis/connections-wms/{self.CONN_NAME}"
        s.setValue(f"{base}/url", url)
        s.setValue("/Qgis/connections-wms/selected", self.CONN_NAME)

    # ---------- GetCapabilities ----------

    def _fetch_capabilities_and_add(self, base_url: str) -> None:
        self._abort_reply()

        url = QUrl(base_url)
        q = QUrlQuery(url.query())
        q.addQueryItem("SERVICE", "WMS")
        q.addQueryItem("REQUEST", "GetCapabilities")
        q.addQueryItem("VERSION", "1.1.1")
        url.setQuery(q)

        self._iface.messageBar().pushInfo("Regio API Plugin", "Loading WMS capabilities")

        req = QNetworkRequest(url)
        self._reply = self._nam.get(req)
        self._timeout.start(12000)

        self._reply.finished.connect(lambda: self._on_capabilities_finished(base_url))

    def _on_timeout(self) -> None:
        self._abort_reply()
        self._iface.messageBar().pushCritical("Regio API Plugin", "WMS GetCapabilities timed out.")

    def _on_capabilities_finished(self, base_url: str) -> None:
        self._timeout.stop()

        reply = self._reply
        self._reply = None
        if reply is None or sip.isdeleted(reply):
            return

        if reply.error() != QNetworkReply.NetworkError.NoError:
            err = reply.errorString()
            reply.deleteLater()
            self._iface.messageBar().pushCritical("Regio API Plugin", f"WMS GetCapabilities failed: {err}")
            return

        data = bytes(reply.readAll())
        reply.deleteLater()

        layer_name = self._first_named_layer(data)
        if not layer_name:
            self._iface.messageBar().pushCritical("Regio API Plugin", "No WMS layers found in GetCapabilities.")
            return

        supported = self._supported_crs(data)
        request_crs = self._choose_request_crs(supported)

        self._add_wms_layer(base_url, layer_name, request_crs)

    @staticmethod
    def _strip_ns(tag: str) -> str:
        return tag.split("}", 1)[-1] if "}" in tag else tag

    def _first_named_layer(self, xml_bytes: bytes) -> Optional[str]:
        try:
            root = ET.fromstring(xml_bytes)
        except Exception:
            return None

        for layer in root.iter():
            if self._strip_ns(layer.tag).lower() != "layer":
                continue
            for ch in layer:
                if self._strip_ns(ch.tag).lower() == "name" and (ch.text or "").strip():
                    return (ch.text or "").strip()
        return None

    # ---------- CRS selection ----------

    @staticmethod
    def _norm_crs(crs: str) -> str:
        c = (crs or "").strip()
        if not c:
            return ""
        if c.lower().startswith("epsg:"):
            code = c.split(":", 1)[1].strip()
            return f"EPSG:{code}"
        return c.upper()

    def _supported_crs(self, xml_bytes: bytes) -> Set[str]:
        supported: Set[str] = set()
        try:
            root = ET.fromstring(xml_bytes)
        except Exception:
            return supported

        for el in root.iter():
            tag = self._strip_ns(el.tag).lower()
            if tag in ("srs", "crs"):
                txt = (el.text or "").strip()
                if txt:
                    supported.add(self._norm_crs(txt))

        return supported

    def _choose_request_crs(self, supported: Set[str]) -> str:
        project_crs = QgsProject.instance().crs().authid()
        project_crs = self._norm_crs(project_crs)

        if project_crs and project_crs in supported:
            return project_crs

        if "EPSG:3857" in supported:
            return "EPSG:3857"
        
        return project_crs or "EPSG:3857"

    # ---------- add layer ----------

    def _add_wms_layer(self, base_url: str, layer_name: str, request_crs: str) -> None:
        safe_url = base_url.replace("&", "%26")

        uri = (
            f"crs={request_crs}"
            "&format=image/png"
            f"&layers={layer_name}"
            "&styles="
            "&transparent=true"
            f"&url={safe_url}"
        )

        layer = QgsRasterLayer(uri, f"Regio Basemap ({layer_name})", "wms")
        if not layer.isValid():
            self._log.error(f"WMS layer invalid for layer={layer_name}. crs={request_crs}. uri={uri}")
            self._iface.messageBar().pushCritical(
                "Regio API Plugin",
                f"Failed to add WMS layer '{layer_name}'."
            )
            return

        layer.setCustomProperty(self.LAYER_KEY, self.BASEMAP_ID)
        QgsProject.instance().addMapLayer(layer)
        self._iface.messageBar().pushSuccess(
            "Regio API Plugin",
            f"Basemap added: {layer_name} (request CRS: {request_crs})"
        )

    # ---------- helpers ----------

    def _abort_reply(self) -> None:
        if self._reply is None:
            return
        try:
            if not sip.isdeleted(self._reply):
                self._reply.abort()
        except Exception:
            pass
        self._reply = None

    def _find_existing_layer(self) -> Optional[QgsRasterLayer]:
        for lyr in QgsProject.instance().mapLayers().values():
            if isinstance(lyr, QgsRasterLayer) and lyr.customProperty(self.LAYER_KEY) == self.BASEMAP_ID:
                return lyr
        return None
