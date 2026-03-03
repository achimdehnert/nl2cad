# Agent PR Checkliste (ADR-086)

## Verlinktes Issue

Closes #<!-- Issue-Nummer -->

## Task-Typ

<!-- feature | bugfix | refactor | test | infra | adr -->

## Zusammenfassung

<!-- Was wurde implementiert? Warum? (≤ 500 Zeichen) -->

## Acceptance Criteria

<!-- Aus dem Issue übernehmen, Status markieren -->

- [ ] Criterion 1
- [ ] Criterion 2

## Scope-Check (ADR-081)

- [ ] Nur Dateien in `affected_paths` geändert
- [ ] Keine `migrations/`, `.env*`, `prod`-Settings geändert
- [ ] `allow_delete = False` — keine Dateien gelöscht (außer explizit erlaubt)

## Quality Gates

- [ ] `uv run pytest -v` → 0 Failures
- [ ] `uv run ruff check packages/` → 0 Errors
- [ ] Coverage-Delta ≥ 0% (kein Rückschritt)
- [ ] `uv run mypy packages/nl2cad-PACKAGE/src` → 0 Errors

## AGENTS.md-Compliance

- [ ] Kein `print()` — nur `logging.getLogger(__name__)`
- [ ] Maßfelder mit Einheit-Suffix (`area_m2`, `height_m`, ...)
- [ ] Dataclasses (nicht Pydantic) in core/areas/gaeb/brandschutz
- [ ] Keine verbotenen Imports (Django, requests, Celery, Redis)
- [ ] `CHANGELOG.md` unter `[Unreleased]` aktualisiert

## Test-Nachweis

```
# Ausgabe von: uv run pytest packages/nl2cad-PACKAGE/ -v --tb=short
```

<!-- Hier kurze Zusammenfassung oder Screenshot einfügen -->
