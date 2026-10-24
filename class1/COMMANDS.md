# Setup (once)
cd class1
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$PWD
cp .env.example .env
bash scripts/setup_modal.sh
bash scripts/modal.sh deploy all
python scripts/download_gguf.py

# New terminal
cd class1 && source .venv/bin/activate && export PYTHONPATH=$PWD

# Warm-up
python inference_101.py
curl -s http://127.0.0.1:8081/health | jq
docker compose --profile cpu up
curl -s http://127.0.0.1:8000/healthz | jq
docker compose --profile cpu down

# Part 0 — naive server
eval "$(bash scripts/modal.sh env naive-server)"
curl -s "$MODAL_BASE_URL/healthz" | jq
curl -s "$MODAL_BASE_URL/v1/chat/completions" -H 'Content-Type: application/json' -d '{"model":"TinyLlama/TinyLlama-1.1B-Chat-v1.0","messages":[{"role":"user","content":"Hi"}],"max_tokens":8}' | jq '.metrics'

# Part 0 — llama engine
eval "$(bash scripts/modal.sh env llama-engine)"
curl -s "$ENGINE_BASE_URL/v1/chat/completions" -H 'Content-Type: application/json' -d '{"model":"TinyLlama/TinyLlama-1.1B-Chat-v1.0","messages":[{"role":"user","content":"Hi"}],"max_tokens":8}' | jq '.timings'

# Part 0 — relay
eval "$(bash scripts/modal.sh env relay-serve)"
curl -s "$RELAY_BASE_URL/v1/chat/completions" -H 'Content-Type: application/json' -d '{"model":"TinyLlama/TinyLlama-1.1B-Chat-v1.0","messages":[{"role":"user","content":"Hi"}],"max_tokens":8}'

# Part 0 — litellm
eval "$(bash scripts/modal.sh env litellm)"
curl -s "$LITELLM_BASE_URL/chat/completions" -H 'Content-Type: application/json' -H 'x-litellm-api-key: Bearer sk-class1-demo' -d '{"model":"naive-local","messages":[{"role":"user","content":"Hi"}],"max_tokens":8}'

# Part 1
eval "$(bash scripts/modal.sh env naive-server)"
python scripts/part1_anatomy.py

# Part 2
eval "$(bash scripts/modal.sh env naive-server)"
curl -s "$MODAL_BASE_URL/v1/chat/completions" -H 'Content-Type: application/json' -d '{"messages":[{"role":"user","content":"Say hi"}],"max_tokens":8}' | jq

# Part 3 — terminal A, leave this running
eval "$(bash scripts/modal.sh env naive-server)"
python scripts/part5_observability.py --url "$METRICS_URL" --interval 1 --count 120

# Part 3 — terminal B, run while A is still printing
eval "$(bash scripts/modal.sh env naive-server)"
curl -s "$MODAL_BASE_URL/healthz" | jq
curl -sN "$MODAL_BASE_URL/v1/chat/completions" -H 'Content-Type: application/json' -d '{"model":"TinyLlama/TinyLlama-1.1B-Chat-v1.0","messages":[{"role":"user","content":"Explain KV cache in one paragraph."}],"max_tokens":64,"stream":true}'
python scripts/part3_break_server.py --base-url "$TARGET_URL"

# Part 4
bash scripts/modal.sh compare
eval "$(bash scripts/modal.sh env llama-engine)"
python scripts/part3_break_server.py --base-url "$TARGET_URL"
eval "$(bash scripts/modal.sh env relay-serve)"
python scripts/part5_observability.py --url "$METRICS_URL" --interval 1 --count 60
python scripts/part3_break_server.py --base-url "$TARGET_URL"
curl -s "$METRICS_URL/metrics" | jq
eval "$(bash scripts/modal.sh env litellm)"
python scripts/part3_break_server.py --base-url "$TARGET_URL"

# Part 5
eval "$(bash scripts/modal.sh env relay-serve)"
python scripts/part5_observability.py --url "$METRICS_URL" --interval 1

# Part 6
eval "$(bash scripts/modal.sh env litellm)"
python scripts/part6_litellm_demo.py

# Stop
bash scripts/modal.sh stop all
docker compose --profile cpu down
