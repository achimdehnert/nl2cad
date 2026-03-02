"""
nl2cad.core.handlers.massen
=============================
MassenHandler — berechnet Flächen- und Volumenmassen aus IFCModel oder DXFModel.

Eingabe:  context["ifc_model"] ODER context["dxf_model"]
Ausgabe:  context["massen"] = MassenResult-dict
"""

from __future__ import annotations

import logging

from nl2cad.core.handlers.base import (
    BaseCADHandler,
    HandlerResult,
    HandlerStatus,
)

logger = logging.getLogger(__name__)


class MassenHandler(BaseCADHandler):
    """
    Berechnet Flaechenermittlung und Volumen aus IFC- oder DXF-Modell.

    Erwartet: context["ifc_model"] = IFCModel  ODER  context["dxf_model"] = DXFModel
    Schreibt: context["massen"] = {
        "raumflaeche_gesamt_m2": float,
        "wandflaeche_gesamt_m2": float,
        "deckenflaeche_gesamt_m2": float,
        "volumen_gesamt_m3": float,
        "raum_count": int,
    }
    """

    name = "MassenHandler"
    description = "Flaechenermittlung und Volumenberechnung (IFC/DXF)"
    required_inputs: list[str] = []
    optional_inputs: list[str] = ["ifc_model", "dxf_model"]

    def execute(self, input_data: dict) -> HandlerResult:
        result = HandlerResult(success=True, handler_name=self.name)

        ifc_model = input_data.get("ifc_model")
        dxf_model = input_data.get("dxf_model")

        if ifc_model is None and dxf_model is None:
            result.add_error(
                "Kein Modell in input_data — ifc_model oder dxf_model erwartet"
            )
            return result

        if ifc_model is not None:
            massen = self._from_ifc(ifc_model, result)
        else:
            massen = self._from_dxf(dxf_model, result)  # type: ignore[arg-type]

        result.data["massen"] = massen

        if result.success:
            result.status = HandlerStatus.SUCCESS
            logger.info(
                "[MassenHandler] raumflaeche=%.1f m2 volumen=%.1f m3 raeume=%d",
                massen["raumflaeche_gesamt_m2"],
                massen["volumen_gesamt_m3"],
                massen["raum_count"],
            )

        return result

    def _from_ifc(self, model: object, result: HandlerResult) -> dict:
        from nl2cad.core.models.ifc import IFCModel

        assert isinstance(model, IFCModel)

        rooms = model.rooms
        raumflaeche = sum(r.area_m2 for r in rooms)
        volumen = sum(r.area_m2 * r.height_m for r in rooms if r.height_m > 0)
        wandflaeche = sum(w.area_m2 for w in model.walls)
        deckenflaeche = sum(s.area_m2 for s in model.slabs)

        return {
            "raumflaeche_gesamt_m2": round(raumflaeche, 4),
            "wandflaeche_gesamt_m2": round(wandflaeche, 4),
            "deckenflaeche_gesamt_m2": round(deckenflaeche, 4),
            "volumen_gesamt_m3": round(volumen, 4),
            "raum_count": len(rooms),
        }

    def _from_dxf(self, model: object, result: HandlerResult) -> dict:
        from nl2cad.core.models.dxf import DXFModel

        assert isinstance(model, DXFModel)

        rooms = model.rooms
        raumflaeche = sum(r.area_m2 for r in rooms)

        result.add_warning(
            "DXF-Modell: Volumen nicht berechenbar (keine Höheninformation)"
        )

        return {
            "raumflaeche_gesamt_m2": round(raumflaeche, 4),
            "wandflaeche_gesamt_m2": 0.0,
            "deckenflaeche_gesamt_m2": 0.0,
            "volumen_gesamt_m3": 0.0,
            "raum_count": len(rooms),
        }
