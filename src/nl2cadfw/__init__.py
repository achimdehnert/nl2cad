"""
iil-nl2cadfw — NL2CAD Framework

Unified entry point for the nl2cad ecosystem:
- nl2cadfw.core     — IFC/DXF domain models and parsers
- nl2cadfw.areas    — DIN 277 / WoFlV area calculators
- nl2cadfw.brandschutz — Fire safety analysis
- nl2cadfw.gaeb     — GAEB tender processing
- nl2cadfw.nlp      — Natural language to CAD intent classification

Install:
    pip install iil-nl2cadfw
    pip install iil-nl2cadfw[ifc]   # with ifcopenshell
    pip install iil-nl2cadfw[nlp]   # with OpenAI
    pip install iil-nl2cadfw[all]   # everything
"""

__version__ = "0.1.0"
__all__ = ["__version__"]
