"""
nl2cad-brandschutz — Brandschutz-Analyse für IFC/DXF.

Usage:
    from nl2cad.brandschutz.analyzer import BrandschutzAnalyzer
    from nl2cad.brandschutz.models import BrandschutzAnalyse, Fluchtweg
"""
__version__ = "0.1.0"
from nl2cad.brandschutz.analyzer import BrandschutzAnalyzer
from nl2cad.brandschutz.models import (
    BrandschutzAnalyse, Fluchtweg, Brandabschnitt,
    Brandschutzeinrichtung, BrandschutzMangel,
)
__all__ = [
    "BrandschutzAnalyzer", "BrandschutzAnalyse", "Fluchtweg",
    "Brandabschnitt", "Brandschutzeinrichtung", "BrandschutzMangel",
]
