# nl2cad

**Redirect package** — installs [`iil-nl2cadfw`](https://pypi.org/project/iil-nl2cadfw/), the NL2CAD umbrella framework.

## What is NL2CAD?

NL2CAD (Natural Language to CAD) provides:

- **IFC/DXF parsing** — domain models for BIM file formats
- **DIN 277 area calculation** — compliant area calculators
- **Brandschutz** — fire safety analysis (ASR A2.3, DIN 4102)
- **GAEB** — X81-X85 cost estimation generator
- **NLP** — natural language to CAD intent classification

## Installation

```bash
pip install nl2cad        # installs iil-nl2cadfw + all sub-packages
pip install iil-nl2cadfw  # canonical package name (same thing)
```

## Usage

```python
# Both work identically:
import nl2cad
import nl2cadfw
```

## Links

- **Repository**: https://github.com/achimdehnert/nl2cad
- **iil-nl2cadfw on PyPI**: https://pypi.org/project/iil-nl2cadfw/
