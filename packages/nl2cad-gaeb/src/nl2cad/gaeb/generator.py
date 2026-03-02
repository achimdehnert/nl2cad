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
        root = ET.Element("GAEB", xmlns=self.GAEB_NAMESPACE)
        hdr = ET.SubElement(root, "GAEBInfo")
        ET.SubElement(hdr, "Vers").text = "3.2"
        ET.SubElement(hdr, "PrjInfo").text = lv.projekt_name
        # LV-Struktur
        lv_el = ET.SubElement(root, "Award")
        for los in lv.lose:
            los_el = ET.SubElement(lv_el, "BoQ", id=los.oz)
            ET.SubElement(los_el, "Descr").text = los.bezeichnung
            for pos in los.positionen:
                pos_el = ET.SubElement(los_el, "Itemlist")
                ET.SubElement(pos_el, "Item", RNO=pos.oz)
                ET.SubElement(pos_el, "T").text = pos.kurztext
                ET.SubElement(pos_el, "Qty").text = str(pos.menge)
                ET.SubElement(pos_el, "QU").text = pos.einheit
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
