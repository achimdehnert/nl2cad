---
description: Einstiegspunkt für jeden Agent — Setup, Orientierung, Task-Auswahl
---

# nl2cad — Agent Start

## Pflichtlektüre (immer zuerst)

1. Lies `AGENTS.md` vollständig durch — das ist dein Arbeitsvertrag für dieses Repo
2. Lies `CHANGELOG.md` → Abschnitt `[Unreleased]` — was ist bereits in Arbeit?
3. Führe aus: `uv sync --all-packages --group dev`
4. Führe aus: `uv run pytest -v` → Alle Tests müssen grün sein (Baseline)
5. Führe aus: `uv run ruff check packages/` → 0 Errors erwartet

## Wichtige Infra-Hinweise

- **IFC-Tests** (`test_ifc_parser.py`): Laufen nur wenn `ifcopenshell` in der uv-venv
  verfügbar ist. Sie sind mit `@ifc_required` markiert und skippen sauber wenn nicht
  verfügbar. `uv run python -c "import ifcopenshell"` prüft die Verfügbarkeit.
- **pytest-Interpreter**: `uv run pytest` muss die uv-venv nutzen (nicht System-Python).
  Sicherstellen mit: `uv run python -c "import sys; print(sys.executable)"`
  → muss `.venv/bin/python` zeigen, nicht `/usr/bin/python3.11`.
- **Coverage-Ziel**: ≥ 80% (`--cov-fail-under=80`). Aktuell: ~82%.
- **Setup-Script**: `bash setup_ifc_venv.sh` erstellt venv mit ifcopenshell-Diagnose.

## Orientierung: Repo-Struktur

```
packages/
  nl2cad-core/        → IFC/DXF Parser, Dataclasses, Handler-Pipeline (BASIS)
  nl2cad-areas/       → DIN 277, WoFlV Rechner
  nl2cad-brandschutz/ → Brandschutz-Analyse, ASR A2.3, DIN 4102
  nl2cad-gaeb/        → GAEB X81-X85 Generator
  nl2cad-nlp/         → Intent-Klassifikation, NL2DXF
tests/integration/    → Cross-Package Pipeline-Tests
```

## Workflow auswählen

Wähle den passenden Workflow für deinen Task:

| Workflow | Befehl in Windsurf |
|----------|-------------------|
| Handler implementieren | `task-01-core-handlers` |
| GAEB Tests schreiben | `task-02-gaeb-tests` |
| NL2DXF portieren | `task-03-nlp-nl2dxf` |
| cad-hub Integration | `task-04-cadhub-integration` |
| Neues Package anlegen | `new-package` |

## Wichtigste Regeln (Kurzfassung)

- **Kein Django** in keinem nl2cad-Package
- **Kein `print()`** → immer `logging.getLogger(__name__)`
- **Maßfelder immer mit Suffix**: `area_m2`, `height_m`, `thickness_m`
- **Dataclasses** (nicht Pydantic) in core/areas/gaeb/brandschutz
- **Tests zuerst** für jeden neuen Handler (oder zeitgleich)
- Nach jeder Implementierung: `uv run pytest -v` + `uv run ruff check packages/`
