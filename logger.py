# -*- coding: utf-8 -*-
from qgis.core import QgsMessageLog, Qgis


class PluginLogger:
    def __init__(self, category: str, debug_enabled: bool = False):
        self._category = category
        self._debug = debug_enabled

    def set_debug(self, enabled: bool) -> None:
        self._debug = bool(enabled)

    def debug(self, msg: str) -> None:
        if self._debug:
            QgsMessageLog.logMessage(msg, self._category, Qgis.Info)

    def info(self, msg: str) -> None:
        QgsMessageLog.logMessage(msg, self._category, Qgis.Info)

    def warning(self, msg: str) -> None:
        QgsMessageLog.logMessage(msg, self._category, Qgis.Warning)

    def error(self, msg: str) -> None:
        QgsMessageLog.logMessage(msg, self._category, Qgis.Critical)
