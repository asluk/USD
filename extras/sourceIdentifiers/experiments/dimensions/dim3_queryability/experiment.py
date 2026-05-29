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
    print('- A, C, D-identifier share storage shape',
          file=buf)
    print('  (`assetInfo.source.<vendor>` dict walk). C and D\'s indexer',
          file=buf)
    print('  functions in `probe.py` are one-line delegations that call',
          file=buf)
    print('  A\'s indexer (`return indexer_A(layer_path)`); the indexer-LoC',
          file=buf)
    print('  column reports the body length of each approach\'s indexer',
          file=buf)
    print('  function, so A=14 is the actual walk and C=D=1 is the',
          file=buf)
    print('  delegation. Vendors enumerate from dict keys with no',
          file=buf)
    print('  pre-registration.',
          file=buf)
    print('- B\'s indexer walks `sourceIdentifier:<vendor>:primaryId`-shaped', file=buf)
    print('  property names. The convention is the property-namespace', file=buf)
    print('  template; a tool that did not know the template would not', file=buf)
    print('  distinguish a source-identifier attribute from another', file=buf)
    print('  namespaced attribute on the prim. Recall is 100% once the', file=buf)
    print('  template is known.', file=buf)
    print('- B\' (Bprime) encodes vendor identity in the schema CLASS name',
          file=buf)
    print('  applied to the prim. The indexer walks `apiSchemas` rather',
          file=buf)
    print('  than the property table to enumerate vendors.', file=buf)
    print('- B\' authors fewer rows than the other approaches in this run',
          file=buf)
    print('  because the experiment plugin ships per-vendor schemas only',
          file=buf)
    print('  for Windchill and IFC. Adobe rows are skipped at author time,',
          file=buf)
    print('  so the *authored count* drops to 36 (vs 52) while recall', file=buf)
    print('  computes against the actually-authored subset.', file=buf)
    print('- B\' (Bprime) shared-base-property effect: the per-vendor',
          file=buf)
    print('  schemas inherit `SourceIdentifierBaseAPI` via `prepend',
          file=buf)
    print('  apiSchemas`, so `sourceId:primaryId` is a SINGLE attribute',
          file=buf)
    print('  slot shared across vendor schemas applied to one prim. When',
          file=buf)
    print('  a prim has both Windchill and IFC applied, only the',
          file=buf)
    print('  most-recently-authored value lives in the shared slot; the',
          file=buf)
    print('  indexer reports both vendor labels with that one value. The',
          file=buf)
    print('  63.9% recall reflects this slot-sharing effect on the',
          file=buf)
    print('  multi-vendor prims, not an indexer-walk limitation.',
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
