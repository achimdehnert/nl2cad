---
description: Publish a Python package to PyPI
---

# Release Workflow — PyPI Publish

## Voraussetzung

`~/.pypirc` mit PyPI API Token vorhanden.

## Build + Publish

```bash
bash ~/github/platform/scripts/publish-package.sh ~/github/nl2cad/packages/nl2cad-core
bash ~/github/platform/scripts/publish-package.sh ~/github/nl2cad/packages/nl2cad-areas
# etc.
```

## Test-Upload zuerst

```bash
bash ~/github/platform/scripts/publish-package.sh ~/github/nl2cad/packages/nl2cad-core --test
```

## Verify

```bash
pip index versions nl2cad-core 2>/dev/null | head -3
```

- Git tag `v<version>` wird automatisch erstellt
- `--dry-run` für sichere Tests
