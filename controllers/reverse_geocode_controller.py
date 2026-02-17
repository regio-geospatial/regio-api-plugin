# -*- coding: utf-8 -*-
from typing import Optional

from qgis.PyQt import sip
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPointXY, QgsProject
from qgis.PyQt.QtNetwork import QNetworkReply

from ..api_client import ApiClient
from ..settings import PluginSettings
from ..tools.reverse_map_tool import ReverseClickMapTool

def tr(text: str) -> str:
    return QCoreApplication.translate("RegioApiPlugin", text)


class ReverseGeocodeController:
    def __init__(self, iface, dock, api: ApiClient, settings: PluginSettings):
        self._iface = iface
        self._dock = dock
        self._api = api
        self._settings = settings

        self._tool: Optional[ReverseClickMapTool] = None
        self._prev_tool = None
        self._ignore_tool_events = False

        self._req_id = 0
        self._active_reply: Optional[QNetworkReply] = None

        self._last_address = ""
        self._last_postcode = ""
        self._last_coords = ""

        self._dock.reverse_toggle.toggled.connect(self._on_toggle)
        self._dock.btn_reverse_copy_address.clicked.connect(self._copy_address)
        self._dock.btn_reverse_copy_coords.clicked.connect(self._copy_coords)

        self._iface.mapCanvas().mapToolSet.connect(self._on_map_tool_set)

    # ---- reply helpers ----

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

    def _tool_active(self) -> bool:
        if self._tool is None:
            return False
        try:
            return not sip.isdeleted(self._tool)
        except Exception:
            return False

    # ---- clipboard ----

    def _copy_address(self):
        QApplication.clipboard().setText(self._last_address or "")

    def _copy_coords(self):
        QApplication.clipboard().setText(self._last_coords or "")

    # ---- activation/deactivation ----

    def deactivate(self):
        try:
            self._iface.mapCanvas().mapToolSet.disconnect(self._on_map_tool_set)
        except Exception:
            pass
        self._stop_reverse(restore_prev=True)

    def _stop_reverse(self, restore_prev: bool):
        self._abort_active_reply()

        canvas = self._iface.mapCanvas()

        if self._tool_active():
            try:
                self._tool.clicked.disconnect(self._on_click)
            except Exception:
                pass

        if restore_prev and self._prev_tool is not None:
            self._ignore_tool_events = True
            try:
                canvas.setMapTool(self._prev_tool)
            except Exception:
                pass
            finally:
                self._ignore_tool_events = False

        self._tool = None
        self._prev_tool = None

        self._dock.reverse_toggle.blockSignals(True)
        self._dock.reverse_toggle.setChecked(False)
        self._dock.reverse_toggle.blockSignals(False)
        self._dock.update_reverse_toggle_ui(False)

    def _on_map_tool_set(self, new_tool):
        if self._ignore_tool_events:
            return

        if self._dock.reverse_toggle.isChecked():
            if (not self._tool_active()) or (new_tool is not self._tool):
                self._stop_reverse(restore_prev=False)

    def _on_toggle(self, enabled: bool):
        canvas = self._iface.mapCanvas()

        if enabled:
            apikey = self._settings.api_key()
            if not apikey:
                self._iface.messageBar().pushWarning("Regio API Plugin", tr("API key not set. Open Settings."))
                self._dock.reverse_toggle.blockSignals(True)
                self._dock.reverse_toggle.setChecked(False)
                self._dock.reverse_toggle.blockSignals(False)
                self._dock.update_reverse_toggle_ui(False)
                return

            self._prev_tool = canvas.mapTool()

            self._tool = ReverseClickMapTool(canvas)
            self._tool.clicked.connect(self._on_click)

            self._ignore_tool_events = True
            try:
                canvas.setMapTool(self._tool)
            finally:
                self._ignore_tool_events = False

            self._iface.messageBar().pushInfo("Regio API Plugin", tr("Click on the map to get the nearest address."))
        else:
            self._stop_reverse(restore_prev=True)

    # ---- click handling and API call ----

    def _on_click(self, pt_canvas: QgsPointXY):
        apikey = self._settings.api_key()
        if not apikey:
            self._iface.messageBar().pushWarning("Regio API Plugin", tr("API key not set. Open Settings."))
            return

        canvas = self._iface.mapCanvas()
        canvas_crs = canvas.mapSettings().destinationCrs()
        wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")

        xform = QgsCoordinateTransform(canvas_crs, wgs84, QgsProject.instance())

        try:
            pt_wgs = xform.transform(pt_canvas)
        except Exception as e:
            self._iface.messageBar().pushWarning("Regio API Plugin", f"CRS transform failed: {e}")
            return

        lng, lat = float(pt_wgs.x()), float(pt_wgs.y())
        country = self._settings.countries_param()

        self._req_id += 1
        rid = self._req_id

        self._abort_active_reply()

        def _done(req_id: int, ok: bool, payload: Optional[dict], err: Optional[str]) -> None:
            self._active_reply = None

            if req_id != rid:
                return

            if not ok:
                self._iface.messageBar().pushCritical("Regio API Plugin", f"Reverse geocode failed: {err}")
                self._dock.set_reverse_result_text("")
                return

            data = (payload or {}).get("data") or []
            if not isinstance(data, list) or not data:
                self._dock.set_reverse_result_text(tr("No results."))
                self._last_address = ""
                self._last_postcode = ""
                self._last_coords = ""
                return

            best = data[0] or {}
            addr = best.get("address", "")
            postcode = best.get("postcode", "")
            g = best.get("geometry") or [lng, lat]

            try:
                glng, glat = float(g[0]), float(g[1])
            except Exception:
                glng, glat = lng, lat

            self._last_address = addr or ""
            self._last_postcode = postcode or ""
            self._last_coords = f"{glat:.8f}, {glng:.8f}"

            self._dock.set_reverse_result_text(
                f"{tr('Address')}: {addr}\n"
                f"{tr('Postcode')}: {postcode}\n"
                f"Lat/Lon (WGS84): {self._last_coords}"
            )

        self._active_reply = self._api.revgeocode(
            lng=lng,
            lat=lat,
            country=country,
            apikey=apikey,
            request_id=rid,
            on_done=_done,
            timeout_ms=10000
        )
