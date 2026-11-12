"""Run the whole project in order, then validate the results.

Order: B (profiling) -> C (cleaning) -> D (graph notebook, then graph.py) -> validate_project.py.
Each notebook is executed in its own fresh kernel. Component A is documentation and is checked by the validator.

Usage:  python run_all.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NOTEBOOKS = ["B_Quality/profiling.ipynb", "C_Cleaning/cleaning.ipynb", "D_Graph/graph.ipynb"]


def run(command, cwd):
    print("\n>>", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


for notebook in NOTEBOOKS:
    path = ROOT / notebook
    run([sys.executable, "-m", "nbconvert", "--to", "notebook", "--execute", "--inplace",
         "--ExecutePreprocessor.timeout=900", path.name], path.parent)

run([sys.executable, "graph.py"], ROOT / "D_Graph")
run([sys.executable, "validate_project.py"], ROOT)
