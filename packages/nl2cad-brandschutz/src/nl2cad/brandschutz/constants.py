"""
nl2cad.brandschutz.constants
==============================
Brandschutz- und Explosionsschutz-Konstanten mit Norm-Version und Quelle.

FIX W-01: Jede Konstante traegt Norm, Paragraf und Versionsdatum.
Kein hardcoded String in Business-Logik — immer aus diesem Modul.

Norm-Versionen als Pflichtfeld in jedem Analyse-Ergebnis (RettungswegNachweis,
GebaeudeklasseResult etc.) — Aenderungen hier sind sofort nachvollziehbar.
"""

# ---------------------------------------------------------------------------
# Norm-Versionen (W-01: explizit versioniert)
# ---------------------------------------------------------------------------

# ASR A2.3 — Technische Regeln fuer Arbeitsstaetten "Fluchtwege und Notausgang"
# Ausgabe: Maerz 2022, GMBl 2022 S. 350
ASR_A23_VERSION: str = "ASR-A2.3-2022"

# MBO — Musterbauordnung, Fassung November 2002, zuletzt geaendert 2016
MBO_VERSION: str = "MBO-2016"

# DIN 4102-1 — Brandverhalten von Baustoffen und Bauteilen, 1998
DIN4102_VERSION: str = "DIN-4102-1998"

# EN 13501-1 — Klassifizierung von Bauprodukten und Bauarten, 2019
EN13501_VERSION: str = "EN-13501-2019"

# ATEX / EN 60079-10-1 — Explosionsgefaehrdete Bereiche, Gas/Dampf, 2016
EN60079_10_1_VERSION: str = "EN-60079-10-1-2016"

# TRBS 2152 — Gefaehrliche explosionsfaehige Atmosphaere, 2012
TRBS2152_VERSION: str = "TRBS-2152-2012"

# BetrSichV — Betriebssicherheitsverordnung, BGBl. I 2015 S. 1583
BETRSICHV_VERSION: str = "BetrSichV-2015"

# ---------------------------------------------------------------------------
# ASR A2.3 — Fluchtweg-Grenzwerte (§ 4 + § 5, Ausgabe 2022)
# ---------------------------------------------------------------------------

# § 5 Abs. 1: Maximale Weglänge ohne Richtungsaenderung
MAX_FLUCHTWEG_LAENGE_M: float = 35.0

# § 5 Abs. 2: Maximale Weglänge mit Richtungsaenderung
MAX_FLUCHTWEG_LAENGE_MIT_ABZWEIG_M: float = 60.0

# § 4 Abs. 2 Tab. 1: Mindestbreite Grundmass
MIN_BREITE_STANDARD_M: float = 0.875

# § 4 Abs. 3: Mindestbreite ab 5 Personen
MIN_BREITE_AB_5_PERSONEN_M: float = 1.0

# § 4 Abs. 3: Mindestbreite ab 20 Personen
MIN_BREITE_AB_20_PERSONEN_M: float = 1.2

# § 4: Lichte Mindestbreite Tueroffnung
MIN_TUERBREITE_M: float = 0.78

# VStaettVO § 7: Maximale Weglänge in Versammlungsstaetten
MAX_FLUCHTWEG_VERSAMMLUNGSSTAETTE_M: float = 30.0

# ---------------------------------------------------------------------------
# MBO § 2 Abs. 3 — Gebaeudehoehen fuer Gebaeudeklassen (Fassung 2016)
# ---------------------------------------------------------------------------

# GK 1/2/3: OKFF letztes Nutzgeschoss <= 7 m
MBO_GK123_MAX_OKFF_M: float = 7.0

# GK 4: OKFF letztes Nutzgeschoss <= 13 m
MBO_GK4_MAX_OKFF_M: float = 13.0

# Ab OKFF > 22 m: Hochhaus (Sonderbau, § 2 Abs. 8 Nr. 1)
MBO_HOCHHAUS_MIN_OKFF_M: float = 22.0

# GK 1/2: max. Nutzflaecheneinheit
MBO_GK12_MAX_NE_FLAECHE_M2: float = 400.0

# GK 4: max. Nutzflaecheneinheit
MBO_GK4_MAX_NE_FLAECHE_M2: float = 400.0

# GK 1/2: max. Nutzungseinheiten
MBO_GK12_MAX_NE_ANZAHL: int = 2

# MBO § 33: Zweiter Rettungsweg via Anleitern — max. UKFF Fenster
MBO_ANLEITERN_MAX_UKFF_M: float = 8.0

# MBO § 33: Mindestbreite Aussentreppe
MBO_AUSSENTREPPE_MIN_BREITE_M: float = 1.2

# ---------------------------------------------------------------------------
# DIN 4102 / EN 13501 — Feuerwiderstandsklassen
# ---------------------------------------------------------------------------

FEUERWIDERSTANDSKLASSEN_DIN4102: tuple[str, ...] = (
    "F30",
    "F60",
    "F90",
    "F120",
    "F180",
)

FEUERWIDERSTANDSKLASSEN_EN13501: tuple[str, ...] = (
    "REI30",
    "REI60",
    "REI90",
    "REI120",
    "EI30",
    "EI60",
    "EI90",
    "EI120",
    "E30",
    "E60",
    "E90",
    "R30",
    "R60",
    "R90",
)

ALLE_FEUERWIDERSTANDSKLASSEN: frozenset[str] = frozenset(
    FEUERWIDERSTANDSKLASSEN_DIN4102 + FEUERWIDERSTANDSKLASSEN_EN13501
)

BRANDSCHUTZTUER_KLASSEN: tuple[str, ...] = (
    "T30",
    "T60",
    "T90",
    "T120",
    "EI230",
    "EI260",
    "EI290",
)

# ---------------------------------------------------------------------------
# EN 60079-10-1 Tabelle 1 — Zonenausdehnung (vereinfacht)
# Schluessel: (freisetzungsgrad, lueftungsklasse) -> (zone_str, ausdehnung_m)
# ---------------------------------------------------------------------------

# Freisetzungsgrad-Kuerzel: K=kontinuierlich, P=primaer, S=sekundaer
# Lueftungsklasse: K1=gut, K2=mittel, K3=schlecht
# I-07: Zonen-Strings MUESSEN mit ExZone.value uebereinstimmen ("Zone 0" etc.)
EX_ZONENAUSDEHNUNG: dict[tuple[str, str], tuple[str, float]] = {
    ("K", "K1"): ("Zone 0", 0.5),
    ("K", "K2"): ("Zone 0", 1.0),
    ("K", "K3"): ("Zone 0", 3.0),
    ("P", "K1"): ("Zone 1", 0.5),
    ("P", "K2"): ("Zone 1", 1.0),
    ("P", "K3"): ("Zone 1", 3.0),
    ("S", "K1"): ("Zone 2", 1.0),
    ("S", "K2"): ("Zone 2", 2.0),
    ("S", "K3"): ("Zone 2", 5.0),
    # Staub: Zone 20/21/22 (EN 60079-10-2)
    ("K_STAUB", "K1"): ("Zone 20", 0.5),
    ("K_STAUB", "K2"): ("Zone 20", 1.0),
    ("K_STAUB", "K3"): ("Zone 20", 3.0),
    ("P_STAUB", "K1"): ("Zone 21", 0.5),
    ("P_STAUB", "K2"): ("Zone 21", 1.0),
    ("P_STAUB", "K3"): ("Zone 21", 3.0),
    ("S_STAUB", "K1"): ("Zone 22", 1.0),
    ("S_STAUB", "K2"): ("Zone 22", 2.0),
    ("S_STAUB", "K3"): ("Zone 22", 5.0),
}

# ATEX 2014/34/EU — Geraetekategorien je Zone (Mindestanforderung)
# Schluessel = ExZone.value ("Zone 0", "Zone 1", ...)
ATEX_ZONE_ZU_GERAETEKATEGORIE: dict[str, str] = {
    "Zone 0": "KAT1",
    "Zone 1": "KAT2",
    "Zone 2": "KAT3",
    "Zone 20": "KAT1",
    "Zone 21": "KAT2",
    "Zone 22": "KAT3",
}

# ---------------------------------------------------------------------------
# BetrSichV § 6 Abs. 9 — ESD-Pflichtfelder (fuer is_vollstaendig()-Pruefung)
# ---------------------------------------------------------------------------

ESD_PFLICHTFELDER: tuple[str, ...] = (
    "betrieb_name",
    "erstellungsdatum",
    "erstellt_von",
    "naechste_pruefung",
    "gefaehrdungsbeurteilung",
    "explosionsfaehige_atmosphaere_moeglich",
)
