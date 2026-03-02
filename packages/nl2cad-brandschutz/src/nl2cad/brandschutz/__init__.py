"""
nl2cad-brandschutz — Brandschutz-Analyse fuer IFC/DXF.

Public API:
    from nl2cad.brandschutz import BrandschutzAnalyzer
    from nl2cad.brandschutz import GebaeudeklasseHandler, GebaeudeklasseResult
    from nl2cad.brandschutz import ExplosionsschutzDokument, BeurteilungsStatus
    from nl2cad.brandschutz import BrandschutzkonzeptReport
"""

__version__ = "0.1.0"

from nl2cad.brandschutz.analyzer import BrandschutzAnalyzer
from nl2cad.brandschutz.explosionsschutz import (
    BeurteilungsStatus,
    ExplosionsschutzDokument,
    ExplosionsschutzMassnahme,
)
from nl2cad.brandschutz.gebaeudeklasse import (
    Gebaeudeklasse,
    GebaeudeklasseHandler,
    GebaeudeklasseResult,
)
from nl2cad.brandschutz.models import (
    Brandabschnitt,
    BrandschutzAnalyse,
    Brandschutzeinrichtung,
    BrandschutzKategorie,
    BrandschutzMangel,
    ExBereich,
    ExZone,
    Fluchtweg,
    MaengelSchwere,  # noqa: F401 — Teil der Public API
)
from nl2cad.brandschutz.report import BrandschutzkonzeptReport

__all__ = [
    "__version__",
    # Analyser
    "BrandschutzAnalyzer",
    # Gebaeudeklasse
    "Gebaeudeklasse",
    "GebaeudeklasseHandler",
    "GebaeudeklasseResult",
    # Explosionsschutz
    "BeurteilungsStatus",
    "ExplosionsschutzDokument",
    "ExplosionsschutzMassnahme",
    # Report
    "BrandschutzkonzeptReport",
    # Modelle
    "BrandschutzAnalyse",
    "Fluchtweg",
    "Brandabschnitt",
    "Brandschutzeinrichtung",
    "BrandschutzMangel",
    "BrandschutzKategorie",
    "ExBereich",
    "ExZone",
    "MaengelSchwere",
]
