# -*- coding: utf-8 -*-
from typing import Optional

from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import QgsPointXY
from qgis.gui import QgsMapTool


class ReverseClickMapTool(QgsMapTool):
    clicked = pyqtSignal(QgsPointXY)

    def __init__(self, canvas):
        super().__init__(canvas)
        self._canvas = canvas

    def canvasReleaseEvent(self, e):
        pt = self.toMapCoordinates(e.pos())
        self.clicked.emit(QgsPointXY(pt))