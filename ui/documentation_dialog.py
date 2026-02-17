# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox


DEFAULT_DOCUMENTATION_HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: sans-serif; font-size: 12px; line-height: 1.35; }
  h2 { margin: 0 0 8px 0; }
  h3 { margin: 14px 0 6px 0; }
  code { background: rgba(127,127,127,0.12); padding: 1px 3px; border-radius: 3px; }
  .note { padding: 8px; border-radius: 8px; background: rgba(127,127,127,0.08); border: 1px solid rgba(127,127,127,0.18); }
  ul { margin: 6px 0 6px 18px; }
</style>
</head>
<body>
  <h2>Regio API Plugin — Quick Guide</h2>

  <div class="note">
    <b>API key:</b> Set your key in <b>Settings</b> before using geocoding, routing, optimization, or basemaps.
    Use your existing Regio API key or contact <b>regio@regio.ee</b> to get one.
    <br><b>Coordinates:</b> Regio API uses WGS84 <code>[lng, lat]</code>. The plugin transforms to/from the project CRS automatically.
  </div>

  <h3>Search (forward geocode)</h3>
  <ul>
    <li>Type an address to get suggestions.</li>
    <li>Select a suggestion to view the result details.</li>
    <li>Use <b>Clear</b> to reset the search field and hide details.</li>
  </ul>

  <h3>Reverse geocode</h3>
  <ul>
    <li>Click <b>Start reverse geocode</b>, then click on the map to get the nearest address.</li>
    <li>Use <b>Copy address</b> / <b>Copy coordinates</b> to reuse the result.</li>
    <li>Click <b>Stop reverse geocode</b> to disable map clicking.</li>
  </ul>

  <h3>Routing</h3>
  <ul>
    <li>Add waypoints using <b>From</b>, <b>To</b>, and optional <b>Add stop</b> entries.</li>
    <li>You can reorder waypoints in the list by dragging the handles.</li>
    <li>Use <b>Import GeoJSON</b> to load waypoint points from a GeoJSON file (Point / MultiPoint; up to 50 points).</li>
    <li>Click <b>Calculate route</b> to create/update the route line and numbered waypoint markers.</li>
    <li><b>Reverse route</b> flips the waypoint order.</li>
    <li><b>Edit route points (drag)</b> lets you drag the numbered waypoint markers on the map. After moving a point, the route updates.</li>
    <li>The <b>Route summary</b> appears after a route is calculated (and is hidden when empty).</li>
  </ul>

  <h3>Route optimization (optional)</h3>
  <ul>
    <li>Open the <b>Route optimization</b> panel inside the <b>Routing</b> section.</li>
    <li>Optimization uses the <i>current routing waypoints</i> (same list) and computes a better visit order.</li>
    <li>Set options to control constraints:
      <ul>
        <li><b>Start at first point</b> keeps the first waypoint as the start.</li>
        <li><b>End at last point</b> keeps the last waypoint as the end.</li>
        <li><b>Roundtrip</b> enables/disables roundtrip behavior.</li>
      </ul>
    </li>
    <li>Click <b>Optimize</b> to reorder waypoints and then compute the route line (route summary updates as usual).</li>
    <li>Note: Optimization is never automatic — it only runs when you press <b>Optimize</b>.</li>
  </ul>

  <h3>Basemaps</h3>
  <ul>
    <li>Add Regio WMS basemap via the <b>Basemaps</b> section (creates a QGIS WMS layer/connection).</li>
  </ul>

</body>
</html>
"""


class DocumentationDialog(QDialog):
    
    def __init__(self, plugin_root: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Regio API Plugin — Documentation")
        self.setMinimumSize(560, 520)
        self.setWindowIcon(QIcon(os.path.join(plugin_root, "icon.png")))

        layout = QVBoxLayout(self)

        self.browser = QTextBrowser(self)
        self.browser.setOpenExternalLinks(True)
        self.browser.setReadOnly(True)

        documentation_path = os.path.join(plugin_root, "documentation.html")
        if os.path.exists(documentation_path):
            self.browser.setSource(QUrl.fromLocalFile(documentation_path))
        else:
            self.browser.setHtml(DEFAULT_DOCUMENTATION_HTML)

        layout.addWidget(self.browser)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.close)
        buttons.accepted.connect(self.close)
        layout.addWidget(buttons)
