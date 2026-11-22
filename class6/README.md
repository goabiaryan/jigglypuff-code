# Class 5b — CrewAI → limiter → gateway (gateway+queue+routing) → two vLLM replicas

Homework (laptop, fake GPU): [hw/README.md](hw/README.md). `admit.py` / `sched.py` / `router.py` / `serve.py`. Do not mix it with `gateway/`.

One GPU on Lambda. `--max-num-seqs 8` is the point — do not raise it.

Walk the stack and what you should see: [class5b.md](./class5b.md).

```
class5b/
  app.py          CrewAI client
  limiter.py      app-side rate limiter
  gateway/        Python package  (python -m gateway.main)
  setup/          Mac sync + Lambda launch
  tests/
  bench/
```

`gateway/` must stay a package at the lab root. Do not nest the lab inside `llm-gateway-lab/`.

---

# ON YOUR MAC

Rsync first. SSH into an empty `~/class5b` is a dead end — the lab is not on the GPU until `sync_to_lambda.sh` finishes.

Open a **new** terminal. `pwd` must end with `class-code/class5b`.

```
cd class-code/class5b
pwd
cp .env.example .env
```

Put your values in `.env` (never commit it):

```
export LAMBDA=ubuntu@YOUR_LAMBDA_IP
export LAMBDA_SSH_KEY=$HOME/.ssh/YOUR_LAMBDA_KEY
export HF_TOKEN=hf_xxxx
```

```
bash setup/sync_to_lambda.sh
```

Wait until it prints `Synced`. Then:

```
bash setup/ssh.sh
```

`setup/ssh.sh` reads `.env` itself and drops you on the GPU in `~/class5b`. The prompt is `ubuntu@...`, not `jarvis@...`.

On Lambda, check the copy landed:

```
ls
```

You must see `app.py`, `Makefile`, `gateway/`, `setup/`. If `ls` is empty, `exit` and run `bash setup/sync_to_lambda.sh` on the Mac again.

Every time you change code, rsync again from the Mac before you expect Lambda to see it:

```
cd class-code/class5b
bash setup/sync_to_lambda.sh
```

---

# ON LAMBDA — setup (once)

Only after rsync. You are already in `~/class5b` if you used `bash setup/ssh.sh`.

```
bash setup/lambda_setup.sh
```

Every new Lambda tab:

```
cd ~/class5b && source .venv/bin/activate
```

---

# ON LAMBDA — run

```
bash setup/launch_replicas.sh
make smoke

python -m gateway.main --replicas http://127.0.0.1:8001,http://127.0.0.1:8002
```

Other Lambda tab:

how to create another lambda tab?

```
cd .../class5b
bash setup/ssh.sh
ssh lambda
cd ~/class5b && source .venv/bin/activate
```
we need to run this

```
cd ~/class5b && source .venv/bin/activate
python app.py "What is KV cache?"

make test
make bench
```

---

# TEAR DOWN

```
kill $(cat /tmp/llm-gateway-lab-8001.pid /tmp/llm-gateway-lab-8002.pid)
```

Then terminate the instance in the Lambda console.
