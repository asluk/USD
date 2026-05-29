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
    print('Four surfaces queried — what does each reveal about the vendor',
          file=buf)
    print('and the identifier value?', file=buf)
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
    print('The label half is measured by authoring a',
          file=buf)
    print('`SemanticLabelsAPI:windchill:partCategory` instance on a',
          file=buf)
    print('separate prim and running the same four surfaces; rows tagged',
          file=buf)
    print('"D (label half)" pull from that measurement.', file=buf)
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
    print('are listed with their `__INSTANCE_NAME__` template (no',
          file=buf)
    print('instance substituted).', file=buf)
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
    print('- A authors the vendor identity in `assetInfo.source.<vendor>`.',
          file=buf)
    print('  The applied-schemas list carries `SourceIdentifiersAPI` (no',
          file=buf)
    print('  vendor segment). A generic walker recovers the vendor via',
          file=buf)
    print('  the assetInfo surface; the applied-schemas surface does not',
          file=buf)
    print('  carry the vendor for A.', file=buf)
    print('- B authors the vendor identity in the apply instance name',
          file=buf)
    print('  (`SourceIdentifierAPI:windchill`). The applied-schemas',
          file=buf)
    print('  surface carries the vendor in the instance segment; the',
          file=buf)
    print('  assetInfo surface does not (`assetInfo_source_keys: []`).',
          file=buf)
    print('- B\' (Bprime) authors the vendor identity in the schema',
          file=buf)
    print('  class name (`WindchillSourceIdAPI`). The applied-schemas',
          file=buf)
    print('  surface carries the vendor in the class name. Enumerating',
          file=buf)
    print('  the set of vendor schemas at the registry level needs the',
          file=buf)
    print('  `UsdSchemaRegistry` query enhancements PR #105 names.',
          file=buf)
    print('- C applies `SourceIdentifierBridgeAPI:<vendor>` and authors',
          file=buf)
    print('  data into `assetInfo.source.<vendor>`. The applied-schemas',
          file=buf)
    print('  surface carries the vendor in the instance segment, and',
          file=buf)
    print('  the assetInfo surface carries the dict key — both. The',
          file=buf)
    print('  schema declares an `assetInfoFallback` customData entry',
          file=buf)
    print('  intended to surface in `UsdPrimDefinition`; in this run',
          file=buf)
    print('  `prim_def_assetInfo` is `null`, so the fallback path did',
          file=buf)
    print('  not bring the source sub-dictionary into the prim',
          file=buf)
    print('  definition. (See `report.json` for the exact field.)',
          file=buf)
    print('- D appears on two rows. The id half (assetInfo authoring)',
          file=buf)
    print('  surfaces via the assetInfo strategy, same as A. The label',
          file=buf)
    print('  half (SemanticLabelsAPI:<vendor>:<labelKind> authoring)',
          file=buf)
    print('  surfaces via the applied-schemas strategy, same as B. The',
          file=buf)
    print('  two halves are exercised independently here; on a real',
          file=buf)
    print('  prim a vendor could author either or both.',
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
