# nl2cad Repository Audit Report

**Datum:** 2026-03-03  
**Geprüft durch:** Cascade Audit  
**Scope:** Alle 5 Packages + Root-Workspace  

---

## Inhaltsverzeichnis

1. [Zusammenfassung](#zusammenfassung)
2. [Code-Konventionen](#1-code-konventionen)
3. [Dependencies](#2-dependencies)
4. [Workflows & CI/CD](#3-workflows--cicd)
5. [Konfigurationsdateien](#4-konfigurationsdateien)
6. [Priorisierte To-Do-Liste](#5-priorisierte-to-do-liste)

---

## Zusammenfassung

| Kategorie         | OK     | Warnings | Critical |
|-------------------|--------|----------|----------|
| Code-Konventionen | 18     | 7        | 1        |
| Dependencies      | 8      | 6        | 1        |
| Workflows / CI/CD | 0      | 1        | 3        |
| Konfiguration     | 3      | 2        | 2        |
| **Gesamt**        | **29** | **16**   | **7**    |

---

## 1. Code-Konventionen

### 1.1 ✅ OK

- **Dataclasses korrekt** — alle Core-/Areas-/GAEB-/Brandschutz-Packages nutzen `@dataclass` (stdlib), kein Pydantic
- **Pydantic nur in nl2cad-nlp** — `NLIntent`, `IntentResult`, `NL2DXFResult` korrekt abgegrenzt (in `nl2cad-nlp`)
  - _Hinweis: `nl2cad-nlp` nutzt aktuell keine Pydantic-BaseModels, sondern ebenfalls stdlib dataclasses — Pydantic ist als Abhängigkeit deklariert, aber nicht verwendet_
- **Einheits-Suffixe** — alle Maß-Felder tragen `_m2`, `_m`, `_m3` konsequent
- **Logging** — `logging.getLogger(__name__)` in allen Modulen, kein `print()`
- **Eigene Exception-Hierarchie** — `NL2CADError` → `IFCParseError`, `DXFParseError`, `UnsupportedFormatError`, `HandlerError`, `PipelineError` in `exceptions.py`
- **Keine hardcoded Strings** — alle Regelwerk-Konstanten in `constants.py` (Core + Brandschutz)
- **PEP 8 / 100-Zeichen-Limit** — Dateien eingehalten (ruff konfiguriert)
- **`from __future__ import annotations`** — konsequent in allen Modulen
- **`field(default_factory=...)` für mutable defaults** — korrekt überall verwendet
- **`__all__` exportiert** — alle Public APIs klar definiert in `__init__.py`
- **`StrEnum`** — korrekt für `HandlerStatus`, `CADCommandType`, `BrandschutzKategorie` etc.
- **Docstrings** — alle öffentlichen Klassen und Methoden haben Docstrings (Google-Style)
- **Structured Logging** — `logger.info("[Handler] %d ...", n)` Format konsequent
- **Regelwerk-Versionen versioniert** — `ASR_A23_VERSION`, `MBO_VERSION`, `DIN4102_VERSION` etc. in `brandschutz/constants.py`
- **Test-Namenskonvention** — `test_should_*` Pattern in allen Test-Klassen korrekt
- **Kein `except Exception: pass`** — alle Catches loggen
- **`CADHandlerPipeline` chainable** — `.add()` gibt `self` zurück
- **`IFCQualityChecker` in core** — korrekt aus brandschutz herausgelöst (FIX B-03)

---

### 1.2 ⚠️ Warnings

#### W-01: Pydantic als Abhängigkeit deklariert, aber nicht als BaseModel verwendet

**Betroffen:** `packages/nl2cad-nlp/pyproject.toml`, `pyproject.toml` (root)  
**Befund:** `nl2cad-nlp` deklariert `pydantic>=2.0` als Abhängigkeit, aber `nl2dxf.py`, `intent.py`, `learning.py` und deren Modelle nutzen ausschließlich stdlib `dataclass`. Es gibt kein `models.py` in `nl2cad-nlp` mit Pydantic-BaseModels.  
**Risiko:** Unnötige schwere Abhängigkeit; Verwirrt künftige Entwickler über die Abgrenzung.

```toml
# pyproject.toml root — pydantic in core-dependencies, sollte nicht sein
dependencies = [
    "pydantic>=2.0",   # ← sollte nicht im Root-Package sein
    "httpx>=0.27",     # ← ebenso
    "ezdxf>=1.3.0",
]
```

#### W-02: Root `pyproject.toml` vermischt nl2cadfw mit Package-Abhängigkeiten

**Betroffen:** `pyproject.toml` (root, Paket `iil-nl2cadfw`)  
**Befund:** Das Root-Projekt deklariert `pydantic>=2.0` und `httpx>=0.27` als direkte Abhängigkeiten, obwohl `core` und `areas` diese Pakete explizit **verboten** haben. Außerdem fehlt ein `[tool.uv.workspace]`-Abschnitt im Root.  
**Risiko:** Verwirrt den Workspace-Aufbau; erzeugt implizite Abhängigkeiten.

#### W-03: `NLLearningStore` schreibt persistent in `~/.nl2cad/` ohne Opt-out

**Betroffen:** `packages/nl2cad-nlp/src/nl2cad/nlp/learning.py`  
**Befund:** Standardpfad ist `Path.home() / ".nl2cad" / "nl_learning.json"` ohne Möglichkeit, persistentes Schreiben zu deaktivieren. In Unit-Tests oder serverless-Umgebungen unerwünscht.

#### W-04: `DXFParser.parse_bytes` löscht temporäre Datei nicht (kein `finally`)

**Betroffen:** `packages/nl2cad-core/src/nl2cad/core/parsers/dxf_parser.py`  
**Befund:** `IFCParser.parse_bytes` hat ein korrektes `try/finally`-Pattern mit `os.unlink`. `DXFParser.parse_bytes` fehlt dieses Pattern — die `tempfile.NamedTemporaryFile` läuft mit `delete=False`, aber es gibt kein explizites Cleanup.

```python
# DXFParser.parse_bytes — MISSING finally cleanup
def parse_bytes(self, content: bytes, filename: str = "upload.dxf") -> DXFModel:
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        tmp.write(content)
        return self.parse(tmp.name)  # ← tmp wird nie gelöscht!
```

#### W-05: Fehlende `conftest.py` / Fixtures für IFC-Tests

**Betroffen:** `packages/nl2cad-core/tests/test_ifc_parser.py`, `test_dxf_parser.py`  
**Befund:** AGENTS.md schreibt vor, dass Parser-Tests **echte Fixtures** aus `tests/fixtures/` verwenden sollen (keine Mocks). Es gibt keine `fixtures/`-Verzeichnisse in den Packages. Die Parser-Tests in `nl2cad-core` verwenden daher wahrscheinlich Mocks oder sind unvollständig.

#### W-06: `MassenHandler.execute` verwendet `assert isinstance(model, IFCModel)`

**Betroffen:** `packages/nl2cad-core/src/nl2cad/core/handlers/massen.py`  
**Befund:** `assert` ist kein geeignetes Mittel für Laufzeit-Typprüfung in Production-Code (wird mit `python -O` deaktiviert). Stattdessen sollte eine explizite `isinstance`-Prüfung mit `HandlerError` verwendet werden.

```python
# Aktuell:
assert isinstance(model, IFCModel)

# Soll:
if not isinstance(model, IFCModel):
    result.add_error("ifc_model ist kein IFCModel")
    return result
```

#### W-07: Fehlende `pytest.ini_options` in `nl2cad-areas`, `nl2cad-brandschutz`, `nl2cad-gaeb`

**Betroffen:** `packages/nl2cad-areas/pyproject.toml`, `packages/nl2cad-brandschutz/pyproject.toml`, `packages/nl2cad-gaeb/pyproject.toml`  
**Befund:** Diese drei Packages deklarieren keinen `[tool.pytest.ini_options]`-Abschnitt. `pytest` läuft ohne explizites `pythonpath = ["src"]`, was bei direktem `pytest`-Aufruf (ohne `uv run`) zu `ModuleNotFoundError` führt.

---

### 1.3 🔴 Critical

#### C-01: `GAEBGenerator.generate_xml` setzt `xmlns` als reguläres Attribut statt Namespace

**Betroffen:** `packages/nl2cad-gaeb/src/nl2cad/gaeb/generator.py`  
**Befund:** `ET.Element("GAEB", xmlns=self.GAEB_NAMESPACE)` ist **kein gültiger XML-Namespace-Ansatz** in `xml.etree.ElementTree`. Das `xmlns`-Attribut wird als normales Attribut geschrieben, nicht als XML-Namespace-Deklaration. Downstream-GAEB-Parser werden die Datei als nicht-konform ablehnen.

```python
# Falsch:
root = ET.Element("GAEB", xmlns=self.GAEB_NAMESPACE)

# Richtig (Clark-Notation):
ns = "http://www.gaeb.de/GAEB_DA_XML/200407"
ET.register_namespace("", ns)
root = ET.Element(f"{{{ns}}}GAEB")
```

---

## 2. Dependencies

### 2.1 ✅ OK

- **Python >= 3.11** — konsistent in allen `pyproject.toml` deklariert
- **`hatchling`** als Build-Backend — modern, konsistent über alle Packages
- **`openpyxl>=3.1`** in `nl2cad-gaeb` — openpyxl ist **lazy importiert** (`from openpyxl import Workbook` nur in `generate_excel`), korrekt
- **`ifcopenshell>=0.8.0`** als Optional-Dep in Root und Core-Dev — korrekt
- **`uv`-Workspace-Sources** — `[tool.uv.sources]` korrekt in `areas`, `brandschutz`, `gaeb`, `nlp`
- **`ruff>=0.4`** und `mypy>=1.10` — in allen Dev-Deps
- **`pytest>=8.0`** — aktuell und konsistent
- **Keine `requests`-Abhängigkeit** — `httpx>=0.27` korrekt verwendet (AGENTS.md-konform)

---

### 2.2 ⚠️ Warnings (veraltete/inkonsistente Versionen)

| Package      | Deklariert  | PyPI aktuell  | Risiko                                              |
|--------------|-------------|---------------|-----------------------------------------------------|
| `pydantic`   | `>=2.0`     | `2.10.x`      | Niedrig — Pin auf `>=2.7` empfohlen                 |
| `httpx`      | `>=0.27`    | `0.28.x`      | Niedrig — ok                                        |
| `ezdxf`      | `>=1.3.0`   | `1.4.x`       | Niedrig — ok                                        |
| `openai`     | `>=1.0`     | `1.65.x`      | Niedrig — sehr breite Pin                           |
| `anthropic`  | `>=0.25`    | `0.49.x`      | Mittel — Breaking Changes zwischen 0.25 und 0.49    |
| `openpyxl`   | `>=3.1`     | `3.1.5`       | Niedrig — ok                                        |

#### DEP-W-01: `anthropic>=0.25` — zu breite Pin

**Betroffen:** `packages/nl2cad-nlp/pyproject.toml`  
`anthropic` hatte zwischen 0.25 und 0.49 mehrere Breaking-API-Changes. Die Pin `>=0.25` erlaubt den Download einer Version, die inkompatibel mit dem aktuellen Code ist.  
**Fix:** `anthropic>=0.40` (stabile async-API seit 0.40)

#### DEP-W-02: Keine `uv.lock`-Datei gefunden

**Befund:** Es gibt kein `uv.lock` im Repository-Root. Ohne Lock-File sind reproduzierbare Builds nicht garantiert. CHANGELOG erwähnt `FIX W-09: CI uv sync --locked` — Lock-File muss committed sein.  
**Fix:** `uv lock` ausführen und `uv.lock` committen.

#### DEP-W-03: Root `pyproject.toml` fehlt `[tool.uv.workspace]`-Definition

**Befund:** Das Root-`pyproject.toml` definiert keinen `[tool.uv.workspace]`-Abschnitt mit `members = ["packages/*"]`. Ohne diesen Abschnitt erkennt `uv` den Mono-Repo-Workspace nicht automatisch.

#### DEP-W-04: `pytest-asyncio>=0.23` fehlt in `nl2cad-brandschutz` und `nl2cad-gaeb`

**Befund:** Root und `nl2cad-core` deklarieren `pytest-asyncio`, aber `nl2cad-brandschutz` und `nl2cad-gaeb` nicht — falls async-Tests hinzukommen, fehlt die Abhängigkeit.

#### DEP-W-05: `mypy>=1.10` fehlt in `nl2cad-gaeb` und `nl2cad-brandschutz` Dev-Deps

**Betroffen:** `packages/nl2cad-gaeb/pyproject.toml`, `packages/nl2cad-brandschutz/pyproject.toml`  
`mypy` ist nicht in den Dev-Abhängigkeiten dieser Packages, obwohl `mypy strict` im Root konfiguriert ist.

#### DEP-W-06: Doppelte Deklaration von `ifcopenshell` in `nl2cad-core`

**Betroffen:** `packages/nl2cad-core/pyproject.toml`  
`ifcopenshell` erscheint sowohl in `[project.dependencies]` als auch in `[project.optional-dependencies] dev`. Es sollte nur in `dependencies` (für Runtime) oder nur optional sein.

---

### 2.3 🔴 Critical

#### DEP-C-01: `iil-nl2cadfw` Root-Package verstößt gegen Dependency-Isolation

**Betroffen:** `pyproject.toml` (root)  
**Befund:** Das Root-Package deklariert `pydantic>=2.0`, `httpx>=0.27` und `ezdxf>=1.3.0` als direkte Runtime-Abhängigkeiten. Laut AGENTS.md sind `pydantic` und `httpx` in `nl2cad-core` explizit **verboten**. Das Root-Package untergräbt diese Isolation, wenn es als Dependency installiert wird.

---

## 3. Workflows & CI/CD

### 3.1 ✅ OK

Keine vollständig korrekte Workflow-Konfiguration vorhanden — alle Befunde sind Warnings oder Critical.

---

### 3.2 ⚠️ Warnings

#### CI-W-01: Nur Shell-Skripte statt CI-Workflows

**Betroffen:** `run_tests.sh`, `run_core_tests.sh`  
**Befund:** Es existieren ausschließlich manuelle Shell-Skripte für Tests. Diese sind funktional, aber nicht als CI-Pipeline ausführbar. CHANGELOG referenziert `FIX W-09: CI uv sync --locked` — das deutet darauf hin, dass ein CI-System geplant war.

---

### 3.3 🔴 Critical

#### CI-C-01: Kein GitHub Actions Workflow vorhanden

**Befund:** Es existiert **kein `.github/workflows/`-Verzeichnis**. Es gibt weder:

- Test-Workflow (`pytest` pro Package)
- Lint-Workflow (`ruff check`, `mypy`)
- Publish-Workflow (PyPI-Upload per Tag)

CHANGELOG und AGENTS.md erwähnen Tag-basierte Releases (`git tag nl2cad-core@0.1.0`) und automatische PyPI-Publizierung — diese Infrastruktur fehlt vollständig.

#### CI-C-02: Kein Lint-/Typecheck-Workflow

**Befund:** Weder `ruff` noch `mypy` werden automatisch ausgeführt. Beide sind als Dev-Deps konfiguriert (inkl. `strict`-mypy im Root), aber ohne CI-Enforcement haben Code-Konventionsverletzungen keine automatische Sperre.

#### CI-C-03: Kein Publish-Workflow (PyPI / GHCR)

**Befund:** Das AGENTS.md beschreibt einen Tag-basierten Release-Prozess:

```bash
git tag nl2cad-core@0.1.0
git push --tags
# → CI published automatisch zu PyPI
```

Diese Automatisierung existiert nicht. Releases müssen manuell gebaut und publiziert werden.

---

## 4. Konfigurationsdateien

### 4.1 ✅ OK

- **`hatchling`-Namespace-Packaging** — `PEP 420 Namespace Package` korrekt dokumentiert; kein `__init__.py` im `nl2cad/`-Root der Packages
- **`line-length = 100`** in Root-`pyproject.toml` ruff-Config konsistent mit AGENTS.md
- **`target-version = "py311"`** in ruff und mypy konsistent

---

### 4.2 ⚠️ Warnings

#### CFG-W-01: Keine `.env.example`-Datei

**Befund:** Es gibt keine `.env.example` oder ähnliche Konfigurationsvorlage. Da das Projekt keine Django/Web-App-Struktur hat, ist das weniger kritisch, aber für den optionalen LLM-Client (`openai`, `anthropic`) wären API-Key-Konventionen dokumentierbar.

#### CFG-W-02: `Zone.Identifier`-Dateien im Repository

**Befund:** Es gibt viele Dateien mit dem Suffix `.Zone.Identifier` (z.B. `pyproject.tomlZone.Identifier`). Dies sind Windows NTFS Alternate Data Streams die beim Kopieren aus dem Internet entstehen. Sie sollten nicht committed sein.

```text
packages/nl2cad-areas/pyproject.tomlZone.Identifier
packages/nl2cad-brandschutz/pyproject.tomlZone.Identifier
packages/nl2cad-core/pyproject.tomlZone.Identifier
... (viele weitere)
```

**Fix:**

```bash
find . -name "*.Zone.Identifier" -delete
# .gitignore erweitern:
echo "*.Zone.Identifier" >> .gitignore
```

---

### 4.3 🔴 Critical

#### CFG-C-01: Kein Dockerfile / Docker-Compose vorhanden

**Befund:** Das Projekt enthält kein `Dockerfile` und keine `docker-compose.yml`. Da `nl2cad` eine reine Python-Library ist (kein Web-Server), ist ein Dockerfile optional — aber für `ifcopenshell` (die native C++-Bindings hat) wäre ein reproduzierbares Build-Image wichtig. Aktuell gibt es `setup_ifc_venv.sh` als manuelles Workaround.

#### CFG-C-02: Kein `uv.lock` committed

**Befund:** (Siehe auch DEP-W-02) Ohne committetes `uv.lock` sind CI-Builds nicht reproduzierbar. `uv sync --locked` (im CHANGELOG erwähnt) schlägt fehl, wenn keine Lock-Datei vorhanden ist.

```bash
# Fix:
uv lock
git add uv.lock
git commit -m "chore: add uv.lock for reproducible builds"
```

---

## 5. Priorisierte To-Do-Liste

### 🔴 KRITISCH — Sofort beheben

#### [TODO-1] GitHub Actions Workflows erstellen

```bash
mkdir -p .github/workflows
```

Minimaler Test-Workflow (`.github/workflows/test.yml`):

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        package: [nl2cad-core, nl2cad-areas, nl2cad-brandschutz, nl2cad-gaeb, nl2cad-nlp]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --locked
      - run: uv run pytest packages/${{ matrix.package }}/ -v --tb=short
```

Lint-Workflow (`.github/workflows/lint.yml`):

```yaml
name: Lint
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --locked
      - run: uv run ruff check packages/
      - run: uv run mypy packages/
```

---

#### [TODO-2] `uv.lock` generieren und committen

```bash
cd /home/dehnert/github/nl2cad
uv lock
git add uv.lock
git commit -m "chore: add uv.lock for reproducible builds"
```

---

#### [TODO-3] `GAEBGenerator.generate_xml` XML-Namespace fixen

**Datei:** `packages/nl2cad-gaeb/src/nl2cad/gaeb/generator.py`

```python
# Alt:
root = ET.Element("GAEB", xmlns=self.GAEB_NAMESPACE)

# Neu:
ns = self.GAEB_NAMESPACE
ET.register_namespace("", ns)
root = ET.Element(f"{{{ns}}}GAEB")
hdr = ET.SubElement(root, f"{{{ns}}}GAEBInfo")
# ... alle SubElements mit Namespace-Prefix
```

---

#### [TODO-4] Root `pyproject.toml` Dependency-Isolation reparieren

**Datei:** `pyproject.toml` (root)

```toml
# Alt:
dependencies = [
    "pydantic>=2.0",
    "httpx>=0.27",
    "ezdxf>=1.3.0",
]

# Neu (Root-Package sollte keine Runtime-Deps haben):
dependencies = []

[tool.uv.workspace]
members = ["packages/*"]
```

---

#### [TODO-5] `Zone.Identifier`-Dateien entfernen und `.gitignore` erweitern

```bash
find /home/dehnert/github/nl2cad -name "*.Zone.Identifier" -delete
echo "*.Zone.Identifier" >> .gitignore
git add .gitignore
git rm --cached $(git ls-files | grep "Zone.Identifier")
git commit -m "chore: remove Windows Zone.Identifier files, update .gitignore"
```

---

#### [TODO-6] `uv.lock` + `[tool.uv.workspace]` im Root ergänzen

```toml
# pyproject.toml root — ergänzen:
[tool.uv.workspace]
members = ["packages/*"]
```

---

### ⚠️ MITTEL — In nächstem Sprint beheben

#### [TODO-7] `DXFParser.parse_bytes` Tempfile-Cleanup fixen

**Datei:** `packages/nl2cad-core/src/nl2cad/core/parsers/dxf_parser.py`

```python
def parse_bytes(self, content: bytes, filename: str = "upload.dxf") -> DXFModel:
    import os
    import tempfile
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        return self.parse(tmp_path)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
```

---

#### [TODO-8] `assert isinstance` in `MassenHandler` durch explizite Checks ersetzen

**Datei:** `packages/nl2cad-core/src/nl2cad/core/handlers/massen.py`

```python
# Alt:
assert isinstance(model, IFCModel)

# Neu:
if not isinstance(model, IFCModel):
    result.add_error(f"ifc_model ist kein IFCModel: {type(model)}")
    return result
```

---

#### [TODO-9] `pytest.ini_options` in fehlenden Packages ergänzen

**Dateien:** `packages/nl2cad-areas/pyproject.toml`, `packages/nl2cad-brandschutz/pyproject.toml`, `packages/nl2cad-gaeb/pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"
pythonpath = ["src"]
```

---

#### [TODO-10] IFC/DXF Test-Fixtures anlegen

```bash
mkdir -p packages/nl2cad-core/tests/fixtures
# Minimale IFC-Testdatei (IFC2X3) ablegen
# Minimale DXF-Testdatei ablegen
```

Dann in `conftest.py`:

```python
import pytest
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.fixture
def fixture_ifc_simple():
    return FIXTURES / "simple.ifc"

@pytest.fixture
def fixture_dxf_simple():
    return FIXTURES / "simple.dxf"
```

---

#### [TODO-11] `anthropic` Pin verschärfen

**Datei:** `packages/nl2cad-nlp/pyproject.toml`

```toml
# Alt:
anthropic = ["anthropic>=0.25"]

# Neu:
anthropic = ["anthropic>=0.40"]
```

---

#### [TODO-12] `NLLearningStore` persistentes Schreiben opt-out ermöglichen

**Datei:** `packages/nl2cad-nlp/src/nl2cad/nlp/learning.py`

```python
class NLLearningStore:
    def __init__(self, data_path: Path | None = None, persist: bool = True) -> None:
        self.data_path = data_path or Path.home() / ".nl2cad" / "nl_learning.json"
        self.persist = persist
        self.patterns: list[LearnedPattern] = []
        if self.persist:
            self._load()

    def _save(self) -> None:
        if not self.persist:
            return
        # ... bestehende Logik
```

---

#### [TODO-13] `mypy` und `pytest-asyncio` in fehlende Dev-Deps ergänzen

**Dateien:** `packages/nl2cad-gaeb/pyproject.toml`, `packages/nl2cad-brandschutz/pyproject.toml`

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.4", "mypy>=1.10", "pytest-asyncio>=0.23"]
```

---

### 🟡 NIEDRIG — Technische Schuld, bei Gelegenheit

#### [TODO-14] `ifcopenshell` Doppeldeklaration in nl2cad-core bereinigen

**Datei:** `packages/nl2cad-core/pyproject.toml`

```toml
# Entfernen aus dev-dependencies (bereits in dependencies):
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.4",
    "mypy>=1.10",
    # ifcopenshell>=0.8.0 ← entfernen (schon in dependencies)
]
```

---

#### [TODO-15] Publish-Workflow für tag-basierte PyPI-Releases erstellen

**Datei:** `.github/workflows/publish.yml`

```yaml
name: Publish
on:
  push:
    tags:
      - "nl2cad-*@*"
jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: Determine package from tag
        run: |
          TAG="${{ github.ref_name }}"
          PACKAGE="${TAG%@*}"
          echo "PACKAGE=$PACKAGE" >> $GITHUB_ENV
      - run: uv build --package ${{ env.PACKAGE }}
      - uses: pypa/gh-action-pypi-publish@release/v1
```

---

#### [TODO-16] Pydantic-Abhängigkeit in nl2cad-nlp tatsächlich nutzen oder entfernen

**Befund:** `pydantic>=2.0` ist als Abhängigkeit deklariert, aber kein `BaseModel` wird verwendet.  
**Option A:** `models.py` in `nl2cad-nlp` mit Pydantic-Modellen für `IntentResult`, `NL2DXFResult` anlegen (AGENTS.md-Konvention: Pydantic nur in nlp erlaubt).  
**Option B:** Pydantic aus den Dependencies entfernen, wenn nicht benötigt.

---

## Legende

| Symbol     | Bedeutung                              |
|------------|----------------------------------------|
| ✅         | Konform, kein Handlungsbedarf          |
| ⚠️         | Warning — sollte behoben werden        |
| 🔴         | Critical — muss behoben werden         |
| `[TODO-N]` | Priorisierte Maßnahme mit Fix-Command  |
