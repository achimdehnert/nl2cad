"""nl2cad.gaeb.converter — IFC → GAEB X83 Konverter."""
from __future__ import annotations
from decimal import Decimal
from io import BytesIO
from .generator import GAEBGenerator
from .models import GAEBPhase, Leistungsverzeichnis, LosGruppe, Position


class IFCX83Converter:
    """Konvertiert IFCModel.to_dict() → GAEB X83 XML."""

    def __init__(self) -> None:
        self._generator = GAEBGenerator()

    def convert_to_x83(
        self,
        ifc_data: dict,
        projekt_name: str,
        projekt_nummer: str = "",
        auftraggeber: str = "",
        include_prices: bool = False,
    ) -> BytesIO:
        lv = self._build_lv(ifc_data, projekt_name, projekt_nummer, auftraggeber, include_prices)
        return self._generator.generate_xml(lv)

    def convert_to_excel(self, ifc_data: dict, projekt_name: str, **kwargs) -> BytesIO:
        lv = self._build_lv(ifc_data, projekt_name, **kwargs)
        return self._generator.generate_excel(lv)

    def _build_lv(self, ifc_data: dict, projekt_name: str,
                  projekt_nummer: str = "", auftraggeber: str = "",
                  include_prices: bool = False) -> Leistungsverzeichnis:
        lv = Leistungsverzeichnis(
            projekt_name=projekt_name,
            projekt_nummer=projekt_nummer,
            auftraggeber=auftraggeber,
            phase=GAEBPhase.X83,
        )
        rooms = ifc_data.get("rooms", [])
        if rooms:
            positionen = [
                Position(
                    oz=f"01.{i+1:03d}",
                    kurztext=f"Bodenbelag {r['name']}",
                    menge=Decimal(str(round(r["area_m2"], 2))),
                    einheit="m²",
                )
                for i, r in enumerate(rooms)
            ]
            lv.lose.append(LosGruppe(oz="01", bezeichnung="Bodenbeläge", positionen=positionen))
        return lv
