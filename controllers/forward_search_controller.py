# -*- coding: utf-8 -*-
from typing import Optional, Dict, Any

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsPointXY
)
from qgis.gui import QgsVertexMarker

def tr(text: str) -> str:
    return QCoreApplication.translate("RegioApiPlugin", text)


class ForwardSearchController:
    def __init__(self, iface, dock):
        self._iface = iface
        self._dock = dock
        self._marker: Optional[QgsVertexMarker] = None

        self._dock.search_input.resultSelected.connect(self._on_selected)
        self._dock.btn_search_clear.clicked.connect(self.clear)
        self._dock.search_input.cleared.connect(self._clear_details_and_marker)

    def clear(self):
        self._dock.search_input.clear()
        self._clear_details_and_marker()

    def _clear_details_and_marker(self):
        self._dock.set_search_details_text("")
        self._remove_marker()

    def _remove_marker(self):
        """
        Remove it from the map canvas scene.
        """
        if not self._marker:
            return

        try:
            canvas = self._iface.mapCanvas()
            canvas.scene().removeItem(self._marker)
        except Exception:
            try:
                self._marker.setVisible(False)
            except Exception:
                pass
        finally:
            self._marker = None

    def _on_selected(self, result: Dict[str, Any]) -> None:
        geom = (result or {}).get("geometry")
        if not (isinstance(geom, (list, tuple)) and len(geom) >= 2):
            return

        lng, lat = float(geom[0]), float(geom[1])

        prj = QgsProject.instance()
        wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        xform = QgsCoordinateTransform(wgs84, prj.crs(), prj)

        try:
            pt_proj = xform.transform(QgsPointXY(lng, lat))
        except Exception as e:
            self._iface.messageBar().pushWarning("Regio API Plugin", f"CRS transform failed: {e}")
            return

        canvas = self._iface.mapCanvas()
        canvas.setCenter(pt_proj)

        try:
            target_scale = 5000.0
            if canvas.scale() > target_scale:
                canvas.zoomScale(target_scale)
        except Exception:
            pass

        canvas.refresh()

        # marker
        self._remove_marker()
        self._marker = QgsVertexMarker(canvas)
        self._marker.setCenter(pt_proj)
        self._marker.setIconType(QgsVertexMarker.IconType.ICON_CROSS)
        self._marker.setIconSize(14)
        self._marker.setPenWidth(3)
        self._marker.setColor(QColor(255, 0, 0))

        # details
        addr = result.get("address", "")
        postcode = result.get("postcode", "")
        self._dock.set_search_details_text(
            f"{tr('Address')}: {addr}\n"
            f"{tr('Postcode')}: {postcode}\n"
            f"Lon/Lat (WGS84): {lng:.8f}, {lat:.8f}"
        )
