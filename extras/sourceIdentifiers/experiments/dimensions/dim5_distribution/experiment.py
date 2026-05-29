"""Dim 5 driver — schema/plugin distribution across the five approaches.

PR #105 Principle 3 (vendor extensibility). Captures, per approach:
what a vendor ships, how vendors avoid name collisions, and an
empirical check that two vendors can coexist on one prim.
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
    print('# Dim 5 — schema/plugin distribution (P3)', file=buf)
    print('', file=buf)
    print('PR #105 Principle 3: "any vendor or standards body can declare',
          file=buf)
    print('their own identifier scheme without central approval. Vendor',
          file=buf)
    print('extensions are data-model-level, not plugin-architecture-level."',
          file=buf)
    print('', file=buf)
    print('This dimension records what a vendor must ship to register a new',
          file=buf)
    print('identifier scheme, and verifies empirically that two vendors can',
          file=buf)
    print('coexist on one prim.', file=buf)
    print('', file=buf)

    # Artifact-shipped table
    print('## Artifact shipped per vendor', file=buf)
    print('', file=buf)
    print('| approach | artifact | uses core schema | vendor collision mode |',
          file=buf)
    print('|---|---|---|---|', file=buf)
    for ap in APPROACHES:
        r = results.get(ap, {})
        print(f'| {ap} | {r.get("artifact_shipped", "—")} | '
              f'{"yes" if r.get("registers_with_core") else "no"} | '
              f'{r.get("vendor_collision_mode", "—")} |', file=buf)
    print('', file=buf)

    # Registration steps
    print('## Registration steps per approach', file=buf)
    print('', file=buf)
    for ap in APPROACHES:
        steps = results.get(ap, {}).get('registration_steps', [])
        print(f'### {ap}', file=buf)
        print('', file=buf)
        for s in steps:
            print(f'- {s}', file=buf)
        print('', file=buf)

    # Coexistence
    print('## Two-vendor coexistence (empirical)', file=buf)
    print('', file=buf)
    print('Two different vendor identifiers (`windchill`, `ifc`) applied to', file=buf)
    print('one prim; layer exported and re-imported; both identifiers', file=buf)
    print('queried back independently. `✓` = both vendors\' values recovered', file=buf)
    print('and equal to the authored value. `~` = applies, but storage', file=buf)
    print('shape constrains per-vendor independence (see notes).', file=buf)
    print('', file=buf)
    print('| approach | windchill round-trip | ifc round-trip | distinct vendor storage |',
          file=buf)
    print('|---|---|---|---|', file=buf)

    def render_coexist_row(label, c):
        if not c or 'error' in c:
            err = c.get('error', '—') if c else '—'
            print(f'| {label} | ERROR | ERROR | {err} |', file=buf)
            return
        wc_mark = '✓' if c.get('windchill_matches') else (
            '~' if c.get('windchill_matches') is None else '✗')
        ifc_mark = '✓' if c.get('ifc_matches') else (
            '~' if c.get('ifc_matches') is None else '✗')
        dist = 'yes' if c.get('distinct_vendor_storage') else 'no'
        print(f'| {label} | {wc_mark} | {ifc_mark} | {dist} |', file=buf)

    for ap in APPROACHES:
        ap_block = results.get(ap, {})
        if ap == 'D' and 'label_half' in ap_block:
            render_coexist_row('D (id half)', ap_block.get('two_vendors_coexist', {}))
            render_coexist_row(
                'D (label half)',
                ap_block.get('label_half', {}).get('two_vendors_coexist', {}))
        else:
            render_coexist_row(ap, ap_block.get('two_vendors_coexist', {}))
    print('', file=buf)

    # Bprime-specific
    bp = results.get('Bprime', {}).get('per_vendor_schemas_shipped', {})
    if bp:
        print('## Bprime per-vendor schemas registered', file=buf)
        print('', file=buf)
        print('Bprime\'s registration step requires the vendor to ship a',
              file=buf)
        print('per-vendor schema class. The experiment plugin ships two as',
              file=buf)
        print('a concrete example, and SchemaRegistry confirms both register:',
              file=buf)
        print('', file=buf)
        for name, registered in bp.items():
            print(f'- `{name}` registered: {registered}', file=buf)
        print('', file=buf)

    # Observations
    print('## Observations', file=buf)
    print('', file=buf)
    print('- A, B, C, D ship the schema in the core (USD or AOUSD), and a',
          file=buf)
    print('  vendor registers a new identifier scheme by authoring data',
          file=buf)
    print('  into the agreed-on slot — no per-vendor schema or plugin.',
          file=buf)
    print('  This is the "data-model-level, not plugin-architecture-level"',
          file=buf)
    print('  form named in P3.', file=buf)
    print('- B\' (Bprime) registers a new identifier scheme by declaring',
          file=buf)
    print('  a per-vendor schema class that inherits from the base via',
          file=buf)
    print('  `prepend apiSchemas`, then publishing a plugin that USD',
          file=buf)
    print('  loads via PXR_PLUGINPATH_NAME. The class name occupies a',
          file=buf)
    print('  slot in the TfType namespace.', file=buf)
    print('- B\' (Bprime) shared-base-property effect: because the',
          file=buf)
    print('  per-vendor schemas inherit `SourceIdentifierBaseAPI` via',
          file=buf)
    print('  `prepend apiSchemas`, `sourceId:primaryId` is one attribute',
          file=buf)
    print('  shared across all applied vendor schemas on a prim. Applying',
          file=buf)
    print('  both WindchillSourceIdAPI and IFCSourceIdAPI to one prim',
          file=buf)
    print('  yields one primaryId slot, with the most-recently-authored',
          file=buf)
    print('  value resolved for both. Vendor-specific properties declared',
          file=buf)
    print('  outside the shared base remain per-vendor.', file=buf)
    print('- For A, C, D the vendor identity is a dict key under',
          file=buf)
    print('  `assetInfo.source`; two vendors coexist as separate',
          file=buf)
    print('  sub-dictionaries.', file=buf)
    print('- For B and D-label the vendor identity is the ApplyAPI',
          file=buf)
    print('  instance name; two vendors coexist as two schema instances',
          file=buf)
    print('  on the same prim. The D label-half row above grounds this',
          file=buf)
    print('  symmetrically with the B row.', file=buf)
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
