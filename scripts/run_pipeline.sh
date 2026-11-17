#!/usr/bin/env bash
# Run the same stages as the GitHub Actions pipeline on your own machine.
# Usage:  bash scripts/run_pipeline.sh        (needs Python 3.11+ and Docker)
set -euo pipefail
cd "$(dirname "$0")/.."

step() { printf '\n==== %s ====\n' "$1"; }

step "Stage 1: Lint (flake8)"
flake8 .
echo "Lint passed"

step "Stage 2: Test (pytest + coverage)"
pytest -v --cov=app --cov-report=term-missing --cov-fail-under=80

step "Stage 3: Build Docker image"
docker build -t shopease:local .

step "Stage 3b: Smoke test container"
docker rm -f shopease-smoke >/dev/null 2>&1 || true
docker run -d --name shopease-smoke -p 8000:8000 -e APP_VERSION=local shopease:local >/dev/null
for i in $(seq 1 15); do
  if curl -fs http://localhost:8000/health; then
    echo; echo "Smoke test passed"
    docker rm -f shopease-smoke >/dev/null
    step "Pipeline finished: all stages passed"
    exit 0
  fi
  sleep 2
done
echo "Smoke test failed"; docker logs shopease-smoke; exit 1
