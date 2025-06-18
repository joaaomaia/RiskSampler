"""PyTest bootstrap for RiskSampler

Adds the project's *src/* directory to ``sys.path`` so that the package
`risk_sampler` can be imported without needing ``pip install -e .``.
"""

from pathlib import Path
import sys

# Resolve project root (parent of ``tests/``)
ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"

if SRC_DIR.exists():
    path = str(SRC_DIR)
    if path not in sys.path:
        sys.path.insert(0, path)
