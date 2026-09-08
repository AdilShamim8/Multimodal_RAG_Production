#!/usr/bin/env bash
# =============================================================================
# validate_release.sh — verify the release meets all requirements
# Exits 0 if valid, 1 if not.
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "Validating release in: $REPO_ROOT"
echo ""

FAIL=0

check_file() {
    if [ -f "$1" ]; then
        echo "  [OK] $1"
    else
        echo "  [MISSING] $1"
        FAIL=1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo "  [OK] $1/"
    else
        echo "  [MISSING] $1/"
        FAIL=1
    fi
}

echo "=== Required top-level files ==="
check_file README.md
check_file QUICKSTART.md
check_file ARCHITECTURE.md
check_file SECURITY.md
check_file CHANGELOG.md
check_file RELEASE_NOTES.md
check_file STEP_BY_STEP_GUIDE.md
check_file RELEASE_CHECKLIST.md
check_file Makefile
check_file pyproject.toml
check_file docker-compose.yml
check_file .env.example
check_file .gitignore

echo ""
echo "=== Required directories ==="
check_dir apps/api
check_dir apps/web
check_dir src
check_dir tests
check_dir evals
check_dir prompts
check_dir configs
check_dir docs
check_dir infra
check_dir docker
check_dir .github/workflows

echo ""
echo "=== Required source modules ==="
check_dir src/ingestion
check_dir src/retrieval
check_dir src/reranking
check_dir src/agents
check_dir src/memory
check_dir src/citations
check_dir src/security
check_dir src/evaluation
check_dir src/observability
check_dir src/core
check_dir src/llm

echo ""
echo "=== Required docs ==="
check_dir docs/architecture
check_dir docs/research
check_dir docs/product
check_dir docs/decisions
check_dir docs/operations
check_dir docs/learning
check_dir docs/security

echo ""
echo "=== Required eval artifacts ==="
check_file evals/datasets/golden.jsonl
check_file evals/datasets/golden_smoke.jsonl
check_dir evals/baselines
check_dir evals/reports

echo ""
echo "=== Required prompts ==="
check_dir prompts/v1

echo ""
echo "=== Secret scan ==="
SECRETS=$(grep -rE "(sk-[a-zA-Z0-9]{20,}|AKIA[A-Z0-9]{16}|ghp_[a-zA-Z0-9]{36})" \
    --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=.git \
    --exclude="*.example" --exclude="*.md" \
    . 2>/dev/null || true)
if [ -n "$SECRETS" ]; then
    echo "  [FAIL] Found potential secrets:"
    echo "$SECRETS"
    FAIL=1
else
    echo "  [OK] No secrets found"
fi

echo ""
if [ $FAIL -eq 0 ]; then
    echo "✅ All checks passed."
    exit 0
else
    echo "❌ Some checks failed. Fix the issues above before releasing."
    exit 1
fi
