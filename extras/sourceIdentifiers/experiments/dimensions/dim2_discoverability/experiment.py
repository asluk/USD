"""Dim 2 driver — discoverability across the five approaches.

PR #105 Principle 5. Per approach, on a prim with one vendor identifier
authored, captures four discovery surfaces and reports what signal each
exposes about the vendor identity and identifier value.
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
    print('# Dim 2 — discoverability (P5)', file=buf)
    print('', file=buf)
    print('PR #105 Principle 5: "tools can discover a prim carries source',
          file=buf)
    print('identifiers without prior pipeline-specific knowledge."', file=buf)
    print('', file=buf)
    print('Probed on a prim with one vendor (`windchill`) identifier authored.',
          file=buf)
    print('Four surfaces queried — what does each reveal about the vendor and',
          file=buf)
    print('the identifier value?', file=buf)
    print('', file=buf)

    # Per-surface table
    print('## Surface 1 — `prim.GetAppliedSchemas()`', file=buf)
    print('', file=buf)
    print('Does the schemas list surface the vendor identity directly?', file=buf)
    print('', file=buf)
    print('| approach | applied_schemas | vendor visible? |', file=buf)
    print('|---|---|---|', file=buf)
    for ap in APPROACHES:
        s = results.get(ap, {}).get('surfaces', {}).get('applied_schemas', {})
        schemas = ', '.join(f'`{x}`' for x in s.get('applied_schemas', []))
        mark = '✓' if s.get('vendor_visible_in_applied_schemas') else '✗'
        print(f'| {ap} | {schemas} | {mark} |', file=buf)
    print('', file=buf)

    print('## Surface 2 — `UsdPrimDefinition.GetMetadata("assetInfo")`', file=buf)
    print('', file=buf)
    print('Does the schema\'s declared fallback metadata expose a `source`',
          file=buf)
    print('sub-dictionary in the prim definition (without scene authoring)?',
          file=buf)
    print('', file=buf)
    print('| approach | prim_def_assetInfo | has `source` fallback? |',
          file=buf)
    print('|---|---|---|', file=buf)
    for ap in APPROACHES:
        s = results.get(ap, {}).get('surfaces', {}).get('prim_def_metadata', {})
        meta = s.get('prim_def_assetInfo')
        meta_str = '`' + str(meta) + '`' if meta else '_(none)_'
        mark = '✓' if s.get('has_source_key_without_authoring') else '✗'
        print(f'| {ap} | {meta_str} | {mark} |', file=buf)
    print('', file=buf)

    print('## Surface 3 — typed property fallbacks (registry-derived)', file=buf)
    print('', file=buf)
    print('What property names does each approach expose via the schema',
          file=buf)
    print('registry without any scene authoring? Multi-apply schemas',
          file=buf)
    print('answered for a `windchill` instance.', file=buf)
    print('', file=buf)
    for ap in APPROACHES:
        s = results.get(ap, {}).get('surfaces', {}).get('prim_def_properties', {})
        print(f'### {ap}', file=buf)
        print('', file=buf)
        if not s:
            print('_(no schema-defined properties)_', file=buf)
        else:
            for schema_name, info in s.items():
                kind = info.get('kind', '?')
                if 'properties' in info:
                    props = info['properties']
                elif 'property_template' in info:
                    props = info['property_template']
                else:
                    props = info.get('error', '?')
                print(f'- `{schema_name}` ({kind}): {props}', file=buf)
        print('', file=buf)

    print('## Surface 4 — generic GUI walk', file=buf)
    print('', file=buf)
    print('Two generic strategies that a tool *not pre-loaded with any',
          file=buf)
    print('vendor schema* could try: (a) scan `GetAppliedSchemas()` for a',
          file=buf)
    print('schema-instance pattern; (b) scan `GetAssetInfo()` for a',
          file=buf)
    print('`source` sub-dictionary. The matrix records which strategy', file=buf)
    print('actually recovers the vendor name on each approach.', file=buf)
    print('', file=buf)
    print('| approach | via applied_schemas (a) | via assetInfo.source (b) |',
          file=buf)
    print('|---|---|---|', file=buf)
    for ap in APPROACHES:
        s = results.get(ap, {}).get('surfaces', {}).get('generic_gui_walk', {})
        a = '✓' if s.get('vendor_found_via_apply_schemas') else '✗'
        b = '✓' if s.get('vendor_found_via_assetInfo_source') else '✗'
        print(f'| {ap} | {a} | {b} |', file=buf)
    print('', file=buf)

    print('## Observations', file=buf)
    print('', file=buf)
    print('- A authors the vendor identity ONLY in assetInfo — the applied',
          file=buf)
    print('  schemas list reveals `SourceIdentifiersAPI` (the contract',
          file=buf)
    print('  marker) but not the specific vendor. A generic GUI walker',
          file=buf)
    print('  finds the vendor via the assetInfo strategy, not via', file=buf)
    print('  applied_schemas.', file=buf)
    print('- B and D-label encode the vendor identity into the apply',
          file=buf)
    print('  instance name (e.g. `SourceIdentifierAPI:windchill`). Generic',
          file=buf)
    print("  applied-schemas walk recovers the vendor directly.", file=buf)
    print('- B\' encodes the vendor into the schema CLASS name', file=buf)
    print('  (`WindchillSourceIdAPI`). Generic applied-schemas walk', file=buf)
    print('  recovers the vendor too — but a tool that wants to enumerate', file=buf)
    print('  *all known* vendors must consult the schema registry for', file=buf)
    print('  classes inheriting from `SourceIdentifierBaseAPI`, requiring', file=buf)
    print('  the registry-query enhancements PR #105 flags as a B\'',
          file=buf)
    print('  prerequisite.', file=buf)
    print("- C is the most surprising: the `assetInfoFallback` mechanism",
          file=buf)
    print('  is not consumed by UsdPrimDefinition in current OpenUSD', file=buf)
    print('  (per v3 findings). C\'s `SourceIdentifierBridgeAPI:windchill`',
          file=buf)
    print('  applied-schema name is visible, but the schema\'s declared',
          file=buf)
    print('  fallback assetInfo dict does NOT surface in the prim',
          file=buf)
    print('  definition. Storage shape reduces to A.', file=buf)
    print('- D has TWO discovery surfaces: applied_schemas (with',
          file=buf)
    print("  `SemanticLabelsAPI:<vendor>:<labelKind>` instances for the", file=buf)
    print("  label half) and assetInfo.source.<vendor> (for the", file=buf)
    print('  identifier half). The applied-schemas list does not by', file=buf)
    print('  itself encode the identifier vendor — that lives in', file=buf)
    print('  assetInfo, same as A.', file=buf)
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
