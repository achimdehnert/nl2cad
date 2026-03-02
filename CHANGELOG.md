# Changelog

Alle nennenswerten Änderungen an `nl2cad`-Packages werden hier dokumentiert.

Format: [Keep a Changelog](https://keepachangelog.com/de/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/lang/de/)

---

## [Unreleased]

### nl2cad-core
- **NEU (Task 01):** FileInputHandler — Format-Erkennung (IFC/DXF) + Parsing in Pipeline
- **NEU (Task 01):** MassenHandler — Flaechenermittlung + Volumenberechnung (IFC/DXF)
- **NEU (Task 01):** handlers/__init__.py Public API (FileInputHandler, MassenHandler)
- Initial scaffold: IFCParser, DXFParser, BaseCADHandler, Pipeline
- Dataclasses: IFCRoom, IFCWall, IFCDoor, IFCWindow, IFCSlab, DXFLayer
- Exceptions: IFCParseError, DXFParseError, UnsupportedFormatError
- Constants: DIN277-Codes, Layer-Keywords
- **NEU:** IFCQualityChecker + IFCQualityReport + IFCQualityIssue (Vollstaendigkeitspruefung)
- **NEU:** IFCQualityHandler fuer Pipeline-Integration
- **FIX B-07:** MaengelSchwere Umlaut entfernt (ADR-Konformitaet)
- **FIX B-08:** TYPE_CHECKING entfernt in quality.py (direkter interner Import)
- **FIX B-09:** bare except in analyzer._estimate_length behoben
- **FIX W-07:** Konstanten-Duplizierung behoben (asr_a23.py, din4102.py)
- **FIX W-08:** Score-Formel vereinfacht (0.0/0.5/1.0 statt relativ)
- **FIX W-09:** CI uv sync --locked, uv lock --check
- **FIX I-06:** feuerlöscher_count → loescheinrichtungen_count
- **FIX I-07:** ExZone-String-Mismatch in constants.py behoben

### nl2cad-areas
- DIN277Calculator mit allen Nutzungsarten (NUF, VF, FF, AF, BF)
- WoFlVCalculator nach WoFlV 2004

### nl2cad-brandschutz
- BrandschutzAnalyzer fuer IFC und DXF
- Regelwerk-Checks: ASR A2.3 (Fluchtwege), DIN 4102 (Feuerwiderstand)
- Dataclasses: BrandschutzAnalyse, Fluchtweg, Brandabschnitt, ExBereich
- constants.py: Alle Norm-Versionen und Grenzwerte mit Quellenangaben
- **NEU (Milestone 1):** GebaeudeklasseHandler — MBO § 2 Abs. 3 (GK1..GK5, Hochhaus)
- **NEU (Milestone 1):** ExplosionsschutzDokument mit __post_init__ Invarianten (BetrSichV § 6)
- **NEU (Milestone 1):** BeurteilungsStatus Enum (kein bool|None, ADR B-06)
- **NEU (Milestone 1):** BrandschutzkonzeptReport — Gesamtbericht mit SHA-256 Hash
- Public API erweitert: GebaeudeklasseHandler, ExplosionsschutzDokument, BrandschutzkonzeptReport

### nl2cad-gaeb
- GAEBGenerator: X81, X83, X84, X85 XML
- GAEBGenerator: Excel-Export
- IFCX83Converter: IFC-Daten → GAEB X83

### nl2cad-nlp
- IntentClassifier: NL-Query → Intent-Erkennung
- NL2DXFGenerator: Natuerlichsprachliche Beschreibung → DXF
- NLLearningStore: Pattern-Lernen aus User-Feedback

---

<!-- Releases werden automatisch per Tag erstellt -->
