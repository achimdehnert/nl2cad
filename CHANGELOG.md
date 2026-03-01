# Changelog

Alle nennenswerten Änderungen an `nl2cad`-Packages werden hier dokumentiert.

Format: [Keep a Changelog](https://keepachangelog.com/de/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/lang/de/)

---

## [Unreleased]

### nl2cad-core
- Initial scaffold: IFCParser, DXFParser, BaseCADHandler, Pipeline
- Dataclasses: IFCRoom, IFCWall, IFCDoor, IFCWindow, IFCSlab, DXFLayer
- Exceptions: IFCParseError, DXFParseError, UnsupportedFormatError
- Constants: DIN277-Codes, Layer-Keywords

### nl2cad-areas
- DIN277Calculator mit allen Nutzungsarten (NUF, VF, FF, AF, BF)
- WoFlVCalculator nach WoFlV 2004

### nl2cad-brandschutz
- BrandschutzAnalyzer für IFC und DXF
- Regelwerk-Checks: ASR A2.3 (Fluchtwege), DIN 4102 (Feuerwiderstand)
- Dataclasses: BrandschutzAnalyse, Fluchtweg, Brandabschnitt, ExBereich

### nl2cad-gaeb
- GAEBGenerator: X81, X83, X84, X85 XML
- GAEBGenerator: Excel-Export
- IFCX83Converter: IFC-Daten → GAEB X83

### nl2cad-nlp
- IntentClassifier: NL-Query → Intent-Erkennung
- NL2DXFGenerator: Natürlichsprachliche Beschreibung → DXF
- NLLearningStore: Pattern-Lernen aus User-Feedback

---

<!-- Releases werden automatisch per Tag erstellt -->
