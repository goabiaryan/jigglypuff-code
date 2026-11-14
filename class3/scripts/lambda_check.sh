#!/usr/bin/env bash
# Quick GPU/Lambda readiness check — run on Mac (deps only) or on the Lambda instance.
set -euo pipefail

CLASS3_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$CLASS3_ROOT"

if [[ -f "$CLASS3_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$CLASS3_ROOT/.env"
  set +a
fi

if [[ -d "$CLASS3_ROOT/.venv" ]]; then
  # shellcheck disable=SC1091
  source "$CLASS3_ROOT/.venv/bin/activate"
fi

export PYTHONPATH="$CLASS3_ROOT"

echo "Host: $(hostname)"
echo "PWD:  $CLASS3_ROOT"
echo ""

python -c "from lib.gpu_check import print_gpu_report; print_gpu_report()"
