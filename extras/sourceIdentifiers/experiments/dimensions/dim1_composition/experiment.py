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
    print('and specialize composition arcs. (Inherit and specialize are',
          file=buf)
    print('exercised via a class prim on the weak layer brought in by',
          file=buf)
    print('reference for reachability; the relative-strength semantic',
          file=buf)
    print('they\'re testing is preserved.)', file=buf)
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
    print('  rules for dict-valued metadata MERGE entries from weaker',
          file=buf)
    print('  opinions when stronger opinions don\'t shadow them. Two',
          file=buf)
    print('  vendors authored in two layers therefore appear as two', file=buf)
    print('  entries in the composed `source` dict; same-key override',
          file=buf)
    print('  takes the strongest opinion.', file=buf)
    print('- For B and D-label, the identifier is stored in typed', file=buf)
    print('  attributes. Composition for attributes is strongest-opinion-',
          file=buf)
    print('  wins per-attribute. Different vendors live in different', file=buf)
    print('  attributes, so they compose independently — both visible.',
          file=buf)
    print('  Same-vendor override is the standard attribute-override',
          file=buf)
    print('  behavior.', file=buf)
    print('- For B\', the per-vendor schema name is what carries vendor', file=buf)
    print('  identity. `apiSchemas` is a listOp, so adding a second',
          file=buf)
    print('  vendor schema in a stronger layer composes into the union of',
          file=buf)
    print("  applied schemas. But the SHARED `sourceId:primaryId` slot",
          file=buf)
    print('  means same-vendor override and cross-vendor authoring',
          file=buf)
    print('  interact: only one primaryId value lives per prim.', file=buf)
    print('- The `inherit` and `specialize` rows in this probe are', file=buf)
    print('  modeled via class prims brought in by reference. The probe',
          file=buf)
    print('  reflects how arcs play out via the layer composition, not',
          file=buf)
    print('  the relative arc-strength semantics in isolation. A future',
          file=buf)
    print('  probe could disentangle direct vs class-arc opinions if',
          file=buf)
    print('  that distinction proves load-bearing for the comparison.',
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
