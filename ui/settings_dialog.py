# -*- coding: utf-8 -*-
from typing import Optional, Callable

from qgis.PyQt import sip
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QCheckBox, QMessageBox, QWidget
)

from ..settings import PluginSettings
from ..api_client import ApiClient


def tr(text: str) -> str:
    return QCoreApplication.translate("RegioApiPlugin", text)


class SettingsDialog(QDialog):
    def __init__(
        self,
        settings: PluginSettings,
        api: ApiClient,
        on_applied: Optional[Callable[[], None]] = None,
        parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle(tr("Settings"))

        self._settings = settings
        self._api = api
        self._on_applied = on_applied

        self._req_id = 0
        self._active_reply = None

        # API key
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setText(self._settings.api_key())

        # Countries
        self.cb_ee = QCheckBox("EE")
        self.cb_lv = QCheckBox("LV")
        self.cb_lt = QCheckBox("LT")
        selected = set(self._settings.countries())
        self.cb_ee.setChecked("EE" in selected)
        self.cb_lv.setChecked("LV" in selected)
        self.cb_lt.setChecked("LT" in selected)

        countries_row = QWidget()
        cr_l = QHBoxLayout()
        cr_l.setContentsMargins(0, 0, 0, 0)
        cr_l.setSpacing(12)
        cr_l.addWidget(self.cb_ee)
        cr_l.addWidget(self.cb_lv)
        cr_l.addWidget(self.cb_lt)
        cr_l.addStretch(1)
        countries_row.setLayout(cr_l)

        # Language
        self.language = QComboBox()
        self.language.addItem("English", "en")
        self.language.addItem("Eesti", "et")
        self.language.addItem("Latviešu", "lv")
        self.language.addItem("Lietuvių", "lt")
        cur = self._settings.language()
        for i in range(self.language.count()):
            if self.language.itemData(i) == cur:
                self.language.setCurrentIndex(i)
                break

        # Debug
        self.debug = QCheckBox(tr("Debug logging"))
        self.debug.setChecked(self._settings.debug_logging())

        # Buttons
        self.btn_test = QPushButton(tr("Test API key"))
        self.btn_test.clicked.connect(self._test_key)

        self.btn_save = QPushButton(tr("Save"))
        self.btn_close = QPushButton(tr("Close"))
        self.btn_save.clicked.connect(self._save)
        self.btn_close.clicked.connect(self.reject)

        layout = QVBoxLayout()

        layout.addWidget(QLabel(tr("API key")))
        layout.addWidget(self.api_key)

        layout.addWidget(QLabel(tr("Countries")))
        layout.addWidget(countries_row)

        layout.addWidget(QLabel(tr("Language")))
        layout.addWidget(self.language)

        layout.addWidget(self.debug)
        layout.addWidget(self.btn_test)

        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.btn_save)
        row.addWidget(self.btn_close)
        layout.addLayout(row)

        self.setLayout(layout)

    def _selected_countries(self) -> list[str]:
        out = []
        if self.cb_ee.isChecked():
            out.append("EE")
        if self.cb_lv.isChecked():
            out.append("LV")
        if self.cb_lt.isChecked():
            out.append("LT")
        return out

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

    def _save(self) -> None:
        countries = self._selected_countries()
        if not countries:
            QMessageBox.warning(self, tr("Settings"), tr("Select at least one country."))
            return

        self._settings.set_api_key(self.api_key.text())
        self._settings.set_countries(countries)
        self._settings.set_language(self.language.currentData())
        self._settings.set_debug_logging(self.debug.isChecked())

        if self._on_applied:
            self._on_applied()

        self.accept()

    def _test_key(self) -> None:
        key = self.api_key.text().strip()
        if not key:
            QMessageBox.warning(self, tr("Settings"), tr("API key is empty."))
            return

        countries = self._selected_countries()
        if not countries:
            QMessageBox.warning(self, tr("Settings"), tr("Select at least one country."))
            return

        country_param = ",".join([c.lower() for c in countries])

        self._req_id += 1
        rid = self._req_id

        self._abort_active_reply()

        def _done(req_id: int, ok: bool, payload: Optional[dict], err: Optional[str]) -> None:
            self._active_reply = None
            if req_id != rid:
                return
            if not ok:
                QMessageBox.critical(self, tr("Test API key"), f"Failed: {err}")
                return
            data = (payload or {}).get("data") or []
            if isinstance(data, list):
                QMessageBox.information(self, tr("Test API key"), "Success")
            else:
                QMessageBox.warning(self, tr("Test API key"), "Unexpected response")

        self._active_reply = self._api.geocode(
            address="Tartu",
            country=country_param,
            apikey=key,
            request_id=rid,
            on_done=_done,
            timeout_ms=10000
        )
