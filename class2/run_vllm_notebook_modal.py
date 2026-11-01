"""Run the vLLM notebook on a Modal L4. Tokens live in the notebook's first code cell."""

import ast
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTEBOOK = HERE / "inside-vllm-anatomy-of-a-high-throughput-llm-inference-system.ipynb"
SECRET_NAMES = ("MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET", "HF_TOKEN")


def _cell_text(cell) -> str:
    source = cell.get("source", "")
    return source if isinstance(source, str) else "".join(source)


def _assignments(text: str) -> dict[str, str]:
    found = {}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return found
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id not in SECRET_NAMES:
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            found[target.id] = node.value.value
    return found


def _notebook_secrets(path: Path) -> dict[str, str]:
    notebook = json.loads(path.read_text())
    found = {}
    for cell in notebook.get("cells", []):
        found.update(_assignments(_cell_text(cell)))
    return found


def _redact(notebook_json: str) -> str:
    notebook = json.loads(notebook_json)
    for cell in notebook.get("cells", []):
        text = _cell_text(cell)
        if "MODAL_TOKEN_SECRET" not in text:
            continue
        redacted = []
        for line in text.splitlines(keepends=True):
            stripped = line.lstrip()
            name = next((item for item in SECRET_NAMES if stripped.startswith(item + " ") or stripped.startswith(item + "=")), "")
            if name:
                newline = "\n" if line.endswith("\n") else ""
                redacted.append(f'{name} = ""{newline}')
            else:
                redacted.append(line)
        cell["source"] = redacted
    return json.dumps(notebook)


def _restore(notebook: dict, saved: dict[str, str]) -> None:
    for cell in notebook.get("cells", []):
        text = _cell_text(cell)
        if "MODAL_TOKEN_SECRET" not in text:
            continue
        restored = []
        for line in text.splitlines(keepends=True):
            stripped = line.lstrip()
            name = next((item for item in SECRET_NAMES if stripped.startswith(item + " ") or stripped.startswith(item + "=")), "")
            if name and name in saved:
                newline = "\n" if line.endswith("\n") else ""
                restored.append(f'{name} = "{saved[name]}"{newline}')
            else:
                restored.append(line)
        cell["source"] = restored


for _key, _value in _notebook_secrets(NOTEBOOK).items():
    if _value:
        os.environ[_key] = _value

import modal

_image_env = {"VLLM_ENABLE_V1_MULTIPROCESSING": "0", "VLLM_USE_V1": "1"}
if os.environ.get("HF_TOKEN"):
    _image_env["HF_TOKEN"] = os.environ["HF_TOKEN"]
    _image_env["HUGGING_FACE_HUB_TOKEN"] = os.environ["HF_TOKEN"]

app = modal.App("vllm-anatomy-notebook")
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "vllm==0.10.1.1",
        "transformers==4.56.0",
        "tokenizers==0.22.0",
        "nbclient>=0.10",
        "nbformat>=5.10",
        "ipykernel>=6.29",
    )
    .run_commands("python -m ipykernel install --sys-prefix --name python3")
    .env(_image_env)
)


@app.function(image=image, gpu="L4", timeout=60 * 60)
def run_notebook(notebook_json: str) -> dict:
    import nbformat
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError

    nb = nbformat.reads(notebook_json, as_version=4)
    for cell in nb.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None

    client = NotebookClient(
        nb,
        timeout=1800,
        kernel_name="python3",
        resources={"metadata": {"path": "/root"}},
    )
    error = None
    execution_count = 0
    with client.setup_kernel():
        for index, cell in enumerate(nb.cells):
            if cell.cell_type != "code":
                continue
            source = cell.source if isinstance(cell.source, str) else "".join(cell.source)
            if not source.strip():
                continue
            if "MODAL_TOKEN_ID" in source and "MODAL_TOKEN_SECRET" in source:
                print(f"cell {index}: token stays on the laptop", flush=True)
                continue
            execution_count += 1
            if "uv pip install" in source and "vllm" in source:
                import vllm

                cell.outputs = [
                    nbformat.v4.new_output(
                        output_type="stream",
                        name="stdout",
                        text=f"vllm {vllm.__version__} already installed\n",
                    )
                ]
                cell.execution_count = execution_count
                print(f"cell {index}: using installed vllm {vllm.__version__}", flush=True)
                continue
            print(f"cell {index}: running", flush=True)
            try:
                client.execute_cell(cell, index, execution_count=execution_count)
            except CellExecutionError as exc:
                error = f"cell {index} failed: {exc}"
                print(error, flush=True)
                break
    return {"error": error, "notebook": nbformat.writes(nb)}


@app.local_entrypoint()
def main():
    saved = _notebook_secrets(NOTEBOOK)
    if not saved.get("MODAL_TOKEN_ID") or not saved.get("MODAL_TOKEN_SECRET"):
        raise SystemExit(
            "Fill in MODAL_TOKEN_ID and MODAL_TOKEN_SECRET in the notebook, then save it."
        )
    result = run_notebook.remote(_redact(NOTEBOOK.read_text()))
    written = json.loads(result["notebook"])
    _restore(written, saved)
    NOTEBOOK.write_text(json.dumps(written, indent=1, ensure_ascii=False) + "\n")
    if result["error"]:
        raise SystemExit(result["error"])
    print(f"wrote {NOTEBOOK}")
