"""Dim 1 driver — composition behavior across the five approaches.

PR #105 Principle 4 ("Composability"). For each approach × each
composition primitive, captures two scenarios: same-vendor override and
two-vendor merge.
"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _harness import APPROACHES, run_all_approaches, write_report

DIM_DIR = Path(__file__).resolve().parent
PROBE = DIM_DIR / 'probe.py'

COMPOSITION_OPS = ['sublayer', 'reference', 'payload', 'inherit', 'specialize']


def render_summary(results):
    buf = io.StringIO()
    print('# Dim 1 — composition behavior (P4)', file=buf)
    print('', file=buf)
    print('PR #105 Principle 4: "Must participate in USD\'s composition', file=buf)
    print('model in a well-defined way; clear behavior under reference,',
          file=buf)
    print('inherit, specialize." For each approach × each composition',
          file=buf)
    print('primitive, two scenarios:', file=buf)
    print('', file=buf)
    print('- **override_same_vendor**: weak layer authors',
          file=buf)
    print('  `windchill.primaryId = "WEAK_WINDCHILL"`; strong layer',
          file=buf)
    print('  overrides with `"STRONG_WINDCHILL"`. Which value wins on the',
          file=buf)
    print('  composed prim?', file=buf)
    print('- **two_vendors_merge**: weak layer authors `windchill`; strong',
          file=buf)
    print('  layer authors `ifc` only (no windchill override). Are both',
          file=buf)
    print('  vendors visible on the composed prim?', file=buf)
    print('', file=buf)
    print('Both scenarios run for sublayer, reference, payload, inherit,',
          file=buf)
    print('and specialize composition arcs. The `inherit` and `specialize`',
          file=buf)
    print('rows are exercised via a class prim on the weak layer brought',
          file=buf)
    print('in by reference for reachability — the probe records what each',
          file=buf)
    print('arc surfaces under that composition assembly; it does not',
          file=buf)
    print('disentangle direct-opinion vs class-arc strength in isolation.',
          file=buf)
    print('', file=buf)
    print('**Note on Approach D.** D is a candidate beyond PR #105',
          file=buf)
    print('(came out of Matt Kuruc\'s review of an earlier internal',
          file=buf)
    print('comparison doc; per the criteria file, "internal NVIDIA',
          file=buf)
    print('discussion, not in PR #105"). Its mechanism combines an',
          file=buf)
    print('identifier half (assetInfo dict shape, mirroring A) and a',
          file=buf)
    print('label half (`SemanticLabelsAPI` multi-apply, mirroring B).',
          file=buf)
    print('Where a dim measurement applies to both halves,',
          file=buf)
    print('this summary shows two rows for D; the comparison stays five',
          file=buf)
    print('approaches (A, B, B\', C, D), not six.', file=buf)
    print('', file=buf)

    for ap in APPROACHES:
        if ap == 'D':
            header = '## D — identifier half'
        else:
            header = f'## {ap}'
        print(header, file=buf)
        print('', file=buf)
        print('### override_same_vendor — which value composes?', file=buf)
        print('', file=buf)
        print('| op | windchill_value | applied_schemas |', file=buf)
        print('|---|---|---|', file=buf)
        ap_results = results.get(ap, {}).get('results', {})
        for op in COMPOSITION_OPS:
            scn = ap_results.get(op, {}).get('override_same_vendor', {})
            if 'error' in scn:
                print(f'| {op} | ERROR | {scn["error"]} |', file=buf)
                continue
            val = scn.get('windchill_value')
            applied = ', '.join(f'`{x}`' for x in scn.get('applied_schemas', []))
            print(f'| {op} | `{val}` | {applied} |', file=buf)
        print('', file=buf)

        print('### two_vendors_merge — both vendors visible?', file=buf)
        print('', file=buf)
        print('| op | windchill_value | ifc_value | vendors_visible |',
              file=buf)
        print('|---|---|---|---|', file=buf)
        for op in COMPOSITION_OPS:
            scn = ap_results.get(op, {}).get('two_vendors_merge', {})
            if 'error' in scn:
                print(f'| {op} | ERROR | ERROR | {scn["error"]} |', file=buf)
                continue
            wc = scn.get('windchill_value')
            ifc = scn.get('ifc_value')
            visible = ', '.join(scn.get('vendors_visible', []))
            print(f'| {op} | `{wc}` | `{ifc}` | {visible} |', file=buf)
        print('', file=buf)

        # D's label half: render only when present in the report.
        if ap == 'D' and 'label_half' in results.get(ap, {}):
            print('## D — label half (SemanticLabelsAPI)', file=buf)
            print('', file=buf)
            print('### override_same_label — which label list composes?', file=buf)
            print('', file=buf)
            print('| op | windchill:partCategory labels | applied_schemas |',
                  file=buf)
            print('|---|---|---|', file=buf)
            lab_results = results.get(ap, {}).get('label_half', {})
            for op in COMPOSITION_OPS:
                scn = lab_results.get(op, {}).get('override_same_label', {})
                if 'error' in scn:
                    print(f'| {op} | ERROR | {scn["error"]} |', file=buf)
                    continue
                labels = scn.get('windchill_partCategory_labels')
                applied = ', '.join(
                    f'`{x}`' for x in scn.get('applied_schemas', []))
                print(f'| {op} | `{labels}` | {applied} |', file=buf)
            print('', file=buf)

            print('### two_kinds_merge — both label instances visible?',
                  file=buf)
            print('', file=buf)
            print('| op | windchill:partCategory | ifc:entityType | instances_visible |',
                  file=buf)
            print('|---|---|---|---|', file=buf)
            for op in COMPOSITION_OPS:
                scn = lab_results.get(op, {}).get('two_kinds_merge', {})
                if 'error' in scn:
                    print(f'| {op} | ERROR | ERROR | {scn["error"]} |', file=buf)
                    continue
                wc = scn.get('windchill_partCategory_labels')
                ifc = scn.get('ifc_entityType_labels')
                visible = ', '.join(scn.get('label_instances_visible', []))
                print(f'| {op} | `{wc}` | `{ifc}` | {visible} |', file=buf)
            print('', file=buf)

    print('## Observations', file=buf)
    print('', file=buf)
    print('- For A, C, D-identifier, the identifier is stored in', file=buf)
    print('  `assetInfo` (a dict-valued metadatum). USD\'s composition',
          file=buf)
    print('  rules for dict-valued metadata merge entries from weaker',
          file=buf)
    print('  opinions when stronger opinions do not shadow them; same-key',
          file=buf)
    print('  override takes the strongest opinion. Two vendors authored',
          file=buf)
    print('  in two layers therefore appear as two entries in the composed',
          file=buf)
    print('  `source` dict.', file=buf)
    print('- For B, the identifier is stored in typed attributes',
          file=buf)
    print('  (`sourceIdentifier:<vendor>:primaryId`). For D\'s label half,',
          file=buf)
    print('  labels (token[] arrays) are stored in typed attributes',
          file=buf)
    print('  (`semantics:labels:<vendor>:<kind>`). Attribute composition',
          file=buf)
    print('  is strongest-opinion-wins per attribute. Different vendors',
          file=buf)
    print('  (B) or different vendor:kind instances (D-label) live in',
          file=buf)
    print('  different attributes, so they compose per-attribute and',
          file=buf)
    print('  both remain visible. Same-attribute override is per-attribute',
          file=buf)
    print('  override.', file=buf)
    print('- For B\', the per-vendor schema name carries vendor identity.',
          file=buf)
    print('  `apiSchemas` is a listOp, so adding a second vendor schema',
          file=buf)
    print('  in a stronger layer composes into the union of applied',
          file=buf)
    print('  schemas. The `sourceId:primaryId` slot is shared across',
          file=buf)
    print('  inherited base schemas, so same-vendor override and',
          file=buf)
    print('  cross-vendor authoring read from one slot: one primaryId',
          file=buf)
    print('  value per prim across applied vendor schemas.', file=buf)
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
