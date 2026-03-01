"""
nl2cad.core.constants
=====================
Konstanten für DIN 277, Layer-Keywords, Dateiformate.
Keine hardcoded Strings in Business-Logik — immer aus diesem Modul.
"""

# ---------------------------------------------------------------------------
# Unterstützte Dateiformate
# ---------------------------------------------------------------------------
SUPPORTED_FORMATS = {".ifc", ".dxf", ".dwg"}
IFC_EXTENSIONS = {".ifc"}
DXF_EXTENSIONS = {".dxf", ".dwg"}

# ---------------------------------------------------------------------------
# DIN 277 — Nutzungsarten (Ausgabe 2016)
# ---------------------------------------------------------------------------
DIN277_CODES: dict[str, str] = {
    # Hauptnutzfläche (NUF)
    "NUF_1": "Wohnen und Aufenthalt",
    "NUF_2": "Büroarbeit",
    "NUF_3": "Produktion, Hand- und Maschinenarbeit, Experimente",
    "NUF_4": "Lagern, Verteilen, Verkaufen",
    "NUF_5": "Bildung, Unterricht, Kultur",
    "NUF_6": "Heilen und Pflegen",
    "NUF_7": "Beherbergung und Freizeit",
    "NUF_8": "Sonstige Nutzungen",
    # Technische Anlagenflächen (TF)
    "TF": "Technische Anlagenflächen",
    # Verkehrsflächen (VF)
    "VF_1": "Flure, Hallen",
    "VF_2": "Treppen",
    "VF_3": "Rampen",
    "VF_4": "Aufzüge, Fahrtreppen",
    # Funktionsflächen (FF)
    "FF": "Funktionsflächen",
    # Konstruktions-Grundflächen (KGF)
    "KGF": "Konstruktions-Grundflächen",
}

# Mapping Raum-Keywords → DIN 277 Code
ROOM_KEYWORD_TO_DIN277: dict[str, str] = {
    "wohnzimmer": "NUF_1",
    "schlafzimmer": "NUF_1",
    "kinderzimmer": "NUF_1",
    "esszimmer": "NUF_1",
    "wohnen": "NUF_1",
    "büro": "NUF_2",
    "office": "NUF_2",
    "besprechung": "NUF_2",
    "lager": "NUF_4",
    "abstellraum": "NUF_4",
    "vorraum": "NUF_4",
    "flur": "VF_1",
    "korridor": "VF_1",
    "diele": "VF_1",
    "eingang": "VF_1",
    "foyer": "VF_1",
    "treppenhaus": "VF_2",
    "treppe": "VF_2",
    "aufzug": "VF_4",
    "lift": "VF_4",
    "bad": "NUF_8",
    "badezimmer": "NUF_8",
    "wc": "NUF_8",
    "toilette": "NUF_8",
    "dusche": "NUF_8",
    "küche": "NUF_8",
    "kochen": "NUF_8",
    "technik": "TF",
    "heizung": "TF",
    "haustechnik": "TF",
}

# ---------------------------------------------------------------------------
# DXF Layer-Keywords — werden beim Parsen zur Klassifikation genutzt
# ---------------------------------------------------------------------------

# Layer die KEINE Nutzflächen enthalten (werden bei Raumerkennung ignoriert)
EXCLUDED_LAYER_KEYWORDS: frozenset[str] = frozenset([
    "symbol", "symbole", "schraffur", "hatch",
    "text", "beschriftung", "annotation",
    "bemaßung", "dimension", "dim",
    "achse", "axis", "grid", "hilfslin", "construction",
    "möbel", "furniture", "einrichtung",
    "elektro", "electric", "sanitär", "sanitary",
    "heizung", "heating", "lüftung", "hvac",
    "legende", "legend", "rahmen", "frame", "border",
    "logo", "titel", "title", "north", "nord",
    "maßstab", "scale", "viewport", "defpoints",
    "ergänzung", "notiz", "note", "comment",
])

# Layer-Keywords für Brandschutz-Erkennung
FLUCHTWEG_KEYWORDS: tuple[str, ...] = (
    "flucht", "rettung", "escape", "notweg", "fluchtweg",
    "rettungsweg", "emergency",
)
NOTAUSGANG_KEYWORDS: tuple[str, ...] = (
    "notausgang", "emergency exit", "notaus", "ausgang_not",
)
BRANDABSCHNITT_KEYWORDS: tuple[str, ...] = (
    "brand", "brandwand", "brandschutz", "fire", "feuerwand",
    "brandabschnitt", "brandschutzwand",
)
LOESCHEINRICHTUNG_KEYWORDS: tuple[str, ...] = (
    "feuerlöscher", "hydrant", "sprinkler", "lösch",
    "fire extinguisher", "löscher",
)
BRANDSCHUTZTUER_KEYWORDS: tuple[str, ...] = (
    "t30", "t60", "t90", "t120",
    "brandschutztür", "brandschutztuer", "feuerschutztür",
)

# ---------------------------------------------------------------------------
# Feuerwiderstandsklassen nach DIN 4102 / EN 13501
# ---------------------------------------------------------------------------
FEUERWIDERSTANDSKLASSEN: tuple[str, ...] = (
    "F30", "F60", "F90", "F120", "F180",    # DIN 4102
    "REI30", "REI60", "REI90", "REI120",    # EN 13501
    "EI30", "EI60", "EI90", "EI120",
    "E30", "E60", "E90",
    "R30", "R60", "R90",
)

BRANDSCHUTZTUER_KLASSEN: tuple[str, ...] = (
    "T30", "T60", "T90", "T120",
    "EI230", "EI260", "EI290",
)
