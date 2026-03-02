"""
nl2cad.core.handlers.ifc_quality
==================================
IFCQualityHandler — Pipeline-Integration des IFCQualityCheckers.

Bricht Pipeline bei KRITISCH ab (result.success=False).
Haengt IFCQualityReport als "quality_report" in den Pipeline-Context.

Implementierungsreihenfolge: Schritt 1 (vor GebaeudeklasseHandler).
"""

from __future__ import annotations

import logging

from nl2cad.core.exceptions import IFCParseError
from nl2cad.core.handlers.base import (
    BaseCADHandler,
    HandlerResult,
    HandlerStatus,
)
from nl2cad.core.quality import IFCQualityChecker

logger = logging.getLogger(__name__)


class IFCQualityHandler(BaseCADHandler):
    """
    Pipeline-Handler: Prueft IFCModel auf Vollstaendigkeit.

    Erwartet: context["ifc_model"] = IFCModel
    Schreibt: context["quality_report"] = IFCQualityReport

    Bei KRITISCH-Issues: result.success=False, Pipeline stoppt
    (ausser continue_on_error=True).
    Bei WARNUNG: result.success=True, Warnungen in result.warnings.

    Usage in Pipeline:
        pipeline = CADHandlerPipeline()
        pipeline.add(FileInputHandler())
        pipeline.add(IFCQualityHandler())       # <- Schritt 1
        pipeline.add(GebaeudeklasseHandler())   # <- abhaengig von quality_report
    """

    name = "IFCQualityHandler"
    description = "IFC-Vollstaendigkeitspruefung (Geschosse, Raeume, Flaechen)"
    required_inputs = ["ifc_model"]

    def __init__(self, raise_on_critical: bool = False) -> None:
        """
        Args:
            raise_on_critical: Bei True wird IFCParseError geworfen statt
                               nur result.success=False zu setzen.
                               Default False (Pipeline-Abbruch via success=False).
        """
        self._checker = IFCQualityChecker()
        self._raise_on_critical = raise_on_critical

    def execute(self, input_data: dict) -> HandlerResult:
        """Fuehrt IFC-Qualitaetspruefung durch."""
        result = HandlerResult(success=True, handler_name=self.name)
        model = input_data["ifc_model"]

        report = self._checker.check(model)
        result.data["quality_report"] = report

        for issue in report.issues:
            from nl2cad.core.quality import SEVERITY_KRITISCH, SEVERITY_WARNUNG

            if issue.severity == SEVERITY_KRITISCH:
                result.add_error(
                    f"[{issue.field_path}] {issue.message}"
                    + (f" (GUID: {issue.ifc_guid})" if issue.ifc_guid else "")
                )
            elif issue.severity == SEVERITY_WARNUNG:
                result.add_warning(f"[{issue.field_path}] {issue.message}")

        if not report.is_valid:
            if self._raise_on_critical:
                kritisch = "; ".join(
                    i.message for i in report.kritische_issues
                )
                raise IFCParseError(
                    f"IFC-Qualitaetspruefung fehlgeschlagen: {kritisch}"
                )
            result.status = HandlerStatus.ERROR
            logger.error(
                "[IFCQualityHandler] %d kritische Issues — Pipeline wird abgebrochen",
                len(report.kritische_issues),
            )
        else:
            result.status = (
                HandlerStatus.WARNING
                if report.warnungen
                else HandlerStatus.SUCCESS
            )
            logger.info(
                "[IFCQualityHandler] score=%.1f warnungen=%d",
                report.completeness_score,
                len(report.warnungen),
            )

        return result
