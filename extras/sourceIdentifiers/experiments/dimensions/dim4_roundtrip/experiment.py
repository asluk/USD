"""Dim 4 driver — runs probe.py across all five approaches and writes
report.json + summary.md.

Round-trip fidelity for identifier VALUES: author a string value, export
to `.usda` and `.usdc`, reimport, compare the recovered string to the
authored string. PR #105 Principle 7 ("Round-trip fidelity").
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _harness import APPROACHES, run_all_approaches, write_report

DIM_DIR = Path(__file__).resolve().parent
PROBE = DIM_DIR / 'probe.py'


def render_summary(results):
    """Per-value × per-approach pass/fail matrix as a markdown table."""
    # Collect all value labels across approaches (probe runs them all but
    # may surface different errors).
    sample = next(iter(results.values()))
    labels = [k for k in sample.get('by_value', {}).keys()]

    lines = [
        '# Dim 4 — round-trip fidelity (P7)',
        '',
        'Identifier *values* set on a prim, exported to `.usda` and `.usdc`,',
        'reimported, compared to the authored value. This dim measures the',
        'value channel; vendor-name lexical-scope behaviour is measured',
        'separately in Dim 7.',
        '',
        '## Result matrix',
        '',
        '`✓` = recovered value equals authored value (both .usda and .usdc).',
        '`✗` = mismatch or failure; see report.json for details.',
        '',
        '| value | ' + ' | '.join(APPROACHES) + ' |',
        '|---|' + '|'.join(['---'] * len(APPROACHES)) + '|',
    ]
    for label in labels:
        row = [label]
        for ap in APPROACHES:
            cell = results.get(ap, {}).get('by_value', {}).get(label, {})
            usda_pass = cell.get('usda', {}).get('pass', False)
            usdc_pass = cell.get('usdc', {}).get('pass', False)
            mark = '✓' if (usda_pass and usdc_pass) else '✗'
            row.append(mark)
        lines.append('| ' + ' | '.join(row) + ' |')

    lines += [
        '',
        '## Notes',
        '',
        '- All approaches store the identifier value as a USD `string` or',
        '  as a string entry in a `VtDictionary`. The matrix records',
        '  whether the recovered string equals the authored string across',
        '  the sampled values; it does not measure byte-level guarantees',
        '  of USD\'s string serialization in general.',
        '- The matrix tests the value channel only. Vendor-name lexical',
        '  scope is measured in Dim 7.',
        '- `empty` row records the round-trip of an authored empty string',
        '  (the matrix marks pass if the recovered value equals `""`).',
    ]
    return '\n'.join(lines) + '\n'


def main():
    results = run_all_approaches(PROBE)
    write_report(DIM_DIR, results)
    (DIM_DIR / 'summary.md').write_text(render_summary(results), encoding='utf-8')
    print(f'Wrote {DIM_DIR / "report.json"}')
    print(f'Wrote {DIM_DIR / "summary.md"}')


if __name__ == '__main__':
    main()
