# Class 5b — TinyLlama on Lambda, Ray engine arguments

Laptop: **app.py → nginx :8780 → gateway :8765 → SSH tunnel → vLLM :8000**.

Parallel sizes (`--tensor-parallel-size`, `--data-parallel-size`, and the rest) go on `vllm serve` on the GPU. The curl only sends the chat.

You need Python 3.10+, **nginx**, and a Lambda account. Docker is only for Prometheus and Grafana. The default command needs **2 GPUs**.

Run the steps in order. Leave each long-running terminal open.

Replace `YOUR_IP` with the instance IP from the Lambda console. Replace `your_email@example.com` once, in step 1.

---

## 1. Laptop — SSH key

Open a terminal on your laptop.

```bash
ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/id_ed25519_lambda -N ""
cat ~/.ssh/id_ed25519_lambda.pub
```

Copy the line that starts with `ssh-ed25519`. That is the public key.

---

## 2. Browser — Lambda

1. Sign in at https://cloud.lambdalabs.com/.
2. **SSH keys** → add the public line from step 1.
3. **Launch instance**: region of your choice, **2 GPUs**, image **Lambda Stack** (not plain Ubuntu), no extra filesystem, firewall allows **SSH port 22**, select the key from step 1.
4. Wait until it is **running**. Copy the public IP. User is `ubuntu`.

Terminate the instance when you are done. It bills while it runs.

---

## 3. GPU terminal — SSH, install, start vLLM

Open a terminal on your laptop. This is the GPU terminal. Leave it open for the rest of the lab.

```bash
ssh -i ~/.ssh/id_ed25519_lambda ubuntu@YOUR_IP
nvidia-smi
sudo apt update && sudo apt install -y python3-venv python3-pip
python3 -m venv ~/vllm-env
source ~/vllm-env/bin/activate
pip install -U pip wheel
pip install "vllm==0.13.0" "ray[default]"
vllm serve TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
  --served-model-name texttinyllama \
  --host 0.0.0.0 \
  --port 8000 \
  --tensor-parallel-size 2 \
  --distributed-executor-backend ray
```

`nvidia-smi` should list 2 GPUs. Wait until the log says **application startup complete**. The first download can take several minutes. A `GET /` 404 is normal. The API is under `/v1/`.

---

## 4. New terminal — SSH tunnel

Open a **new terminal** on your laptop. Leave it open. Do not close the GPU terminal.

```bash
ssh -i ~/.ssh/id_ed25519_lambda -L 8000:127.0.0.1:8000 -N ubuntu@YOUR_IP
```

This tab has no shell. Laptop `127.0.0.1:8000` is vLLM on the instance.

---

## 5. New terminal — project setup

Open a **new terminal** on your laptop. `cd` into this `class5b` folder.

```bash
cd <path-to-class5b>
cp .env.example .env
```

In `.env` set:

```bash
VLLM_BASE_URL=http://127.0.0.1:8000
VLLM_SERVER_PROFILE=tensor_parallel
```

`VLLM_SERVER_PROFILE` is a metric label. It does not change the engine.

```bash
pip install -r requirements.txt
curl -sS http://127.0.0.1:8000/v1/models
```

That install includes the gateway, CrewAI, and Locust.

The curl should show `"id":"texttinyllama"`. If it fails, check the GPU terminal and the tunnel terminal.

---

## 6. New terminal — gateway

Open a **new terminal**. `cd` into `class5b`. Leave it open.

```bash
cd <path-to-class5b>
set -a && source .env && set +a
python gateway.py
```

Gateway listens on `127.0.0.1:8765`. Metrics are on `127.0.0.1:9101`.

---

## 7. New terminal — check the gateway, start nginx, send a chat

Open a **new terminal**. `cd` into `class5b`.

```bash
cd <path-to-class5b>
curl -sS http://127.0.0.1:8765/health
curl -sS http://127.0.0.1:8765/v1/models
```

`/health` should say `"status":"ok"`.

```bash
cd monitoring
nginx -t -p /tmp -c "$(pwd)/nginx-gateway-lb.conf"
nginx -p /tmp -c "$(pwd)/nginx-gateway-lb.conf"
cd ..
curl -sS http://127.0.0.1:8780/health
curl -sS http://127.0.0.1:8780/v1/models
curl -sS "http://127.0.0.1:8780/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "X-Technique: tensor_parallel" \
  -d '{"model":"texttinyllama","messages":[{"role":"user","content":"Say hi in five words."}],"max_tokens":32}'
```

The JSON is only the chat (`model`, `messages`, `max_tokens`). Do not put `--tensor-parallel-size` in it. `X-Technique` is a metric label.

Same terminal, run the app:

```bash
set -a && source .env && set +a
python app.py --technique tensor_parallel
```

Path: app.py → nginx **8780** → gateway **8765** → tunnel → vLLM **8000**.

---

## 8. New terminal — concurrent crews (Locust)

Open a **new terminal** after step 7 is working. `cd` into `class5b`. The GPU, tunnel, nginx, and gateway terminals stay open.

```bash
cd <path-to-class5b>
set -a && source .env && set +a
locust -f locustfile.py --headless -u 4 -r 1 -t 60s
```

Locust comes from `requirements.txt` in step 5. If that install was from before Locust was added, run `pip install -r requirements.txt` again in this terminal.

`-u 4` is four CrewAI crews at once. Each crew is the same two agents as `app.py` (researcher, then writer), labeled with `VLLM_SERVER_PROFILE` (or `LOCUST_TECHNIQUE` if you set it). For the web UI instead of a fixed 60 seconds:

```bash
locust -f locustfile.py
```

Open http://127.0.0.1:8089, set the user count and spawn rate, and start. Leave the host field empty.

---

## 9. New terminal — Prometheus and Grafana

Optional. Open a **new terminal**. `cd` into `class5b`. The GPU, tunnel, and gateway terminals must still be running.

```bash
cd <path-to-class5b>/monitoring
docker compose up -d
```

- Prometheus: http://127.0.0.1:9090 (targets `gateway` and `vllm_tunnel` should be UP)
- Grafana: http://127.0.0.1:3000 (`admin` / `admin`)
- Dashboards → **TinyLlama** → **TinyLlama — GPU, runs & cost**
- Send the step 7 curl again, wait about 15 seconds, refresh the dashboard

---

## Another parallel layout

On the **GPU terminal**, press `Ctrl-C`, then run `vllm serve` again with the same model, name, host, and port, and one of these flag sets. The tunnel stays on **8000**. Then set `VLLM_SERVER_PROFILE` to the matching name, restart `python gateway.py` in its terminal, and curl again with the same `X-Technique`.

| Name | Flags | GPUs |
|---|---|---|
| `tensor_parallel` | `--tensor-parallel-size 2 --distributed-executor-backend ray` | 2 |
| `pipeline_parallel` | `--pipeline-parallel-size 2 --distributed-executor-backend ray` | 2 |
| `data_parallel` | `--data-parallel-size 2 --data-parallel-backend ray` | 2 |
| `tensor_data_parallel` | `--data-parallel-size 2 --tensor-parallel-size 2 --data-parallel-backend ray --distributed-executor-backend ray` | 4 |
| `pipeline_tensor_parallel` | `--pipeline-parallel-size 2 --tensor-parallel-size 2 --distributed-executor-backend ray` | 4 |
| `prefill_context_parallel` | `--prefill-context-parallel-size 2 --distributed-executor-backend ray` | 2 |

Expert parallel needs a Mixture-of-Experts model (TinyLlama has none): add `--enable-expert-parallel` and change the model, for example `Qwen/Qwen3-30B-A3B`, with `--data-parallel-size 2 --data-parallel-backend ray`.

Several machines: on the head, `ray start --head --port=6379 --dashboard-host=127.0.0.1` (dashboard **127.0.0.1:8265**). On each worker, `ray start --address=<head-ip>:6379`. Then on the head, `RAY_ADDRESS=<head-ip>:6379` in front of `vllm serve`.

---

## Stop

```bash
nginx -s quit -p /tmp -c "<path-to-class5b>/monitoring/nginx-gateway-lb.conf"
```

`Ctrl-C` the Locust terminal, the gateway terminal, the tunnel terminal, and the GPU terminal. Terminate the instance in the Lambda console.

---

## If a command fails

| What you see | Check |
|---|---|
| SSH permission denied | Key added in Lambda, user `ubuntu`, IP is current |
| `nvidia-smi` missing | Relaunch with a GPU type and Lambda Stack |
| `127.0.0.1:8000` refused | GPU terminal still in `vllm serve`, tunnel terminal still open |
| `127.0.0.1:8765` refused | Gateway terminal still running |
| `127.0.0.1:8780` refused | nginx command in step 7 |
| `502` from `8780` | Gateway on `8765` is down |
| `/health` is not `"ok"` | `VLLM_BASE_URL=http://127.0.0.1:8000` and the tunnel is up |
| Grafana empty | http://127.0.0.1:9090/targets — both jobs UP, then send the curl again |
