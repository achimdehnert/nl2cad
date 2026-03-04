# ADR-009: Generische Modul-Registry — DB-getrieben, Multi-Product, Multi-Tenant

| Attribut      | Wert |
| ------------- | ---- |
| **Status**    | Draft |
| **Datum**     | 2026-03-04 |
| **Autoren**   | Achim Dehnert |
| **Betrifft**  | `cad-hub` (Phase B), `nl2cad-registry` (Phase C) |
| **Verknüpft** | ADR-001 (Brandschutz), ADR-002..008 (Module) |

---

## 1. Kontext und Problemstellung

### Ist-Zustand
`docs/data/modules.json` im `nl2cad`-Repo ist die einzige Quelle für Modul-Definitionen:
- Modul hinzufügen = Git-Commit + Deployment
- Preisänderung = Git-Commit
- Kein Admin-UI
- Nur nl2cad-Module (eine Produktfamilie)
- Konfigurator (`docs/configurator.html`) liest JSON per `fetch()`

### Wachstumspfad
Die Platform umfasst **mehrere Produkt-Familien** mit je eigenen Modulen:

| Produkt-Familie | Beispiel-Module |
|----------------|-----------------|
| `nl2cad`       | core, areas, brandschutz, gaeb, nlp, explosionsschutz, … |
| `coachhub`     | basis-coaching, team-coaching, executive, 360-feedback, … |
| `writing-hub`  | blog-standard, blog-premium, whitepaper, seo-optimierung, illu-basis, illu-premium, … |
| `risk-hub`     | risk-basic, compliance, audit-trail, … |
| *(zukünftig)*  | beliebige neue Produkt-Familien |

**Kernproblem:** Jede Produktfamilie hat eigene Module, Preise, Features, Abhängigkeiten,
Tenant-Konfigurationen — und alle brauchen denselben Konfigurator-Flow (Stufe 1–3).

---

## 2. Entscheidung

**Zweistufige Migration:**

### Phase B — Registry in `cad-hub` (sofort umsetzbar)
Django-Models in `cad-hub` verwalten nl2cad-Module und Tenants.
`modules.json` wird als initiales Seed-Fixture importiert.
Konfigurator ruft `GET /api/registry/modules/?product=nl2cad` statt statischer JSON.

### Phase C — Eigenständiges `nl2cad-registry` Repo (wenn mehrere Produkt-Familien aktiv)
Separates Django-Projekt `nl2cad-registry` mit eigener Domain (`registry.iil.pet`).
Verwaltet alle Produkt-Familien, Module, Tenants, Preise plattformübergreifend.
`cad-hub`, `coachhub`, `writing-hub` etc. sind **Konsumenten** der Registry-API.

---

## 3. Datenmodell — Phase B (`cad-hub/apps/registry/`)

```python
# cad-hub/apps/registry/models.py

from django.db import models


class ProductFamily(models.Model):
    """Produktfamilie: nl2cad, coachhub, writing-hub, ..."""

    id = models.SlugField(primary_key=True)          # "nl2cad", "coachhub"
    name = models.CharField(max_length=100)           # "nl2cad BIM Suite"
    description = models.TextField(blank=True)
    landing_url = models.URLField(blank=True)
    repo_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "registry_product_family"
        verbose_name = "Produkt-Familie"
        verbose_name_plural = "Produkt-Familien"

    def __str__(self) -> str:
        return self.name


class Module(models.Model):
    """
    Ein buchbares Modul einer Produktfamilie.

    Entspricht einem Eintrag in modules.json,
    aber DB-verwaltet und Admin-editierbar.
    """

    class Status(models.TextChoices):
        STABLE  = "stable",  "Stabil (produktiv)"
        PLANNED = "planned", "In Planung"
        BETA    = "beta",    "Beta"
        DEPRECATED = "deprecated", "Veraltet"

    product   = models.ForeignKey(
        ProductFamily, on_delete=models.PROTECT, related_name="modules"
    )
    id        = models.SlugField(max_length=80)       # "brandschutz", "blog-premium"
    package   = models.CharField(max_length=120)      # "nl2cad-brandschutz"
    name      = models.CharField(max_length=120)      # "Brandschutz-Analyse"
    icon      = models.CharField(max_length=10, default="📦")
    color     = models.CharField(max_length=7, default="#2563eb")  # Hex
    tagline   = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    features  = models.JSONField(default=list)        # ["Feature 1", ...]
    deps      = models.JSONField(default=list)        # ["nl2cad-core", ...]
    is_required = models.BooleanField(default=False)  # immer aktiviert (core)
    status    = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PLANNED
    )
    adr_path  = models.CharField(max_length=255, blank=True)   # "docs/adr/ADR-001..."
    workflow_path = models.CharField(max_length=255, blank=True)
    pypi_url  = models.URLField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "registry_module"
        unique_together = [("product", "id")]
        ordering = ["product", "sort_order", "id"]
        verbose_name = "Modul"
        verbose_name_plural = "Module"
        indexes = [
            models.Index(fields=["product", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.product_id}/{self.id}"


class ModulePricing(models.Model):
    """
    Preismodell für ein Modul.

    Ermöglicht tenant-spezifische Preise (Custom Pricing)
    und zeitlich begrenzte Angebote.
    """

    class PricingType(models.TextChoices):
        STANDARD = "standard", "Standard"
        CUSTOM   = "custom",   "Individuell (Tenant-spezifisch)"
        FREE     = "free",     "Kostenlos"

    module       = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="pricing_tiers"
    )
    tenant       = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE,
        null=True, blank=True, related_name="custom_pricing"
    )  # null = Standard-Preis; gesetzt = Tenant-individuell
    pricing_type = models.CharField(
        max_length=20, choices=PricingType.choices, default=PricingType.STANDARD
    )
    setup_eur    = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    monthly_eur  = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    label        = models.CharField(max_length=100, blank=True)
    valid_from   = models.DateField(null=True, blank=True)
    valid_until  = models.DateField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "registry_module_pricing"
        verbose_name = "Modul-Preis"
        verbose_name_plural = "Modul-Preise"
        indexes = [
            models.Index(fields=["module", "tenant"]),
        ]

    def __str__(self) -> str:
        tenant_label = f" [{self.tenant_id}]" if self.tenant_id else ""
        return f"{self.module}{tenant_label}: {self.monthly_eur} €/Monat"


class Tenant(models.Model):
    """
    Gebuchter Tenant einer Produktfamilie.
    Entsteht nach Freigabe via GitHub Actions Workflow (ADR-009).
    """

    class Status(models.TextChoices):
        PENDING  = "pending",  "Ausstehend (Freigabe erwartet)"
        ACTIVE   = "active",   "Aktiv"
        INACTIVE = "inactive", "Inaktiv"
        OFFBOARDED = "offboarded", "Offboarded"

    id            = models.SlugField(primary_key=True)   # "baufirma-mueller"
    product       = models.ForeignKey(
        ProductFamily, on_delete=models.PROTECT, related_name="tenants"
    )
    name          = models.CharField(max_length=255)      # "Baufirma Müller GmbH"
    contact_email = models.EmailField()
    branch        = models.CharField(max_length=50, blank=True)
    enabled_modules = models.ManyToManyField(
        Module, related_name="tenants", blank=True
    )
    status        = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    approved_by   = models.CharField(max_length=100, blank=True)
    onboarded_at  = models.DateTimeField(null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "registry_tenant"
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        indexes = [
            models.Index(fields=["product", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.id} ({self.product_id})"


class DiscountRule(models.Model):
    """Rabatt-Regeln pro Produktfamilie (z.B. 15% ab 3 Modulen)."""

    product           = models.ForeignKey(
        ProductFamily, on_delete=models.CASCADE, related_name="discount_rules"
    )
    min_modules       = models.PositiveIntegerField(default=3)
    discount_percent  = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    label             = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "registry_discount_rule"
        verbose_name = "Rabatt-Regel"
```

---

## 4. API-Endpoint — Phase B

```python
# cad-hub/apps/registry/views.py

from django.http import JsonResponse
from django.views import View
from .models import ProductFamily, Module, ModulePricing, DiscountRule


class ModuleListView(View):
    """
    GET /api/registry/modules/?product=nl2cad
    Gibt Module-Liste im Format zurück, das der Konfigurator erwartet.
    Abwärtskompatibel zu modules.json-Format.
    """

    def get(self, request):
        product_id = request.GET.get("product", "nl2cad")

        try:
            product = ProductFamily.objects.get(id=product_id, is_active=True)
        except ProductFamily.DoesNotExist:
            return JsonResponse({"error": "Product not found"}, status=404)

        modules = (
            Module.objects
            .filter(product=product)
            .prefetch_related("pricing_tiers")
            .order_by("sort_order", "id")
        )

        discount_rule = (
            DiscountRule.objects
            .filter(product=product)
            .order_by("min_modules")
            .first()
        )

        return JsonResponse({
            "version": "2.0.0",
            "product": product_id,
            "currency": "EUR",
            "discount_threshold": discount_rule.min_modules if discount_rule else 3,
            "discount_percent": float(discount_rule.discount_percent) if discount_rule else 15,
            "modules": [_serialize_module(m) for m in modules],
        })


def _serialize_module(m: Module) -> dict:
    standard_price = (
        m.pricing_tiers.filter(tenant__isnull=True).first()
    )
    return {
        "id":          m.id,
        "package":     m.package,
        "name":        m.name,
        "icon":        m.icon,
        "color":       m.color,
        "tagline":     m.tagline,
        "description": m.description,
        "features":    m.features,
        "deps":        m.deps,
        "required":    m.is_required,
        "status":      m.status,
        "adr":         m.adr_path or None,
        "workflow":    m.workflow_path or None,
        "pypi":        m.pypi_url or None,
        "pricing": {
            "setup_eur":   float(standard_price.setup_eur)   if standard_price else 0,
            "monthly_eur": float(standard_price.monthly_eur) if standard_price else 0,
            "label":       standard_price.label              if standard_price else "",
        },
    }
```

---

## 5. Konfigurator — API-URL konfigurierbar (Vorbereitung Phase C)

`docs/configurator.html` erhält einen konfigurierbaren `DATA_URL`-Parameter:

```javascript
// Priorität: URL-Parameter > window.NL2CAD_MODULES_API > statische JSON
const DATA_URL = (
  new URLSearchParams(window.location.search).get("modules_api") ||
  window.NL2CAD_MODULES_API ||
  "./data/modules.json"
);

fetch(DATA_URL)
  .then(r => r.json())
  .then(data => { /* … */ });
```

Damit ist **ohne Code-Änderung** umschaltbar:
- `./data/modules.json` — heute (statisch)
- `https://devhub.iil.pet/api/registry/modules/?product=nl2cad` — Phase B
- `https://registry.iil.pet/api/modules/?product=nl2cad` — Phase C

---

## 6. Phase C — `nl2cad-registry` Repo-Struktur

```
nl2cad-registry/                   ← eigenständiges Django-Projekt
├── registry/
│   ├── apps/
│   │   ├── products/              # ProductFamily, Module, ModulePricing
│   │   ├── tenants/               # Tenant, TenantOnboarding
│   │   ├── billing/               # Invoice, Subscription
│   │   └── api/                   # DRF ViewSets, Serializers
│   ├── settings/
│   └── urls.py
├── fixtures/
│   ├── nl2cad_modules.json        # Import aus docs/data/modules.json
│   ├── coachhub_modules.json
│   └── writinghub_modules.json
├── docker-compose.yml
└── .github/workflows/
    ├── ci.yml
    └── deploy.yml
```

**Domain:** `registry.iil.pet`

**Produkt-Familien-Beispiele:**

| Produkt | Module-Typen |
|---------|-------------|
| `nl2cad` | core, areas, brandschutz, gaeb, nlp, explosionsschutz, … |
| `coachhub` | einzel-coaching, team-coaching, executive-coaching, 360-feedback, … |
| `writing-hub` | blog-standard, blog-premium, whitepaper, seo, illu-basis, illu-premium, … |
| `risk-hub` | risk-basic, compliance-check, audit-trail, … |

---

## 7. Migrations-Pfad (ohne Datenverlust)

```
Heute:   modules.json (statisch)
           │
           ▼ Schritt 1: Management-Command
         python manage.py import_modules_json docs/data/modules.json
           │  → legt ProductFamily + Module + ModulePricing in DB an
           │
           ▼ Schritt 2: Konfigurator-URL umstellen
         DATA_URL = https://devhub.iil.pet/api/registry/modules/?product=nl2cad
           │
           ▼ Schritt 3 (optional): Phase C Repo anlegen
         registry.iil.pet als eigenständiger Service
```

---

## 8. Abgelehnte Alternativen

### Alt. A: modules.json bleibt Master (dauerhaft)
**Abgelehnt.** Skaliert nicht für mehrere Produktfamilien, keine Admin-UI,
keine tenant-spezifischen Preise, kein Audit-Trail.

### Alt. X: GraphQL statt REST
**Zurückgestellt.** DRF REST reicht für die initiale Phase vollständig aus.
GraphQL in Phase C evaluieren wenn Konfiguratoren für 5+ Produkte live sind.

---

## 9. Konsequenzen

### Positiv
- **Admin-UI ohne Code:** neue Module, Preise, Features per Django Admin
- **Multi-Product:** ein Registry-Service für alle Produkt-Familien der Platform
- **Tenant-spezifische Preise:** Custom Pricing pro Tenant möglich
- **Konfigurator ist product-agnostisch:** `?product=coachhub` → anderen Konfigurator
- **Abwärtskompatibel:** modules.json bleibt bis Phase B vollständig funktional

### Negativ / Risiken
- **cad-hub muss produktiv laufen** bevor Phase B aktiv wird
- **Phase C = neues Deployment** — Infrastruktur-Aufwand
- **Datenkonsistenz:** `modules.json` und DB müssen synchron bleiben bis vollständige Migration

---

## 10. Implementierungs-Reihenfolge

```
Phase A (heute — abgeschlossen):
  ✅ docs/data/modules.json mit adr + workflow Feldern
  ✅ .windsurf/workflows/new-module.md
  ✅ .github/workflows/tenant-onboarding.yml

Phase B (nächster Sprint — cad-hub):
  1. cad-hub/apps/registry/ anlegen (models.py, views.py, admin.py, urls.py)
  2. Management-Command: import_modules_json
  3. GET /api/registry/modules/?product=nl2cad
  4. Konfigurator: DATA_URL konfigurierbar machen
  5. Migrations + Tests

Phase C (wenn 2+ Produkt-Familien aktiv):
  1. Repo nl2cad-registry anlegen
  2. Models aus cad-hub/apps/registry/ übernehmen
  3. Fixtures für alle Produktfamilien
  4. registry.iil.pet deployen
  5. cad-hub, coachhub, writing-hub als API-Konsumenten umstellen
```
