# -*- coding: utf-8 -*-
from qgis.gui import QgsMapTool
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import QgsPointXY


class RoutePointPickTool(QgsMapTool):
    clicked = pyqtSignal(QgsPointXY)

    def canvasReleaseEvent(self, e):
        p = QgsPointXY(self.toMapCoordinates(e.pos()))
        self.clicked.emit(p)