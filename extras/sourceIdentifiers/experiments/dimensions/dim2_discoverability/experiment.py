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


def iter_rows(results):
    """Yield (label, surfaces_block) for each approach row in the tables.
    D appears twice when label_half data is present: once as the identifier
    half and once as the label half."""
    for ap in APPROACHES:
        ap_block = results.get(ap, {})
        if ap == 'D' and 'label_half' in ap_block:
            yield ('D (id half)', ap_block.get('surfaces', {}))
            yield ('D (label half)', ap_block.get('label_half', {}))
        else:
            yield (ap, ap_block.get('surfaces', {}))


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
    print('the identifier value? For approach D, the label half is measured',
          file=buf)
    print('separately by authoring a `SemanticLabelsAPI:windchill:partCategory`',
          file=buf)
    print('instance on a fresh prim and re-running the same four surfaces.',
          file=buf)
    print('', file=buf)

    # Per-surface table
    print('## Surface 1 — `prim.GetAppliedSchemas()`', file=buf)
    print('', file=buf)
    print('Does the schemas list surface the vendor identity directly?', file=buf)
    print('', file=buf)
    print('| approach | applied_schemas | vendor visible? |', file=buf)
    print('|---|---|---|', file=buf)
    for label, surfaces in iter_rows(results):
        s = surfaces.get('applied_schemas', {})
        schemas = ', '.join(f'`{x}`' for x in s.get('applied_schemas', []))
        mark = '✓' if s.get('vendor_visible_in_applied_schemas') else '✗'
        print(f'| {label} | {schemas} | {mark} |', file=buf)
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
    for label, surfaces in iter_rows(results):
        s = surfaces.get('prim_def_metadata', {})
        meta = s.get('prim_def_assetInfo')
        meta_str = '`' + str(meta) + '`' if meta else '_(none)_'
        mark = '✓' if s.get('has_source_key_without_authoring') else '✗'
        print(f'| {label} | {meta_str} | {mark} |', file=buf)
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
    for label, surfaces in iter_rows(results):
        s = surfaces.get('generic_gui_walk', {})
        a = '✓' if s.get('vendor_found_via_apply_schemas') else '✗'
        b = '✓' if s.get('vendor_found_via_assetInfo_source') else '✗'
        print(f'| {label} | {a} | {b} |', file=buf)
    print('', file=buf)

    print('## Observations', file=buf)
    print('', file=buf)
    print('- A authors the vendor identity in assetInfo only. The applied',
          file=buf)
    print('  schemas list shows `SourceIdentifiersAPI` but not the specific',
          file=buf)
    print('  vendor. A generic walker recovers the vendor via the',
          file=buf)
    print('  assetInfo strategy, not via applied_schemas.', file=buf)
    print('- B encodes the vendor identity into the apply instance name',
          file=buf)
    print('  (e.g. `SourceIdentifierAPI:windchill`). A generic',
          file=buf)
    print('  applied-schemas walk recovers the vendor directly.', file=buf)
    print('- B\' (Bprime) encodes the vendor into the schema CLASS name',
          file=buf)
    print('  (`WindchillSourceIdAPI`). The applied-schemas walk recovers',
          file=buf)
    print('  the vendor token via the class name. Enumerating all known',
          file=buf)
    print('  vendors at the registry level requires querying for classes',
          file=buf)
    print('  inheriting from `SourceIdentifierBaseAPI`; PR #105 flags',
          file=buf)
    print('  the registry-query enhancements this needs.',
          file=buf)
    print('- C\'s `SourceIdentifierBridgeAPI:windchill` applied-schema',
          file=buf)
    print('  name is visible, but the `assetInfoFallback` customData on',
          file=buf)
    print('  the schema does NOT surface in UsdPrimDefinition in this',
          file=buf)
    print('  run (`prim_def_assetInfo: null` in report.json). The',
          file=buf)
    print('  resulting storage shape is the same as A.', file=buf)
    print('- D appears on two rows in the surface tables — one for the',
          file=buf)
    print('  identifier half (assetInfo.source authoring) and one for the',
          file=buf)
    print('  label half (SemanticLabelsAPI:<vendor>:<labelKind>',
          file=buf)
    print('  authoring). The two halves land on different surfaces: the',
          file=buf)
    print('  identifier half surfaces via assetInfo (vendor not in',
          file=buf)
    print('  applied_schemas); the label half surfaces via applied_schemas',
          file=buf)
    print('  (vendor in instance name, no assetInfo authored).',
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
