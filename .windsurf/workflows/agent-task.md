---
description: Agent Task ausführen — ADR-086-konformer Sprint-Workflow für nl2cad
source_adr: ADR-086
last_reviewed: 2026-03-03
review_interval_days: 30
version: "1.0"
---

# nl2cad — Agent Task Workflow (ADR-086)

## Schritt 0: Pflicht-Setup

// turbo
1. Lies `docs/AGENT_HANDOVER.md` vollständig — Repo-Kontext und Regeln
2. Lies das verlinkter GitHub Issue (agent-task Template)
3. Führe Baseline-Check aus:
   ```bash
   uv run pytest -v --tb=short 2>&1 | tail -5
   uv run ruff check packages/ 2>&1 | tail -3
   ```
4. Stelle sicher dass alle Tests grün sind BEVOR du anfängst

## Schritt 1: Scope-Lock festlegen (ADR-081)

Aus dem Issue `affected_paths` ableiten:

- **Erlaubte Pfade**: nur was im Issue steht
- **Immer verboten** (auch wenn nicht im Issue): `migrations/`, `.env*`, `config/settings/prod*`, `*.pem`, `*.key`
- **Max. Dateien**: 10 (bugfix), 30 (feature), 50 (refactor)
- **Keine Deletes** (außer explizit im Issue: `allow_delete: true`)

## Schritt 2: Feature-Branch erstellen

```bash
git checkout -b ai/developer/<task-id>
```

## Schritt 3: Implementieren

Reihenfolge laut AGENTS.md:

1. **Model/Dataclass** in `models.py` des betroffenen Packages
2. **Service/Handler** in `services/` oder `handlers/`
3. **Test** schreiben — KEINE Mocks für Parser-Tests, echte Fixtures verwenden
4. **`__init__.py`** Public API updaten
5. **`CHANGELOG.md`** Eintrag unter `[Unreleased]`

## Schritt 4: Quality Gates (Post-Execution)

// turbo
Alle müssen grün sein BEVOR PR:

```bash
uv run pytest packages/nl2cad-PACKAGE/ -v --tb=short --cov=packages/nl2cad-PACKAGE/src
uv run ruff check packages/
uv run ruff format --check packages/
uv run mypy packages/nl2cad-PACKAGE/src
```

Bei Failure → Fix, dann erneut prüfen. Nicht weiter bei roten Tests.

## Schritt 5: AGENTS.md-Compliance prüfen

- [ ] Kein `print()` → nur `logging.getLogger(__name__)`
- [ ] Maßfelder mit Einheit-Suffix (`area_m2`, `height_m`, ...)
- [ ] Dataclasses (nicht Pydantic) in core/areas/gaeb/brandschutz
- [ ] Keine verbotenen Imports: Django, requests, Celery, Redis
- [ ] Exceptions via `nl2cad.core.exceptions`

## Schritt 6: PR erstellen

```bash
git push -u origin ai/developer/<task-id>
```

PR-Body: `.github/PULL_REQUEST_TEMPLATE/agent-pr.md` ausfüllen.
- Verlinktes Issue: `Closes #NNN`
- Acceptance Criteria aus Issue übernehmen + Status markieren
- Test-Ausgabe einfügen

## Schritt 7: Performance-Log Eintrag

Nach erfolgreichem Merge — Eintrag in `platform/docs/agent-team/performance-log.md`
(falls Zugriff vorhanden):

```
| nl2cad | <task-id> | <task-type> | <duration> | <guardian-pass> | <review-rounds> |
```

---

## Wichtige Regeln (Kurzfassung)

- **Kein Django** — reine Python-Library
- **Kein Pydantic** in core/areas/gaeb/brandschutz
- **`uv run pytest`** muss `.venv/bin/python` nutzen (nicht System-Python)
- **IFC-Tests** skippen sauber wenn `ifcopenshell` nicht verfügbar
- **Coverage ≥ 80%** — kein Rückschritt erlaubt
