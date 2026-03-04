# nl2cad — Python Library für BIM/CAD-Verarbeitung

[![CI](https://github.com/achimdehnert/nl2cad/actions/workflows/test.yml/badge.svg)](https://github.com/achimdehnert/nl2cad/actions/workflows/test.yml)
[![PyPI nl2cad-core](https://img.shields.io/pypi/v/nl2cad-core.svg?label=nl2cad-core)](https://pypi.org/project/nl2cad-core/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Framework-agnostische Python-Library für IFC/DXF-Verarbeitung, DIN 277, Brandschutz und GAEB-Export.

## Packages

| Package | PyPI | Beschreibung |
|---------|------|--------------|
| `nl2cad-core` | [![PyPI](https://img.shields.io/pypi/v/nl2cad-core.svg)](https://pypi.org/project/nl2cad-core/) | IFC/DXF Parser, Handler-Pipeline, Dataclasses |
| `nl2cad-areas` | [![PyPI](https://img.shields.io/pypi/v/nl2cad-areas.svg)](https://pypi.org/project/nl2cad-areas/) | DIN 277 & WoFlV Flächenrechner |
| `nl2cad-brandschutz` | [![PyPI](https://img.shields.io/pypi/v/nl2cad-brandschutz.svg)](https://pypi.org/project/nl2cad-brandschutz/) | Brandschutz-Analyse, ASR A2.3, DIN 4102 |
| `nl2cad-gaeb` | [![PyPI](https://img.shields.io/pypi/v/nl2cad-gaeb.svg)](https://pypi.org/project/nl2cad-gaeb/) | GAEB X81–X85 Generator |
| `nl2cad-nlp` | [![PyPI](https://img.shields.io/pypi/v/nl2cad-nlp.svg)](https://pypi.org/project/nl2cad-nlp/) | Natural Language → CAD Intent & NL2DXF |

## Quick Start

```bash
pip install nl2cad-core nl2cad-areas nl2cad-brandschutz nl2cad-gaeb
```

```python
from nl2cad.core.parsers import IFCParser
from nl2cad.areas.din277 import DIN277Calculator
from nl2cad.brandschutz.analyzer import BrandschutzAnalyzer
from nl2cad.gaeb.converter import IFCX83Converter

# IFC parsen
parser = IFCParser()
model = parser.parse("gebaeude.ifc")

# DIN 277 berechnen
calc = DIN277Calculator()
result = calc.calculate(model.rooms)
print(f"NUF: {result.nutzungsflaeche_m2:.1f} m²")

# Brandschutz analysieren
analyzer = BrandschutzAnalyzer()
bs_result = analyzer.analyze(model)
for mangel in bs_result.maengel:
    print(f"⚠️  {mangel.beschreibung}")

# GAEB X83 exportieren
converter = IFCX83Converter()
xml_bytes = converter.convert_to_x83(model, projekt_name="Neubau EFH")
```

## Development

```bash
# Repo klonen
git clone https://github.com/achimdehnert/nl2cad.git
cd nl2cad

# uv installieren (falls nicht vorhanden)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Workspace setup (alle Packages als editable)
uv sync --all-packages

# Tests
uv run pytest

# Linting
uv run ruff check packages/
uv run mypy packages/
```

## Für Coding Agents

→ Lies zuerst [AGENTS.md](AGENTS.md) — enthält alle Konventionen, Package-Grenzen und Workflows.

## Architektur

```
nl2cad-nlp
    └── nl2cad-brandschutz ──┐
    └── nl2cad-gaeb          ├──→ nl2cad-core (ifcopenshell, ezdxf)
    └── nl2cad-areas         │
        └── nl2cad-core ─────┘
```

## License

MIT — siehe [LICENSE](LICENSE)
