"""nl2cad.gaeb.generator — GAEB X84 XML + Excel Generator."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from io import BytesIO

from .models import Leistungsverzeichnis


class GAEBGenerator:
    """Generiert GAEB XML (X81-X85) und Excel."""

    GAEB_NAMESPACE = "http://www.gaeb.de/GAEB_DA_XML/200407"

    def generate_xml(self, lv: Leistungsverzeichnis) -> BytesIO:
        """Generiert GAEB XML."""
        ns = self.GAEB_NAMESPACE
        ET.register_namespace("", ns)

        root = ET.Element(f"{{{ns}}}GAEB")
        hdr = ET.SubElement(root, f"{{{ns}}}GAEBInfo")
        ET.SubElement(hdr, f"{{{ns}}}Vers").text = "3.2"
        ET.SubElement(hdr, f"{{{ns}}}PrjInfo").text = lv.projekt_name
        # LV-Struktur
        lv_el = ET.SubElement(root, f"{{{ns}}}Award")
        for los in lv.lose:
            los_el = ET.SubElement(lv_el, f"{{{ns}}}BoQ", id=los.oz)
            ET.SubElement(los_el, f"{{{ns}}}Descr").text = los.bezeichnung
            for pos in los.positionen:
                pos_el = ET.SubElement(los_el, f"{{{ns}}}Itemlist")
                ET.SubElement(pos_el, f"{{{ns}}}Item", RNO=pos.oz)
                ET.SubElement(pos_el, f"{{{ns}}}T").text = pos.kurztext
                ET.SubElement(pos_el, f"{{{ns}}}Qty").text = str(pos.menge)
                ET.SubElement(pos_el, f"{{{ns}}}QU").text = pos.einheit
        output = BytesIO()
        ET.ElementTree(root).write(
            output, encoding="utf-8", xml_declaration=True
        )
        output.seek(0)
        return output

    def generate_excel(self, lv: Leistungsverzeichnis) -> BytesIO:
        """Generiert Excel-LV."""
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Leistungsverzeichnis"
        ws.append(["OZ", "Kurztext", "Menge", "Einheit", "EP", "GP"])
        for los in lv.lose:
            ws.append([los.oz, los.bezeichnung, "", "", "", ""])
            for pos in los.positionen:
                ws.append(
                    [
                        pos.oz,
                        pos.kurztext,
                        float(pos.menge),
                        pos.einheit,
                        float(pos.einheitspreis),
                        float(pos.gesamtpreis),
                    ]
                )
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output
