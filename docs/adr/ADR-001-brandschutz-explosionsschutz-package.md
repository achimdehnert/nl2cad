# ADR-001: nl2cad-brandschutz — Scope, Pflicht-Use-Cases und Architektur

| Attribut      | Wert                                                                                                                              |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Status**    | Accepted (Rev 2 — nach Review ADR-001-REVIEW.md 2026-03-01)                                                                      |
| **Datum**     | 2026-03-01                                                                                                                        |
| **Autoren**   | Achim Dehnert                                                                                                                     |
| **Packages**  | `nl2cad-brandschutz` (primary), `nl2cad-core`                                                                                    |
| **Ersetzt**   | ADR-001 Rev 1                                                                                                                     |
| **Verknüpft** | ADR-002 (ATEX), ADR-003 (Barrierefreiheit), ADR-004 (Sonderbauten), ADR-005 (PDF-Export)                                         |
| **Review**    | ADR-001-REVIEW.md — 6 Blocking Issues behoben: B-01 DB-Schema, B-02 Umlaute, B-03 Quality→core, B-04 Distanz, B-05 Invarianten, B-06 BeurteilungsStatus |

---

## 1. Kontext und Problemstellung

`nl2cad-brandschutz` soll als **fachlich vollständige Python-Library** für die automatisierte
Brandschutz- und Explosionsschutzanalyse von IFC- und DXF-Modellen eingesetzt werden.

Zielgruppen:

- **Architekten** — Nachweis bauordnungsrechtlicher Anforderungen (MBO, LBO)
- **Brandschutzplaner** — Erstellung und Prüfung von Brandschutzkonzepten
- **Explosionsschutzbeauftragte** — ESD-Erstellung nach BetrSichV § 6
- **Downstream-Applikationen** — `cad-hub` (Django), Behörden-Portale, BIM-Viewer

### Bisheriger Stand (Kritisch)

Das Package enthält nur:

- Layer-basierte Keyword-Erkennung (DXF) ohne Regelwerk-Tiefe
- ASR A2.3 Fluchtweglängen-Check (unvollständig, siehe ADR-Bug-Log)
- DIN 4102 Feuerwiderstandsklassen-Validierung (nur Formatcheck)
- Leere `ExBereich`-Dataclass ohne jede Funktionalität

**Ohne Gebäudeklassen-Ermittlung sind alle Brandschutz-Checks fachlich wertlos** —
jede MBO-Anforderung ist GK-abhängig.

---

## 2. Entscheidung

Das Package `nl2cad-brandschutz` wird in **drei Ausbaustufen** (Milestones) erweitert.
Jede Stufe liefert einen in sich geschlossenen, produktiv einsetzbaren Funktionsumfang.

---

## 3. Pflicht-Use-Cases (Milestone 1 — ohne diese kein produktiver Einsatz)

### UC-01: Gebäudeklassen-Ermittlung nach MBO § 2 Abs. 3

**Norm:** MBO § 2 Abs. 3, jeweilige Landes-Bauordnung (LBO)

**Fachliche Grundlage:**

| GK | Kriterium |
|----|-----------|
| 1  | Freistehend, ≤ 2 NE, OKFF ≤ 7 m, Nutzfläche je NE ≤ 400 m² |
| 2  | Freistehend, ≤ 2 NE, OKFF ≤ 7 m |
| 3  | OKFF ≤ 7 m |
| 4  | OKFF ≤ 13 m, NE ≤ 400 m² |
| 5  | Alle anderen (Hochhäuser: OKFF > 22 m → Sonderbau) |

**Eingabe:** `IFCModel` (Geschoss-Höhen, Nutzungsarten, Anzahl Nutzungseinheiten)

**Ausgabe:**
```python
# FIX B-02: ASCII-only Klassennamen — keine Umlaute (AGENTS.md, ruff UP031)
@dataclass
class GebaeudeklasseResult:
    gk: Gebaeudeklasse              # Enum GK1..GK5, SONDERBAU
    okff_hoechstes_geschoss_m: float
    nutzungseinheiten_count: int
    nutzung: GebaeudeNutzung        # WOHNEN, BUERO, INDUSTRIE, SONDERBAU
    begruendung: str
    bauteilanforderungen: BauteilAnforderungen  # abgeleitete F/REI-Klassen
    norm_version: str               # W-01: z.B. "MBO-2016" — Pflichtfeld
```

**Implementierungsort:** `nl2cad/brandschutz/gebaeudeklasse.py`

**Abhängigkeiten:** `IFCModel`, `DIN277Result` (für Nutzungsart-Ableitung)

**GK-Prüfreihenfolge (I-04 Fix):** GK1 vor GK2 prüfen (First-Match, GK1 ⊂ GK2).

---

### UC-02: IFC-Vollständigkeitsprüfer

**Fachliche Grundlage:** Alle nachgelagerten Analysen setzen valide IFC-Quantities voraus.
Fehlende Werte erzeugen stille `0.0`-Ergebnisse (bekannter Bug, ifc_parser.py).

**Prüfregeln:**

| Feld | Mindestanforderung | Fehlerklasse |
|------|--------------------|--------------|
| `IfcSpace.area_m2` | > 0.1 m² | KRITISCH |
| `IfcBuildingStorey.elevation_m` | Nicht alle 0.0 | WARNUNG |
| `IfcDoor.fire_rating` | Befüllt wenn Layer enthält `t30/t60/t90` | WARNUNG |
| `IfcSpace.name` | Nicht leer oder `"Space"` | INFO |
| Mindestanzahl Räume | ≥ 1 | KRITISCH |
| Mindestanzahl Geschosse | ≥ 1 | KRITISCH |

**Ausgabe:**
```python
@dataclass
class IFCQualityReport:
    is_valid: bool
    issues: list[IFCQualityIssue]   # severity, field_path, ifc_guid, message
    completeness_score: float        # 0.0–1.0
```

**Implementierungsort:** `nl2cad/core/quality.py` (**FIX B-03 — gehört in nl2cad-core**, nicht nl2cad-brandschutz)

**Hinweis:** Dieser Check MUSS als erster Schritt in jeder Analyse-Pipeline laufen.
Bei KRITISCH-Issues setzt `IFCQualityHandler` `result.success=False` — Pipeline stoppt (FIX W-03).

---

### UC-03: Rettungsweglänge je Nutzungseinheit

**Norm:** ASR A2.3 § 5, MBO § 33

**Fachliche Grundlage:**
Die aktuelle Implementierung misst Gesamtlänge eines Fluchtweg-Layers.
Der normative Nachweis erfordert die **maximale Weglänge vom entferntesten Punkt
einer Nutzungseinheit bis zum nächsten Treppenraum-Eingang** — unabhängig von
Layer-Namensgebung.

**Grenzwerte:**
- Regelfall: ≤ 35 m (ohne Richtungsänderung)
- Mit Richtungsänderung: ≤ 60 m
- Wohngebäude GK 4/5: ≤ 35 m bis Treppenraum-Tür
- Versammlungsstätten: ≤ 30 m (VStättVO § 7)

**Eingabe:** `IFCModel` mit Raum-Geometrien + erkannte Treppenraum-Positionen

**Ausgabe:**
```python
# FIX B-02: ASCII-only; FIX B-04: Methode dokumentiert
@dataclass
class RettungswegNachweis:
    nutzungseinheit_name: str
    max_weglaenge_m: float          # B-02: kein Umlaut
    distanz_methode: str            # B-04: "KONSERVATIV_OBERGRENZE" | "DIJKSTRA"
    treppenraum_erreichbar: bool
    konform: bool
    grenzwert_m: float
    regelwerk: str                  # W-01: z.B. "ASR-A2.3-2022"
    norm_version: str               # W-01: Norm-Version als Pflichtfeld
```

**Implementierungsort:** `nl2cad/brandschutz/rettungsweg.py`

**FIX B-04 — Distanz-Methode:** Manhattan-Distanz ist rechtlich nicht verwendbar (systematisch
zu kurz bei realen Grundrissen). Milestone 1 nutzt **konservative Obergrenze**:
`max_weglaenge_m = max(Raumdiagonale_NE) + geschaetzte_Flurlänge`. Ergebnis
"konform" nur wenn Obergrenze ≤ Grenzwert — sicherer Fallback, kein false-positive.
Output wird als `beurteilungsstatus=VORPRUEFUNG` markiert (kein rechtsverbindlicher Nachweis).
Echte Dijkstra-Graphensuche in Milestone 2.

---

### UC-04: Zweiter Rettungsweg — Nachweis

**Norm:** MBO § 33 Abs. 1, LBO

**Fachliche Grundlage:**
Jede Nutzungseinheit benötigt **zwei voneinander unabhängige Rettungswege**.
Der zweite Rettungsweg kann sein:
1. Zweites notwendiges Treppenhaus
2. Außentreppe (mind. 1,20 m breit)
3. Anleitern durch die Feuerwehr (nur bis GK 4, max. 8 m UKFF)

**Prüflogik:**
```
Nutzungseinheit hat zweiten RW wenn:
  (Treppenräume_count ≥ 2 AND räumlich_getrennt)
  OR (Außentreppe erkannt AND Breite ≥ 1.20m)
  OR (GK ≤ 4 AND UKFF ≤ 8m AND kein_Hindernis_für_Feuerwehr)
```

**Ausgabe:**
```python
@dataclass
class ZweiterRettungswegNachweis:
    nutzungseinheit_name: str
    erster_rettungsweg: RettungswegNachweis
    zweiter_rettungsweg_typ: ZweiterRWTyp   # TREPPENHAUS, AUSSENTREPPE, ANLEITERN
    zweiter_rettungsweg_vorhanden: bool
    begruendung: str
    regelwerk: str
    norm_version: str               # W-01: z.B. "MBO-2016"
```

**Implementierungsort:** `nl2cad/brandschutz/rettungsweg.py` (Erweiterung UC-03)

---

### UC-05: Explosionsschutzdokument (ESD) — Generator

**Norm:** BetrSichV § 6 Abs. 9, TRBS 2152, EN 60079-10-1/-2

**Fachliche Grundlage:**
Das ESD ist ein **gesetzlich vorgeschriebenes Pflichtdokument** für jeden Betrieb
mit explosionsgefährdeten Bereichen. Fehlendes ESD = Ordnungswidrigkeit (§ 25 BetrSichV),
Bußgeld bis 30.000 €, im Wiederholungsfall Betriebsuntersagung.

**Minimalinhalt ESD nach BetrSichV Anhang 1:**

```python
@dataclass
class ExplosionsschutzDokument:
    betrieb_name: str
    erstellungsdatum: date
    erstellt_von: str
    naechste_pruefung: date

    # Pflichtinhalt §6 Abs.9 Nr.1: Gefährdungsbeurteilung
    gefaehrdungsbeurteilung: str
    explosionsfaehige_atmosphaere_moeglich: bool

    # Pflichtinhalt §6 Abs.9 Nr.2: Schutzziele
    ex_zonen: list[ExZoneDetail]

    # Pflichtinhalt §6 Abs.9 Nr.3: Schutzmaßnahmen
    schutzmassnahmen: list[Schutzmassnahme]

    # Pflichtinhalt §6 Abs.9 Nr.4: Geräte-Verzeichnis
    geraete: list[ExGeraet]

    # Pflichtinhalt §6 Abs.9 Nr.5: Koordinationsmaßnahmen
    koordinationsmassnahmen: list[str]

    # Abgeleitete Felder
    zonenplan_verfuegbar: bool
    lueftungsnachweis_verfuegbar: bool
    prueffristen: list[Prueffrist]

    def to_dict(self) -> dict: ...
    def is_vollstaendig(self) -> tuple[bool, list[str]]: ...

    # FIX B-05: Invarianten via __post_init__ — kein stilles Fallback
    def __post_init__(self) -> None:
        errors: list[str] = []
        if not self.betrieb_name.strip():
            errors.append("betrieb_name darf nicht leer sein")
        if self.naechste_pruefung <= self.erstellungsdatum:
            errors.append("naechste_pruefung muss nach erstellungsdatum liegen")
        if self.explosionsfaehige_atmosphaere_moeglich and not self.ex_zonen:
            errors.append(
                "ex_zonen muss befuellt sein wenn "
                "explosionsfaehige_atmosphaere_moeglich=True (BetrSichV §6 Abs.9 Nr.2)"
            )
        if errors:
            raise ValueError(f"ExplosionsschutzDokument ungueltig: {'; '.join(errors)}")
```

**ExZoneDetail — Pflichtfelder (FIX B-02 Umlaute + FIX W-02 Geraete-Kategorien getrennt):**

```python
# FIX B-02: lueftungsklasse statt lüftungsklasse
# FIX W-02: geraete_kategorie_min (Anforderung) getrennt von geraete_ist (Ist-Zustand)
@dataclass
class ExZoneDetail:
    zone: ExZone                         # Zone 0/1/2, Zone 20/21/22
    medium: ExMedium                     # GAS, DAMPF, NEBEL, STAUB, HYBRID
    quelle_beschreibung: str
    freisetzungsgrad: FreisetzungsGrad   # KONTINUIERLICH, PRIMAER, SEKUNDAER
    lueftungsklasse: LueftungsKlasse     # B-02: ASCII; K1 (gut), K2 (mittel), K3 (schlecht)
    ausdehnung_m: float                  # Zonenradius nach EN 60079-10-1 Tabelle
    etage: str
    raum_name: str
    geraete_kategorie_min: ExGeraeteKategorie  # W-02: Mindestanforderung (normativ)
    geraete_ist: list["ExGeraet"] = field(default_factory=list)  # W-02: Ist-Zustand
    norm_version: str = "EN-60079-10-1"  # W-01: Norm-Version

    @property
    def atex_konform(self) -> bool | None:
        """None wenn keine Ist-Geraete erfasst — kein stilles True."""
        if not self.geraete_ist:
            return None
        return all(g.kategorie <= self.geraete_kategorie_min for g in self.geraete_ist)
```

**Ausdehnung nach EN 60079-10-1 (vereinfacht):**

| Freisetzungsgrad | Lüftung K1 | Lüftung K2 | Lüftung K3 |
|-----------------|------------|------------|------------|
| Kontinuierlich  | Zone 0, 0.5 m | Zone 0, 1.0 m | Zone 0, 3.0 m |
| Primär          | Zone 1, 0.5 m | Zone 1, 1.0 m | Zone 1, 3.0 m |
| Sekundär        | Zone 2, 1.0 m | Zone 2, 2.0 m | Zone 2, 5.0 m |

**Implementierungsort:** `nl2cad/brandschutz/explosionsschutz/esd.py`

---

### UC-06: Brandschutzkonzept-Report

**Norm:** Musterbauordnung, landesspezifische Anforderungen

**Fachliche Grundlage:**
Das Lieferobjekt gegenüber Baubehörde und Prüfer. Ohne strukturierten,
nachvollziehbaren Report sind alle Analysen intern und nicht verwertbar.

**Struktur:**
```python
# FIX B-06: BeurteilungsStatus statt bool|None; FIX B-02: ASCII-only Typen
# FIX I-01: SonderbauTyp Enum statt str; FIX I-02/I-03: Nutzungseinheit + BauteilAnforderungen

class BeurteilungsStatus(str, Enum):
    """FIX B-06: Kein bool|None — expliziter Status, keine Rechtsaussage."""
    KEINE_KRITISCHEN_MAENGEL = "keine_kritischen_maengel"  # != baugenehmigungsfaehig!
    KRITISCHE_MAENGEL        = "kritische_maengel"
    NICHT_BEURTEILBAR        = "nicht_beurteilbar"         # explizit, kein None
    VORPRUEFUNG              = "vorpruefung"               # B-04: Milestone-1 Distanz


class SonderbauTyp(str, Enum):
    """FIX I-01: Enum statt hardcoded str."""
    KEINE             = "keine"
    VERSAMMLUNGSSTAETTE = "versammlungsstaette"
    SCHULE            = "schule"
    KRANKENHAUS       = "krankenhaus"
    TIEFGARAGE        = "tiefgarage"
    INDUSTRIEBAU      = "industriebau"


@dataclass
class BauteilAnforderungen:
    """FIX I-02: Explizit definiert."""
    wand_f_klasse: str       = ""   # z.B. "F90"
    decke_rei_klasse: str    = ""   # z.B. "REI90"
    treppenraum_f_klasse: str = ""  # z.B. "F90"
    trennwand_f_klasse: str  = ""   # Nutzungseinheiten-Trennung


@dataclass
class Nutzungseinheit:
    """FIX I-03: Explizit definiert."""
    name: str
    flaeche_m2: float
    din277_code: str
    etage: str
    rettungswegnachweise: list["ZweiterRettungswegNachweis"] = field(default_factory=list)


@dataclass
class BrandschutzkonzeptReport:
    # Metadaten
    projekt_name: str
    erstellt_am: date
    ifc_quelldatei: str
    ifc_qualitaet: "IFCQualityReport"    # W-04: aus nl2cad-core — explizit erlaubt

    # Gebaeude-Grunddaten
    gebaeudeklasse: GebaeudeklasseResult  # B-02: ASCII
    ist_sonderbau: bool
    sonderbau_typ: SonderbauTyp          # I-01: Enum

    # Nutzungseinheiten
    nutzungseinheiten: list[Nutzungseinheit]  # I-03

    # Bauteilanforderungen (aus GK abgeleitet)
    bauteilanforderungen: BauteilAnforderungen  # I-02

    # Rettungswege
    rettungswegnachweise: list[ZweiterRettungswegNachweis]

    # Brandschutzeinrichtungen
    einrichtungen: list[Brandschutzeinrichtung]

    # Maengel sortiert: KRITISCH -> WARNUNG -> INFO
    maengel: list[MaengelSchwere]

    # Explosionsschutz
    esd_erforderlich: bool
    ex_zonen: list[ExZoneDetail]

    # FIX B-06: Kein bool|None — expliziter Enum, keine Rechtsaussage
    beurteilungsstatus: BeurteilungsStatus
    beurteilungshinweis: str             # Pflicht: Begruendung des Status
    offene_nachweise: list[str]          # Was fehlt fuer volle Beurteilung

    def to_dict(self) -> dict: ...
    def kritische_maengel(self) -> list[BrandschutzMangel]: ...
```

**Implementierungsort:** `nl2cad/brandschutz/report.py`

---

## 4. Architektur-Entscheidungen

### 4.1 Modulstruktur (Zielzustand)

```
packages/nl2cad-brandschutz/src/nl2cad/brandschutz/
├── __init__.py
├── analyzer.py              # Haupt-Orchestrierung (bestehend, refaktorieren)
├── models.py                # Basis-Dataclasses (bestehend, erweitern)
├── report.py                # UC-06: BrandschutzkonzeptReport
├── ifc_quality.py           # UC-02: IFCQualityReport
├── gebaeudeklasse.py        # UC-01: GebäudeKlasseResult
├── rettungsweg.py           # UC-03 + UC-04: Rettungsweg-Nachweise
├── explosionsschutz/
│   ├── __init__.py
│   ├── esd.py               # UC-05: ESD-Generator
│   ├── zonen.py             # Zoneneinteilung + Ausdehnung
│   ├── geraete.py           # ATEX-Geräte-Kategorisierung
│   └── models.py            # ExZoneDetail, ExGeraet, Schutzmassnahme
├── rules/
│   ├── __init__.py
│   ├── asr_a23.py           # bestehend — Fluchtweg-Checks (Bugfix erforderlich)
│   ├── din4102.py           # bestehend — Feuerwiderstand
│   ├── mbo.py               # NEU: GK-Ableitung, Nutzungseinheiten
│   └── atex.py              # NEU: ATEX 2014/34/EU Geräte-Checks
└── constants.py             # FEHLT — aus nl2cad-core hierher verschieben
```

### 4.2 Pipeline-Integration

Jede vollständige Analyse läuft als `CADHandlerPipeline`:

```
IFCQualityHandler          # UC-02 — Abbruch bei KRITISCH
  → GebäudeKlasseHandler   # UC-01 — setzt GK im Context
    → RettungswegHandler    # UC-03/04 — nutzt GK für Grenzwerte
      → ExSchutzHandler     # UC-05 — nur wenn esd_erforderlich
        → ReportHandler     # UC-06 — sammelt alle Results
```

### 4.3 Abhängigkeits-Regel

```text
nl2cad-brandschutz darf IMPORTIEREN:
  nl2cad-core  (IFCModel, DXFModel, Exceptions, CADHandlerPipeline, IFCQualityReport)
  nl2cad-areas (DIN277Result fuer GK-Nutzungsableitung in UC-01)

nl2cad-brandschutz darf NICHT importieren:
  httpx, pydantic, Django ORM, Celery, Redis
  nl2cad-gaeb, nl2cad-nlp
```

**Korrektur gegenüber Status-quo:** Die bisher ungerechtfertigte `nl2cad-areas`-Abhängigkeit
wird durch UC-01 (GK-Ableitung aus DIN277-Nutzungsart) inhaltlich gerechtfertigt.

**FIX W-04 — Explizite Import-Erlaubnis:** `nl2cad-brandschutz` darf
`nl2cad.core.quality.IFCQualityReport` importieren und in `BrandschutzkonzeptReport`
einbetten. Dies ist eine bewusste Entscheidung: Core-Ergebnis wird im Domain-Report
aggregiert. Diese Erlaubnis gilt nur in eine Richtung (`brandschutz` → `core`).

### 4.4 Datenfluss IFC → Report

```text
IFCModel
  |
  +--> IFCQualityChecker (nl2cad-core)  --> IFCQualityReport
  |        [KRITISCH => Pipeline-Abbruch via result.success=False]
  |
  +--> DIN277Calculator (nl2cad-areas)  --> DIN277Result
  |        |
  |        +--> GebaeudeklasseAnalyzer  --> GebaeudeklasseResult
  |                  |
  |                  +--> BauteilAnforderungen
  |
  +--> BrandschutzAnalyzer              --> BrandschutzAnalyse
  |
  +--> RettungswegAnalyzer              --> list[ZweiterRettungswegNachweis]
  |
  +--> ExSchutzAnalyzer (wenn noetig)   --> ExplosionsschutzDokument
  |
  +--> ReportBuilder                    --> BrandschutzkonzeptReport
                                            (beurteilungsstatus: BeurteilungsStatus)
```

### 4.5 Datenbankschema — cad-hub (FIX B-01)

`nl2cad-brandschutz` ist eine reine Python-Library ohne Persistenz.
Die Persistenz liegt ausschließlich in `cad-hub` (Django + Postgres 16).
Folgendes Schema ist **Pflicht** für BetrSichV-konformes ESD und Audit-Trail:

```python
# cad-hub/apps/brandschutz/models.py
import hashlib
import json

from django.db import models


class BrandschutzAnalyseRecord(models.Model):
    """Persistiertes Ergebnis einer nl2cad-brandschutz Analyse."""

    # Multi-Tenancy Pflicht (global rule)
    tenant_id             = models.UUIDField(db_index=True)
    projekt               = models.ForeignKey(
        "projekte.Projekt", on_delete=models.PROTECT, related_name="brandschutz_analysen"
    )
    ifc_upload            = models.ForeignKey(
        "uploads.IFCUpload", on_delete=models.PROTECT
    )
    erstellt_am           = models.DateTimeField(auto_now_add=True)
    erstellt_von          = models.ForeignKey(
        "auth.User", on_delete=models.PROTECT, null=True
    )
    gebaeudeklasse        = models.CharField(max_length=20, db_index=True)  # "GK3"
    beurteilungsstatus    = models.CharField(max_length=40, db_index=True)  # BeurteilungsStatus
    report_json           = models.JSONField()           # BrandschutzkonzeptReport.to_dict()
    report_hash           = models.CharField(max_length=64, db_index=True)  # SHA-256
    hat_kritische_maengel = models.BooleanField(default=False, db_index=True)
    esd_erforderlich      = models.BooleanField(default=False)
    version               = models.PositiveIntegerField(default=1)  # optimistic locking

    class Meta:
        db_table = "brandschutz_analyse"
        indexes  = [
            models.Index(fields=["tenant_id", "projekt"]),
            models.Index(fields=["tenant_id", "hat_kritische_maengel"]),
            models.Index(fields=["tenant_id", "esd_erforderlich"]),
        ]

    def save(self, *args, **kwargs) -> None:
        # Idempotenter Hash: mehrfaches Speichern desselben Inhalts = gleicher Hash
        self.report_hash = hashlib.sha256(
            json.dumps(self.report_json, sort_keys=True).encode()
        ).hexdigest()
        super().save(*args, **kwargs)


class ExplosionsschutzDokumentRecord(models.Model):
    """Persistiertes ESD — append-only, unveraenderlich nach Erstellung."""

    tenant_id         = models.UUIDField(db_index=True)
    analyse           = models.ForeignKey(
        BrandschutzAnalyseRecord, on_delete=models.PROTECT,
        related_name="esd_records"
    )
    betrieb_name      = models.CharField(max_length=255)
    erstellt_am       = models.DateTimeField(auto_now_add=True)
    erstellt_von      = models.CharField(max_length=255)
    naechste_pruefung = models.DateField()
    esd_json          = models.JSONField()
    esd_hash          = models.CharField(max_length=64, unique=True)  # unveraenderlich
    ist_aktuell       = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "brandschutz_esd"
        indexes  = [models.Index(fields=["tenant_id", "ist_aktuell"])]

    def save(self, *args, **kwargs) -> None:
        if self.pk:
            # ESD ist append-only: kein Update erlaubt
            raise ValueError(
                "ExplosionsschutzDokumentRecord ist unveraenderlich (append-only). "
                "Erstelle einen neuen Record und setze ist_aktuell=False beim alten."
            )
        self.esd_hash = hashlib.sha256(
            json.dumps(self.esd_json, sort_keys=True).encode()
        ).hexdigest()
        super().save(*args, **kwargs)
```

**Migration-Idempotenz:** `python manage.py migrate --noinput` ist idempotent.
In `docker-compose.prod.yml` via `depends_on: db: condition: service_healthy` sicherstellen,
dass App erst startet wenn Migrations abgeschlossen.

---

## 5. Abgelehnte Alternativen

### Alt. A: Pydantic statt Dataclasses für Brandschutz-Models
**Abgelehnt.** `nl2cad-brandschutz` gehört zur `core/areas/gaeb/brandschutz`-Gruppe,
die ausschließlich stdlib-Dataclasses verwenden. Pydantic ist nur in `nl2cad-nlp` erlaubt.
Pydantic würde eine unnötige Abhängigkeit einführen und die Package-Grenze verletzen.

### Alt. B: Regelwerk-Checks als externe Konfiguration (YAML/JSON)
**Abgelehnt für Milestone 1.** Grenzwerte wie `MAX_FLUCHTWEG_LAENGE_M = 35.0` sind normativ
festgelegt und ändern sich selten. Konfigurierbarkeit wird in Milestone 3 evaluiert
(Stichwort: LBO-Varianten je Bundesland).

### Alt. C: Geometrie-Engine für echte Raumgraph-Navigation
**Zurückgestellt auf Milestone 2.** Milestone 1 nutzt vereinfachte Manhattan-Distanz für
Rettungsweglängen. Echte Graphensuche (Dijkstra über Raumgraph) erfordert vollständige
Türöffnungs-Geometrie aus IFC — Datenlage in realen IFC-Dateien oft unvollständig.

---

## 6. Ausblick — Folge-ADRs

### ADR-002: ATEX Vollimplementierung (Milestone 2)
- Automatische Zoneneinteilung aus `DIN277`-Raumkategorie + Nutzungsdaten
- Lüftungsnachweis-Berechnung nach TRBS 2152
- Geräte-Kategorisierung nach ATEX 2014/34/EU
- Ex-Zonen-Plan DXF-Export mit normativen Symbolen (EN 60079-10)
- Zündquellen-Inventar mit Freisetzungsgrad-Klassifikation

### ADR-003: Barrierefreiheit DIN 18040 (Milestone 2)
- Türbreiten-Check (≥ 0,90 m nach DIN 18040-1)
- Wendekreis-Nachweis (Ø 1,50 m)
- Rampenneigung (max. 6 %)
- Aufzugspflicht-Check nach GK und Geschossanzahl
- Integration in `BrandschutzkonzeptReport` als eigener Abschnitt

### ADR-004: Sonderbauten-Regelwerke (Milestone 3)
- Versammlungsstättenverordnung (VStättVO) — Ausgangbreiten, Personendichte
- GarVO — Tiefgaragen-Entrauchung, CO-Messung, Sprinkler-Pflicht
- IndBauR — Brandbekämpfungsabschnitte bis 18.000 m²
- KhBauVO — Krankenhäuser (Bettenstationen, OP-Bereiche)
- SchulbauR — Schulen und Kindergärten

### ADR-005: Brandschutzkonzept PDF-Export (Milestone 3)
- `BrandschutzkonzeptReport.to_dict()` → strukturierter PDF-Output
- Integration mit `nl2cad-gaeb` für Kostenermittlung Brandschutzmaßnahmen
- Baugenehmigungsunterlagen-Vollständigkeitsprüfung je Bundesland

---

## 7. Nicht-Ziele dieses ADR

- **Statische Berechnungen** (Tragwerk, Lasten) → eigenes Package `nl2cad-statik`
- **Energieeinsparnachweis** (EnEV/GEG) → `nl2cad-energie`
- **Schallschutz** (DIN 4109) → `nl2cad-schallschutz`
- **LBO-spezifische Varianten** (16 Bundesländer) → Milestone 3, konfigurierbare Regelwerke
- **Behörden-Schnittstellen** (XPlanung, XBau) → `cad-hub`-Verantwortung

---

## 8. Konsequenzen

### Positive Konsequenzen
- **Rechtssicherheit:** ESD-Generator erfüllt BetrSichV §6 Pflichtdokumentation
- **Vollständigkeit:** GK-Ermittlung macht alle Brandschutz-Checks fachlich korrekt
- **Vertrauenswürdigkeit:** IFC-Quality-Check verhindert stille 0-Werte in Analysen
- **Lieferfähigkeit:** `BrandschutzkonzeptReport` ist unmittelbar an Behörden übergabefähig
- **Kohärenz:** `nl2cad-areas`-Abhängigkeit wird durch UC-01 inhaltlich gerechtfertigt

### Negative Konsequenzen / Risiken
- **Komplexität steigt:** `nl2cad-brandschutz` wird das umfangreichste Package
  → Dateigröße-Limit 500 Zeilen je Modul strikt einhalten, `explosionsschutz/` als Subpackage
- **IFC-Datenqualität:** Viele reale IFC-Dateien liefern keine vollständigen Geometrien
  für Rettungsweglängen-Berechnung → UC-02 (Quality-Check) ist Pflicht-Voraussetzung
- **Normänderungen:** MBO/ASR/TRBS ändern sich — Grenzwerte in `constants.py`
  mit Norm-Version und Datum versionieren

---

## 9. Implementierungs-Reihenfolge (Milestone 1)

**FIX W-06: Bug-Fixes zuerst — sonst laufen alle Tests auf defektem Input.**

```text
1.  BUG-FIX: ifc_parser.py   — bare-except entfernen, number-Feld korrigieren
2.  BUG-FIX: asr_a23.py      — _check_notausgang aus Schleife herausziehen
3.  nl2cad-core/quality.py   — IFCQualityChecker, IFCQualityReport, IFCQualityIssue
4.  nl2cad-core/__init__.py  — IFCQualityReport, IFCQualityIssue in __all__ ergaenzen
5.  nl2cad-brandschutz/constants.py — Norm-Versionen + Grenzwerte mit Quellenangabe
6.  nl2cad-brandschutz/gebaeudeklasse.py — GebaeudeklasseResult, Gebaeudeklasse Enum
7.  nl2cad-brandschutz/rettungsweg.py   — RettungswegNachweis (KONSERVATIV_OBERGRENZE)
8.  nl2cad-brandschutz/explosionsschutz/models.py — ExZoneDetail, ExGeraet
9.  nl2cad-brandschutz/explosionsschutz/esd.py    — ExplosionsschutzDokument
10. nl2cad-brandschutz/report.py                  — BrandschutzkonzeptReport
11. nl2cad-brandschutz/analyzer.py refaktorieren  — Pipeline-Integration
12. cad-hub/apps/brandschutz/models.py            — DB-Schema (B-01)
13. cad-hub migrations                            — makemigrations + migrate
14. .github/workflows/ci.yml                      — CI-Workflow (W-05)
15. tests/fixtures/                               — Minimal-IFC + Minimal-DXF
16. Tests: je UC min. 5 Tests, coverage >= 80%
```
