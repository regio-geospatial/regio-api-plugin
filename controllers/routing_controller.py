# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional, Dict, Any, List, Tuple

from qgis.PyQt import sip

from qgis.PyQt.QtCore import QObject, QTimer, QMetaType, QSignalBlocker, QSize, QEvent, QCoreApplication
from qgis.PyQt.QtNetwork import QNetworkReply
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QListWidgetItem, QFileDialog

from qgis.core import (
    QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsVectorLayer, QgsField, QgsFields, QgsFeature, QgsGeometry, QgsPointXY,
    QgsLineSymbol, QgsSingleSymbolRenderer,
    QgsMarkerSymbol,
    QgsPalLayerSettings, QgsVectorLayerSimpleLabeling,
    QgsTextFormat, QgsTextBufferSettings, QgsWkbTypes
)

from ..api_client import ApiClient
from ..settings import PluginSettings
from ..logger import PluginLogger
from ..ui.widgets import RoutingWaypointRow, GeocodeAutocompleteWidget
from ..controllers.autocomplete_controller import GeocodeAutocompleteController
from ..tools.route_point_drag_tool import RoutePointDragTool
from ..tools.route_point_pick_tool import RoutePointPickTool

FIELD_DOUBLE = QMetaType.Type.Double
FIELD_INT = QMetaType.Type.Int
FIELD_STRING = QMetaType.Type.QString

def tr(text: str) -> str:
    return QCoreApplication.translate("RegioApiPlugin", text)


class RoutingController(QObject):
    def __init__(self, iface, dock, api: ApiClient, settings: PluginSettings, logger: PluginLogger):
        super().__init__(dock)
        self._iface = iface
        self._dock = dock
        self._api = api
        self._settings = settings
        self._log = logger

        self._req_id = 0
        self._active_reply: Optional[QNetworkReply] = None

        self._route_layer_id: Optional[str] = None
        self._points_layer_id: Optional[str] = None

        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self._auto_calc_now)
        self._suppress_auto = False

        self._drag_tool: Optional[RoutePointDragTool] = None
        self._prev_tool = None

        self._pick_tool: Optional[RoutePointPickTool] = None
        self._pick_prev_tool = None
        self._pick_target: Optional[RoutingWaypointRow] = None

        self._rows: List[Tuple[RoutingWaypointRow, GeocodeAutocompleteController]] = []

        # UI signals
        dock.btn_routing_add_stop.clicked.connect(self.add_stop)
        dock.btn_routing_import_geojson.clicked.connect(self.import_geojson_points)
        dock.btn_routing_calc.clicked.connect(lambda: self.calculate_route(auto=False))
        dock.btn_routing_clear.clicked.connect(self.clear_route)
        dock.btn_routing_reverse.clicked.connect(self.reverse_route)
        dock.btn_routing_edit_points.toggled.connect(self._toggle_drag_points)

        dock.chk_opt_start_first.toggled.connect(self._update_optimize_constraints)
        dock.chk_opt_end_last.toggled.connect(self._update_optimize_constraints)
        dock.chk_opt_roundtrip.toggled.connect(self._update_optimize_constraints)
        self._update_optimize_constraints()

        dock.btn_routing_optimize.clicked.connect(self.optimize_and_calculate)

        self._routing_vp = dock.routing_points_list.viewport()
        self._routing_vp.installEventFilter(self)

        dock.routing_profile.currentIndexChanged.connect(lambda _i: self._schedule_auto_calc())

        dock.routing_points_list.model().rowsMoved.connect(self._on_rows_moved)

        self._iface.mapCanvas().mapToolSet.connect(self._on_map_tool_set_for_pick)

        self._init_default_rows()

        # initial UI state
        dock.btn_routing_edit_points.setVisible(False)

    # ---------------- list row helpers ----------------

    def _init_default_rows(self) -> None:
        lw = self._dock.routing_points_list
        lw.clear()
        self._rows.clear()

        self._append_row(placeholder=tr("From"))
        self._append_row(placeholder=tr("To"))
        self._renumber_ui()

    def _append_row(self, placeholder: str = tr("Stop"), insert_index: Optional[int] = None) -> RoutingWaypointRow:
        lw = self._dock.routing_points_list

        row = RoutingWaypointRow(lw, placeholder=placeholder)
        auto = GeocodeAutocompleteController(row.input, self._api, self._settings, self._log, debounce_ms=300)

        row.removeRequested.connect(self._remove_row)
        row.pickRequested.connect(self._start_pick_for_row)
        row.input.resultSelected.connect(lambda _r: self._schedule_auto_calc())

        if insert_index is None:
            item_index = lw.count()
        else:
            item_index = max(0, min(int(insert_index), lw.count()))

        item = QListWidgetItem()
        lw.insertItem(item_index, item)
        lw.setItemWidget(item, row)
        sh = row.sizeHint()
        item.setSizeHint(QSize(0, sh.height()))
        QTimer.singleShot(0, self._sync_routing_row_widths)

        self._sync_rows_from_list()
        self._rows.append((row, auto))
        self._sync_rows_from_list()

        return row

    def _sync_rows_from_list(self) -> None:
        lw = self._dock.routing_points_list
        new_rows: List[Tuple[RoutingWaypointRow, GeocodeAutocompleteController]] = []

        m = {r: a for (r, a) in self._rows}

        for i in range(lw.count()):
            it = lw.item(i)
            w = lw.itemWidget(it)
            if isinstance(w, RoutingWaypointRow):
                a = m.get(w)
                if a is not None:
                    new_rows.append((w, a))

        self._rows = new_rows

    def _on_rows_moved(self, *args) -> None:
        self._sync_rows_from_list()
        self._renumber_ui()
        QTimer.singleShot(0, self._sync_routing_row_widths)
        self._dock.set_routing_summary_text("")
        self._schedule_auto_calc()

    def _renumber_ui(self) -> None:
        for i, (row, _auto) in enumerate(self._rows, start=1):
            row.set_seq(i)

    def add_stop(self) -> None:
        lw = self._dock.routing_points_list
        idx = max(0, lw.count() - 1)
        self._append_row(placeholder=tr("Stop"), insert_index=idx)
        self._renumber_ui()
        self._dock.set_routing_summary_text("")

    def add_stop_from_map(self) -> None:
        lw = self._dock.routing_points_list
        idx = max(0, lw.count() - 1)
        row = self._append_row(placeholder=tr("Stop"), insert_index=idx)
        self._renumber_ui()
        self._dock.set_routing_summary_text("")
        self._start_pick_for_row(row)

    def _remove_row(self, row_obj: RoutingWaypointRow) -> None:
        lw = self._dock.routing_points_list
        if lw.count() <= 2:
            self._iface.messageBar().pushWarning("Regio API Plugin", "Routing needs at least 2 points.")
            return

        for i in range(lw.count()):
            it = lw.item(i)
            w = lw.itemWidget(it)
            if w is row_obj:
                lw.removeItemWidget(it)
                it2 = lw.takeItem(i)
                del it2
                try:
                    row_obj.setParent(None)
                    row_obj.deleteLater()
                except Exception:
                    pass
                break

        self._sync_rows_from_list()
        self._renumber_ui()
        self._dock.set_routing_summary_text("")
        self._schedule_auto_calc()

    # ---------------- reply helpers ----------------

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

    # ---------------- map pick ----------------

    def _on_map_tool_set_for_pick(self, new_tool, old_tool):
        if self._pick_tool is not None and new_tool is not self._pick_tool:
            self._pick_tool = None
            self._pick_prev_tool = None
            self._pick_target = None

    def _start_pick_for_row(self, row_obj: RoutingWaypointRow) -> None:
        canvas = self._iface.mapCanvas()
        self._pick_target = row_obj
        self._pick_prev_tool = canvas.mapTool()

        self._pick_tool = RoutePointPickTool(canvas)
        self._pick_tool.clicked.connect(self._on_pick_clicked)
        canvas.setMapTool(self._pick_tool)

        self._iface.messageBar().pushInfo("Regio API Plugin", "Click on map to place point.")

    def _on_pick_clicked(self, pt_canvas):
        canvas = self._iface.mapCanvas()

        row = self._pick_target
        if row is None:
            return

        canvas_crs = canvas.mapSettings().destinationCrs()
        wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        xform = QgsCoordinateTransform(canvas_crs, wgs84, QgsProject.instance())

        try:
            pt_wgs = xform.transform(pt_canvas)
        except Exception:
            return

        lng, lat = float(pt_wgs.x()), float(pt_wgs.y())

        widget: GeocodeAutocompleteWidget = row.input
        widget.set_selected_result(
            {"address": f"{lat:.6f}, {lng:.6f}", "geometry": [lng, lat], "postcode": "", "type": "map"},
            set_text=True
        )

        try:
            if self._pick_tool:
                self._pick_tool.clicked.disconnect(self._on_pick_clicked)
        except Exception:
            pass

        self._pick_tool = None
        self._pick_target = None

        if self._pick_prev_tool:
            try:
                canvas.setMapTool(self._pick_prev_tool)
            except Exception:
                pass
        self._pick_prev_tool = None

        apikey = self._settings.api_key().strip()
        if not apikey:
            self._schedule_auto_calc()
            return

        country = self._settings.countries_param()

        self._req_id += 1
        rid = self._req_id
        self._abort_active_reply()

        def _done(req_id: int, ok: bool, payload: Optional[dict], err: Optional[str]) -> None:
            self._active_reply = None
            if req_id != rid:
                return

            addr = ""
            if ok:
                data = (payload or {}).get("data") or []
                if isinstance(data, list) and data:
                    best = data[0] or {}
                    addr = best.get("address", "") or ""

            widget.set_selected_result(
                {
                    "address": addr if addr else widget.text(),
                    "geometry": [lng, lat],
                    "postcode": "",
                    "type": "map"
                },
                set_text=True
            )
            self._schedule_auto_calc()

        self._active_reply = self._api.revgeocode(
            lng=lng, lat=lat,
            country=country,
            apikey=apikey,
            request_id=rid,
            on_done=_done,
            timeout_ms=12000
        )

    # ---------------- UX helpers ----------------

    def deactivate(self):
        self._toggle_drag_points(False)

        prj = QgsProject.instance()

        if self._route_layer_id:
            lyr = prj.mapLayer(self._route_layer_id)
            if lyr:
                prj.removeMapLayer(lyr.id())
            self._route_layer_id = None

        if self._points_layer_id:
            lyr = prj.mapLayer(self._points_layer_id)
            if lyr:
                prj.removeMapLayer(lyr.id())
            self._points_layer_id = None

        try:
            self._iface.mapCanvas().refresh()
        except Exception:
            pass

    def _schedule_auto_calc(self):
        if self._suppress_auto:
            return
        self._auto_timer.start(350)

    def _auto_calc_now(self):
        if self._suppress_auto:
            return
        if len(self._rows) < 2:
            return
        for row, _auto in self._rows:
            if row.input.selected_result() is None:
                return
        self.calculate_route(auto=True)

    def _route_already_drawn(self) -> bool:
        prj = QgsProject.instance()
        if not self._route_layer_id:
            return False
        lyr = prj.mapLayer(self._route_layer_id)
        return isinstance(lyr, QgsVectorLayer) and lyr.featureCount() > 0
    
    def eventFilter(self, obj, event):
        vp = getattr(self, "_routing_vp", None)

        try:
            if vp is None or sip.isdeleted(vp):
                return False
        except Exception:
            return False

        if obj is vp and event.type() == QEvent.Type.Resize:
            QTimer.singleShot(0, self._sync_routing_row_widths)
            return False

        return super().eventFilter(obj, event)


    def _sync_routing_row_widths(self) -> None:
        lw = self._dock.routing_points_list
        vw = max(0, lw.viewport().width())

        for i in range(lw.count()):
            it = lw.item(i)
            w = lw.itemWidget(it)
            if w is None:
                continue

            w.setFixedWidth(vw)
            w.updateGeometry()

            sh = w.sizeHint()
            it.setSizeHint(QSize(0, sh.height()))

        lw.doItemsLayout()
        lw.viewport().update()

    # ---------------- reverse route ----------------

    def reverse_route(self):
        if len(self._rows) < 2:
            return

        try:
            canvas = self._iface.mapCanvas()
            if self._pick_tool:
                try:
                    self._pick_tool.clicked.disconnect(self._on_pick_clicked)
                except Exception:
                    pass
                self._pick_tool = None
                self._pick_target = None
                if self._pick_prev_tool:
                    try:
                        canvas.setMapTool(self._pick_prev_tool)
                    except Exception:
                        pass
                self._pick_prev_tool = None
        except Exception:
            pass

        self._suppress_auto = True
        try:
            snap = []
            for row, _auto in self._rows:
                sel = row.input.selected_result()
                sel_copy = dict(sel) if isinstance(sel, dict) else None
                txt = row.input.text()
                snap.append((sel_copy, txt))

            snap.reverse()

            for (row, _auto), (sel, txt) in zip(self._rows, snap):
                row.input.set_selected_result(sel, set_text=True)

                if sel is None:
                    row.input.edit.blockSignals(True)
                    row.input.edit.setText(txt)
                    row.input.edit.blockSignals(False)

            self._renumber_ui()
            self._dock.set_routing_summary_text("")
        finally:
            self._suppress_auto = False

        self._schedule_auto_calc()

    # ---------------- clear route ----------------

    def clear_route(self):
        self._suppress_auto = True
        try:
            self._auto_timer.stop()
            self._abort_active_reply()
            self._toggle_drag_points(False)

            self._dock.set_routing_summary_text("")

            self._init_default_rows()

            prj = QgsProject.instance()

            if self._route_layer_id:
                lyr = prj.mapLayer(self._route_layer_id)
                if lyr:
                    prj.removeMapLayer(lyr.id())
                self._route_layer_id = None

            if self._points_layer_id:
                lyr = prj.mapLayer(self._points_layer_id)
                if lyr:
                    try:
                        if lyr.isEditable():
                            lyr.rollBack()
                    except Exception:
                        pass
                    prj.removeMapLayer(lyr.id())
                self._points_layer_id = None

            self._dock.btn_routing_edit_points.setVisible(False)

            self._iface.mapCanvas().refresh()

        finally:
            self._suppress_auto = False

    # ---------------- point extraction ----------------

    @staticmethod
    def _extract_lnglat(sel: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        geom = (sel or {}).get("geometry")
        if not (isinstance(geom, (list, tuple)) and len(geom) >= 2):
            return None
        try:
            lng = float(geom[0])
            lat = float(geom[1])
            return lng, lat
        except Exception:
            return None

    def _collect_waypoints(self) -> Optional[List[Tuple[float, float]]]:
        pts: List[Tuple[float, float]] = []

        if len(self._rows) < 2:
            self._iface.messageBar().pushWarning("Regio API Plugin", "Add at least 2 points.")
            return None

        for row, _auto in self._rows:
            sel = row.input.selected_result()
            if not sel:
                self._iface.messageBar().pushWarning("Regio API Plugin", "Select suggestions for all points.")
                return None
            p = self._extract_lnglat(sel)
            if not p:
                return None
            pts.append(p)

        return pts

    # ---------------- GeoJSON import for routing ----------------

    def _clear_all_rows(self) -> None:
        lw = self._dock.routing_points_list

        for i in reversed(range(lw.count())):
            it = lw.item(i)
            w = lw.itemWidget(it)
            if w is not None:
                try:
                    lw.removeItemWidget(it)
                except Exception:
                    pass
                try:
                    w.setParent(None)
                    w.deleteLater()
                except Exception:
                    pass
            it2 = lw.takeItem(i)
            try:
                del it2
            except Exception:
                pass

        self._rows.clear()

    def import_geojson_points(self) -> None:
        path, _flt = QFileDialog.getOpenFileName(
            self._dock,
            "Import GeoJSON",
            "",
            "GeoJSON (*.geojson *.json);;All files (*.*)"
        )
        if not path:
            return

        vl = QgsVectorLayer(path, "Imported Route GeoJSON", "ogr")
        if not vl.isValid():
            self._iface.messageBar().pushCritical("Regio API Plugin", "Invalid GeoJSON.")
            return

        QgsProject.instance().addMapLayer(vl)

        wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        xform = QgsCoordinateTransform(vl.crs(), wgs84, QgsProject.instance())

        pts: List[Tuple[float, float]] = []
        for f in vl.getFeatures():
            g = f.geometry()
            if not g or g.isEmpty():
                continue
            if QgsWkbTypes.geometryType(g.wkbType()) != QgsWkbTypes.PointGeometry:
                continue

            if QgsWkbTypes.isMultiType(g.wkbType()):
                try:
                    for p in g.asMultiPoint():
                        pt = xform.transform(QgsPointXY(p))
                        pts.append((float(pt.x()), float(pt.y())))
                except Exception:
                    continue
            else:
                try:
                    p = g.asPoint()
                    pt = xform.transform(QgsPointXY(p))
                    pts.append((float(pt.x()), float(pt.y())))
                except Exception:
                    continue

            if len(pts) >= 50:
                break

        if len(pts) < 2:
            self._iface.messageBar().pushWarning("Regio API Plugin", "GeoJSON must contain at least 2 points.")
            return

        self._suppress_auto = True
        try:
            self._auto_timer.stop()
            self._abort_active_reply()
            self._toggle_drag_points(False)

            self._dock.set_routing_summary_text("")

            self._clear_all_rows()

            n = len(pts)
            for i, (lng, lat) in enumerate(pts):
                placeholder = tr("Stop")
                if i == 0:
                    placeholder = tr("From")
                elif i == n - 1:
                    placeholder = tr("To")

                row = self._append_row(placeholder=placeholder, insert_index=None)
                row.input.set_selected_result(
                    {"address": f"{lat:.6f}, {lng:.6f}", "geometry": [lng, lat], "postcode": "", "type": "geojson"},
                    set_text=True
                )

            self._sync_rows_from_list()
            self._renumber_ui()
        finally:
            self._suppress_auto = False

        self.calculate_route(auto=False)

    # ---------------- calculate route ----------------

    def calculate_route(self, auto: bool):
        apikey = self._settings.api_key().strip()
        if not apikey:
            self._iface.messageBar().pushWarning("Regio API Plugin", "API key not set. Open Settings.")
            return

        wps = self._collect_waypoints()
        if not wps:
            return

        coords_param = ";".join([f"{lng:.8f},{lat:.8f}" for (lng, lat) in wps])
        profile = str(self._dock.routing_profile.currentData() or "car")

        self._req_id += 1
        rid = self._req_id

        self._abort_active_reply()

        if not auto:
            self._dock.set_routing_summary_text(tr("Calculating"))
        self._dock.btn_routing_calc.setEnabled(False)

        def _done(req_id: int, ok: bool, payload: Optional[dict], err: Optional[str]) -> None:
            self._active_reply = None
            self._dock.btn_routing_calc.setEnabled(True)

            if req_id != rid:
                return

            if not ok:
                self._dock.set_routing_summary_text("")
                self._iface.messageBar().pushCritical("Regio API Plugin", f"Routing failed: {err}")
                return

            route = (payload or {}).get("routes", [None])[0] or None
            if not route:
                self._dock.set_routing_summary_text("No route found.")
                return

            dist_m = float(route.get("distance", 0.0) or 0.0)
            dur_s = float(route.get("duration", 0.0) or 0.0)

            geom = route.get("geometry")
            coords_ll: List[Tuple[float, float]] = []

            if isinstance(geom, dict) and geom.get("type") == "LineString":
                try:
                    coords_ll = [(float(x), float(y)) for (x, y) in (geom.get("coordinates") or [])]
                except Exception:
                    coords_ll = []

            if len(coords_ll) < 2:
                self._dock.set_routing_summary_text("No route geometry.")
                return

            self._update_route_layers(coords_ll, wps, dist_m, dur_s, profile)

            self._dock.btn_routing_edit_points.setVisible(True)
            self._dock.set_routing_summary_text(self._format_summary(dist_m, dur_s, profile))

        self._active_reply = self._api.routing(
            coordinates=coords_param,
            profile=profile,
            apikey=apikey,
            request_id=rid,
            on_done=_done,
            overview="full",
            geometries="geojson",
            timeout_ms=20000
        )

    # ---------------- Optimize then calculate route ----------------

    def optimize_and_calculate(self) -> None:
        apikey = self._settings.api_key().strip()
        if not apikey:
            self._iface.messageBar().pushWarning("Regio API Plugin", "API key not set. Open Settings.")
            return

        wps = self._collect_waypoints()
        if not wps:
            return

        coords_param = ";".join([f"{lng:.7f},{lat:.7f}" for (lng, lat) in wps])
        profile = str(self._dock.routing_profile.currentData() or "car")

        source = "first" if self._dock.chk_opt_start_first.isChecked() else "any"
        destination = "last" if self._dock.chk_opt_end_last.isChecked() else "any"
        roundtrip = "true" if self._dock.chk_opt_roundtrip.isChecked() else "false"

        self._req_id += 1
        rid = self._req_id

        self._abort_active_reply()

        def _done(req_id: int, ok: bool, payload: Optional[dict], err: Optional[str]) -> None:
            self._active_reply = None
            if req_id != rid:
                return

            if not ok:
                self._iface.messageBar().pushCritical("Regio API Plugin", f"Optimize failed: {err}")
                return

            wps_resp = (payload or {}).get("waypoints") or []
            if isinstance(wps_resp, list) and len(wps_resp) == len(self._rows):
                try:
                    order = sorted(
                        range(len(self._rows)),
                        key=lambda i: int((wps_resp[i] or {}).get("waypoint_index", i))
                    )
                    self._reorder_rows_by_order(order)
                except Exception:
                    pass

            trip = (payload or {}).get("trips", [None])[0] or None
            wps_resp = (payload or {}).get("waypoints") or []

            if isinstance(wps_resp, list) and len(wps_resp) == len(self._rows):
                order = sorted(
                    range(len(self._rows)),
                    key=lambda i: int((wps_resp[i] or {}).get("waypoint_index", i))
                )
                self._reorder_rows_by_order(order)

            if trip and isinstance(trip.get("geometry"), dict):
                geom = trip.get("geometry") or {}
                coords = geom.get("coordinates") or []

                coords_ll = [(float(x), float(y)) for (x, y) in coords if isinstance(x, (int, float))]

                dist_m = float(trip.get("distance", 0.0) or 0.0)
                dur_s = float(trip.get("duration", 0.0) or 0.0)

                ordered_wp = sorted(wps_resp, key=lambda w: int((w or {}).get("waypoint_index", 0)))
                waypoints_ll = [(float(w["location"][0]), float(w["location"][1])) for w in ordered_wp if w.get("location")]

                self._update_route_layers(coords_ll, waypoints_ll, dist_m, dur_s, profile)

                self._dock.btn_routing_edit_points.setVisible(True)
                self._dock.set_routing_summary_text(self._format_summary(dist_m, dur_s, profile))
                return

            QTimer.singleShot(0, lambda: self.calculate_route(auto=False))

        self._active_reply = self._api.optimize(
            coordinates=coords_param,
            apikey=apikey,
            request_id=rid,
            on_done=_done,
            overview="full",
            profile=profile,
            source=source,
            destination=destination,
            roundtrip=roundtrip,
            timeout_ms=20000
        )

    def _update_optimize_constraints(self) -> None:
        unsupported = (not self._dock.chk_opt_roundtrip.isChecked()
            and not self._dock.chk_opt_start_first.isChecked()
            and not self._dock.chk_opt_end_last.isChecked())

        if unsupported:
            self._dock.btn_routing_optimize.setEnabled(False)
        else:
            self._dock.btn_routing_optimize.setEnabled(True)

    def _reorder_rows_by_order(self, order: List[int]) -> None:
        if not order:
            return
        if sorted(order) != list(range(len(self._rows))):
            return

        try:
            if self._dock.btn_routing_edit_points.isChecked():
                self._toggle_drag_points(False)
        except Exception:
            pass

        lw = self._dock.routing_points_list

        new_rows = [self._rows[i] for i in order]

        blocker = QSignalBlocker(lw.model())
        try:
            lw.setUpdatesEnabled(False)

            for row, _auto in self._rows:
                try:
                    row.setParent(None)
                except Exception:
                    pass

            lw.clear()

            for row, _auto in new_rows:
                it = QListWidgetItem()
                lw.addItem(it)
                lw.setItemWidget(it, row)
                sh = row.sizeHint()
                it.setSizeHint(QSize(0, sh.height()))

        finally:
            lw.setUpdatesEnabled(True)
            del blocker

        self._rows = new_rows
        self._renumber_ui()
        QTimer.singleShot(0, self._sync_routing_row_widths)
        self._dock.set_routing_summary_text("")

    # ---------------- layer helpers ----------------

    @staticmethod
    def _profile_rgb(profile: str) -> str:
        colors = {
            "car": "220,50,50",      # red
            "foot": "50,170,80",     # green
            "truck": "150,80,200",   # purple
        }
        return colors.get((profile or "").lower(), "220,50,50")
    
    def _apply_route_style(self, line_layer: QgsVectorLayer, profile: str) -> None:
        rgb = self._profile_rgb(profile)
        symbol = QgsLineSymbol.createSimple({"color": rgb, "width": "1.6"})
        line_layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        line_layer.triggerRepaint()

    def _apply_points_style(self, point_layer: QgsVectorLayer, profile: str) -> None:
        rgb = self._profile_rgb(profile)
        ms = QgsMarkerSymbol.createSimple({
            "name": "circle",
            "color": "255,255,255,180",
            "outline_color": f"{rgb},220",
            "outline_width": "0.8",
            "size": "4.2"
        })
        point_layer.setRenderer(QgsSingleSymbolRenderer(ms))
        point_layer.triggerRepaint()

    def _add_layer_to_top(self, layer: QgsVectorLayer) -> None:
        prj = QgsProject.instance()
        prj.addMapLayer(layer, False)
        prj.layerTreeRoot().insertLayer(0, layer)
    
    def _ensure_route_layer(self, profile: str) -> QgsVectorLayer:
        prj = QgsProject.instance()
        if self._route_layer_id:
            lyr = prj.mapLayer(self._route_layer_id)
            if isinstance(lyr, QgsVectorLayer):
                lyr.setName(f"Regio Route ({profile})")
                self._apply_route_style(lyr, profile)
                return lyr

        dst = prj.crs()
        crs_id = dst.authid() if dst.authid() else dst.toWkt()

        line_layer = QgsVectorLayer(f"LineString?crs={crs_id}", f"Regio Route ({profile})", "memory")
        prov = line_layer.dataProvider()

        fields = QgsFields()
        fields.append(QgsField("distance_m", FIELD_DOUBLE))
        fields.append(QgsField("duration_s", FIELD_DOUBLE))
        fields.append(QgsField("profile", FIELD_STRING))
        prov.addAttributes(fields)
        line_layer.updateFields()

        self._apply_route_style(line_layer, profile)

        self._add_layer_to_top(line_layer)
        self._route_layer_id = line_layer.id()
        return line_layer

    def _ensure_points_layer(self, profile: str) -> QgsVectorLayer:
        prj = QgsProject.instance()
        if self._points_layer_id:
            lyr = prj.mapLayer(self._points_layer_id)
            if isinstance(lyr, QgsVectorLayer):
                self._apply_points_style(lyr, profile)
                return lyr

        dst = prj.crs()
        crs_id = dst.authid() if dst.authid() else dst.toWkt()

        point_layer = QgsVectorLayer(f"Point?crs={crs_id}", "Regio Route Points", "memory")
        pprov = point_layer.dataProvider()

        pfields = QgsFields()
        pfields.append(QgsField("seq", FIELD_INT))
        pfields.append(QgsField("role", FIELD_STRING))
        pfields.append(QgsField("address", FIELD_STRING))
        pprov.addAttributes(pfields)
        point_layer.updateFields()

        self._apply_points_style(point_layer, profile)

        pal = QgsPalLayerSettings()
        pal.enabled = True
        pal.fieldName = "seq"
        pal.placement = QgsPalLayerSettings.Placement.OverPoint

        tf = QgsTextFormat()
        tf.setSize(10)
        tf.setColor(QColor(30, 30, 30))

        buf = QgsTextBufferSettings()
        buf.setEnabled(True)
        buf.setSize(0.8)
        buf.setColor(QColor(255, 255, 255))
        tf.setBuffer(buf)

        pal.setFormat(tf)

        point_layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
        point_layer.setLabelsEnabled(True)

        self._add_layer_to_top(point_layer)
        self._points_layer_id = point_layer.id()
        return point_layer

    # ---------------- update layers in-place ----------------

    def _update_route_layers(
        self,
        route_coords_ll: List[Tuple[float, float]],
        waypoints_ll: List[Tuple[float, float]],
        dist_m: float,
        dur_s: float,
        profile: str
    ) -> None:
        prj = QgsProject.instance()
        wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        dst = prj.crs()
        xform = QgsCoordinateTransform(wgs84, dst, prj)
        had_route_before = self._route_already_drawn()

        pts_xy: List[QgsPointXY] = []
        for lng, lat in route_coords_ll:
            try:
                p = xform.transform(QgsPointXY(lng, lat))
                pts_xy.append(QgsPointXY(p))
            except Exception:
                continue
        if len(pts_xy) < 2:
            self._iface.messageBar().pushWarning("Regio API Plugin", "CRS transform failed for route geometry.")
            return

        line_layer = self._ensure_route_layer(profile)
        point_layer = self._ensure_points_layer(profile)

        self._apply_route_style(line_layer, profile)
        self._apply_points_style(point_layer, profile)

        line_layer.setName(f"Regio Route ({profile})")
        lprov = line_layer.dataProvider()

        feats = list(line_layer.getFeatures())
        if feats:
            fid = feats[0].id()
            geom = QgsGeometry.fromPolylineXY(pts_xy)
            lprov.changeGeometryValues({fid: geom})
            lprov.changeAttributeValues({fid: {0: dist_m, 1: dur_s, 2: profile}})
            if len(feats) > 1:
                try:
                    lprov.deleteFeatures([f.id() for f in feats[1:]])
                except Exception:
                    pass
        else:
            f = QgsFeature(line_layer.fields())
            f.setAttributes([dist_m, dur_s, profile])
            f.setGeometry(QgsGeometry.fromPolylineXY(pts_xy))
            lprov.addFeatures([f])

        line_layer.updateExtents()
        line_layer.triggerRepaint()

        pprov = point_layer.dataProvider()
        existing = [f.id() for f in point_layer.getFeatures()]
        if existing:
            try:
                pprov.deleteFeatures(existing)
            except Exception:
                pass

        n = len(waypoints_ll)
        pfeats: List[QgsFeature] = []

        for i, (lng, lat) in enumerate(waypoints_ll, start=1):
            try:
                p = xform.transform(QgsPointXY(lng, lat))
            except Exception:
                continue

            role = "stop"
            if i == 1:
                role = "from"
            elif i == n:
                role = "to"

            pf = QgsFeature(point_layer.fields())

            addr = ""
            if 0 <= (i - 1) < len(self._rows):
                w = self._rows[i - 1][0].input
                sel = w.selected_result() or {}
                addr = (sel.get("address") or w.text() or "").strip()

            pf.setAttributes([i, role, addr])
            pf.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(p)))
            pfeats.append(pf)

        if pfeats:
            pprov.addFeatures(pfeats)

        point_layer.updateExtents()
        point_layer.triggerRepaint()

        try:
            canvas = self._iface.mapCanvas()
            if not had_route_before:
                canvas.setExtent(line_layer.extent())
            canvas.refresh()
        except Exception:
            pass

    # ---------------- summary formatting ----------------

    @staticmethod
    def _format_summary(dist_m: float, dur_s: float, profile: str) -> str:
        km = dist_m / 1000.0
        mins = dur_s / 60.0
        if mins < 60:
            dur = f"{mins:.0f} min"
        else:
            h = int(mins // 60)
            m = int(round(mins - h * 60))
            dur = f"{h} h {m} min"
        return f"Profile: {profile}\nDistance: {km:.2f} km\nDuration: {dur}"

    # ---------------- draggable route points ----------------

    def _toggle_drag_points(self, enabled: bool):
        enabled = bool(enabled)
        canvas = self._iface.mapCanvas()

        if not enabled:
            if self._drag_tool:
                try:
                    self._drag_tool.moved.disconnect(self._on_waypoint_moved)
                except Exception:
                    pass
            self._drag_tool = None

            if self._prev_tool:
                try:
                    canvas.setMapTool(self._prev_tool)
                except Exception:
                    pass
            self._prev_tool = None

            self._dock.btn_routing_edit_points.blockSignals(True)
            self._dock.btn_routing_edit_points.setChecked(False)
            self._dock.btn_routing_edit_points.blockSignals(False)
            self._dock.btn_routing_edit_points.setText(tr("Edit route points (drag)"))
            return

        prj = QgsProject.instance()
        pl = prj.mapLayer(self._points_layer_id) if self._points_layer_id else None
        if not isinstance(pl, QgsVectorLayer):
            self._iface.messageBar().pushWarning("Regio API Plugin", "No route points layer to edit.")
            self._dock.btn_routing_edit_points.blockSignals(True)
            self._dock.btn_routing_edit_points.setChecked(False)
            self._dock.btn_routing_edit_points.blockSignals(False)
            return

        self._prev_tool = canvas.mapTool()
        self._drag_tool = RoutePointDragTool(canvas, pl, tolerance_px=12)
        self._drag_tool.moved.connect(self._on_waypoint_moved)
        canvas.setMapTool(self._drag_tool)

        self._dock.btn_routing_edit_points.setText(tr("Stop editing route points"))

    def _on_waypoint_moved(self, fid: int, pt_proj: QgsPointXY):
        prj = QgsProject.instance()
        wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        xform = QgsCoordinateTransform(prj.crs(), wgs84, prj)

        try:
            pt_wgs = xform.transform(pt_proj)
        except Exception as e:
            self._iface.messageBar().pushWarning("Regio API Plugin", f"CRS transform failed: {e}")
            return

        lng, lat = float(pt_wgs.x()), float(pt_wgs.y())

        pl = prj.mapLayer(self._points_layer_id) if self._points_layer_id else None
        if not isinstance(pl, QgsVectorLayer):
            return

        feat = None
        for f in pl.getFeatures():
            if f.id() == fid:
                feat = f
                break
        if not feat:
            return

        seq = int(feat["seq"] or 0)
        if seq <= 0 or seq > len(self._rows):
            return

        widget = self._rows[seq - 1][0].input

        apikey = self._settings.api_key().strip()
        if not apikey:
            return

        self._req_id += 1
        rid = self._req_id

        country = self._settings.countries_param()

        self._abort_active_reply()

        def _done(req_id: int, ok: bool, payload: Optional[dict], err: Optional[str]) -> None:
            self._active_reply = None
            if req_id != rid:
                return

            addr = ""
            if ok:
                data = (payload or {}).get("data") or []
                if isinstance(data, list) and data:
                    best = data[0] or {}
                    addr = best.get("address", "") or ""
                    
            widget.set_selected_result({
                "address": addr if addr else widget.text(),
                "geometry": [lng, lat],
                "postcode": "",
                "type": ""
            }, set_text=True)

            self._schedule_auto_calc()

        self._active_reply = self._api.revgeocode(
            lng=lng, lat=lat,
            country=country,
            apikey=apikey,
            request_id=rid,
            on_done=_done,
            timeout_ms=12000
        )
