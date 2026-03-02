---
description: cad-hub auf nl2cad-* umstellen — vendor/ durch echte Package-Imports ersetzen
---

# Task 04 — cad-hub Integration

## Kontext

Wenn Tasks 01-03 abgeschlossen sind, kann `cad-hub` (Django-App) die nl2cad-Library
direkt nutzen statt die Logik selbst zu implementieren.

**Ziel:** Django-App wird zum thin wrapper. Business-Logik liegt in nl2cad-*.

## Voraussetzungen prüfen

Bevor du anfängst:
```bash
# In nl2cad Repo: alle Packages bauen
cd /path/to/achimdehnert/nl2cad
uv run pytest -v   # alle Tests grün?

# In cad-hub Repo:
cd /path/to/achimdehnert/cad-hub
python manage.py test  # Baseline: alle Tests grün?
```

## Schritt 1 — nl2cad in cad-hub requirements.txt

**Zieldatei:** `cad-hub/requirements.txt`

Füge hinzu (vor erstem Release: git-URL, danach PyPI):

```
# nl2cad-* Packages
# Option A: Während Entwicklung (vor PyPI-Release)
nl2cad-core @ git+https://github.com/achimdehnert/nl2cad.git#subdirectory=packages/nl2cad-core
nl2cad-areas @ git+https://github.com/achimdehnert/nl2cad.git#subdirectory=packages/nl2cad-areas
nl2cad-brandschutz @ git+https://github.com/achimdehnert/nl2cad.git#subdirectory=packages/nl2cad-brandschutz
nl2cad-gaeb @ git+https://github.com/achimdehnert/nl2cad.git#subdirectory=packages/nl2cad-gaeb
nl2cad-nlp @ git+https://github.com/achimdehnert/nl2cad.git#subdirectory=packages/nl2cad-nlp

# Option B: Nach PyPI-Release
# nl2cad-core>=0.1.0
# nl2cad-areas>=0.1.0
# nl2cad-brandschutz>=0.1.0
# nl2cad-gaeb>=0.1.0
# nl2cad-nlp>=0.1.0
```

Entferne dann aus `vendor/`:
- `vendor/nl2cad/` (falls vorhanden)

## Schritt 2 — IFC-Handler umstellen

**Zieldatei:** `cad-hub/apps/ifc/handlers/room_analysis.py`

**Vorher (cad-hub intern):**
```python
# Eigene RoomInfo Dataclass, eigener Parser-Code
from apps.ifc.handlers.area_classifier import AreaCategory
```

**Nachher (nl2cad-Library):**
```python
from nl2cad.core.models.ifc import IFCModel, IFCRoom
from nl2cad.core.handlers.base import BaseCADHandler, HandlerResult, HandlerStatus
from nl2cad.areas.din277 import DIN277Calculator
```

Die Django-Handler-Klasse delegiert an nl2cad:
```python
class RoomAnalysisHandler(BaseCADHandler):
    name = "RoomAnalysisHandler"

    def execute(self, input_data: dict) -> HandlerResult:
        result = HandlerResult(success=True, handler_name=self.name,
                               status=HandlerStatus.RUNNING)

        ifc_model = input_data.get("ifc_model")
        dxf_model = input_data.get("dxf_model")

        if ifc_model:
            calc = DIN277Calculator()
            din277 = calc.calculate_from_ifc(ifc_model)
            result.data["rooms"] = ifc_model.to_dict()["rooms"]
            result.data["din277"] = din277.to_dict()
            result.data["total_area_m2"] = ifc_model.total_area_m2

        result.status = HandlerStatus.SUCCESS
        return result
```

## Schritt 3 — Brandschutz-Handler umstellen

**Zieldatei:** `cad-hub/apps/brandschutz/handlers/brandschutz.py`

```python
# Vorher: Eigene Layer-Erkennung, eigene Dataclasses
# Nachher: Delegation an nl2cad-brandschutz

from nl2cad.brandschutz.analyzer import BrandschutzAnalyzer

class BrandschutzHandler(BaseCADHandler):
    def execute(self, input_data: dict) -> HandlerResult:
        result = HandlerResult(success=True, handler_name=self.name,
                               status=HandlerStatus.RUNNING)
        analyzer = BrandschutzAnalyzer()
        format_type = input_data.get("format", "dxf")
        loader = input_data.get("loader")

        if format_type == "ifc":
            analyse = analyzer.analyze_ifc(input_data["ifc_model"])
        else:
            analyse = analyzer.analyze_dxf(loader,
                                           etage=input_data.get("etage", "EG"))

        result.data["brandschutz"] = analyse.to_dict()
        result.data["hat_kritische_maengel"] = analyse.hat_kritische_maengel
        result.status = HandlerStatus.SUCCESS
        return result
```

## Schritt 4 — GAEB Export umstellen

**Zieldatei:** `cad-hub/apps/ifc/views_export.py`

```python
# Vorher: Eigene GAEBGenerator-Klasse
# Nachher:
from nl2cad.gaeb.converter import IFCX83Converter
from nl2cad.gaeb.generator import GAEBGenerator

class ExportGAEBView(View):
    def get(self, request, model_id):
        ifc_model = get_object_or_404(IFCModel, pk=model_id)

        # IFC Django-Model → dict für nl2cad
        ifc_data = {
            "rooms": list(ifc_model.rooms.values("name", "number", "area", "perimeter")),
            # area → area_m2 Mapping!
        }

        converter = IFCX83Converter()
        output = converter.convert_to_x83(
            ifc_data,
            projekt_name=ifc_model.project.name,
        )
        response = HttpResponse(output.read(), content_type="application/xml")
        response["Content-Disposition"] = f'attachment; filename="LV_{ifc_model.project.name}.x83"'
        return response
```

**Achtung:** Django-Feldname `area` muss auf nl2cad-Feldname `area_m2` gemappt werden!
Das ist das Normalisierungsproblem aus ADR-034. Lösung: Mapping-Dict oder Property.

## Schritt 5 — Regressionstests

```bash
cd cad-hub
pip install -r requirements.txt   # nl2cad-* installieren
python manage.py test apps.ifc apps.brandschutz apps.avb
```

Falls Tests brechen: Feldname-Mapping zwischen Django-ORM (`area`) und
nl2cad-Dataclasses (`area_m2`) prüfen.

## Schritt 6 — vendor/ aufräumen

Dateien die nach erfolgreicher Integration aus `cad-hub/vendor/` entfernt werden:
- Alle nl2cad-related Code (wenn er noch dort liegt)

Dateien die BLEIBEN (separate Platform-Packages):
- `vendor/chat_agent/`
- `vendor/creative_services/`
- `vendor/django_tenancy/`

## Definition of Done

- [ ] `requirements.txt` enthält nl2cad-* Abhängigkeiten
- [ ] `RoomAnalysisHandler` delegiert an `nl2cad.areas.din277`
- [ ] `BrandschutzHandler` delegiert an `nl2cad.brandschutz.analyzer`
- [ ] GAEB Export nutzt `nl2cad.gaeb.converter`
- [ ] `python manage.py test` → keine Regression
- [ ] `vendor/` von nl2cad-Code befreit
