#!/usr/bin/env bash
# Mac → Lambda: push class3/ (run from class3/ on your Mac, NOT on the instance).
set -euo pipefail

CLASS3_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$CLASS3_ROOT"

if [[ -f "$CLASS3_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$CLASS3_ROOT/.env"
  set +a
fi

if [[ -z "${LAMBDA:-}" ]]; then
  echo "Set LAMBDA in .env (cp .env.example .env)" >&2
  exit 1
fi
if [[ -z "${LAMBDA_SSH_KEY:-}" || ! -f "$LAMBDA_SSH_KEY" ]]; then
  echo "Set LAMBDA_SSH_KEY in .env to your Lambda SSH private key" >&2
  exit 1
fi

echo "Sync Mac → $LAMBDA:~/class3/"
ssh -i "$LAMBDA_SSH_KEY" -o BatchMode=yes "$LAMBDA" echo "SSH OK"

rsync -avz --progress -e "ssh -i $LAMBDA_SSH_KEY" \
  --exclude '.venv' \
  --exclude '.ipynb_checkpoints' \
  --exclude '__pycache__' \
  --exclude 'logs' \
  --exclude 'class3_with_outputs.pdf' \
  --exclude 'class3_with_outputs.html' \
  --exclude '.env' \
  ./ \
  "$LAMBDA:~/class3/"

# Remove stale copies from an old rsync layout (real paths: lib/, smol-vllm/, scripts/).
ssh -i "$LAMBDA_SSH_KEY" -o BatchMode=yes "$LAMBDA" \
  'cd ~/class3 && rm -f causal_model.py metrics.py gpu_check.py export_notebook.py smol_crew_llm.py tokenizer.py export_notebook.sh'

echo ""
echo "Synced. On Lambda:"
echo "  ssh -i \"\$LAMBDA_SSH_KEY\" \$LAMBDA"
echo "  cd ~/class3 && bash scripts/lambda_setup.sh   # first time only"
echo "  bash scripts/lambda_jupyter.sh"
