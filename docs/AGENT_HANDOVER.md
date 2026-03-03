# nl2cad — Agent Handover Document

> **ADR-086-konform** | Zuletzt aktualisiert: 2026-03-03 | Review-Intervall: 30 Tage

## Repo-Zweck

`nl2cad` ist eine **reine Python-Library** (kein Django, kein Web-Framework) für
BIM/CAD-Verarbeitung in der deutschen Baubranche.

**Downstream-Konsumenten:** `cad-hub` (Django-App), zukünftige Apps.

---

## Package-Übersicht

| Package | PyPI-Name | Zweck |
|---------|-----------|-------|
| `nl2cad-core` | `nl2cad-core` | IFC/DXF Parser, Dataclasses, Handler-Pipeline |
| `nl2cad-areas` | `nl2cad-areas` | DIN 277, WoFlV Flächenrechner |
| `nl2cad-brandschutz` | `nl2cad-brandschutz` | Brandschutz, ASR A2.3, DIN 4102 |
| `nl2cad-gaeb` | `nl2cad-gaeb` | GAEB X81–X85 Generator + Excel |
| `nl2cad-nlp` | `nl2cad-nlp` | Intent-Klassifikation, NL2DXF |

---

## Technischer Stack

| Komponente | Details |
|------------|---------|
| Python | >= 3.11 |
| Build | `hatchling` + `uv` Workspace |
| Linting | `ruff>=0.4` (line-length=100) |
| Typing | `mypy>=1.10` (strict) |
| Tests | `pytest>=8.0` + `pytest-cov` (Ziel: ≥ 80%) |
| IFC | `ifcopenshell>=0.8.0` (optional, native C++-Bindings) |
| DXF | `ezdxf>=1.3.0` |
| LLM | `httpx>=0.27` + `openai>=1.0` / `anthropic>=0.40` (nur nl2cad-nlp) |

---

## Kritische Regeln (STRIKT)

- **Kein Django** in keinem Package — reine stdlib + erlaubte deps
- **Kein Pydantic** in core/areas/gaeb/brandschutz — nur stdlib `@dataclass`
- **Pydantic** nur in `nl2cad-nlp` erlaubt
- **Kein `print()`** — immer `logging.getLogger(__name__)`
- **Maßfelder immer mit Suffix**: `area_m2`, `height_m`, `thickness_m`
- **Eigene Exceptions**: `NL2CADError` → `IFCParseError`, `DXFParseError`, etc.
- **Keine hardcoded Strings** für Regelwerk-Codes → `constants.py`

---

## Repo-Struktur

```
packages/
  nl2cad-core/src/nl2cad/core/
    models/         # Dataclasses (IFCRoom, DXFLayer, ...)
    parsers/        # ifcopenshell + ezdxf wrapper
    handlers/       # BaseCADHandler, CADHandlerPipeline
    services/       # CADLoader, Konverter
    exceptions.py   # Alle nl2cad Exceptions
    constants.py    # DIN-Codes, Layer-Keywords
  nl2cad-areas/src/nl2cad/areas/
  nl2cad-brandschutz/src/nl2cad/brandschutz/
  nl2cad-gaeb/src/nl2cad/gaeb/
  nl2cad-nlp/src/nl2cad/nlp/
tests/integration/  # Cross-Package Pipeline-Tests
.github/workflows/  # test.yml, lint.yml, publish.yml
```

---

## Setup (Pflicht vor erstem Task)

```bash
uv sync --all-packages --group dev
uv run pytest -v                          # Baseline: alle grün
uv run ruff check packages/               # 0 Errors erwartet
uv run python -c "import ifcopenshell"    # IFC optional — skip wenn fehlt
```

---

## CI/CD

| Workflow | Trigger | Aktion |
|----------|---------|--------|
| `test.yml` | push/PR → main | pytest pro Package mit Coverage |
| `lint.yml` | push/PR → main | ruff check + ruff format + mypy |
| `publish.yml` | Tag `nl2cad-*@*` | uv build + PyPI publish |

**Release:**
```bash
git tag nl2cad-core@0.1.1
git push --tags
# → publish.yml deployt automatisch zu PyPI
```

---

## Bekannte Besonderheiten

- **ifcopenshell** hat native C++-Bindings — `setup_ifc_venv.sh` für Diagnose
- **uv.lock** ist committed — immer `uv sync --locked` für reproduzierbare Builds
- **Namespace-Package** (PEP 420) — kein `__init__.py` im `nl2cad/`-Root der Packages
- **Zone.Identifier-Dateien** sind in `.gitignore` ausgeschlossen (Windows NTFS)
- **`uv run pytest`** muss die uv-venv nutzen, nicht System-Python

---

## Workflows (Windsurf)

| Workflow | Zweck |
|----------|-------|
| `/start` | Einstiegspunkt, Setup + Orientierung |
| `/agent-task` | Task ausführen (ADR-086-konform) |
| `/new-package` | Neues nl2cad-Package anlegen |
| `/task-01-core-handlers` | Handler implementieren |
| `/task-02-gaeb-tests` | GAEB Tests schreiben |
| `/task-03-nlp-nl2dxf` | NL2DXF portieren |
| `/task-04-cadhub-integration` | cad-hub Integration |

---

## Offene Tasks / Backlog

- [ ] IFC/DXF Test-Fixtures (`simple.ifc`, `simple.dxf`) in `tests/fixtures/` ablegen
- [ ] Integration-Tests für Cross-Package Pipeline erweitern
- [ ] `nl2cad-nlp`: `models.py` mit Pydantic-BaseModels implementieren (AGENTS.md-Konvention)
- [ ] Phase 3: `nl2cad-brandschutz` Dockerfile für reproduzierbare ifcopenshell-Builds

---

## Letzte größere Änderungen

| Datum | Änderung |
|-------|----------|
| 2026-03-03 | Audit-TODO-Umsetzung: GAEB XML-Namespace fix, uv.lock, GitHub Actions, Guardrails |
| 2026-03-03 | `pyproject.toml` Root: pydantic/httpx entfernt, `[tool.uv.workspace]` ergänzt |
| 2026-03-03 | `nl2cad-nlp`: anthropic>=0.40, pydantic entfernt |
| 2026-03-03 | `DXFParser.parse_bytes`: Tempfile-Leak behoben |
