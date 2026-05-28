"""Common harness for the source-identifier dimension experiments.

Each dimension under ``dimensions/dim<N>_<slug>/`` exercises all five
approaches (A, B, B', C, D) on one PR #105 criterion and emits comparable
result data. Because Approaches A and D both export a public schema named
``SourceIdentifiersAPI`` (intentional collision — they propose the same
public name for the identifier half), the approaches cannot share a
TfType registry. Each approach therefore runs in its own subprocess with
``PXR_PLUGINPATH_NAME`` overridden to point at that approach's experiment
directory exclusively.

USD's built-in plugins (Sdf, Usd, ...) load from ``$installRoot/lib/usd``
independently of ``PXR_PLUGINPATH_NAME``, so dropping the other example
plugin paths in the child env is safe.

Usage from a dimension driver::

    from dimensions._harness import APPROACHES, run_all_approaches, write_report

    results = run_all_approaches(Path(__file__).parent / 'probe.py')
    write_report(Path(__file__).parent, results)
"""

import json
import os
import subprocess
from pathlib import Path

APPROACHES = ['A', 'B', 'Bprime', 'C', 'D']

REPO_ROOT = Path(__file__).resolve().parents[4]
EXPERIMENTS_ROOT = REPO_ROOT / 'extras' / 'sourceIdentifiers' / 'experiments'
DIMENSIONS_ROOT = EXPERIMENTS_ROOT / 'dimensions'


def experiment_dir(approach):
    return EXPERIMENTS_ROOT / approach


def usd_python():
    py = os.environ.get('USD_PYTHON')
    if not py:
        raise RuntimeError(
            "USD_PYTHON is not set. Source _install/activate.ps1 first.")
    return py


def run_probe(probe_script, approach, *args, timeout=120):
    """Run a probe script for one approach in an isolated subprocess.

    The child process sees PXR_PLUGINPATH_NAME set to only this approach's
    plugin dir; this defeats the A/D schema-name collision.

    The probe must print exactly one JSON document to stdout.

    Returns a dict. On failure the dict carries an ``__error__`` key with
    diagnostics so the driver can record the failure without crashing the
    whole dimension run.
    """
    env = os.environ.copy()
    env['PXR_PLUGINPATH_NAME'] = str(experiment_dir(approach))
    # Force UTF-8 stdout in the child so non-ASCII characters in JSON
    # payloads (em-dash, unicode test values, etc.) survive the pipe.
    env['PYTHONIOENCODING'] = 'utf-8'
    cmd = [usd_python(), str(probe_script), approach, *[str(a) for a in args]]
    try:
        proc = subprocess.run(
            cmd, env=env, capture_output=True, text=True,
            timeout=timeout, encoding='utf-8', errors='replace')
    except subprocess.TimeoutExpired:
        return {'__error__': f'timeout after {timeout}s'}
    if proc.returncode != 0:
        return {
            '__error__': f'exit {proc.returncode}',
            '__stderr__': proc.stderr,
            '__stdout__': proc.stdout,
        }
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return {
            '__error__': f'json decode: {e}',
            '__stdout__': proc.stdout,
            '__stderr__': proc.stderr,
        }


def run_all_approaches(probe_script, *args, timeout=120, approaches=None):
    """Run a probe script across all approaches; return {approach: result}."""
    results = {}
    for ap in (approaches or APPROACHES):
        results[ap] = run_probe(probe_script, ap, *args, timeout=timeout)
    return results


def write_report(dim_dir, results):
    """Write report.json with stable key order for diffing."""
    (Path(dim_dir) / 'report.json').write_text(
        json.dumps(results, indent=2, sort_keys=True) + '\n',
        encoding='utf-8')
