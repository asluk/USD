"""Dim 8 driver — within-approach lifecycle behavior across A/B/B'/C/D.

PR #105 Principle 3 ("Vendor extensibility... tiered lifecycle: vendor →
multi-vendor → core"). Three sub-scenarios in one probe:

  8.1 promotion              vendor name `windchill` → `multiVendor`
  8.2 coexistence            mixed `windchill` + `multiVendor` on one stage
  8.3 within-vendor versioning  field rename `primaryId` → `oid` on one stage

Per-approach observations only — no comparative verdicts.
"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _harness import APPROACHES, run_all_approaches, write_report

DIM_DIR = Path(__file__).resolve().parent
PROBE = DIM_DIR / 'probe.py'


def _fmt(val):
    if isinstance(val, bool):
        return '`True`' if val else '`False`'
    if val is None:
        return '`None`'
    if isinstance(val, list):
        return ', '.join(str(x) for x in val) if val else '(empty)'
    return f'`{val}`'


def render_summary(results):
    buf = io.StringIO()
    print('# Dim 8 — within-approach lifecycle (P3)', file=buf)
    print('', file=buf)
    print('PR #105 Principle 3 ("Vendor extensibility... tiered lifecycle:',
          file=buf)
    print('vendor → multi-vendor → core"). Three sub-scenarios probed per',
          file=buf)
    print('approach; all three reduce to "rewrite layer content, measure',
          file=buf)
    print('what changed in layers / schemas / plugins."', file=buf)
    print('', file=buf)
    print('- **8.1 promotion**: 3 prims under `windchill` are rewritten',
          file=buf)
    print('  into a new layer with the vendor name changed to',
          file=buf)
    print('  `multiVendor`. Measure layer text size before/after and',
          file=buf)
    print('  whether the approach\'s schema/plugin registration must also',
          file=buf)
    print('  change for the rewritten layer to be recognized.', file=buf)
    print('- **8.2 coexistence**: 3 prims under `windchill` + 3 prims',
          file=buf)
    print('  under `multiVendor` on the same stage. Measure whether both',
          file=buf)
    print('  names resolve on a single read pass.', file=buf)
    print('- **8.3 within-vendor versioning**: one prim with the canonical',
          file=buf)
    print('  v1 field (`primaryId`), one prim with a renamed v2 field',
          file=buf)
    print('  (`oid`), coexisting on one stage. Measure where the v2 field',
          file=buf)
    print('  lives relative to the approach\'s schema-declared properties.',
          file=buf)
    print('', file=buf)
    print('"Schema/plugin diff" is descriptive: it answers whether the',
          file=buf)
    print('approach\'s registration files (`schema.usda`, `plugInfo.json`)',
          file=buf)
    print('must be edited for the rewrite to land in the schema registry.',
          file=buf)
    print('Larger or smaller diffs are not scored.', file=buf)
    print('', file=buf)

    # --- 8.1 promotion table -----------------------------------------------
    print('## 8.1 Promotion — `windchill` → `multiVendor` (3 prims)', file=buf)
    print('', file=buf)
    print('| approach | v1 lines | v2 lines | Δ | rewritten | v2 read | '
          'vendor-identity location | schema change | plugin change |',
          file=buf)
    print('|---|---|---|---|---|---|---|---|---|', file=buf)
    for ap in APPROACHES:
        r = results.get(ap, {}).get('scenarios', {}).get('8.1_promotion', {})
        if 'error' in r:
            print(f'| {ap} | ERROR | | | | | {r["error"]} | | |', file=buf)
            continue
        print(
            f'| {ap} | {r.get("layer_v1_lines")} | {r.get("layer_v2_lines")} '
            f'| {r.get("layer_line_delta")} | {r.get("prims_rewritten")} '
            f'| {r.get("v2_readable_prims")} '
            f'| {r.get("vendor_identity_location")} '
            f'| {_fmt(r.get("schema_change_required"))} '
            f'| {_fmt(r.get("plugin_change_required"))} |',
            file=buf)
    print('', file=buf)

    # --- 8.2 coexistence table ---------------------------------------------
    print('## 8.2 Coexistence — `windchill` + `multiVendor` on one stage',
          file=buf)
    print('', file=buf)
    print('| approach | windchill read | multiVendor read | vendors observable on stage | both resolve |',
          file=buf)
    print('|---|---|---|---|---|', file=buf)
    for ap in APPROACHES:
        r = results.get(ap, {}).get('scenarios', {}).get('8.2_coexistence', {})
        if 'error' in r:
            print(f'| {ap} | ERROR | | {r["error"]} | |', file=buf)
            continue
        wc = (f'{r.get("windchill_readable")}/'
              f'{r.get("authored_windchill_prims")}')
        mv = (f'{r.get("multivendor_readable")}/'
              f'{r.get("authored_multivendor_prims")}')
        observed = ', '.join(r.get('vendors_observable_on_stage', []))
        print(
            f'| {ap} | {wc} | {mv} | {observed} '
            f'| {_fmt(r.get("both_resolve_on_one_stage"))} |',
            file=buf)
    print('', file=buf)

    # --- 8.3 versioning table ----------------------------------------------
    print('## 8.3 Within-vendor versioning — `primaryId` → `oid`', file=buf)
    print('', file=buf)
    print('| approach | v1 read | v2 read | v1 in schema | v2 in schema | v2 field location |',
          file=buf)
    print('|---|---|---|---|---|---|', file=buf)
    for ap in APPROACHES:
        r = results.get(ap, {}).get('scenarios', {}).get('8.3_versioning', {})
        if 'error' in r:
            print(f'| {ap} | ERROR | | {r["error"]} | | |', file=buf)
            continue
        print(
            f'| {ap} | {_fmt(r.get("v1_readable"))} '
            f'| {_fmt(r.get("v2_readable"))} '
            f'| {_fmt(r.get("v1_field_in_schema"))} '
            f'| {_fmt(r.get("v2_field_in_schema"))} '
            f'| {_fmt(r.get("v2_field_location"))} |',
            file=buf)
    print('', file=buf)

    # --- observations ------------------------------------------------------
    print('## Observations', file=buf)
    print('', file=buf)
    print('- **Vendor-identity location drives 8.1.** For A, B, C, D the',
          file=buf)
    print('  vendor name lives as data (assetInfo dict key for A/C/D;',
          file=buf)
    print('  multi-apply instance name for B; both for C). Promotion is a',
          file=buf)
    print('  layer-data rewrite. For B′ the vendor name is a schema class',
          file=buf)
    print('  identifier (`WindchillSourceIdAPI`), so promotion would',
          file=buf)
    print('  additionally require renaming or issuing the registered',
          file=buf)
    print('  schema and updating `plugInfo.json`. The probe reports this',
          file=buf)
    print('  descriptively — schema/plugin diff size is not scored.',
          file=buf)
    print('- **8.2 coexistence is supported by all approaches** because',
          file=buf)
    print('  each mechanism allows independent authoring of two vendor',
          file=buf)
    print('  names on different prims of the same stage. Disambiguation', file=buf)
    print('  between the two names (e.g., "if both are authored on the',
          file=buf)
    print('  SAME prim, which wins?") is an application-level convention',
          file=buf)
    print('  question, not a mechanism affordance, and is out of scope', file=buf)
    print('  for this probe.', file=buf)
    print('- **8.3 versioning splits by schema kind, not by approach',
          file=buf)
    print('  family.** Approaches whose vendor sub-shape is a documented',
          file=buf)
    print('  dict contract with no typed properties (A, C, D) absorb the',
          file=buf)
    print('  field rename inside the dict without USD-schema involvement.',
          file=buf)
    print('  Approaches whose fields are typed schema properties (B, B′)',
          file=buf)
    print('  accept the renamed field as a custom attribute on the same',
          file=buf)
    print('  prim; the v2 field is NOT in `UsdPrimDefinition` and has no',
          file=buf)
    print('  schema fallback. Either path round-trips; the difference is',
          file=buf)
    print('  whether the field is schema-aware.', file=buf)
    print('- **D, labels half (not exercised here directly).** Promotion',
          file=buf)
    print('  and versioning of labels track B-shape behavior (instance',
          file=buf)
    print('  name + property segment rewrite for promotion; custom',
          file=buf)
    print('  attribute for v2 field). Coexistence of two label vendors',
          file=buf)
    print('  on one stage tracks B. The identifier half (probed above)',
          file=buf)
    print('  tracks A.', file=buf)
    print('- **B′ "base-only" branch** — when an authoring path needs a',
          file=buf)
    print('  vendor without a registered per-vendor schema (e.g.,',
          file=buf)
    print('  `multiVendor` in this probe), the only mechanism available',
          file=buf)
    print('  is to apply `SourceIdentifierBaseAPI` directly. The prim',
          file=buf)
    print('  then carries no schema-level vendor identity; coexistence',
          file=buf)
    print('  with windchill on the same stage is observable via the',
          file=buf)
    print('  applied-schema list per prim, not as a stage-wide vendor',
          file=buf)
    print('  set.', file=buf)
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
