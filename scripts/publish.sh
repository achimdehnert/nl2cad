#!/usr/bin/env bash
# =============================================================================
# publish.sh — Build + publish all nl2cad sub-packages to PyPI
# Based on: platform/scripts/publish-monorepo.sh
# =============================================================================
#
# USAGE:
#   bash scripts/publish.sh                        # all 5 packages
#   bash scripts/publish.sh --only nl2cad-core     # single package
#   bash scripts/publish.sh --dry-run              # build only, no upload
#   bash scripts/publish.sh --test                 # upload to TestPyPI
#   PYPI_TOKEN=pypi-xxx bash scripts/publish.sh    # non-interactive (CI)
#
# TOKEN: never pass as CLI argument — use env var or interactive prompt.
# =============================================================================
set -euo pipefail

# ── Colours ───────────────────────────────────────────────────────────────────
_BOLD='\033[1m'; _GREEN='\033[0;32m'; _YELLOW='\033[1;33m'
_RED='\033[0;31m'; _CYAN='\033[0;36m'; _RESET='\033[0m'

ok()     { echo -e "${_GREEN}[publish] ✓${_RESET} $*"; }
warn()   { echo -e "${_YELLOW}[publish] ⚠${_RESET}  $*" >&2; }
err()    { echo -e "${_RED}[publish] ✗${_RESET} $*" >&2; exit 1; }
info()   { echo -e "${_CYAN}[publish]  $*${_RESET}"; }
header() { echo -e "\n${_BOLD}[publish] ══ $* ══${_RESET}"; }

# ── nl2cad packages ──────────────────────────────────────────────────────────
DEFAULT_PACKAGES=(nl2cad-core nl2cad-areas nl2cad-brandschutz nl2cad-gaeb nl2cad-nlp)

# ── Argument parsing ─────────────────────────────────────────────────────────
TEST_PYPI=false
DRY_RUN=false
ONLY_PACKAGES=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --test)    TEST_PYPI=true;  shift ;;
        --dry-run) DRY_RUN=true;    shift ;;
        --only)
            [[ -z "${2:-}" ]] && err "--only requires a comma-separated package list"
            ONLY_PACKAGES="$2"; shift 2 ;;
        --only=*)  ONLY_PACKAGES="${1#--only=}"; shift ;;
        -h|--help) grep '^#' "$0" | grep -v '#!/' | sed 's/^# \?//'; exit 0 ;;
        *) err "Unknown argument: $1. Use --help for usage." ;;
    esac
done

if [[ -n "$ONLY_PACKAGES" ]]; then
    IFS=',' read -ra PACKAGES <<< "$ONLY_PACKAGES"
else
    PACKAGES=("${DEFAULT_PACKAGES[@]}")
fi

# ── Repo root ────────────────────────────────────────────────────────────────
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# ── uv check ─────────────────────────────────────────────────────────────────
command -v uv &>/dev/null || err "'uv' not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"

# ── Token — secure read only (no CLI arg, no history leakage) ────────────────
if ! $DRY_RUN; then
    if [[ -z "${PYPI_TOKEN:-}" ]]; then
        $TEST_PYPI \
            && read -r -s -p "[publish] TestPyPI token (pypi-...): " PYPI_TOKEN \
            || read -r -s -p "[publish] PyPI token (pypi-...): " PYPI_TOKEN
        echo
    fi
    [[ -z "${PYPI_TOKEN:-}" ]] && err "No token provided. Set PYPI_TOKEN or enter interactively."
    [[ "$PYPI_TOKEN" == pypi-* ]] || warn "Token does not start with 'pypi-' — double-check format"
fi

# ── Header ───────────────────────────────────────────────────────────────────
header "nl2cad publish"
info "Packages : ${PACKAGES[*]}"
info "uv       : $(uv --version 2>&1 | head -1)"
$TEST_PYPI && info "Target   : TestPyPI" || info "Target   : PyPI (production)"
$DRY_RUN   && warn  "DRY-RUN — build only, no upload"

# ── Git state ────────────────────────────────────────────────────────────────
header "Git state"
if git rev-parse --git-dir &>/dev/null; then
    DIRTY="$(git status --porcelain | wc -l | tr -d ' ')"
    info "Branch : $(git rev-parse --abbrev-ref HEAD) @ $(git rev-parse --short HEAD)"
    [[ "$DIRTY" -gt 0 ]] \
        && warn "$DIRTY uncommitted change(s)" \
        || ok "Working tree clean"
fi

# ── Build ────────────────────────────────────────────────────────────────────
header "Build"
rm -rf dist/
mkdir -p dist/

for pkg in "${PACKAGES[@]}"; do
    info "Building: $pkg"
    uv build --package "$pkg" || err "Build failed for $pkg"
    ok "Built: $pkg"
done

ARTIFACT_COUNT="$(ls dist/*.whl dist/*.tar.gz 2>/dev/null | wc -l | tr -d ' ')"
ok "$ARTIFACT_COUNT artifact(s) in dist/"
ls dist/ | sed 's/^/    /'

# ── Upload ───────────────────────────────────────────────────────────────────
header "Upload"
if $DRY_RUN; then
    warn "DRY-RUN — skipping upload"
    echo "  Would run: uv publish dist/* --token pypi-***"
elif $TEST_PYPI; then
    uv publish dist/* \
        --publish-url "https://test.pypi.org/legacy/" \
        --token "$PYPI_TOKEN"
    ok "Published to TestPyPI"
else
    uv publish dist/* --token "$PYPI_TOKEN"
    ok "Published to PyPI"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${_BOLD}[publish] ══ Done ══${_RESET}"
for pkg in "${PACKAGES[@]}"; do
    if $DRY_RUN; then
        echo "  $pkg  (dry-run, not uploaded)"
    elif $TEST_PYPI; then
        echo "  https://test.pypi.org/project/$pkg/"
    else
        echo "  https://pypi.org/project/$pkg/"
    fi
done
echo ""
