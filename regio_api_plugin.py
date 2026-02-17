# -*- coding: utf-8 -*-
from typing import Optional

from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon, QAction

from .settings import PluginSettings
from .ui.documentation_dialog import DocumentationDialog
from .translations import DictTranslator
from .api_client import ApiClient
from .logger import PluginLogger

from .ui.dockwidget import RegioDockWidget
from .ui.settings_dialog import SettingsDialog

from .controllers.autocomplete_controller import GeocodeAutocompleteController
from .controllers.forward_search_controller import ForwardSearchController
from .controllers.reverse_geocode_controller import ReverseGeocodeController
from .controllers.routing_controller import RoutingController
from .controllers.basemap_controller import BasemapController


class RegioApiPlugin:
    MENU_NAME = "&Regio API Plugin"

    def __init__(self, iface):
        self.iface = iface

        self._settings = PluginSettings()
        self._documentation_dlg = None
        self._log = PluginLogger("RegioApiPlugin", debug_enabled=self._settings.debug_logging())
        self._api = ApiClient(self._log)

        self._translator: Optional[DictTranslator] = None

        self._dock: Optional[RegioDockWidget] = None
        self._action_toggle: Optional[QAction] = None
        self._action_settings: Optional[QAction] = None

        # Controllers
        self._auto_search: Optional[GeocodeAutocompleteController] = None
        self._forward_search: Optional[ForwardSearchController] = None
        self._reverse_ctrl: Optional[ReverseGeocodeController] = None
        self._routing_ctrl: Optional[RoutingController] = None
        self._basemap_ctrl: Optional[BasemapController] = None

    def initGui(self):
        self._install_translator()

        icon = QIcon(self._icon_path())
        text = QCoreApplication.translate("RegioApiPlugin", "Regio API Plugin")

        self._action_toggle = QAction(icon, text, self.iface.mainWindow())
        self._action_toggle.setCheckable(True)
        self._action_toggle.setChecked(False)
        self._action_toggle.triggered.connect(self._toggle_dock)

        self._action_settings = QAction(
            QCoreApplication.translate("RegioApiPlugin", "Settings"),
            self.iface.mainWindow()
        )
        self._action_settings.triggered.connect(self._open_settings)

        self.iface.addToolBarIcon(self._action_toggle)
        self.iface.addPluginToMenu(self.MENU_NAME, self._action_toggle)
        self.iface.addPluginToMenu(self.MENU_NAME, self._action_settings)

        self._ensure_dock()
        self._dock.setVisible(False)

    def unload(self):
        if self._reverse_ctrl:
            try:
                self._reverse_ctrl.deactivate()
            except Exception:
                pass

        # Dock
        if self._dock:
            try:
                self._dock.visibilityChanged.disconnect(self._sync_action_state)
            except Exception:
                pass
            try:
                self._dock.settingsRequested.disconnect(self._open_settings)
            except Exception:
                pass
            try:
                self._dock.documentationRequested.disconnect(self._show_documentation)
            except Exception:
                pass
            
            self.iface.removeDockWidget(self._dock)
            self._dock.deleteLater()
            self._dock = None

        # Actions
        if self._action_toggle:
            try:
                self._action_toggle.triggered.disconnect(self._toggle_dock)
            except Exception:
                pass
            self.iface.removeToolBarIcon(self._action_toggle)
            self.iface.removePluginMenu(self.MENU_NAME, self._action_toggle)
            self._action_toggle.deleteLater()
            self._action_toggle = None

        if self._documentation_dlg:
            try:
                self._documentation_dlg.close()
            except Exception:
                pass
            self._documentation_dlg = None

        if self._action_settings:
            try:
                self._action_settings.triggered.disconnect(self._open_settings)
            except Exception:
                pass
            self.iface.removePluginMenu(self.MENU_NAME, self._action_settings)
            self._action_settings.deleteLater()
            self._action_settings = None

        if self._routing_ctrl:
            try:
                self._routing_ctrl.clear_route()
                self._routing_ctrl.deactivate()
            except Exception:
                pass

        self._remove_translator()

        # Controllers
        self._auto_search = None
        self._forward_search = None
        self._reverse_ctrl = None
        self._routing_ctrl = None
        self._basemap_ctrl = None

    def _ensure_dock(self):
        if self._dock:
            return

        self._dock = RegioDockWidget(self.iface.mainWindow())
        self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._dock)
        self._dock.visibilityChanged.connect(self._sync_action_state)
        self._dock.documentationRequested.connect(self._show_documentation)
        self._dock.settingsRequested.connect(self._open_settings)

        # Wire Search autocomplete and selection behavior
        self._auto_search = GeocodeAutocompleteController(
            self._dock.search_input,
            self._api,
            self._settings,
            self._log,
            debounce_ms=300
        )
        self._forward_search = ForwardSearchController(self.iface, self._dock)

        # Wire other controllers
        self._reverse_ctrl = ReverseGeocodeController(self.iface, self._dock, self._api, self._settings)
        self._routing_ctrl = RoutingController(self.iface, self._dock, self._api, self._settings, self._log)
        self._basemap_ctrl = BasemapController(self.iface, self._dock, self._settings, self._log)

    def _toggle_dock(self, checked: bool):
        self._ensure_dock()
        self._dock.setVisible(bool(checked))

        if not checked and self._reverse_ctrl:
            self._reverse_ctrl.deactivate()

        if self._routing_ctrl:
            self._routing_ctrl.deactivate()

    def _sync_action_state(self, visible: bool):
        if not self._action_toggle:
            return
        self._action_toggle.blockSignals(True)
        self._action_toggle.setChecked(bool(visible))
        self._action_toggle.blockSignals(False)

        if not visible and self._reverse_ctrl:
            self._reverse_ctrl.deactivate()

        if self._routing_ctrl:
            self._routing_ctrl.deactivate()

    def _show_documentation(self):
        import os
        plugin_root = os.path.dirname(__file__)

        if self._documentation_dlg is None:
            self._documentation_dlg = DocumentationDialog(plugin_root, self.iface.mainWindow())
        self._documentation_dlg.show()
        self._documentation_dlg.raise_()
        self._documentation_dlg.activateWindow()

    def _open_settings(self):
        def _applied():
            self._log.set_debug(self._settings.debug_logging())
            self._install_translator()
            if self._dock:
                self._dock.retranslate()

        dlg = SettingsDialog(
            self._settings,
            self._api,
            on_applied=_applied,
            parent=self.iface.mainWindow()
        )
        dlg.exec()

    def _install_translator(self):
        self._remove_translator()
        lang = (self._settings.language() or "en").strip().lower()
        if lang != "en":
            self._translator = DictTranslator(lang)
            QCoreApplication.installTranslator(self._translator)

    def _remove_translator(self):
        if self._translator:
            QCoreApplication.removeTranslator(self._translator)
            self._translator = None

    def _icon_path(self) -> str:
        import os
        return os.path.join(os.path.dirname(__file__), "icon.png")
