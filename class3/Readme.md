# Class 3 — Build an inference engine from scratch

**Goal:** Walk through the internal workflow of an LLM inference engine using [smol-vllm](./smol-vllm/) — run the 5 built-in experiments, then send real user requests through CrewAI.

**Prerequisite:** Class 2 (inference *from the outside* — HTTP, llama.cpp, gateways). Class 3 opens the hood.

| Resource | Path |
|----------|------|
| **Notebook (everything)** | [class3.ipynb](./class3.ipynb) — Part A manual + Part C experiments + Part B CrewAI |
| **CLI agent demo** | [agent_demo.py](./agent_demo.py) |
| **Commands cheat sheet** | [COMMANDS.md](./COMMANDS.md) |
| **Engine source** | [smol-vllm/](./smol-vllm/) |
| **Workflow diagram** | [assets/engine_workflow.png](./assets/engine_workflow.png) |
| **Instructor runbook** | [extra/class3/main.md](../../extra/class3/main.md) |
| **Lambda GPU (remote Jupyter)** | [LAMBDA.md](./LAMBDA.md) |

Commands below — same content as [COMMANDS.md](./COMMANDS.md).

---

# SETUP (once)
cd class3
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$PWD
source .env
python -c "from smol_vllm import LLMEngine; print('smol_vllm OK')"

# EVERY NEW TAB
cd class3 && source .venv/bin/activate && export PYTHONPATH=$PWD

# If import fails: vendor folder must be smol-vllm/ (not smol_vllm/) — reinstall:
pip install -r requirements.txt

# NOTEBOOK — Part A (manual) + Part C (5 experiments) + Part B (CrewAI)
jupyter notebook class3.ipynb

# CLI: same experiments as notebook Part C
smol-vllm-demo

# CLI: CrewAI demo (notebook Part B)
python agent_demo.py "What is paged attention?"

# OPTIONAL — real model (GPU + HF token for gated models)
pip install -e smol-vllm[tinyllama-1.1b]
source .env
