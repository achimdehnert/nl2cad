# ADR-001 — Kritischer Review 2 (nach Rev1-Korrekturen)

| Attribut        | Wert                                                             |
| --------------- | ---------------------------------------------------------------- |
| **Review von**  | IT-Architekt / Brandschutzexperte / Explosionsschutzexperte      |
| **Datum**       | 2026-03-01                                                       |
| **Basis**       | ADR-001 Rev2 + Code-Stand nach Review-1-Korrekturen              |
| **Urteil**      | BEDINGT FREIGEGEBEN — 3 neue BLOCKING + 4 WARNING nach Rev1      |

Scope: Tiefenprüfung der Rev1-Fixes und des tatsächlichen Code-Stands.
Rev1-Blocking-Issues B-01..B-06 sind im ADR dokumentiert — aber der **Code**
weist noch kritische Abweichungen vom ADR auf.

---

## BLOCKING — Code-Realität vs. ADR-Spezifikation

---

### B-07: `MängelSchwere` — Umlaut-Residuum in produktivem Code

**Befund:**
Rev1 hat Umlaute in *ADR-Dataclasses* behoben, aber der **produktive Code**
`models.py` und `asr_a23.py` enthält noch:

```python
# models.py:33
class MängelSchwere(str, Enum):   # ← ä im Klassennamen

# models.py:91
schwere: MängelSchwere = MängelSchwere.WARNUNG

# asr_a23.py:18
from nl2cad.brandschutz.models import (
    ...
    MängelSchwere,                # ← importiert Umlaut-Klasse
)
```

Das ADR (Rev2) schreibt `MaengelSchwere` vor — Review-1-Befund B-02 wurde
im ADR korrigiert, aber **nicht im Code**. Das ist der gefährlichste Fehlertyp:
ADR und Code sind divergent. Jedes neue Modul das das ADR als Referenz nutzt,
importiert eine nicht-existierende Klasse.

**Risiko:** KRITISCH
- Ruff `UP031` bei strenger Konfiguration: non-ASCII identifier
- Auf Hetzner VM mit `LANG=C` oder `LC_ALL=C.UTF-8` kann der Import fehlschlagen
- `mypy --strict` läuft durch, aber `grep MängelSchwere` in Bash-Skripten schlägt fehl
- Neue Module die `MaengelSchwere` (ADR-konform) importieren, erhalten `ImportError`

**Empfehlung:**
```bash
# Prüfen (WSL):
grep -r "MängelSchwere\|feuerlöscher\|MängelSchwere" \
  packages/nl2cad-brandschutz/src/ --include="*.py" -l
```

Rename in `models.py` und alle Imports:
```python
# models.py — vorher: MängelSchwere, nachher: MaengelSchwere
class MaengelSchwere(str, Enum):
    INFO     = "info"
    WARNUNG  = "warnung"
    KRITISCH = "kritisch"
```

Alle abhängigen Dateien (`asr_a23.py`, `analyzer.py`, `din4102.py`):
```python
from nl2cad.brandschutz.models import MaengelSchwere
```

---

### B-08: `IFCQualityChecker.check()` — TYPE_CHECKING-Import bricht Runtime

**Befund:**
```python
# quality.py:18-19
if TYPE_CHECKING:
    from nl2cad.core.models import IFCModel

# quality.py:95
def check(self, model: IFCModel) -> IFCQualityReport:
```

`IFCModel` ist nur unter `TYPE_CHECKING` importiert — das bedeutet: zur Laufzeit
ist `IFCModel` **nicht** im Namespace. Mit `from __future__ import annotations`
(PEP 563) funktioniert das für Typ-Annotationen, aber:

1. `model.floors`, `model.all_rooms` werden zur Laufzeit aufgerufen — das funktioniert
   (Duck Typing), aber mypy kann nicht verifizieren, dass das übergebene Objekt
   tatsächlich `IFCModel` ist.
2. `isinstance(model, IFCModel)` in zukünftigem Code würde `NameError` werfen.
3. Der Docstring `raise IFCParseError(...)` im Beispiel referenziert einen Import
   der nie stattfindet.

Hintergrund: `IFCModel` ist in `nl2cad.core.models` — `quality.py` ist ebenfalls
in `nl2cad.core`. Das ist ein **interner Import innerhalb desselben Packages**.
Es gibt keinen Grund für `TYPE_CHECKING` — das erzeugt nur falsche Sicherheit.

**Risiko:** HOCH
- Zukünftige Entwickler fügen `isinstance`-Checks hinzu und erhalten `NameError`
- mypy-strict erkennt den Fehler nicht (wegen `from __future__ import annotations`)
- Kein echter Typ-Schutz zur Laufzeit

**Empfehlung:** Direkter Import — kein `TYPE_CHECKING` für interne Packages:
```python
# quality.py — KEIN TYPE_CHECKING fuer interne Core-Imports
from nl2cad.core.models import IFCModel
```

Der ursprüngliche Ruff-Hinweis `TC001` war ein False Positive:
`nl2cad.core.models` und `nl2cad.core.quality` sind im selben installierten
Package — kein zirkulärer Import möglich.

---

### B-09: `analyzer.py` — `_estimate_length` schluckt alle Exceptions still

**Befund:**
```python
# analyzer.py:205-206
    except Exception:
        pass
    return 0.0
```

`bare except: pass` ohne Logging für `_estimate_length`. Das ist exakt der
Bug der in `ifc_parser.py` (Rev1 W-06) behoben wurde — hier besteht er noch.

Konsequenz: Eine `Fluchtweg`-Instanz mit `laenge_m=0.0` wird erstellt.
`_check_laenge` erkennt `laenge_m <= 0` als "Nicht prüfbar" (`laenge_ok=None`).
Ergebnis: Ein geometrisch defektes DXF-Element erzeugt einen Fluchtweg-Eintrag
**ohne jede Prüfung** — stiller False-Positive in der Analyse.

**Risiko:** HOCH
- DXF-Datei mit defekten Entities erzeugt `fluchtweg.laenge_ok=None` statt Fehler
- Downstream: `BrandschutzkonzeptReport` enthält ungeprüfte Fluchtwege
- `_check_notausgang` zählt diese Einträge als valide Fluchtwege

**Empfehlung:**
```python
def _estimate_length(self, entity) -> float:
    """Schätzt Laenge einer Entity (LINE, LWPOLYLINE). 0.0 bei unbekanntem Typ."""
    try:
        if entity.dxftype() == "LINE":
            dx = entity.dxf.end.x - entity.dxf.start.x
            dy = entity.dxf.end.y - entity.dxf.start.y
            return (dx**2 + dy**2) ** 0.5
        if entity.dxftype() == "LWPOLYLINE":
            pts = list(entity.get_points(format="xy"))
            length = 0.0
            for i in range(len(pts) - 1):
                dx = pts[i + 1][0] - pts[i][0]
                dy = pts[i + 1][1] - pts[i][1]
                length += (dx**2 + dy**2) ** 0.5
            return length
        # Unbekannter Entity-Typ — explizit loggen, kein stilles 0.0
        logger.debug(
            "[BrandschutzAnalyzer] Unbekannter Entity-Typ fuer Laengenbestimmung: %s",
            entity.dxftype(),
        )
    except Exception as e:
        logger.debug("[BrandschutzAnalyzer] Laengenberechnung fehlgeschlagen: %s", e)
    return 0.0
```

---

## WARNING — vor Milestone-1-Abschluss zu beheben

---

### W-07: `constants.py` (brandschutz) und `asr_a23.py` — Dopplung der Grenzwerte

**Befund:**
```python
# asr_a23.py:29-34 — lokale Konstanten
MAX_FLUCHTWEG_LAENGE_M = 35.0
MAX_FLUCHTWEG_LAENGE_MIT_ABZWEIG_M = 60.0
MIN_BREITE_STANDARD_M = 0.875
MIN_BREITE_AB_5_PERSONEN_M = 1.0
MIN_BREITE_AB_20_PERSONEN_M = 1.2
MIN_TUERBREITE_M = 0.78

# constants.py:44-59 — identische Konstanten mit Norm-Version
MAX_FLUCHTWEG_LAENGE_M: float = 35.0
MAX_FLUCHTWEG_LAENGE_MIT_ABZWEIG_M: float = 60.0
...
```

Dieselben Werte existieren zweimal. `asr_a23.py` nutzt seine **eigenen** lokalen
Konstanten, ignoriert `constants.py` vollständig. Norm-Update in `constants.py`
wird in `asr_a23.py` **nicht** wirksam — das ist der Fehler den W-01 beheben sollte,
aber der Fix wurde nur halb durchgeführt (constants.py erstellt, nicht importiert).

**Risiko:** MITTEL — stille Divergenz bei Norm-Update, DRY verletzt.

**Empfehlung:** `asr_a23.py` importiert aus `constants.py`:
```python
# asr_a23.py — lokale Konstanten entfernen, aus constants importieren
from nl2cad.brandschutz.constants import (
    MAX_FLUCHTWEG_LAENGE_M,
    MAX_FLUCHTWEG_LAENGE_MIT_ABZWEIG_M,
    MIN_BREITE_STANDARD_M,
    MIN_BREITE_AB_5_PERSONEN_M,
    MIN_BREITE_AB_20_PERSONEN_M,
    MIN_TUERBREITE_M,
    ASR_A23_VERSION,
)
```

---

### W-08: `IFCQualityReport.completeness_score` — Formel semantisch falsch

**Befund:**
```python
# quality.py:105-109
kritisch_count = sum(1 for i in issues if i.severity == SEVERITY_KRITISCH)
total_checks = max(
    len(model.floors) + sum(len(f.rooms) for f in model.floors), 1
)
score = max(0.0, 1.0 - (kritisch_count / total_checks))
```

`total_checks` ist `Anzahl Geschosse + Anzahl Räume` — das ist keine sinnvolle
Normierungsbasis für einen Quality-Score. Beispiel:

- 1 Geschoss, 10 Räume → `total_checks=11`
- 3 kritische Issues → `score = 1 - 3/11 = 0.727` — suggeriert "72% vollständig"
- Aber: alle 3 Issues betreffen dieselbe fehlende Information

Der Score ist irreführend und erzeugt falsche Sicherheit in `cad-hub`-Templates.

**Risiko:** MITTEL — falsche UX-Signale; Behörde sieht "Score 0.8" als beruhigend.

**Empfehlung:** Einfacherer, semantisch klarer Score:
```python
# Score basiert auf Anteil bestandener Checks, nicht auf Strukturgröße
total_issues = len(issues)
if total_issues == 0:
    score = 1.0
else:
    gewichtete_maengel = sum(
        3 if i.severity == SEVERITY_KRITISCH else
        1 if i.severity == SEVERITY_WARNUNG else 0
        for i in issues
    )
    # Max erreichbarer Score-Verlust: 3 pro Prüfregel (5 Checks)
    max_verlust = 3 * 5
    score = max(0.0, 1.0 - (gewichtete_maengel / max_verlust))
```

Alternativ — vollständig simpel und ehrlich:
```python
# 0.0 wenn KRITISCH vorhanden, 0.5 wenn nur WARNUNG, 1.0 wenn alles ok
if any(i.severity == SEVERITY_KRITISCH for i in issues):
    score = 0.0
elif any(i.severity == SEVERITY_WARNUNG for i in issues):
    score = 0.5
else:
    score = 1.0
```

---

### W-09: CI-Workflow — `uv sync` ohne `--locked` ist nicht reproduzierbar

**Befund:**
```yaml
# ci.yml:33, 67
- run: uv sync --all-packages --dev
```

`uv sync` ohne `--locked` aktualisiert `uv.lock` bei jedem CI-Lauf wenn neue
Versionen verfügbar sind. Das verletzt Reproduzierbarkeit: gleicher Commit kann
morgen andere Dependencies haben.

**Risiko:** MITTEL
- Hetzner-Deployment nutzt Docker-Build — muss identisch mit CI sein
- `uv.lock` in Git ohne `--locked` in CI ist wertlos

**Empfehlung:**
```yaml
# ci.yml — --locked erzwingt exakt uv.lock
- name: Install all workspace dependencies
  run: uv sync --all-packages --dev --locked
```

Außerdem: `uv.lock` muss in `.gitignore` entfernt sein (muss committed sein).
Prüfung:
```bash
grep "uv.lock" .gitignore && echo "FEHLER: uv.lock in gitignore" || echo "OK"
```

---

### W-10: CI-Workflow — kein `uv.lock` Freshness-Check

**Befund:**
Kein Step der prüft ob `uv.lock` mit `pyproject.toml` übereinstimmt.
Ein Entwickler der `pyproject.toml` ändert aber `uv.lock` nicht committed,
lässt CI mit veralteter Lock-Datei laufen.

**Empfehlung:**
```yaml
# ci.yml — nach Checkout, vor sync
- name: Check uv.lock is up-to-date
  run: uv lock --check
```

---

## INFO — Optimierungen ohne Blocking-Charakter

---

### I-05: `analyzer.py` — `analyze_ifc` ignoriert Räume vollständig

**Befund:**
`analyze_ifc()` iteriert nur über `floor.doors` — Räume werden nicht analysiert.
Fluchtweg-Erkennung aus IFC-Properties (`IfcSpace.LongName`, `IsEscape`) fehlt.
IFC-Modelle ohne Brandschutztüren-Properties liefern leere `analyse.fluchtwege`.

**Risiko:** NIEDRIG für Milestone 1, HOCH für produktiven Einsatz.
**Empfehlung:** In `analyze_ifc` auch Räume auf Fluchtweg-Properties prüfen:
```python
for room in floor.rooms:
    props = room.properties or {}
    if props.get("IsEscape") or props.get("IsEmergencyExit"):
        fluchtweg = Fluchtweg(
            name=room.name,
            laenge_m=room.area_m2 ** 0.5,  # Näherung bis Milestone 2
            etage=etage,
            hat_notausgang=True,
        )
        analyse.fluchtwege.append(fluchtweg)
```

### I-06: `models.py` — `feuerlöscher_count` Property mit Umlaut im Namen

**Befund:**
```python
# models.py:120
@property
def feuerlöscher_count(self) -> int:
```

Umlaut `ö` im Property-Namen — verletzt B-02-Konvention. In Bash-Skripten,
HTMX-Templates (`{{ analyse.feuerlöscher_count }}`) und Postgres-JSONB-Keys
potentiell problematisch.

**Empfehlung:** `loescheinrichtungen_count` oder `feuerlоescher_count`.

### I-07: `constants.py` — `EX_ZONENAUSDEHNUNG` nicht gegen `ExZone` Enum validiert

**Befund:**
```python
# constants.py:123-143
EX_ZONENAUSDEHNUNG: dict[tuple[str, str], tuple[str, float]] = {
    ("K", "K1"): ("Zone0", 0.5),
    ...
}
```

`"Zone0"` als String — aber `models.py:24` definiert `ExZone.ZONE_0 = "Zone 0"`
(mit Leerzeichen). Lookup `EX_ZONENAUSDEHNUNG[("K","K1")]` liefert `"Zone0"`,
aber `ExZone.ZONE_0.value == "Zone 1"` — **String-Mismatch**.

**Empfehlung:** Enum-Values in `constants.py` angleichen oder `ExZone`-Enum direkt
als Key verwenden:
```python
from nl2cad.brandschutz.models import ExZone

ATEX_ZONE_ZU_GERAETEKATEGORIE: dict[ExZone, str] = {
    ExZone.ZONE_0:  "KAT1",
    ExZone.ZONE_1:  "KAT2",
    ExZone.ZONE_2:  "KAT3",
    ExZone.ZONE_20: "KAT1",
    ExZone.ZONE_21: "KAT2",
    ExZone.ZONE_22: "KAT3",
}
```

---

## Gesamtbewertung Rev2

| Kategorie                    | Rev1-Urteil | Rev2-Urteil                                     |
| ---------------------------- | ----------- | ----------------------------------------------- |
| **ADR-Architekturkonformität** | NICHT OK    | OK (ADR korrigiert)                             |
| **Code-Architekturkonformität** | —          | NICHT OK (B-07: Umlaut im Code, B-08: TYPE_CHECKING) |
| **Invarianten**              | NICHT OK    | OK (ESD __post_init__ im ADR)                   |
| **Seiteneffekte**            | TEILWEISE   | NICHT OK (B-09: stiller 0.0-Fallback bleibt)    |
| **Migrationsrisiken**        | NICHT OK    | OK (DB-Schema definiert)                        |
| **Naming Conventions**       | NICHT OK    | TEILWEISE (ADR ok, Code noch nicht vollständig) |
| **Kein magisches Verhalten** | NICHT OK    | TEILWEISE (W-08: Score-Formel)                  |
| **DRY**                      | —           | NICHT OK (W-07: doppelte Konstanten)            |
| **CI-Reproduzierbarkeit**    | NICHT OK    | TEILWEISE (W-09/W-10: kein --locked)            |
| **Rechtliche Belastbarkeit** | NICHT OK    | OK (BeurteilungsStatus, Vorprüfungs-Kennzeichnung) |

**Entscheidung: BEDINGT FREIGEGEBEN für Implementierungsstart.**

B-07, B-08, B-09 müssen **im Code** behoben werden (nicht nur im ADR).
W-07 (Konstanten-Duplizierung) und W-09 (CI `--locked`) sind Pflicht vor
erstem Merge auf `main`.

Nach Behebung dieser 5 Punkte: FREIGEGEBEN.
