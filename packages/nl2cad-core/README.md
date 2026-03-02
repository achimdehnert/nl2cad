# nl2cad-core

IFC/DXF domain models, parsers, handler pipeline and quality checks for the nl2cad ecosystem.

## Installation

```bash
pip install nl2cad-core
```

## Packages

- `nl2cad.core.models` — IFCModel, IFCRoom, DXFModel, ...
- `nl2cad.core.parsers` — IFCParser, DXFParser
- `nl2cad.core.handlers` — BaseCADHandler, CADHandlerPipeline, IFCQualityHandler
- `nl2cad.core.quality` — IFCQualityChecker, IFCQualityReport
- `nl2cad.core.exceptions` — IFCParseError, DXFParseError, ...
