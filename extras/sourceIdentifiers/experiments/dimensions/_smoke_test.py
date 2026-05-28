"""Smoke test for the dimension-experiment harness.

Runs _smoke_probe.py across all five approaches and prints which schemas
each subprocess actually saw. Sanity check that:

  1. The subprocess can find USD via the shell's USD_PYTHON / PYTHONPATH.
  2. Each subprocess sees ONLY its assigned approach's plugin (no leak).
  3. A and D both report SourceIdentifiersAPI registered, but in separate
     subprocesses — no TfType collision.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _harness import APPROACHES, run_all_approaches

PROBE = Path(__file__).parent / '_smoke_probe.py'


def main():
    results = run_all_approaches(PROBE)
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
