"""
nl2cad.core.handlers.base
==========================
Abstrakte Basis-Klassen für den Handler-Pipeline-Pattern.
Framework-agnostisch — kein Django, kein HTTP.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum

from nl2cad.core.exceptions import HandlerError, PipelineError

logger = logging.getLogger(__name__)


class HandlerStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class HandlerResult:
    """Ergebnis eines einzelnen Handlers."""

    success: bool
    handler_name: str
    status: HandlerStatus = HandlerStatus.PENDING
    data: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.success = False
        self.status = HandlerStatus.ERROR
        logger.error("[%s] %s", self.handler_name, msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)
        if self.status == HandlerStatus.SUCCESS:
            self.status = HandlerStatus.WARNING
        logger.warning("[%s] %s", self.handler_name, msg)


class BaseCADHandler(ABC):
    """
    Abstrakte Basis für alle CAD-Handler.

    Handler folgen dem Chain-of-Responsibility-Pattern:
    Jeder Handler liest aus `input_data`, verarbeitet, und gibt HandlerResult zurück.
    Die Pipeline akkumuliert alle results["data"] zum nächsten Handler.

    Implementierung:
        class MyHandler(BaseCADHandler):
            name = "MyHandler"
            description = "Was ich tue"
            required_inputs = ["ifc_model"]

            def execute(self, input_data: dict) -> HandlerResult:
                model = input_data["ifc_model"]
                result = HandlerResult(success=True, handler_name=self.name)
                # ... verarbeiten ...
                result.data["my_output"] = ...
                result.status = HandlerStatus.SUCCESS
                return result
    """

    name: str = "BaseCADHandler"
    description: str = ""
    required_inputs: list[str] = []
    optional_inputs: list[str] = []

    @abstractmethod
    def execute(self, input_data: dict) -> HandlerResult:
        """
        Führt Handler-Logik aus.

        Args:
            input_data: Akkumulierter Context der Pipeline

        Returns:
            HandlerResult mit Ergebnis-Daten
        """

    def validate_inputs(self, input_data: dict) -> list[str]:
        """Prüft ob alle required_inputs vorhanden sind."""
        missing = [k for k in self.required_inputs if k not in input_data]
        return missing

    def run(self, input_data: dict) -> HandlerResult:
        """
        Wrapper um execute() mit Validierung und Fehlerbehandlung.
        Sollte statt execute() direkt aufgerufen werden.
        """
        missing = self.validate_inputs(input_data)
        if missing:
            result = HandlerResult(success=False, handler_name=self.name)
            result.add_error(f"Fehlende Eingaben: {', '.join(missing)}")
            return result

        try:
            return self.execute(input_data)
        except HandlerError:
            raise
        except Exception as e:
            result = HandlerResult(success=False, handler_name=self.name)
            result.add_error(f"Unerwarteter Fehler: {e}")
            logger.exception("[%s] Unerwarteter Fehler", self.name)
            return result


class CADHandlerPipeline:
    """
    Sequentielle Handler-Pipeline.

    Jeder Handler erhält den akkumulierten Context aller vorherigen Handler.
    Bei Fehler stoppt die Pipeline (außer `continue_on_error=True`).

    Usage:
        pipeline = CADHandlerPipeline()
        pipeline.add(FileInputHandler())
        pipeline.add(RoomAnalysisHandler())
        pipeline.add(DIN277Handler())

        results = pipeline.run({"file_path": "gebaeude.ifc"})
        final = pipeline.get_context()
        print(final["rooms"])
    """

    def __init__(self, continue_on_error: bool = False) -> None:
        self._handlers: list[BaseCADHandler] = []
        self._results: list[HandlerResult] = []
        self._context: dict = {}
        self.continue_on_error = continue_on_error

    def add(self, handler: BaseCADHandler) -> CADHandlerPipeline:
        """Fügt Handler zur Pipeline hinzu. Chainable."""
        self._handlers.append(handler)
        return self

    def run(self, initial_context: dict | None = None) -> list[HandlerResult]:
        """
        Führt alle Handler sequenziell aus.

        Args:
            initial_context: Initiale Daten (z.B. file_path, options)

        Returns:
            Liste aller HandlerResults

        Raises:
            PipelineError: Wenn kein Handler registriert
        """
        if not self._handlers:
            raise PipelineError("Keine Handler registriert")

        self._context = initial_context or {}
        self._results = []

        for handler in self._handlers:
            logger.info("[Pipeline] Running %s", handler.name)
            result = handler.run(self._context)
            self._results.append(result)

            # Context mit Handler-Output akkumulieren
            if result.success:
                self._context.update(result.data)
            elif not self.continue_on_error:
                logger.error("[Pipeline] Abbruch bei %s", handler.name)
                break

        return self._results

    def get_context(self) -> dict:
        """Gibt den akkumulierten Context zurück."""
        return self._context

    def get_final_result(self) -> HandlerResult | None:
        """Gibt das letzte HandlerResult zurück."""
        return self._results[-1] if self._results else None

    @property
    def success(self) -> bool:
        """True wenn alle Handler erfolgreich."""
        return all(r.success for r in self._results)

    @property
    def errors(self) -> list[str]:
        """Alle Fehler aus allen Handlern."""
        return [err for r in self._results for err in r.errors]

    @property
    def warnings(self) -> list[str]:
        """Alle Warnungen aus allen Handlern."""
        return [w for r in self._results for w in r.warnings]
