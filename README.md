# Regio API Plugin (QGIS Plugin)

A QGIS plugin that integrates **Regio API** services into a dockable panel:

- Geocoding with autocomplete
- Reverse geocoding
- Routing
- Optional route optimization
- Basemap (Regio WMS) add-to-project

Use your existing Regio API key or contact geospatial@regio.ee

---

## Features

### 1) Search (Geocode)
- Autocomplete-as-you-type
- Simple in-memory cache for recent queries
- Shows result details after selecting a suggestion

### 2) Reverse Geocode
- Toggle button enables/disables map click mode
- Converts clicked map coordinates → WGS84 (lon/lat)
- Copy buttons: address / coordinates

### 3) Routing
- From → To routing with optional intermediate stops
- Waypoints can be reordered in the list
- Supports profiles: `car`, `truck`, `foot`
- Renders:
  - Route line as an in-memory layer
  - Waypoints as an in-memory point layer (numbered/labelled)
- Summary shows distance and duration
- Supports re-calculation (e.g., profile changes)

#### GeoJSON Import (Routing)
- Import waypoint points from a GeoJSON file (Point / MultiPoint features)
- Coordinates are transformed to WGS84 internally
- Up to **50** points are imported
- After import, the route is calculated immediately for convenience

#### Edit Route Points
- After a route exists, you can enable **Edit route points (drag)**
- Drag numbered waypoint markers on the map to refine the route
- Points are updated (optionally reverse geocoded) and the route recalculates

### 4) Route Optimization
Route optimization is available **inside the Routing section** as a collapsed panel.

- Uses current routing waypoints
- Options:
  - Start at first point
  - End at last point
  - Roundtrip
- After optimizing, the plugin reorders the waypoint list and then calculates the route

### 5) Basemap (Regio WMS)
- Adds Regio WMS basemap to the project
- Uses EPSG:3857 or project crs if supported

---

## Installation

In QGIS:
- Plugins → Manage and Install Plugins
- Search **Regio API Plugin** and install plugin

---

## Configuration

### API Key Storage
The API key is stored in `QgsSettings` under the plugin namespace.

- **How to set:** Dock widget → **Settings** (gear icon)

> **Note:** Because WMS access uses `apikey` in the URL, the key can end up in layer sources / project files.

---

## CRS Handling

- API geometries are always treated as **WGS84** in order: **[lng, lat]**
- When displaying on map, controllers transform WGS84 → project CRS via `QgsCoordinateTransform`
- For map clicks, controllers transform project CRS → WGS84 before calling reverse geocode

---

## UI & Translations

### Dock Widget
A dock widget contains collapsible sections:
- Search
- Reverse geocode
- Routing (includes Route optimization panel)
- Basemaps

### Language / Translation
- Default: English
- Supported: Estonian, Latvian, Lithuanian

---

## Logging & Debugging

- Logging uses `QgsMessageLog` under a dedicated plugin category.
- A debug logging toggle (stored in settings) can enable verbose logs.
- **API keys are redacted** in logs when URLs are written.

---

## How to Use

1. Open the **Regio API Plugin** panel (dock widget).
2. Click the **Settings** (gear) button:
   - Paste your API key
   - Choose default country/countries and language

3. **Search:**
   - Start typing an address
   - Pick a suggestion to see details

4. **Reverse geocode:**
   - Click "Start reverse geocode"
   - Click on the map to get nearest address
   - Use copy buttons to reuse the result

5. **Routing:**
   - Choose From and To (and optional stops)
   - Optional: reorder waypoints by dragging in the list
   - Choose profile (car/truck/foot)
   - Click **Calculate route**

6. **Optimization (optional):**
   - Expand the **Route optimization** panel in Routing
   - Set options (start/end/roundtrip)
   - Click **Optimize**

7. **GeoJSON import (routing waypoints):**
   - Click **Import GeoJSON**
   - Select a GeoJSON file with Point/MultiPoint geometries
   - The route is calculated after import

8. **Basemap:**
   - Click "Add basemap"
   - A WMS layer is added to the project

---

## License

This program is licensed under terms of GNU GPL v.2 or any later version.

## Commercial support

Need to fix a bug or add a feature to Regio API Plugin?

Contact geospatial@regio.ee

We provide custom development and support for this software.
