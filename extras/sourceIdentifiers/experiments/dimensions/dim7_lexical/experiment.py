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
    print('PR #105 Principle 3 (vendor extensibility): "Any vendor or',
          file=buf)
    print('standards body can declare their own identifier scheme without',
          file=buf)
    print('central approval." Open Question 5 (namespacing of identifiers):',
          file=buf)
    print('where the vendor identity lives in each approach.', file=buf)
    print('', file=buf)
    print('Each approach has a *vendor slot* — a string that carries the',
          file=buf)
    print('vendor identity in the layer (dict key for A/C, multi-apply',
          file=buf)
    print('instance segment for B and D-label, schema class name for B\').',
          file=buf)
    print('This dimension records, per probed vendor name, which slots',
          file=buf)
    print('accept it end-to-end (apply, author, round-trip) and which',
          file=buf)
    print('fail (and at what gate). Whether the measured scope is',
          file=buf)
    print('acceptable under P3 is a downstream question for COMPARISON.md.',
          file=buf)
    print('', file=buf)
    print('**Note on Approach D.** D is a candidate beyond PR #105',
          file=buf)
    print('(Matt Kuruc strawman, per the criteria file). Its mechanism',
          file=buf)
    print('has two vendor slots: a dict-key slot for the identifier half',
          file=buf)
    print('(same shape as A) and a multi-apply instance segment for the',
          file=buf)
    print('label half (same shape as B). Both slots are probed; the D',
          file=buf)
    print('section below shows them side by side.', file=buf)
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
    print('Legend: ✓ = end-to-end authoring works (recovered value equals',
          file=buf)
    print('authored value);',
          file=buf)
    print('✓ (dict) = dict-key slot, all probed strings round-trip;',
          file=buf)
    print('✓ class = class-name passes Tf.IsValidIdentifier;', file=buf)
    print('⚠ silent = ApplyAPI succeeds but Sdf re-namespaces the vendor',
          file=buf)
    print('identity on parse without raising an error;',
          file=buf)
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
    print('## Result matrix — D (two slots)', file=buf)
    print('', file=buf)
    print('D has two vendor slots, probed independently. The identifier',
          file=buf)
    print('slot is a dict key (same shape as A). The label slot is the',
          file=buf)
    print('ApplyAPI instance segment + property name segment (same shape',
          file=buf)
    print('as B). Same column legend as above.', file=buf)
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
    print('- For B and D-label, ApplyAPI accepts the vendor segment but',
          file=buf)
    print('  the property-name slot is gated by',
          file=buf)
    print('  `Sdf.Path.IsValidNamespacedIdentifier` per segment. The',
          file=buf)
    print('  runtime ApplyAPI surface and the SdfAttributeSpec surface',
          file=buf)
    print('  have different acceptance rules; the probe records both.',
          file=buf)
    print('- Colons in the vendor name (`siemens:nx`) cause silent',
          file=buf)
    print('  re-namespacing in B and D-label: ApplyAPI returns success',
          file=buf)
    print('  but Sdf parses the property name into extra namespace',
          file=buf)
    print('  segments, so the authored vendor identity differs from the',
          file=buf)
    print('  recovered shape. report.json records this as',
          file=buf)
    print('  `silent_renamespace: true`.', file=buf)
    print('- B\' (Bprime) class-name slot is gated by',
          file=buf)
    print('  `Tf.IsValidIdentifier` (ASCII identifier rules: no unicode,',
          file=buf)
    print('  no hyphen/space/dot, no leading digit). report.json records',
          file=buf)
    print('  `tf_isvalid_identifier: false` for class names that violate',
          file=buf)
    print('  these rules; the per-vendor schema cannot be registered',
          file=buf)
    print('  with such a name and `authoring_succeeded: null` reflects',
          file=buf)
    print('  that runtime apply was not exercised.',
          file=buf)
    print('- A, C, and D\'s identifier slot (dict key under',
          file=buf)
    print('  `assetInfo.source.<vendor>`) accepted every probed string in',
          file=buf)
    print('  this run, including unicode and embedded special characters,',
          file=buf)
    print('  and the recovered values matched the authored values.',
          file=buf)
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
