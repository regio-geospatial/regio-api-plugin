# -*- coding: utf-8 -*-
from typing import Optional

from qgis.PyQt import sip

from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import QgsFeatureRequest, QgsGeometry, QgsPointXY, QgsRectangle, QgsVectorLayer
from qgis.gui import QgsMapTool


class RoutePointDragTool(QgsMapTool):
    moved = pyqtSignal(int, QgsPointXY)

    def __init__(self, canvas, point_layer: Optional[QgsVectorLayer], tolerance_px: int = 10):
        super().__init__(canvas)
        self._canvas = canvas
        self._layer: Optional[QgsVectorLayer] = point_layer
        self._tol_px = int(tolerance_px)

        self._dragging_fid: Optional[int] = None

    def set_layer(self, point_layer: Optional[QgsVectorLayer]) -> None:
        self._layer = point_layer
        self._dragging_fid = None

    def _layer_active(self) -> bool:
        if self._layer is None:
            return False
        try:
            return not sip.isdeleted(self._layer)
        except Exception:
            return False

    def _find_nearest_feature(self, p: QgsPointXY) -> Optional[int]:
        if not self._layer_active():
            return None

        mupp = self._canvas.mapUnitsPerPixel()
        tol_mu = self._tol_px * mupp

        rect = QgsRectangle(p.x() - tol_mu, p.y() - tol_mu, p.x() + tol_mu, p.y() + tol_mu)
        req = QgsFeatureRequest().setFilterRect(rect)

        best = None
        best_d2 = None

        for f in self._layer.getFeatures(req):
            g = f.geometry()
            if not g:
                continue
            q = g.asPoint()
            dx = q.x() - p.x()
            dy = q.y() - p.y()
            d2 = dx * dx + dy * dy
            if best_d2 is None or d2 < best_d2:
                best_d2 = d2
                best = f.id()

        return best

    def canvasPressEvent(self, e):
        if not self._layer_active():
            return
        p = self.toMapCoordinates(e.pos())
        self._dragging_fid = self._find_nearest_feature(QgsPointXY(p))

    def canvasMoveEvent(self, e):
        if self._dragging_fid is None:
            return
        if not self._layer_active():
            self._dragging_fid = None
            return

        p = QgsPointXY(self.toMapCoordinates(e.pos()))
        geom = QgsGeometry.fromPointXY(p)

        try:
            prov = self._layer.dataProvider()
            prov.changeGeometryValues({int(self._dragging_fid): geom})
            self._layer.triggerRepaint()
        except Exception:
            pass

    def canvasReleaseEvent(self, e):
        if self._dragging_fid is None:
            return
        if not self._layer_active():
            self._dragging_fid = None
            return

        fid = int(self._dragging_fid)
        self._dragging_fid = None

        p = QgsPointXY(self.toMapCoordinates(e.pos()))
        self.moved.emit(fid, p)

        try:
            if self._layer.isEditable():
                self._layer.commitChanges()
                self._layer.startEditing()
        except Exception:
            pass
