# -*- coding: utf-8 -*-
import os
from typing import Optional

from qgis.PyQt.QtCore import QCoreApplication, Qt, pyqtSignal
from qgis.PyQt.QtGui import QIcon, QPixmap
from qgis.PyQt.QtWidgets import (
    QWidget, QDockWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QToolButton, QSizePolicy, QPushButton, QComboBox, QFrame, QCheckBox,
    QGridLayout, QListWidget, QAbstractItemView
)

from qgis.core import QgsApplication

from .widgets import GeocodeAutocompleteWidget


def tr(text: str) -> str:
    return QCoreApplication.translate("RegioApiPlugin", text)


class CollapsibleSection(QWidget):
    def __init__(self, title: str, content: QWidget, expanded: bool = True, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._content = content

        self.header_btn = QToolButton(self)
        self.header_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.header_btn.setCheckable(True)
        self.header_btn.setChecked(bool(expanded))
        self.header_btn.setText(title)
        self.header_btn.setAutoRaise(True)
        self.header_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._set_arrow(self.header_btn.isChecked())
        self.header_btn.toggled.connect(self._on_toggled)

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)
        outer.addWidget(self.header_btn)
        outer.addWidget(self._content)
        self.setLayout(outer)

        self._content.setVisible(bool(expanded))

    def _set_arrow(self, expanded: bool) -> None:
        self.header_btn.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)

    def _on_toggled(self, checked: bool) -> None:
        self._set_arrow(bool(checked))
        self._content.setVisible(bool(checked))

    def setTitle(self, title: str) -> None:
        self.header_btn.setText(title)


class RegioDockWidget(QDockWidget):
    settingsRequested = pyqtSignal()
    documentationRequested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("RegioApiPluginDockWidget")
        self.setWindowTitle(tr("Regio API Plugin"))

        root = QWidget(self)
        self.setWidget(root)

        # --- Top bar ---
        top_bar = QFrame(root)
        top_bar.setObjectName("regioHeader")
        top_l = QHBoxLayout(top_bar)
        top_l.setContentsMargins(10, 10, 10, 10)
        top_l.setSpacing(10)

        icon_lbl = QLabel(top_bar)
        pm = QPixmap(self._icon_path())
        if not pm.isNull():
            icon_lbl.setPixmap(pm.scaled(24, 24))
        else:
            icon_lbl.setText("")

        self.title_label = QLabel(tr("Regio API Plugin"), top_bar)
        self.title_label.setObjectName("regioTitle")

        self.btn_documentation = QToolButton(top_bar)
        self.btn_documentation.setAutoRaise(True)
        self.btn_documentation.setToolTip(tr("Documentation"))
        self.btn_documentation.setIcon(QIcon(QgsApplication.iconPath("mActionHelpContents.svg")))
        self.btn_documentation.clicked.connect(self.documentationRequested.emit)

        self.btn_settings = QToolButton(top_bar)
        self.btn_settings.setObjectName("regioSettingsBtn")
        self.btn_settings.setAutoRaise(True)
        self.btn_settings.setToolTip(tr("Settings"))
        self.btn_settings.setIcon(QIcon(QgsApplication.iconPath("mActionOptions.svg")))
        self.btn_settings.clicked.connect(self.settingsRequested.emit)

        top_l.addWidget(icon_lbl)
        top_l.addWidget(self.title_label)
        top_l.addStretch(1)
        top_l.addWidget(self.btn_documentation)
        top_l.addWidget(self.btn_settings)

        self.setStyleSheet(self.styleSheet() + """
            #regioHeader {
                border: 1px solid rgba(127,127,127,60);
                border-radius: 10px;
                background: rgba(127,127,127,10);
            }
            #regioTitle {
                font-size: 15px;
                font-weight: 700;
            }
            #regioScrollViewport { background: transparent; }
            #regioScroll { background: transparent; }
            QPushButton { text-align: center; padding: 6px 8px; }
        """)

        # --- Scroll container ---
        self.scroll = QScrollArea(root)
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("regioScroll")
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.viewport().setObjectName("regioScrollViewport")

        self.page = QWidget()
        self.scroll.setWidget(self.page)

        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.page.setMinimumWidth(0)

        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(10)

        # ===== Search content =====
        self.search_content = QWidget()
        search_l = QVBoxLayout(self.search_content)
        search_l.setContentsMargins(12, 0, 12, 0)
        search_l.setSpacing(6)

        self.search_input = GeocodeAutocompleteWidget(placeholder=tr("Search address"))
        self.btn_search_clear = QPushButton(tr("Clear"))
        self.search_details = QLabel("")
        self.search_details.setWordWrap(True)

        self.lbl_search_details_title = QLabel(tr("Details"))
        self.lbl_search_details_title.setVisible(False)

        search_l.addWidget(self.search_input)
        search_l.addWidget(self.btn_search_clear)
        search_l.addWidget(self.lbl_search_details_title)
        search_l.addWidget(self.search_details)

        # ===== Reverse content =====
        self.reverse_content = QWidget()
        rev_l = QVBoxLayout(self.reverse_content)
        rev_l.setContentsMargins(12, 0, 12, 0)
        rev_l.setSpacing(6)

        self.reverse_toggle = QPushButton("")
        self.reverse_toggle.setCheckable(True)
        self.reverse_toggle.setObjectName("reverseToggle")
        self.reverse_toggle.setProperty("active", False)

        self.reverse_toggle.setStyleSheet("""
            QPushButton#reverseToggle {
                padding: 6px;
                font-weight: 600;
            }
            QPushButton#reverseToggle[active="true"] {
                background-color: rgba(220, 50, 50, 50);
                border: 1px solid rgba(220, 50, 50, 160);
            }
        """)

        self.reverse_status = QLabel("")
        self.reverse_status.setWordWrap(True)

        self.reverse_hint = QLabel("")
        self.reverse_hint.setWordWrap(True)

        self.reverse_result = QLabel("")
        self.reverse_result.setWordWrap(True)

        self.lbl_reverse_result_title = QLabel(tr("Result"))
        self.lbl_reverse_result_title.setVisible(False)

        btn_row = QHBoxLayout()
        self.btn_reverse_copy_address = QPushButton(tr("Copy address"))
        self.btn_reverse_copy_coords = QPushButton(tr("Copy coordinates"))
        btn_row.addWidget(self.btn_reverse_copy_address)
        btn_row.addWidget(self.btn_reverse_copy_coords)
        btn_row.addStretch(1)

        rev_l.addWidget(self.reverse_toggle)
        rev_l.addWidget(self.reverse_status)
        rev_l.addWidget(self.reverse_hint)
        rev_l.addWidget(self.lbl_reverse_result_title)
        rev_l.addWidget(self.reverse_result)
        rev_l.addLayout(btn_row)

        self.reverse_toggle.toggled.connect(self.update_reverse_toggle_ui)
        self.update_reverse_toggle_ui(self.reverse_toggle.isChecked())

        # ===== Routing content =====
        self.routing_content = QWidget()
        rt_l = QVBoxLayout(self.routing_content)
        rt_l.setContentsMargins(12, 0, 12, 0)
        rt_l.setSpacing(6)

        self.lbl_routing_points = QLabel(tr("Waypoints"))

        self.routing_points_list = QListWidget()
        self.routing_points_list.setFrameShape(QFrame.Shape.NoFrame)
        self.routing_points_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.routing_points_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.routing_points_list.setDragEnabled(True)
        self.routing_points_list.setAcceptDrops(True)
        self.routing_points_list.setDropIndicatorShown(True)
        self.routing_points_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.routing_points_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Buttons
        self.btn_routing_add_stop = QPushButton(tr("Add stop"))
        self.btn_routing_import_geojson = QPushButton(tr("Import GeoJSON"))
        self.btn_routing_calc = QPushButton(tr("Calculate route"))
        self.btn_routing_clear = QPushButton(tr("Clear route"))
        self.btn_routing_reverse = QPushButton(tr("Reverse route"))
        self.btn_routing_edit_points = QPushButton(tr("Edit route points (drag)"))
        self.btn_routing_edit_points.setCheckable(True)
        self.btn_routing_edit_points.setVisible(False)

        self.lbl_routing_profile = QLabel(tr("Profile"))
        self.lbl_routing_summary = QLabel(tr("Route summary"))
        self.lbl_routing_summary.setVisible(False)

        # Profile row
        prof_row = QHBoxLayout()
        prof_row.setContentsMargins(0, 0, 0, 0)
        prof_row.setSpacing(6)
        prof_row.addWidget(self.lbl_routing_profile)
        self.routing_profile = QComboBox()
        self.routing_profile.addItem(tr("Car"), "car")
        self.routing_profile.addItem(tr("Truck"), "truck")
        self.routing_profile.addItem(tr("Foot"), "foot")
        prof_row.addWidget(self.routing_profile, 1)

        # Button grid
        btn_grid_routing = QGridLayout()
        btn_grid_routing.setContentsMargins(0, 0, 0, 0)
        btn_grid_routing.setHorizontalSpacing(6)
        btn_grid_routing.setVerticalSpacing(6)
        btn_grid_routing.addWidget(self.btn_routing_calc, 0, 0)
        btn_grid_routing.addWidget(self.btn_routing_clear, 0, 1)
        btn_grid_routing.addWidget(self.btn_routing_reverse, 1, 0)
        btn_grid_routing.addWidget(self.btn_routing_edit_points, 1, 1)

        self.routing_summary = QLabel("")
        self.routing_summary.setWordWrap(True)

        # ===== Optimization panel inside Routing =====
        self.routing_opt_content = QWidget()
        opt_l = QVBoxLayout(self.routing_opt_content)
        opt_l.setContentsMargins(12, 0, 12, 0)
        opt_l.setSpacing(6)

        self.chk_opt_start_first = QCheckBox(tr("Start at first point"))
        self.chk_opt_end_last = QCheckBox(tr("End at last point"))
        self.chk_opt_roundtrip = QCheckBox(tr("Roundtrip"))

        self.chk_opt_start_first.setChecked(True)
        self.chk_opt_end_last.setChecked(True)
        self.chk_opt_roundtrip.setChecked(True)

        chk_grid = QGridLayout()
        chk_grid.setContentsMargins(0, 0, 0, 0)
        chk_grid.setHorizontalSpacing(12)
        chk_grid.setVerticalSpacing(4)

        chk_grid.addWidget(self.chk_opt_start_first, 0, 0)
        chk_grid.addWidget(self.chk_opt_end_last, 0, 1)
        chk_grid.addWidget(self.chk_opt_roundtrip, 1, 0, 1, 2)

        self.btn_routing_optimize = QPushButton(tr("Optimize"))

        opt_l.addLayout(chk_grid)
        opt_l.addWidget(self.btn_routing_optimize)

        self.section_routing_opt = CollapsibleSection(tr("Route optimization"), self.routing_opt_content, expanded=False)

        # Build routing layout
        rt_l.addLayout(prof_row)
        rt_l.addWidget(self.lbl_routing_points)
        rt_l.addWidget(self.routing_points_list)
        rt_l.addWidget(self.btn_routing_add_stop)
        rt_l.addWidget(self.btn_routing_import_geojson)
        rt_l.addLayout(btn_grid_routing)
        rt_l.addWidget(self.lbl_routing_summary)
        rt_l.addWidget(self.routing_summary)
        rt_l.addWidget(self.section_routing_opt)

        # ===== Basemaps content =====
        self.basemap_content = QWidget()
        bm_l = QVBoxLayout(self.basemap_content)
        bm_l.setContentsMargins(12, 0, 12, 0)
        bm_l.setSpacing(6)

        self.lbl_basemap_title = QLabel(tr("Basemap"))

        self.basemap_combo = QComboBox()
        self.basemap_combo.addItem(tr("Regio Baltic WMS"), "regio_baltic_wms")

        self.btn_basemap_add = QPushButton(tr("Add basemap"))
        self.basemap_status = QLabel("")
        self.basemap_status.setWordWrap(True)

        bm_l.addWidget(self.lbl_basemap_title)
        bm_l.addWidget(self.basemap_combo)
        bm_l.addWidget(self.btn_basemap_add)
        bm_l.addWidget(self.basemap_status)

        # Sections
        self.section_search = CollapsibleSection(tr("Search"), self.search_content, expanded=True)
        self.section_reverse = CollapsibleSection(tr("Reverse geocode"), self.reverse_content, expanded=False)
        self.section_routing = CollapsibleSection(tr("Routing"), self.routing_content, expanded=False)
        self.section_basemaps = CollapsibleSection(tr("Basemaps"), self.basemap_content, expanded=False)

        page_layout.addWidget(self.section_search)
        page_layout.addWidget(self.section_reverse)
        page_layout.addWidget(self.section_routing)
        page_layout.addWidget(self.section_basemaps)
        page_layout.addStretch(1)

        for b in [
            self.btn_search_clear,
            self.btn_routing_add_stop, self.btn_routing_import_geojson, self.btn_routing_calc, self.btn_routing_clear,
            self.btn_routing_reverse, self.btn_routing_edit_points,
            self.btn_routing_optimize,
        ]:
            b.setMinimumWidth(0)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.setToolTip(b.text())

        self.page.setLayout(page_layout)

        # Root layout
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addWidget(top_bar)
        layout.addWidget(self.scroll)
        root.setLayout(layout)

    def update_reverse_toggle_ui(self, active: bool) -> None:
        active = bool(active)

        self.reverse_toggle.setProperty("active", active)

        self.reverse_toggle.setText(
            tr("Stop reverse geocode") if active
            else tr("Start reverse geocode")
        )

        self.reverse_status.setText(tr("Status: ON") if active else tr("Status: OFF"))
        self.reverse_hint.setText(tr("Click on the map to get the nearest address.") if active else "")

        # Re-polish for dynamic property styling
        self.reverse_toggle.style().unpolish(self.reverse_toggle)
        self.reverse_toggle.style().polish(self.reverse_toggle)
        self.reverse_toggle.update()

    def set_search_details_text(self, txt: str) -> None:
        txt = (txt or "").strip()
        self.search_details.setText(txt)
        self.lbl_search_details_title.setVisible(bool(txt))

    def set_reverse_result_text(self, txt: str) -> None:
        txt = (txt or "").strip()
        self.reverse_result.setText(txt)
        self.lbl_reverse_result_title.setVisible(bool(txt))

    def set_routing_summary_text(self, txt: str) -> None:
        txt = (txt or "").strip()
        self.routing_summary.setText(txt)
        self.lbl_routing_summary.setVisible(bool(txt))

    def _icon_path(self) -> str:
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.png")

    @staticmethod
    def _set_placeholder(widget: object, text: str) -> None:
        try:
            if hasattr(widget, "set_placeholder"):
                widget.set_placeholder(text)
                return
        except Exception:
            pass
        try:
            edit = getattr(widget, "edit", None)
            if edit is not None and hasattr(edit, "setPlaceholderText"):
                edit.setPlaceholderText(text)
        except Exception:
            pass

    def retranslate(self) -> None:
        # Window and header
        self.setWindowTitle(tr("Regio API Plugin"))
        self.title_label.setText(tr("Regio API Plugin"))
        self.btn_documentation.setToolTip(tr("Documentation"))
        self.btn_settings.setToolTip(tr("Settings"))

        # Sections
        self.section_search.setTitle(tr("Search"))
        self.section_reverse.setTitle(tr("Reverse geocode"))
        self.section_routing.setTitle(tr("Routing"))
        self.section_basemaps.setTitle(tr("Basemaps"))

        # Search
        self.btn_search_clear.setText(tr("Clear"))
        self.lbl_search_details_title.setText(tr("Details"))
        self.lbl_search_details_title.setVisible(bool(self.search_details.text().strip()))
        self._set_placeholder(self.search_input, tr("Search address"))

        # Reverse
        self.btn_reverse_copy_address.setText(tr("Copy address"))
        self.btn_reverse_copy_coords.setText(tr("Copy coordinates"))
        self.lbl_reverse_result_title.setText(tr("Result"))
        self.lbl_reverse_result_title.setVisible(bool(self.reverse_result.text().strip()))
        self.update_reverse_toggle_ui(self.reverse_toggle.isChecked())

        # Routing labels/buttons
        self.lbl_routing_points.setText(tr("Waypoints"))
        self.lbl_routing_profile.setText(tr("Profile"))
        self.lbl_routing_summary.setText(tr("Route summary"))
        self.lbl_routing_summary.setVisible(bool(self.routing_summary.text().strip()))

        self.btn_routing_add_stop.setText(tr("Add stop"))
        self.btn_routing_import_geojson.setText(tr("Import GeoJSON"))
        self.btn_routing_calc.setText(tr("Calculate route"))
        self.btn_routing_clear.setText(tr("Clear route"))
        self.btn_routing_reverse.setText(tr("Reverse route"))
        self.btn_routing_edit_points.setText(tr("Edit route points (drag)"))

        # Routing profile combo item texts
        i = self.routing_profile.findData("car")
        if i >= 0:
            self.routing_profile.setItemText(i, tr("Car"))
        i = self.routing_profile.findData("truck")
        if i >= 0:
            self.routing_profile.setItemText(i, tr("Truck"))
        i = self.routing_profile.findData("foot")
        if i >= 0:
            self.routing_profile.setItemText(i, tr("Foot"))

        # Optimization panel inside routing
        self.section_routing_opt.setTitle(tr("Route optimization"))
        self.chk_opt_start_first.setText(tr("Start at first point"))
        self.chk_opt_end_last.setText(tr("End at last point"))
        self.chk_opt_roundtrip.setText(tr("Roundtrip"))
        self.btn_routing_optimize.setText(tr("Optimize"))

        # Basemap
        self.lbl_basemap_title.setText(tr("Basemap"))
        self.btn_basemap_add.setText(tr("Add basemap"))
        i = self.basemap_combo.findData("regio_baltic_wms")
        if i >= 0:
            self.basemap_combo.setItemText(i, tr("Regio Baltic WMS"))
