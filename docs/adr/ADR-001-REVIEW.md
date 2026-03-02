# ADR-001 — Kritischer Review

| Attribut        | Wert                                                          |
| --------------- | ------------------------------------------------------------- |
| **Review von**  | IT-Architekt / Brandschutzexperte / Explosionsschutzexperte   |
| **Datum**       | 2026-03-01                                                    |
| **ADR**         | ADR-001 nl2cad-brandschutz v1.0                               |
| **Urteil**      | ⚠️ BEDINGT AKZEPTIERT — 6 BLOCKING ISSUES vor Implementierung |

Vorgaben: Django + HTMX + Postgres 16 (persistent, separat) auf Hetzner VMs via Docker.
Qualitätskriterien: datenbankgetrieben, konsequente Normalisierung, Separation of Concerns,
Naming Conventions, kein magisches Verhalten, robustes Error Handling, Idempotenz.

---

## BLOCKING — muss vor Implementierungsstart behoben sein

---

### B-01: Kein Datenbankmodell definiert — Library produziert flüchtige Objekte

**Befund:**
Das ADR definiert ausschließlich Python-Dataclasses mit `to_dict()`. Es gibt kein einziges
Datenbankmodell, keine Migration, keine Persistenzschicht. `BrandschutzkonzeptReport`,
`ExplosionsschutzDokument` und `IFCQualityReport` sind flüchtige In-Memory-Objekte.

`cad-hub` (Django + Postgres 16) ist der einzige Downstream-Konsument — aber das ADR
schweigt vollständig darüber, wie die Ergebnisse persistiert, versioniert und auditiert werden.

**Risiko:** KRITISCH
- Behördliche Nachvollziehbarkeit (BetrSichV § 6: ESD muss "aktuell gehalten" werden)
  ist ohne Persistenz nicht gegeben.
- Jede Re-Analyse überschreibt das vorherige Ergebnis ohne Versionshistorie.
- `to_dict()` als einzige Serialisierung ist nicht ausreichend für Postgres JSONB + Audit-Trail.
- Ein ESD ohne unveränderliche Signatur/Hash ist rechtlich angreifbar.

**Empfehlung:**
Das ADR muss ein explizites Datenbankschema für `cad-hub` definieren — entweder als
eigenständiges Sub-ADR oder als Abschnitt 4.5. Mindestanforderung:

```python
# cad-hub/apps/brandschutz/models.py  (NICHT in nl2cad-brandschutz!)

class BrandschutzAnalyse(models.Model):
    """Persistiertes Ergebnis einer nl2cad-brandschutz Analyse."""
    tenant_id        = models.UUIDField(db_index=True)              # Multi-Tenancy Pflicht
    projekt          = models.ForeignKey("Projekt", on_delete=models.PROTECT)
    ifc_upload       = models.ForeignKey("IFCUpload", on_delete=models.PROTECT)
    erstellt_am      = models.DateTimeField(auto_now_add=True)
    gebaeudeklasse   = models.CharField(max_length=20)              # "GK3", "GK5", "SONDERBAU"
    report_json      = models.JSONField()                           # BrandschutzkonzeptReport.to_dict()
    report_hash      = models.CharField(max_length=64)              # SHA-256 für Audit
    hat_kritische_maengel = models.BooleanField(db_index=True)
    esd_erforderlich = models.BooleanField(default=False)
    version          = models.PositiveIntegerField(default=1)       # optimistic locking

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "projekt"]),
            models.Index(fields=["tenant_id", "hat_kritische_maengel"]),
        ]

class ExplosionsschutzDokumentRecord(models.Model):
    """Persistiertes ESD — unveränderlich nach Erstellung (append-only)."""
    tenant_id        = models.UUIDField(db_index=True)
    analyse          = models.ForeignKey(BrandschutzAnalyse, on_delete=models.PROTECT)
    betrieb_name     = models.CharField(max_length=255)
    erstellt_am      = models.DateTimeField(auto_now_add=True)
    erstellt_von     = models.CharField(max_length=255)
    naechste_pruefung = models.DateField()
    esd_json         = models.JSONField()
    esd_hash         = models.CharField(max_length=64, unique=True)  # unveränderlich
    ist_aktuell      = models.BooleanField(default=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["tenant_id", "ist_aktuell"])]
```

---

### B-02: `GebäudeKlasseResult` — Umlaut im Klassennamen, verletzt Naming Convention

**Befund:**
```python
class GebäudeKlasseResult:   # ← ä in Klassenname
class GebäudeKlasse:         # ← ä in Enum
class GebäudeNutzung:        # ← ä in Enum
```
Analog in `ExZoneDetail`:
```python
lüftungsklasse: LüftungsKlasse   # ← ü in Feldname und Typ
```
AGENTS.md schreibt PascalCase für Klassen und snake_case für Felder vor — keine Umlaute.
Python 3 erlaubt Umlaute syntaktisch, aber: ruff, mypy, Postgres-Migrations, Django-ORM
und alle Shell-Skripte haben Encoding-Probleme mit nicht-ASCII-Bezeichnern.

**Risiko:** HOCH
- Postgres-Migration scheitert auf Hetzner-VM mit `LC_ALL=C` wenn ORM-Reflection genutzt wird.
- `ruff check` markiert non-ASCII-Identifier als Warnung (UP031).
- Downstream-Konsumenten (cad-hub) importieren Klassen mit Umlauten — Copy-Paste-Fehler garantiert.

**Empfehlung:** Konsequent ASCII-only. Vollständige Ersetzungsliste:

```python
# FALSCH → RICHTIG
GebäudeKlasseResult  → GebaeudeklasseResult
GebäudeKlasse        → Gebaeudeklasse
GebäudeNutzung       → GebaeudeNutzung
LüftungsKlasse       → LueftungsKlasse
lüftungsklasse       → lueftungsklasse
max_weglänge_m       → max_weglaenge_m
MängelSchwere        → MaengelSchwere   # bereits in models.py — konsistent halten
```

Das ADR muss diese Konvention explizit in Abschnitt 4 festschreiben und als
Invariante für alle Folge-ADRs gelten.

---

### B-03: `IFCQualityChecker` falsch platziert — verletzt Separation of Concerns

**Befund:**
UC-02 (`IFCQualityChecker`) ist in `nl2cad/brandschutz/ifc_quality.py` platziert.
Das bedeutet: IFC-Qualitätsprüfung ist eine Abhängigkeit von `nl2cad-brandschutz`.
Jedes andere Package (`nl2cad-areas`, `nl2cad-gaeb`) das IFC-Daten verarbeitet, muss
dann `nl2cad-brandschutz` importieren — **zirkuläre Abhängigkeit im Entstehen**.

```
nl2cad-areas  → nl2cad-core          ✅ (korrekt)
nl2cad-gaeb   → nl2cad-core          ✅ (korrekt)
nl2cad-areas  → nl2cad-brandschutz   ❌ (wenn Quality-Check Pflicht wird)
```

**Risiko:** KRITISCH — Architekturbruch, der mit wachsender Codebasis nicht mehr rückgängig zu machen ist.

**Empfehlung:**
`IFCQualityChecker` gehört in `nl2cad-core`:

```
packages/nl2cad-core/src/nl2cad/core/
└── quality.py    # IFCQualityChecker, IFCQualityReport, IFCQualityIssue
```

Das ADR muss Abschnitt 4.1 und 4.3 entsprechend korrigieren:
```
nl2cad-core (NEW): quality.py — IFCQualityChecker
  ← importiert von nl2cad-brandschutz, nl2cad-areas, nl2cad-gaeb
```

---

### B-04: Manhattan-Distanz für Rettungsweglänge ist rechtlich nicht verwendbar

**Befund:**
Abschnitt UC-03: *"Vereinfachte Manhattan-Distanz wenn keine vollständige
Raumgraph-Navigation verfügbar."*

Manhattan-Distanz misst `|Δx| + |Δy|` — das ist die Distanz entlang Achsen, nicht
entlang tatsächlicher Gehwege. In einem Gebäude mit Wänden, Türen und Fluren ist die
Manhattan-Distanz **systematisch zu kurz** (keine Wände berücksichtigt) oder
**systematisch zu lang** (direkte Luftlinie wäre kürzer).

Ein konformer Brandschutz-Nachweis nach ASR A2.3 § 5 basiert auf der
**tatsächlichen Gehweglänge** — nicht auf einer geometrischen Approximation.

**Risiko:** KRITISCH — rechtlich
- Ergebnis "konform" bei Manhattan-Distanz = 33 m kann tatsächliche Gehweglänge
  von 48 m bedeuten → Brandschutzmangel nicht erkannt → Haftungsrisiko.
- Ein Sachverständiger wird diese Methode nicht akzeptieren.
- Das ADR labelt dies als "Einschränkung" — aber es ist ein **disqualifizierender Fehler**
  für produktiven Einsatz.

**Empfehlung:**
Zwei Optionen — eine muss ins ADR als verbindliche Entscheidung:

**Option A (Milestone 1 tauglich):** Konservative Überschätzung statt Manhattan.
Nutze `max(Raumdiagonale aller Räume in NE) + Flurkorridorlänge` als Obergrenze.
Ergebnis "konform" nur wenn Obergrenze ≤ Grenzwert. **Sicherer Fallback, rechtlich vertretbar.**

**Option B (Milestone 2):** Echter Raumgraph aus `IfcRelSpaceBoundary` oder
DXF-Türöffnungen → Dijkstra-Suche. Korrekt, aber IFC-Datenqualität-abhängig.

Das ADR muss explizit festhalten: *"Milestone 1 liefert keinen rechtsverbindlichen
ASR A2.3-Nachweis — Output ist als Vorprüfung zu kennzeichnen."*

---

### B-05: `ExplosionsschutzDokument` — stille Fehlzustände, kein Invarianten-Schutz

**Befund:**
```python
@dataclass
class ExplosionsschutzDokument:
    zonenplan_verfuegbar: bool
    lueftungsnachweis_verfuegbar: bool
    ...
    def is_vollstaendig(self) -> tuple[bool, list[str]]: ...
```

Das Dokument kann instanziiert werden mit `zonenplan_verfuegbar=False` und
`ex_zonen=[]` — also ein leeres, unvollständiges ESD. `is_vollstaendig()` ist
eine nachträgliche Prüfung, kein struktureller Schutz.

Nach BetrSichV § 6 Abs. 9 ist ein unvollständiges ESD **kein ESD** — es darf nicht
existieren oder weitergegeben werden. Der Code erlaubt genau das.

**Risiko:** HOCH
- `cad-hub` könnte ein unvollständiges ESD persistieren und dem Nutzer präsentieren.
- Kein Compile-Time-Schutz, kein Exception bei fehlenden Pflichtfeldern.
- "Magisches Verhalten" durch bool-Flags statt harter Invarianten.

**Empfehlung:**
Pflichtfelder ohne Default-Wert, explizite Factory-Methode mit Validierung:

```python
@dataclass
class ExplosionsschutzDokument:
    # Pflichtfelder ohne Default — TypeError bei Weglassen ist gewollt
    betrieb_name: str
    erstellungsdatum: date
    erstellt_von: str
    naechste_pruefung: date
    gefaehrdungsbeurteilung: str
    explosionsfaehige_atmosphaere_moeglich: bool
    ex_zonen: list[ExZoneDetail]          = field(default_factory=list)
    schutzmassnahmen: list[Schutzmassnahme] = field(default_factory=list)
    geraete: list[ExGeraet]               = field(default_factory=list)
    koordinationsmassnahmen: list[str]    = field(default_factory=list)
    prueffristen: list[Prueffrist]        = field(default_factory=list)

    def __post_init__(self) -> None:
        """Invarianten-Check — kein stilles Fallback."""
        errors: list[str] = []
        if not self.betrieb_name.strip():
            errors.append("betrieb_name darf nicht leer sein")
        if self.naechste_pruefung <= self.erstellungsdatum:
            errors.append("naechste_pruefung muss nach erstellungsdatum liegen")
        if self.explosionsfaehige_atmosphaere_moeglich and not self.ex_zonen:
            errors.append(
                "ex_zonen muss befüllt sein wenn "
                "explosionsfaehige_atmosphaere_moeglich=True (BetrSichV §6 Abs.9 Nr.2)"
            )
        if errors:
            raise ValueError(
                f"ExplosionsschutzDokument ungültig: {'; '.join(errors)}"
            )
```

---

### B-06: `BrandschutzkonzeptReport.baugenehmigungsfaehig: bool | None` — magischer Zustand

**Befund:**
```python
baugenehmigungsfaehig: bool | None   # None = nicht beurteilbar
```

`None` als semantischer Zustand ("nicht beurteilbar") ist magisches Verhalten.
Downstream-Code in `cad-hub` muss `if report.baugenehmigungsfaehig is None` prüfen —
wird vergessen, führt zu `TypeError` oder falschem `False`.

Zusätzlich: "baugenehmigungsfähig" ist **keine Aussage die ein Algorithmus treffen darf**.
Das ist eine Entscheidung des Sachverständigen / der Baubehörde. Der Code suggeriert
eine Rechtsaussage die er fachlich nicht leisten kann.

**Risiko:** HOCH — rechtlich und technisch
- Haftungsrisiko: Software "bescheinigt" Baugenehmigungsfähigkeit.
- `None`-Propagation durch cad-hub Templates (HTMX-Rendering) erzeugt stille Leerfelder.

**Empfehlung:**
Enum statt `bool | None`, fachlich korrekter Begriff:

```python
class BeurteilungsStatus(str, Enum):
    KEINE_KRITISCHEN_MAENGEL = "keine_kritischen_maengel"   # ≠ "baugenehmigungsfähig"!
    KRITISCHE_MAENGEL        = "kritische_maengel"
    NICHT_BEURTEILBAR        = "nicht_beurteilbar"          # explizit, kein None
    VORPRUEFUNG              = "vorpruefung"                # Milestone 1: Manhattan-Distanz

@dataclass
class BrandschutzkonzeptReport:
    ...
    beurteilungsstatus: BeurteilungsStatus   # ersetzt baugenehmigungsfaehig: bool | None
    beurteilungshinweis: str                 # Pflichtfeld: Begründung des Status
```

---

## WARNING — sollte vor Milestone-1-Abschluss behoben sein

---

### W-01: Keine Versionierung von Normen und Grenzwerten

**Befund:**
`MAX_FLUCHTWEG_LAENGE_M = 35.0` in `asr_a23.py` ohne Norm-Version und Gültigkeitsdatum.
ASR A2.3 wurde 2022 aktualisiert. Grenzwerte können sich ändern (z.B. LBO-Varianten).
Das ADR erwähnt das Problem, definiert aber keine Lösung.

**Risiko:** MITTEL — Norm-Update → stiller Fehler in Produktion.

**Empfehlung:**

```python
# nl2cad/brandschutz/constants.py
# Jede Konstante trägt Norm, Paragraf und Gültigkeitsdatum als Kommentar

# ASR A2.3 (Ausgabe: März 2022, GMBI 2022 S. 350)
MAX_FLUCHTWEG_LAENGE_M: float = 35.0          # § 5 Abs. 1
MAX_FLUCHTWEG_LAENGE_MIT_ABZWEIG_M: float = 60.0  # § 5 Abs. 2
MIN_BREITE_STANDARD_M: float = 0.875          # § 4 Abs. 2 Tab. 1
ASR_A23_VERSION: str = "2022-03"              # Pflichtfeld für Report-Metadaten

# MBO (Musterbauordnung 2002, Fassung 2016)
MBO_GK4_MAX_OKFF_M: float = 13.0             # § 2 Abs. 3 Nr. 4
MBO_GK5_HOCHHAUS_OKFF_M: float = 22.0        # § 2 Abs. 8 Nr. 1
MBO_VERSION: str = "2016"
```

---

### W-02: `ExZoneDetail.geraete_kategorie` — Einzelwert statt Liste

**Befund:**
```python
geraete_kategorie: ExGeraeteKategorie   # KAT1, KAT2, KAT3
```

Eine Ex-Zone hat nicht eine einzige Gerätekategorie. Nach ATEX 2014/34/EU kann
eine Zone 1 sowohl Kategorie-1G-Geräte (erlaubt) als auch Kategorie-3G-Geräte
(nicht erlaubt) enthalten. Das Datenmodell muss die **Anforderungskategorie** (Minimum)
von der **vorhandenen Kategorie** (Ist-Zustand) trennen.

**Risiko:** MITTEL — falsche ATEX-Prüfung, übersehene Nicht-Konformität.

**Empfehlung:**

```python
@dataclass
class ExZoneDetail:
    ...
    # Pflicht: Mindestanforderung aus Zone (normativ festgelegt)
    geraete_kategorie_min: ExGeraeteKategorie   # Zone 0→KAT1, Zone 1→KAT2, Zone 2→KAT3
    # Optional: tatsächlich vorhandene Geräte (aus IFC oder manuell)
    geraete_ist: list[ExGeraet] = field(default_factory=list)

    @property
    def atex_konform(self) -> bool | None:
        """None wenn keine Ist-Geräte erfasst."""
        if not self.geraete_ist:
            return None
        return all(g.kategorie <= self.geraete_kategorie_min for g in self.geraete_ist)
```

---

### W-03: Pipeline-Abbruchstrategie inkonsistent mit `CADHandlerPipeline`

**Befund:**
ADR Abschnitt 4.2: *"IFCQualityHandler — Abbruch bei KRITISCH"*

`CADHandlerPipeline` in `nl2cad-core` stoppt bei `continue_on_error=False` wenn
`result.success=False`. UC-02 erzeugt aber ein `IFCQualityReport` mit `is_valid=False` —
das ist ein **valides Ergebnis** (kein Exception), kein `HandlerError`.

Die Pipeline würde also **nicht abbrechen**, weil kein `success=False` gesetzt wird,
sondern weil `IFCQualityReport.is_valid=False` ist. Das ist ein Schnittstellenmissverständnis.

**Risiko:** MITTEL — Pipeline läuft weiter trotz ungültigem IFC → alle nachfolgenden
Handler produzieren wertlose Ergebnisse mit 0-Werten.

**Empfehlung:**
`IFCQualityHandler.execute()` muss explizit `result.success = False` setzen
bei KRITISCH-Issues und `HandlerError` nicht schlucken:

```python
class IFCQualityHandler(BaseCADHandler):
    name = "IFCQualityHandler"
    required_inputs = ["ifc_model"]

    def execute(self, input_data: dict) -> HandlerResult:
        result = HandlerResult(success=True, handler_name=self.name)
        model: IFCModel = input_data["ifc_model"]
        checker = IFCQualityChecker()
        quality = checker.check(model)
        result.data["ifc_quality"] = quality

        kritisch = [i for i in quality.issues if i.severity == "KRITISCH"]
        if kritisch:
            for issue in kritisch:
                result.add_error(f"[IFC-Quality] {issue.field_path}: {issue.message}")
            # add_error setzt result.success=False → Pipeline stoppt
        return result
```

---

### W-04: `BrandschutzkonzeptReport` enthält `IFCQualityReport` direkt — verletzt Single Source of Truth

**Befund:**
```python
class BrandschutzkonzeptReport:
    ifc_qualitaet: IFCQualityReport
```

Wenn `IFCQualityReport` in `nl2cad-core` liegt (Empfehlung B-03) und
`BrandschutzkonzeptReport` in `nl2cad-brandschutz`, entsteht eine zirkuläre
oder unerwünschte Kopplung: `nl2cad-brandschutz` importiert das Ergebnis eines
`nl2cad-core`-Checks in seinem Top-Level-Report.

Das ist architektonisch korrekt (core ← brandschutz ist erlaubt), aber das ADR
dokumentiert es nicht explizit als bewusste Entscheidung.

**Risiko:** NIEDRIG bis MITTEL — kein Fehler, aber unklare Intention für zukünftige
Entwickler führt zu falschen Imports.

**Empfehlung:**
Abschnitt 4.3 ergänzen:

```text
EXPLIZITE IMPORT-ERLAUBNIS:
nl2cad-brandschutz darf nl2cad-core.quality.IFCQualityReport importieren
und in BrandschutzkonzeptReport einbetten — dies ist gewollt (Core-Ergebnis
im Domain-Report aggregieren).
```

---

### W-05: Keine Docker/CI-Integration definiert — Deployment-Lücke

**Befund:**
Das ADR behandelt ausschließlich die Python-Library. Es fehlen:
- Kein `.github/workflows/ci.yml` (README zeigt Badge auf nicht-existierende Datei)
- Keine Definition wie `nl2cad-brandschutz` in `cad-hub`s Docker-Image landet
- Keine Migration-Strategie für Postgres 16 wenn Datenbankmodelle (B-01) hinzukommen
- Kein Health-Check-Endpunkt für `cad-hub` der nl2cad-Version meldet

**Risiko:** MITTEL — Deployment auf Hetzner scheitert oder ist manuell.

**Empfehlung:**
Als minimales CI-Workflow-Template für das Repo:

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Install dependencies
        run: uv sync --all-packages

      - name: Ruff lint
        run: uv run ruff check packages/

      - name: Mypy
        run: uv run mypy packages/

      - name: Pytest with coverage
        run: uv run pytest --cov=packages --cov-report=xml --cov-fail-under=80

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
```

Für `cad-hub` Dockerfile-Integration (Dependency Install aus PyPI oder local editable):

```dockerfile
# docker/app/Dockerfile (cad-hub)
# nl2cad-Packages aus PyPI (nach Release) oder lokal (Entwicklung)
RUN pip install nl2cad-core nl2cad-areas nl2cad-brandschutz nl2cad-gaeb
```

Migration-Idempotenz-Sicherung in `docker-compose.prod.yml`:

```yaml
# Healthcheck verhindert App-Start vor Migrations-Abschluss
web:
  depends_on:
    db:
      condition: service_healthy
  command: >
    sh -c "python manage.py migrate --noinput &&
           gunicorn cadhub.wsgi:application --bind 0.0.0.0:8000"
```

---

### W-06: Implementierungs-Reihenfolge Schritt 8 (Bug-Fixes) zu spät

**Befund:**
```
8. Bug-Fixes: asr_a23.py (_check_notausgang), ifc_parser.py (bare except, number-Feld)
```

Die bekannten Bugs in `ifc_parser.py` (`bare except: pass`, falsches `number`-Feld)
betreffen den **Input** aller UC-01 bis UC-06. Bug-Fixes nach der Implementierung
der Use-Cases bedeutet: alle Tests in Schritt 9 laufen auf buggy Input-Daten.

**Risiko:** MITTEL — Tests bestehen zufällig oder schlagen falsch an.

**Empfehlung:** Bug-Fixes auf Schritt 1 vorziehen:

```text
1. Bug-Fixes: ifc_parser.py + asr_a23.py   ← ZUERST
2. constants.py anlegen
3. ifc_quality.py (UC-02)
...
```

---

## INFO — nice-to-have, kein Blocker

---

### I-01: `sonderbau_typ: str` sollte Enum sein

`str` für `sonderbau_typ` ("Versammlungsstätte", "Schule") ist ein implizites Enum.
Hardcoded Strings in Business-Logik sind laut AGENTS.md verboten.
→ `SonderbauTyp(str, Enum)` mit Konstanten in `constants.py`.

### I-02: `BauteilAnforderungen` nicht definiert

Das ADR referenziert `BauteilAnforderungen` in UC-01 und UC-06, definiert aber
nirgends die Struktur. Für Folge-Entwickler ist unklar was diese Klasse enthält.
→ Dataclass-Skeleton im ADR ergänzen: `wand_f_klasse`, `decke_rei_klasse`, `treppenraum_f_klasse`.

### I-03: `Nutzungseinheit` nicht definiert

`nutzungseinheiten: list[Nutzungseinheit]` in UC-06 — Klasse nirgends definiert.
→ Skeleton ergänzen: `name`, `flaeche_m2`, `din277_code`, `etage`, `rettungswegnachweise`.

### I-04: GK-Tabelle im ADR unvollständig — GK1 und GK2 überlappen

Die GK-Tabelle in UC-01 listet GK1 als Teilmenge von GK2. Das stimmt mit MBO §2
überein (GK2 schließt freistehende Gebäude ≤ 2 NE ≤ 7m ein, GK1 ist die engere
Teilmenge). Das Algorithmus-Design muss GK1 vor GK2 prüfen (First-Match-Logik).
Das ADR dokumentiert die Prüfreihenfolge nicht. → Explizit ergänzen.

---

## Gesamtbewertung

| Kategorie                | Befund                                              |
| ------------------------ | --------------------------------------------------- |
| **Architekturkonformität** | ⚠️ Verletzt durch IFCQualityChecker-Platzierung (B-03) |
| **Invarianten**           | ❌ Fehlen bei ESD (B-05), bool\|None (B-06)         |
| **Seiteneffekte**         | ⚠️ Pipeline-Abbruch inkonsistent (W-03)             |
| **Migrationsrisiken**     | ❌ Kein DB-Schema, keine Migration (B-01)           |
| **Naming Conventions**    | ❌ Umlaute in Klassennamen (B-02)                   |
| **Kein magisches Verhalten** | ❌ bool\|None, Manhattan-Distanz ohne Kennzeichnung (B-04, B-06) |
| **Error Handling**        | ⚠️ Stille Fallbacks durch bool-Flags (B-05)        |
| **Idempotenz**            | ⚠️ Nicht adressiert (W-05)                         |
| **Rechtliche Belastbarkeit** | ❌ Manhattan-Distanz (B-04), "baugenehmigungsfähig" (B-06) |

**Entscheidung: NICHT FREIGEGEBEN für Implementierungsstart.**

B-01, B-02, B-03, B-05, B-06 müssen im ADR korrigiert werden.
B-04 muss als explizite Limitation mit Vorprüfungs-Kennzeichnung dokumentiert werden.
Danach: Re-Review vor Implementierungsstart.
