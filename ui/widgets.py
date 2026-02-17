# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional

from qgis.PyQt.QtCore import pyqtSignal, Qt, QEvent, QPointF, QPoint
from qgis.PyQt.QtGui import QIcon, QMouseEvent
from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QLabel,
    QHBoxLayout, QToolButton, QSizePolicy, QApplication
)
from qgis.core import QgsApplication


class GeocodeAutocompleteWidget(QWidget):
    textEdited = pyqtSignal(str)
    resultSelected = pyqtSignal(dict)
    cleared = pyqtSignal()

    def __init__(self, placeholder: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._selected: Optional[Dict[str, Any]] = None

        self.edit = QLineEdit(self)
        self.edit.setPlaceholderText(placeholder)
        self.edit.textEdited.connect(self._on_text_edited)

        self.edit.returnPressed.connect(self._on_return_pressed)

        self.suggestions = QListWidget(self)

        self.suggestions.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.suggestions.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.suggestions.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.suggestions.setVisible(False)
        self.suggestions.itemClicked.connect(self._on_item_clicked)
        self.suggestions.itemPressed.connect(self._on_item_clicked)

        QApplication.instance().installEventFilter(self)

        self.hint = QLabel(self)
        self.hint.setVisible(False)
        self.hint.setWordWrap(True)

        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.edit.setMinimumWidth(0)
        self.edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self.edit)
        layout.addWidget(self.hint)
        self.setLayout(layout)

    def _on_text_edited(self, txt: str) -> None:
        self._selected = None
        self.textEdited.emit(txt)
        if not txt.strip():
            self.clear_suggestions()
            self.hint.setVisible(False)
            self.cleared.emit()

    def _on_return_pressed(self) -> None:
        if self.suggestions.isVisible() and self.suggestions.count() > 0:
            row = self.suggestions.currentRow()
            if row < 0:
                row = 0
            item = self.suggestions.item(row)
            if item is not None:
                self._on_item_clicked(item)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        r = item.data(Qt.ItemDataRole.UserRole) or {}
        self._selected = r

        self.edit.blockSignals(True)
        self.edit.setText(r.get("address", ""))
        self.edit.blockSignals(False)

        self.clear_suggestions()
        self.resultSelected.emit(r)

    def eventFilter(self, obj, event):
        if self.suggestions.isVisible() and event.type() == QEvent.Type.MouseButtonPress:
            if isinstance(event, QMouseEvent):
                if hasattr(event, "globalPos"):
                    global_position = event.globalPos()
                else:
                    global_position = event.globalPosition().toPoint()

                w = QApplication.widgetAt(global_position)
                if w is None:
                    self.clear_suggestions()
                    return False

                if w is self.edit or self.edit.isAncestorOf(w):
                    return False

                if w is self.suggestions or self.suggestions.isAncestorOf(w):
                    return False

                self.clear_suggestions()

        return super().eventFilter(obj, event)

    # ---- public helpers ----

    def set_hint(self, message: str) -> None:
        msg = (message or "").strip()
        self.hint.setText(msg)
        self.hint.setVisible(bool(msg))

    def set_suggestions(self, results: List[Dict[str, Any]]) -> None:
        self.suggestions.clear()

        for r in results:
            addr = (r or {}).get("address", "")
            postcode = (r or {}).get("postcode", "")
            typ = (r or {}).get("type", "")

            label = addr
            extra = []
            if postcode:
                extra.append(postcode)
            if typ:
                extra.append(typ)
            if extra:
                label = f"{addr}  ({', '.join(extra)})"

            item = QListWidgetItem(label)
            item.setToolTip(label)
            item.setData(Qt.ItemDataRole.UserRole, r)
            self.suggestions.addItem(item)

        if self.suggestions.count() <= 0:
            self.suggestions.setVisible(False)
            return
        
        self.suggestions.setCurrentRow(0)

        p = self.edit.mapToGlobal(QPoint(0, self.edit.height()))
        w = self.edit.width()

        rows = min(self.suggestions.count(), 7)
        rh = self.suggestions.sizeHintForRow(0) if self.suggestions.count() else 22
        h = rows * rh + 8
        h = min(max(h, 90), 220)

        self.suggestions.setFixedWidth(max(w, 220))
        self.suggestions.setFixedHeight(h)
        self.suggestions.move(p)
        self.suggestions.setVisible(True)
        self.suggestions.raise_()
        self.edit.setFocus(Qt.FocusReason.OtherFocusReason)

    def set_selected_result(self, result: Optional[Dict[str, Any]], set_text: bool = True) -> None:
        self._selected = result

        if set_text:
            self.edit.blockSignals(True)
            self.edit.setText((result or {}).get("address", "") if result else "")
            self.edit.blockSignals(False)

        self.clear_suggestions()

    def clear_suggestions(self) -> None:
        self.suggestions.clear()
        self.suggestions.setVisible(False)

    def selected_result(self) -> Optional[Dict[str, Any]]:
        return self._selected

    def text(self) -> str:
        return self.edit.text().strip()

    def clear_selection(self) -> None:
        self.set_selected_result(None, set_text=True)

    def clear(self) -> None:
        self.edit.clear()
        self._selected = None
        self.clear_suggestions()
        self.set_hint("")
        self.cleared.emit()


class RoutingWaypointRow(QWidget):
    removeRequested = pyqtSignal(object)
    pickRequested = pyqtSignal(object)

    def __init__(self, list_widget: QListWidget, placeholder: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._list_widget = list_widget

        self.lbl_drag = QLabel("⋮⋮", self)
        self.lbl_drag.setToolTip("Drag to reorder")
        self.lbl_drag.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        self.lbl_drag.setMinimumWidth(18)
        self.lbl_drag.setCursor(Qt.CursorShape.OpenHandCursor)
        self.lbl_drag.installEventFilter(self)

        self.lbl_seq = QLabel("", self)
        self.lbl_seq.setMinimumWidth(18)
        self.lbl_seq.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.input = GeocodeAutocompleteWidget(placeholder=placeholder)

        self.btn_pick = QToolButton(self)
        self.btn_pick.setAutoRaise(True)
        self.btn_pick.setIcon(QIcon(QgsApplication.iconPath("mActionCapturePoint.svg")))
        self.btn_pick.setToolTip("Pick on map")
        self.btn_pick.clicked.connect(lambda: self.pickRequested.emit(self))

        self.btn_remove = QToolButton(self)
        self.btn_remove.setAutoRaise(True)
        self.btn_remove.setToolTip("Remove")
        self.btn_remove.setIcon(QIcon(QgsApplication.iconPath("mActionDeleteSelected.svg")))
        self.btn_remove.clicked.connect(lambda: self.removeRequested.emit(self))

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.addWidget(self.lbl_drag)
        row.addWidget(self.lbl_seq)
        row.addWidget(self.input)
        row.addWidget(self.btn_pick)
        row.addWidget(self.btn_remove)

    def set_seq(self, n: int) -> None:
        self.lbl_seq.setText(str(int(n)))

    def set_placeholder(self, text: str) -> None:
        try:
            self.input.edit.setPlaceholderText(text)
        except Exception:
            pass

    def eventFilter(self, obj, event):
        if obj is self.lbl_drag and event.type() in (
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonRelease,
        ):
            if not isinstance(event, QMouseEvent):
                return super().eventFilter(obj, event)

            vp = self._list_widget.viewport()

            if hasattr(event, "position"):  # Qt6
                src_pos_qpoint = event.position().toPoint()
            else:  # Qt5
                src_pos_qpoint = event.pos()

            mapped = self.lbl_drag.mapTo(vp, src_pos_qpoint)
            local_f = QPointF(mapped)

            # ---- global position ----
            if hasattr(event, "globalPosition"):  # Qt6
                global_f = event.globalPosition()
                global_qpoint = global_f.toPoint()

                me = None
                try:
                    me = QMouseEvent(
                        event.type(),
                        local_f,
                        local_f,
                        global_f,
                        event.button(),
                        event.buttons(),
                        event.modifiers(),
                    )
                except TypeError:
                    try:
                        me = QMouseEvent(
                            event.type(),
                            local_f,
                            global_f,
                            event.button(),
                            event.buttons(),
                            event.modifiers(),
                        )
                    except TypeError:
                        me = None

            else:  # Qt5
                global_qpoint = event.globalPos()
                me = None
                try:
                    me = QMouseEvent(
                        event.type(),
                        local_f,
                        global_qpoint,
                        event.button(),
                        event.buttons(),
                        event.modifiers(),
                    )
                except TypeError:
                    try:
                        me = QMouseEvent(
                            event.type(),
                            local_f,
                            QPointF(global_qpoint),
                            event.button(),
                            event.buttons(),
                            event.modifiers(),
                        )
                    except TypeError:
                        me = None

            if me is not None:
                QApplication.sendEvent(vp, me)
                return True

            return False

        return super().eventFilter(obj, event)
