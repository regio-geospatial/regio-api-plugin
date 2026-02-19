# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QTranslator

_TRANSLATIONS = {
    "et": {
        ("RegioApiPlugin", "Regio API Plugin"): "Regio API teenused",
        ("RegioApiPlugin", "Settings"): "Seaded",
        ("RegioApiPlugin", "Documentation"): "Dokumentatsioon",

        ("RegioApiPlugin", "Search"): "Otsing",
        ("RegioApiPlugin", "Reverse geocode"): "Pöördgeokodeerimine",
        ("RegioApiPlugin", "Routing"): "Marsruutimine",
        ("RegioApiPlugin", "Basemaps"): "Taustakaardid",

        ("RegioApiPlugin", "API key"): "API võti",
        ("RegioApiPlugin", "Countries"): "Riigid",
        ("RegioApiPlugin", "Language"): "Keel",
        ("RegioApiPlugin", "Debug logging"): "Silumislogimine",

        ("RegioApiPlugin", "Test API key"): "Testi API võtit",
        ("RegioApiPlugin", "Save"): "Salvesta",
        ("RegioApiPlugin", "Close"): "Sulge",

        ("RegioApiPlugin", "Search address"): "Otsi aadressi",
        ("RegioApiPlugin", "Clear"): "Tühjenda",
        ("RegioApiPlugin", "Details"): "Üksikasjad",

        ("RegioApiPlugin", "Address"): "Aadress",
        ("RegioApiPlugin", "Postcode"): "Postikood",
        ("RegioApiPlugin", "Result"): "Tulemus",
        ("RegioApiPlugin", "Copy address"): "Kopeeri aadress",
        ("RegioApiPlugin", "Copy coordinates"): "Kopeeri koordinaadid",

        ("RegioApiPlugin", "Start reverse geocode"): "Alusta pöördgeokodeerimist",
        ("RegioApiPlugin", "Stop reverse geocode"): "Peata pöördgeokodeerimine",
        ("RegioApiPlugin", "Status: ON"): "Olek: SEES",
        ("RegioApiPlugin", "Status: OFF"): "Olek: VÄLJAS",
        ("RegioApiPlugin", "No results."): "Tulemusi pole.",
        ("RegioApiPlugin", "Click on the map to get the nearest address."): "Klõpsa kaardil, et saada lähim aadress.",

        ("RegioApiPlugin", "API key is empty."): "API võti on tühi.",
        ("RegioApiPlugin", "API key not set. Open Settings."): "API võti pole määratud. Ava seaded.",
        ("RegioApiPlugin", "Select at least one country."): "Vali vähemalt üks riik.",
        ("RegioApiPlugin", "Contact geospatial@regio.ee for new API key."): "Võta ühendust geospatial@regio.ee, et saada uus API võti.",

        ("RegioApiPlugin", "Waypoints"): "Teekonnapunktid",
        ("RegioApiPlugin", "Stop"): "Peatus",
        ("RegioApiPlugin", "From"): "Algus",
        ("RegioApiPlugin", "To"): "Sihtpunkt",

        ("RegioApiPlugin", "Add stop"): "Lisa peatus",
        ("RegioApiPlugin", "Profile"): "Profiil",
        ("RegioApiPlugin", "Car"): "Auto",
        ("RegioApiPlugin", "Truck"): "Veoauto",
        ("RegioApiPlugin", "Foot"): "Jalgsi",

        ("RegioApiPlugin", "Calculate route"): "Arvuta marsruut",
        ("RegioApiPlugin", "Clear route"): "Eemalda marsruut",
        ("RegioApiPlugin", "Route summary"): "Marsruudi kokkuvõte",

        ("RegioApiPlugin", "Calculating"): "Arvutan",

        ("RegioApiPlugin", "Reverse route"): "Pööra marsruut ümber",
        ("RegioApiPlugin", "Edit route points (drag)"): "Muuda marsruudi punkte (lohista)",
        ("RegioApiPlugin", "Stop editing route points"): "Lõpeta punktide muutmine",

        ("RegioApiPlugin", "Basemap"): "Aluskaart",
        ("RegioApiPlugin", "Regio Baltic WMS"): "Regio Balti WMS",
        ("RegioApiPlugin", "Add basemap"): "Lisa aluskaart",
        ("RegioApiPlugin", "Basemap already added."): "Aluskaart on juba lisatud.",

        ("RegioApiPlugin", "Route optimization"): "Teekonna optimeerimine",
        ("RegioApiPlugin", "Start at first point"): "Alusta esimesest punktist",
        ("RegioApiPlugin", "End at last point"): "Lõpeta viimases punktis",
        ("RegioApiPlugin", "Roundtrip"): "Ringreis",
        ("RegioApiPlugin", "Points"): "Punktid",
        ("RegioApiPlugin", "Add point"): "Lisa punkt",
        ("RegioApiPlugin", "Import GeoJSON"): "Impordi GeoJSON",
        ("RegioApiPlugin", "Optimize"): "Optimeeri",
        ("RegioApiPlugin", "Edit points (drag)"): "Muuda punkte (lohista)",
        ("RegioApiPlugin", "Stop editing points"): "Lõpeta punktide muutmine",
        ("RegioApiPlugin", "Trip summary"): "Teekonna kokkuvõte",
        ("RegioApiPlugin", "Point"): "Punkt",
        ("RegioApiPlugin", "Remove"): "Eemalda",
    },

    "lv": {
        ("RegioApiPlugin", "Regio API Plugin"): "Regio API pakalpojumi",
        ("RegioApiPlugin", "Settings"): "Iestatījumi",
        ("RegioApiPlugin", "Documentation"): "Dokumentācija",

        ("RegioApiPlugin", "Search"): "Meklēšana",
        ("RegioApiPlugin", "Reverse geocode"): "Reversā ģeokodēšana",
        ("RegioApiPlugin", "Routing"): "Maršrutēšana",
        ("RegioApiPlugin", "Basemaps"): "Pamatkartes",

        ("RegioApiPlugin", "API key"): "API atslēga",
        ("RegioApiPlugin", "Countries"): "Valstis",
        ("RegioApiPlugin", "Language"): "Valoda",
        ("RegioApiPlugin", "Debug logging"): "Atkļūdošanas reģistrēšana",

        ("RegioApiPlugin", "Test API key"): "Pārbaudīt API atslēgu",
        ("RegioApiPlugin", "Save"): "Saglabāt",
        ("RegioApiPlugin", "Close"): "Aizvērt",

        ("RegioApiPlugin", "Address"): "Adrese",
        ("RegioApiPlugin", "Postcode"): "Pasta indekss",
        ("RegioApiPlugin", "Search address"): "Meklēt adresi",
        ("RegioApiPlugin", "Clear"): "Notīrīt",
        ("RegioApiPlugin", "Details"): "Detaļas",

        ("RegioApiPlugin", "Result"): "Rezultāts",
        ("RegioApiPlugin", "Copy address"): "Kopēt adresi",
        ("RegioApiPlugin", "Copy coordinates"): "Kopēt koordinātas",

        ("RegioApiPlugin", "Start reverse geocode"): "Sākt reverso ģeokodēšanu",
        ("RegioApiPlugin", "Stop reverse geocode"): "Apturēt reverso ģeokodēšanu",
        ("RegioApiPlugin", "Status: ON"): "Statuss: IESLĒGTS",
        ("RegioApiPlugin", "Status: OFF"): "Statuss: IZSLĒGTS",
        ("RegioApiPlugin", "No results."): "Nav rezultātu.",
        ("RegioApiPlugin", "Click on the map to get the nearest address."): "Klikšķiniet kartē, lai iegūtu tuvāko adresi.",

        ("RegioApiPlugin", "API key is empty."): "API atslēga ir tukša.",
        ("RegioApiPlugin", "API key not set. Open Settings."): "API atslēga nav iestatīta. Atveriet iestatījumus.",
        ("RegioApiPlugin", "Select at least one country."): "Izvēlieties vismaz vienu valsti.",
        ("RegioApiPlugin", "Contact geospatial@regio.ee for new API key."): "Sazinieties ar geospatial@regio.ee, lai iegūtu jaunu API atslēgu.",

        ("RegioApiPlugin", "Waypoints"): "Maršruta punkti",
        ("RegioApiPlugin", "Stop"): "Pietura",
        ("RegioApiPlugin", "From"): "No",
        ("RegioApiPlugin", "To"): "Uz",

        ("RegioApiPlugin", "Add stop"): "Pievienot pieturu",
        ("RegioApiPlugin", "Profile"): "Profils",
        ("RegioApiPlugin", "Car"): "Auto",
        ("RegioApiPlugin", "Truck"): "Kravas auto",
        ("RegioApiPlugin", "Foot"): "Kājām",

        ("RegioApiPlugin", "Calculate route"): "Aprēķināt maršrutu",
        ("RegioApiPlugin", "Clear route"): "Notīrīt maršrutu",
        ("RegioApiPlugin", "Route summary"): "Maršruta kopsavilkums",

        ("RegioApiPlugin", "Calculating"): "Aprēķinu",

        ("RegioApiPlugin", "Reverse route"): "Apgriezt maršrutu",
        ("RegioApiPlugin", "Edit route points (drag)"): "Rediģēt maršruta punktus (vilkt)",
        ("RegioApiPlugin", "Stop editing route points"): "Pārtraukt punktu rediģēšanu",

        ("RegioApiPlugin", "Basemap"): "Pamatkarte",
        ("RegioApiPlugin", "Regio Baltic WMS"): "Regio Baltijas WMS",
        ("RegioApiPlugin", "Add basemap"): "Pievienot pamatkarti",
        ("RegioApiPlugin", "Basemap already added."): "Pamatkarte jau pievienota.",

        ("RegioApiPlugin", "Route optimization"): "Maršruta optimizācija",
        ("RegioApiPlugin", "Start at first point"): "Sākt no pirmā punkta",
        ("RegioApiPlugin", "End at last point"): "Beigt pie pēdējā punkta",
        ("RegioApiPlugin", "Roundtrip"): "Apļveida maršruts",
        ("RegioApiPlugin", "Points"): "Punkti",
        ("RegioApiPlugin", "Add point"): "Pievienot punktu",
        ("RegioApiPlugin", "Import GeoJSON"): "Importēt GeoJSON",
        ("RegioApiPlugin", "Optimize"): "Optimizēt",
        ("RegioApiPlugin", "Edit points (drag)"): "Rediģēt punktus (vilkt)",
        ("RegioApiPlugin", "Stop editing points"): "Pārtraukt punktu rediģēšanu",
        ("RegioApiPlugin", "Trip summary"): "Maršruta kopsavilkums",
        ("RegioApiPlugin", "Point"): "Punkts",
        ("RegioApiPlugin", "Remove"): "Noņemt",
    },

    "lt": {
        ("RegioApiPlugin", "Regio API Plugin"): "Regio API paslaugos",
        ("RegioApiPlugin", "Settings"): "Nustatymai",
        ("RegioApiPlugin", "Documentation"): "Dokumentacija",

        ("RegioApiPlugin", "Search"): "Paieška",
        ("RegioApiPlugin", "Reverse geocode"): "Atvirkštinis geokodavimas",
        ("RegioApiPlugin", "Routing"): "Maršrutai",
        ("RegioApiPlugin", "Basemaps"): "Pagrindo žemėlapiai",

        ("RegioApiPlugin", "API key"): "API raktas",
        ("RegioApiPlugin", "Countries"): "Šalys",
        ("RegioApiPlugin", "Language"): "Kalba",
        ("RegioApiPlugin", "Debug logging"): "Derinimo žurnalas",

        ("RegioApiPlugin", "Test API key"): "Tikrinti API raktą",
        ("RegioApiPlugin", "Save"): "Išsaugoti",
        ("RegioApiPlugin", "Close"): "Uždaryti",

        ("RegioApiPlugin", "Address"): "Adresas",
        ("RegioApiPlugin", "Postcode"): "Pašto kodas",
        ("RegioApiPlugin", "Search address"): "Ieškoti adreso",
        ("RegioApiPlugin", "Clear"): "Išvalyti",
        ("RegioApiPlugin", "Details"): "Išsami informacija",

        ("RegioApiPlugin", "Result"): "Rezultatas",
        ("RegioApiPlugin", "Copy address"): "Kopijuoti adresą",
        ("RegioApiPlugin", "Copy coordinates"): "Kopijuoti koordinates",

        ("RegioApiPlugin", "Start reverse geocode"): "Pradėti atvirkštinį geokodavimą",
        ("RegioApiPlugin", "Stop reverse geocode"): "Sustabdyti atvirkštinį geokodavimą",
        ("RegioApiPlugin", "Status: ON"): "Būsena: ĮJUNGTA",
        ("RegioApiPlugin", "Status: OFF"): "Būsena: IŠJUNGTA",
        ("RegioApiPlugin", "No results."): "Nėra rezultatų.",
        ("RegioApiPlugin", "Click on the map to get the nearest address."): "Spustelėkite žemėlapyje, kad gautumėte artimiausią adresą.",

        ("RegioApiPlugin", "API key is empty."): "API raktas tuščias.",
        ("RegioApiPlugin", "API key not set. Open Settings."): "API raktas nenustatytas. Atidarykite nustatymus.",
        ("RegioApiPlugin", "Select at least one country."): "Pasirinkite bent vieną šalį.",
        ("RegioApiPlugin", "Contact geospatial@regio.ee for new API key."): "Susisiekite su geospatial@regio.ee, kad gautumėte naują API raktą.",

        ("RegioApiPlugin", "Waypoints"): "Maršruto taškai",
        ("RegioApiPlugin", "Stop"): "Stotelė",
        ("RegioApiPlugin", "From"): "Iš",
        ("RegioApiPlugin", "To"): "Į",

        ("RegioApiPlugin", "Add stop"): "Pridėti stotelę",
        ("RegioApiPlugin", "Profile"): "Profilis",
        ("RegioApiPlugin", "Car"): "Automobilis",
        ("RegioApiPlugin", "Truck"): "Sunkvežimis",
        ("RegioApiPlugin", "Foot"): "Pėsčiomis",

        ("RegioApiPlugin", "Calculate route"): "Skaičiuoti maršrutą",
        ("RegioApiPlugin", "Clear route"): "Išvalyti maršrutą",
        ("RegioApiPlugin", "Route summary"): "Maršruto santrauka",

        ("RegioApiPlugin", "Calculating"): "Skaičiuoju",

        ("RegioApiPlugin", "Reverse route"): "Apversti maršrutą",
        ("RegioApiPlugin", "Edit route points (drag)"): "Redaguoti maršruto taškus (vilkti)",
        ("RegioApiPlugin", "Stop editing route points"): "Baigti taškų redagavimą",

        ("RegioApiPlugin", "Basemap"): "Pagrindo žemėlapis",
        ("RegioApiPlugin", "Regio Baltic WMS"): "Regio Baltijos WMS",
        ("RegioApiPlugin", "Add basemap"): "Pridėti pagrindo žemėlapį",
        ("RegioApiPlugin", "Basemap already added."): "Pagrindo žemėlapis jau pridėtas.",

        ("RegioApiPlugin", "Route optimization"): "Maršruto optimizavimas",
        ("RegioApiPlugin", "Start at first point"): "Pradėti nuo pirmojo taško",
        ("RegioApiPlugin", "End at last point"): "Baigti prie paskutinio taško",
        ("RegioApiPlugin", "Roundtrip"): "Aplinkkelionė",
        ("RegioApiPlugin", "Points"): "Taškai",
        ("RegioApiPlugin", "Add point"): "Pridėti tašką",
        ("RegioApiPlugin", "Import GeoJSON"): "Importuoti GeoJSON",
        ("RegioApiPlugin", "Optimize"): "Optimizuoti",
        ("RegioApiPlugin", "Edit points (drag)"): "Redaguoti taškus (vilkti)",
        ("RegioApiPlugin", "Stop editing points"): "Baigti taškų redagavimą",
        ("RegioApiPlugin", "Trip summary"): "Maršruto santrauka",
        ("RegioApiPlugin", "Point"): "Taškas",
        ("RegioApiPlugin", "Remove"): "Pašalinti",
    },
}


class DictTranslator(QTranslator):
    """
    Context-aware QTranslator using a dictionary for translations.
    """

    def __init__(self, lang: str):
        super().__init__()
        self._map = _TRANSLATIONS.get(lang, {})

    def translate(self, context: str, source_text: str, disambiguation: str = None, n: int = -1) -> str:
        ctx = (context or "").strip()

        v = self._map.get((ctx, source_text))
        if v is not None:
            return v

        v = self._map.get(source_text)
        if v is not None:
            return v

        return source_text
