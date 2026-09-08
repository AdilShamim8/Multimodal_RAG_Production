#!/usr/bin/env bash
# =============================================================================
# build_release.sh — build the production-agentic-rag.zip release
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

VERSION="${1:-1.0.0}"
ZIP_NAME="production-agentic-rag.zip"

echo "Building release: $ZIP_NAME (version $VERSION)"

# Clean
echo "Cleaning build artifacts..."
rm -rf .venv .mypy_cache .pytest_cache .ruff_cache .coverage htmlcov
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
rm -rf apps/web/.next apps/web/node_modules 2>/dev/null || true
rm -rf data/embeddings/*.bin 2>/dev/null || true
rm -rf .git 2>/dev/null || true

# Validate
echo "Validating release..."
./scripts/validate_release.sh

# Zip
echo "Creating ZIP..."
cd ..
rm -f "$ZIP_NAME"
zip -r "$ZIP_NAME" "$(basename "$REPO_ROOT")" \
    -x "*/.venv/*" "*/node_modules/*" "*/__pycache__/*" "*/.git/*" "*.pyc" \
    -x "*/.mypy_cache/*" "*/.pytest_cache/*" "*/.ruff_cache/*" \
    -x "*/.coverage" "*/htmlcov/*" "*/.next/*"

echo ""
echo "✅ Release built: $(pwd)/$ZIP_NAME"
echo "Size: $(du -h "$ZIP_NAME" | cut -f1)"
echo ""
echo "Validate by extracting:"
echo "  unzip $ZIP_NAME -d /tmp/validate"
echo "  cd /tmp/validate/$(basename "$REPO_ROOT")"
echo "  cat README.md"
