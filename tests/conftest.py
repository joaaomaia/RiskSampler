"""PyTest bootstrap for RiskSampler

Adds the project's *src/* directory to ``sys.path`` so that the package
`risk_sampler` can be imported without needing ``pip install -e .``.
"""

from pathlib import Path
import sys

# Resolve project root two levels up from this file (tests/ -> ROOT)
ROOT = Path(__file__).resolve().parents[1].parent
SRC_DIR = ROOT / "src"

if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))
