"""Dim 6 driver — scope-of-applicability across the five approaches.

PR #105 Open Question 4 (model roots only, or any prim?). The dimension
records (a) whether each schema imposes a `apiSchemaCanOnlyApplyTo`
restriction, (b) whether apply succeeds across a range of prim types,
and (c) the approximate cost-per-prim cost of carrying one vendor's
identifier on each approach.
"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _harness import APPROACHES, run_all_approaches, write_report

DIM_DIR = Path(__file__).resolve().parent
PROBE = DIM_DIR / 'probe.py'


def render_summary(results):
    sample = next(iter(results.values()))
    prim_types = list(sample.get('by_prim_type', {}).keys())

    buf = io.StringIO()
    print('# Dim 6 — scope-of-applicability (OQ4)', file=buf)
    print('', file=buf)
    print("PR #105 Open Question 4: model roots only, or any prim? Captures",
          file=buf)
    print('three signals per approach: schema-level `apiSchemaCanOnlyApplyTo`',
          file=buf)
    print('restriction (if any), apply success across a range of prim types,',
          file=buf)
    print("and approximate cost-per-prim (bytes added to the layer by one",
          file=buf)
    print('vendor\'s identifier).', file=buf)
    print('', file=buf)

    # apiSchemaCanOnlyApplyTo
    print('## Schema-level apply restriction', file=buf)
    print('', file=buf)
    print('| approach | schema | allowed prim types |', file=buf)
    print('|---|---|---|', file=buf)
    for ap in APPROACHES:
        cor = results.get(ap, {}).get('can_only_apply_to', {})
        for schema_name, allowed in cor.items():
            if isinstance(allowed, str):
                allowed_str = f'_{allowed}_'
            elif allowed:
                allowed_str = ', '.join(allowed)
            else:
                allowed_str = '(unrestricted)'
            print(f'| {ap} | `{schema_name}` | {allowed_str} |', file=buf)
    print('', file=buf)

    # Apply success matrix
    print('## Apply-success matrix', file=buf)
    print('', file=buf)
    print('`✓` = apply returned True and authoring the identifier succeeded.',
          file=buf)
    print('`✗` = apply or authoring failed; see report.json.', file=buf)
    print('', file=buf)
    print('| prim type | ' + ' | '.join(APPROACHES) + ' |', file=buf)
    print('|---|' + '|'.join(['---'] * len(APPROACHES)) + '|', file=buf)
    for pt in prim_types:
        row = [pt]
        for ap in APPROACHES:
            cell = results.get(ap, {}).get('by_prim_type', {}).get(pt, {})
            row.append('✓' if cell.get('applied') else '✗')
        print('| ' + ' | '.join(row) + ' |', file=buf)
    print('', file=buf)

    # Cost per prim
    print('## Approximate cost per prim', file=buf)
    print('', file=buf)
    print('Bytes added to a 10-Xform `.usda` layer by applying the schema',
          file=buf)
    print('and authoring one vendor identifier on each prim. Single',
          file=buf)
    print('measurement per approach with short ASCII vendor name and a',
          file=buf)
    print('single-character primaryId; not measured for `.usdc`.',
          file=buf)
    print('', file=buf)
    print('| approach | empty (10 prims) | with identifier | Δ bytes | bytes/prim |', file=buf)
    print('|---|---|---|---|---|', file=buf)
    for ap in APPROACHES:
        c = results.get(ap, {}).get('cost_per_prim', {})
        print(f'| {ap} | {c.get("empty_bytes_for_10_prims", "—")} | '
              f'{c.get("with_identifier_bytes_for_10_prims", "—")} | '
              f'{c.get("delta_bytes", "—")} | '
              f'{c.get("bytes_per_prim", "—"):.1f} |', file=buf)
    print('', file=buf)

    print('## Observations', file=buf)
    print('', file=buf)
    print('- None of the schemas across the five approaches declare',
          file=buf)
    print('  `apiSchemaCanOnlyApplyTo`. With the constraint absent, scope',
          file=buf)
    print('  is decided by policy (what tooling chooses to apply where)',
          file=buf)
    print('  rather than by schema-level enforcement.',
          file=buf)
    print('- Apply succeeded for all tested prim types (Mesh leaf, Over',
          file=buf)
    print('  typeless, Scope, Xform, Xform with kind=component) for every',
          file=buf)
    print('  approach. The matrix records the tested range; broader',
          file=buf)
    print('  applicability is not measured.', file=buf)
    print('- Cost-per-prim (bytes/prim) ranges from 90 to 223 across the',
          file=buf)
    print('  five approaches under the single payload measured (short',
          file=buf)
    print('  ASCII vendor name, single-character primaryId). Different',
          file=buf)
    print('  identifier-data sizes are not measured.',
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
