---
description: Quality Gate vor Publish
---

# Repo Health Check

## python-package

```bash
python3 -c "
import tomllib
d = tomllib.load(open('pyproject.toml','rb'))['project']
fields = ['name','version','description','readme','authors']
print('MISSING:', [f for f in fields if not d.get(f)] or 'none')
"
```

- [ ] `test.yml` + `publish.yml` mit `needs: test`

```bash
python3 ~/github/platform/tools/repo_health_check.py --profile python-package --path .
```
