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
    print('- A, C, D-identifier share the same storage shape and the same',
          file=buf)
    print('  indexer (`assetInfo.source.<vendor>` walk). Indexer is short', file=buf)
    print('  and naturally enumerates vendors from the dictionary keys.', file=buf)
    print('- B\'s indexer must know the property-namespace template', file=buf)
    print('  (`sourceIdentifier:<vendor>:primaryId`) — without that', file=buf)
    print('  knowledge, a tool can\'t distinguish a source-identifier', file=buf)
    print('  attribute from any other namespaced attribute on the prim.', file=buf)
    print('  Recall still 100% once the convention is known.', file=buf)
    print('- B\' encodes the vendor identity into the schema CLASS name',
          file=buf)
    print('  applied to the prim. The indexer must walk `apiSchemas`', file=buf)
    print('  rather than properties to enumerate vendors.', file=buf)
    print('- B\' authors fewer rows than the other approaches because the',
          file=buf)
    print('  experiment plugin ships per-vendor schemas only for Windchill',
          file=buf)
    print('  and IFC (no Adobe). Per-vendor schemas are the artifact',
          file=buf)
    print("  B' requires a vendor to ship; the missing Adobe schema models",
          file=buf)
    print('  that real cost. Adobe rows are skipped at author time, so',
          file=buf)
    print('  they affect the *authored count* (36 vs 52) but not recall.',
          file=buf)
    print('- The 63.9% recall reflects a separate, structural finding: the',
          file=buf)
    print("  shared-base-property effect (per v3 findings). B's expression",
          file=buf)
    print('  via `prepend apiSchemas` makes `sourceId:primaryId` a SINGLE',
          file=buf)
    print('  slot shared across vendor schemas applied to one prim. When',
          file=buf)
    print('  a prim has both Windchill and IFC applied, the second author',
          file=buf)
    print("  overwrites the first — the index can't recover the original",
          file=buf)
    print('  per-vendor primaryId. The 63.9% number is the fraction of',
          file=buf)
    print('  authored entries whose value survived this clobbering.',
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
