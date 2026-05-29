"""Dim 3 driver — external queryability across the five approaches.

PR #105 Principle 6 ("External queryability") + Open Question 1
(Cross-system resolution and indexing).

The probe builds a synthetic project per approach (30 prims, 3 vendors,
deterministic multi-vendor mix), saves it as `.usda`, and walks the saved
layer with a hand-written Sdf-level indexer that knows ONLY the
approach's storage convention. Reports recall, vendor-discovery, and
indexer LoC.
"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _harness import APPROACHES, run_all_approaches, write_report

DIM_DIR = Path(__file__).resolve().parent
PROBE = DIM_DIR / 'probe.py'


def render_summary(results):
    buf = io.StringIO()
    print('# Dim 3 — external queryability (P6 + OQ1)', file=buf)
    print('', file=buf)
    print('PR #105 Principle 6 ("External queryability") + Open Question 1', file=buf)
    print('(Cross-system resolution and indexing). The probe asks: given a',
          file=buf)
    print('saved `.usda` layer with identifiers across multiple vendors, how',
          file=buf)
    print('tractable is it to build an external index recovering', file=buf)
    print('`(prim_path, vendor, primaryId)` triples?', file=buf)
    print('', file=buf)
    print('Each indexer walks the Sdf-level layer ONLY — no `Usd.Stage`', file=buf)
    print('composition, no schema introspection beyond the approach\'s', file=buf)
    print('storage convention.', file=buf)
    print('', file=buf)

    print('## Indexer effort and recall', file=buf)
    print('', file=buf)
    print('| approach | indexer LoC | authored | recovered | recall |',
          file=buf)
    print('|---|---|---|---|---|', file=buf)
    for ap in APPROACHES:
        r = results.get(ap, {})
        print(f'| {ap} | {r.get("indexer_loc", "—")} | '
              f'{r.get("authored_count", "—")} | '
              f'{r.get("recovered_count", "—")} | '
              f'{r.get("recall_pct", 0.0):.1f}% |',
              file=buf)
    print('', file=buf)

    print('## Vendor discovery without prior knowledge', file=buf)
    print('', file=buf)
    print('Did the indexer recover every vendor it had data on, just from',
          file=buf)
    print('the layer (no pipeline-config knowing what vendors exist)?',
          file=buf)
    print('', file=buf)
    print('| approach | vendors authored | vendors discovered |', file=buf)
    print('|---|---|---|', file=buf)
    for ap in APPROACHES:
        r = results.get(ap, {})
        va = ', '.join(r.get('vendors_authored', []))
        vd = ', '.join(r.get('vendors_discovered', []))
        print(f'| {ap} | {va} | {vd} |', file=buf)
    print('', file=buf)

    print('## Sample recovered identifiers (per approach)', file=buf)
    print('', file=buf)
    for ap in APPROACHES:
        sample = results.get(ap, {}).get('sample_recovered', [])
        print(f'### {ap}', file=buf)
        print('', file=buf)
        if not sample:
            print('_(none)_', file=buf)
        else:
            for path, vendor, pid in sample:
                print(f'- `{path}` → ({vendor}, `{pid}`)', file=buf)
        print('', file=buf)

    print('## Observations', file=buf)
    print('', file=buf)
    print('- Each indexer relies on knowing its approach\'s storage',
          file=buf)
    print('  convention: A/C/D walk `assetInfo.source.<vendor>` dict',
          file=buf)
    print('  keys; B walks property-name segments matching',
          file=buf)
    print('  `sourceIdentifier:<vendor>:primaryId`; B\' walks',
          file=buf)
    print('  `apiSchemas` for class names ending in `SourceIdAPI`.',
          file=buf)
    print('  The convention is the input each indexer needs.',
          file=buf)
    print('- A, C, D identifier-half share storage shape',
          file=buf)
    print('  (`assetInfo.source.<vendor>`). In `probe.py`, C\'s and D\'s',
          file=buf)
    print('  indexer functions are one-line delegations that call A\'s',
          file=buf)
    print('  indexer (`return indexer_A(layer_path)`); the indexer-LoC',
          file=buf)
    print('  column reports each approach\'s function body length, so',
          file=buf)
    print('  A=14 is the actual walk and C=D=1 are the delegations.',
          file=buf)
    print('- B and B\' have indexer LoC closer to A\'s (16 and 22): the',
          file=buf)
    print('  property-template walk (B) and apiSchemas-class walk (B\')',
          file=buf)
    print('  are similar in complexity to A\'s dict walk on this probe\'s',
          file=buf)
    print('  data shape.', file=buf)
    print('- B\' (Bprime) authored 36 rows vs 52 for the others. The',
          file=buf)
    print('  experiment plugin ships per-vendor schemas for Windchill',
          file=buf)
    print('  and IFC only; Adobe rows are skipped at author time, so',
          file=buf)
    print('  the *authored count* records what actually landed in the',
          file=buf)
    print('  layer. Recall is computed against the actually-authored',
          file=buf)
    print('  subset.', file=buf)
    print('- B\' (Bprime) shared-base-property effect: the per-vendor',
          file=buf)
    print('  schemas inherit `SourceIdentifierBaseAPI` via `prepend',
          file=buf)
    print('  apiSchemas`, so `sourceId:primaryId` is one attribute',
          file=buf)
    print('  shared across vendor schemas applied on one prim. On a',
          file=buf)
    print('  prim with both Windchill and IFC applied, the shared slot',
          file=buf)
    print('  resolves to the most-recently-authored value; the indexer',
          file=buf)
    print('  reports both vendor labels with that one value. This',
          file=buf)
    print('  contributes the 63.9% recall on multi-vendor prims (recall',
          file=buf)
    print('  on single-vendor prims is 100%).',
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
