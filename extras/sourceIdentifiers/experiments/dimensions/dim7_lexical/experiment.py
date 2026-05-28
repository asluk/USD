"""Dim 7 driver — vendor-name lexical scope across the five approaches.

PR #105 Principle 3 (vendor extensibility) + Open Question 5 (namespacing
of identifiers). Framing: vendor-extension-paradigm question, not lexical
fidelity. The probe captures what character classes each approach's
vendor slot accepts AND the failure mode when it doesn't.
"""
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _harness import APPROACHES, run_all_approaches, write_report

DIM_DIR = Path(__file__).resolve().parent
PROBE = DIM_DIR / 'probe.py'


def cell_mark(approach, row):
    """Reduce a row to a short status string for the result matrix.

    Returns one of:
      ✓          authoring works end-to-end including round-trip
      ✓ (slot)   permissive at runtime; constraint lives elsewhere
      ⚠ silent   silent re-namespacing on round-trip
      ✗          authoring fails (typed-property creation rejected)
      ✗ class    rejected at schema-class-name validation
      —          n/a
    """
    if 'error' in row:
        return f'? {row.get("error", "err")[:18]}'

    # B'/class-name slot
    if 'class_name_under_test' in row:
        if row.get('tf_isvalid_identifier'):
            return '✓ class'
        return '✗ class'

    # Dict-key slot
    if row.get('slot') == 'dict_key':
        if row.get('round_trips'):
            return '✓ (dict)'
        return '✗ (dict)'

    # Apply-instance-and-property slot
    if row.get('slot') == 'apply_instance_and_property':
        if row.get('silent_renamespace'):
            return '⚠ silent'
        if row.get('round_trips'):
            return '✓'
        if row.get('apply_succeeded') and not row.get('authoring_succeeded'):
            return '✗ prop'
        if not row.get('apply_succeeded'):
            return '✗ apply'
        return '✗'

    return '—'


def render_summary(results):
    """Two tables: single-slot approaches and D's two-slot split."""
    sample = next(iter(results.values()))
    labels = list(sample.get('by_value', {}).keys())

    buf = io.StringIO()
    print('# Dim 7 — vendor-name lexical scope (P3 + OQ5)', file=buf)
    print('', file=buf)
    print('Framing: PR #105 names vendor extensibility (P3) as a core principle —',
          file=buf)
    print('vendors must be able to declare their own scheme without central',
          file=buf)
    print('approval. The vendor *name* is the operational carrier of that vendor',
          file=buf)
    print('identity in every approach. This dimension records what character',
          file=buf)
    print('classes each approach\'s vendor slot accepts and how it fails when it',
          file=buf)
    print("doesn't. Findings inform whether the proposed extension paradigm",
          file=buf)
    print('imposes a soft form of central approval via naming constraints',
          file=buf)
    print('(tensions with P3\'s "no central approval" stance) — captured here',
          file=buf)
    print('as data, not verdict.', file=buf)
    print('', file=buf)

    print('## Slot per approach', file=buf)
    print('', file=buf)
    for ap in APPROACHES:
        slot = results.get(ap, {}).get('slot_kind', '—')
        print(f'- **{ap}** — {slot}', file=buf)
    print('', file=buf)

    # Main matrix (non-D)
    print('## Result matrix — A, B, B\', C', file=buf)
    print('', file=buf)
    print('Legend: ✓ = end-to-end authoring works (including round-trip);',
          file=buf)
    print('✓ (dict) = permissive dict-key slot (runtime always succeeds);',
          file=buf)
    print('✓ class = class-name passes Tf.IsValidIdentifier;', file=buf)
    print('⚠ silent = ApplyAPI succeeds but Sdf silently re-namespaces the',
          file=buf)
    print('vendor identity on parse;', file=buf)
    print('✗ apply / ✗ prop / ✗ class = failure at that gate.', file=buf)
    print('', file=buf)

    cols = ['A', 'B', 'Bprime', 'C']
    print('| vendor name | ' + ' | '.join(cols) + ' |', file=buf)
    print('|---|' + '|'.join(['---'] * len(cols)) + '|', file=buf)
    for label in labels:
        row = [label]
        for ap in cols:
            cell = results.get(ap, {}).get('by_value', {}).get(label, {})
            row.append(cell_mark(ap, cell))
        print('| ' + ' | '.join(row) + ' |', file=buf)
    print('', file=buf)

    # D's split-slot matrix
    print('## Result matrix — D (split-by-concern)', file=buf)
    print('', file=buf)
    print('D has two slots, probed independently. Identifier slot is a dict',
          file=buf)
    print('key (A-shaped). Label slot is ApplyAPI instance + property segment',
          file=buf)
    print('(B-shaped). Same column legend as above.', file=buf)
    print('', file=buf)
    print('| vendor name | identifier slot | label slot |', file=buf)
    print('|---|---|---|', file=buf)
    for label in labels:
        d_cell = results.get('D', {}).get('by_value', {}).get(label, {})
        id_mark = cell_mark('D', d_cell.get('identifier_slot', {})) if isinstance(d_cell, dict) else '—'
        lb_mark = cell_mark('D', d_cell.get('label_slot', {})) if isinstance(d_cell, dict) else '—'
        print(f'| {label} | {id_mark} | {lb_mark} |', file=buf)
    print('', file=buf)

    print('## Observations', file=buf)
    print('', file=buf)
    print('- Two layers of constraint, not one: ApplyAPI/dict-key behavior is',
          file=buf)
    print('  permissive at the runtime API; the harder constraint lives in',
          file=buf)
    print('  `SdfAttributeSpec::New`, which enforces `Sdf.Path.IsValidNamespacedIdentifier`',
          file=buf)
    print('  per property-name segment.', file=buf)
    print('- Colons in the vendor name (`siemens:nx`) trigger silent',
          file=buf)
    print('  re-namespacing in B and D-label: Sdf parses the property name into',
          file=buf)
    print('  extra namespace segments, producing a different shape than what',
          file=buf)
    print("  was authored — no error raised. This is a separable USD bug",
          file=buf)
    print('  ([[bugs-vs-proposal-considerations]]), distinct from the',
          file=buf)
    print('  vendor-extension-paradigm question.', file=buf)
    print('- B\' is the most-restrictive of the slots: schema class name must',
          file=buf)
    print('  satisfy `Tf.IsValidIdentifier` (ASCII identifier rules — no',
          file=buf)
    print('  unicode, no hyphen/space/dot, no leading digit). Codeless',
          file=buf)
    print('  schemas do not relax this; the constraint sits in', file=buf)
    print('  `Sdf_TextFileFormatParser` + the usdGenSchema validator, neither',
          file=buf)
    print('  bypassed by `skipCodeGeneration`.', file=buf)
    print('- A, C, D-identifier (dict-key slot) accept every probed string',
          file=buf)
    print('  including unicode and embedded special characters. Round-trips',
          file=buf)
    print('  byte-for-byte through `.usda`.', file=buf)
    print('', file=buf)

    return buf.getvalue()


def main():
    results = run_all_approaches(PROBE)
    write_report(DIM_DIR, results)
    (DIM_DIR / 'summary.md').write_text(render_summary(results), encoding='utf-8')
    print(f'Wrote {DIM_DIR / "report.json"}')
    print(f'Wrote {DIM_DIR / "summary.md"}')


if __name__ == '__main__':
    main()
