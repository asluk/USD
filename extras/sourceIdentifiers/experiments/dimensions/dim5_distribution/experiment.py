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
    print('byte-for-byte. `~` = applies, but storage shape constrains the', file=buf)
    print('per-vendor independence (see notes).', file=buf)
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
        print('## Bprime per-vendor schemas (sanity check)', file=buf)
        print('', file=buf)
        print('Bprime requires the vendor to ship a per-vendor schema class.',
              file=buf)
        print('The experiment plugin already ships two as a concrete example:',
              file=buf)
        print('', file=buf)
        for name, registered in bp.items():
            print(f'- `{name}` registered: {registered}', file=buf)
        print('', file=buf)

    # Observations
    print('## Observations', file=buf)
    print('', file=buf)
    print('- A, B, C, D are all "data-only" from a vendor\'s perspective —',
          file=buf)
    print('  the core (USD or AOUSD) ships the schema, and vendors just',
          file=buf)
    print('  author data into the agreed-on slot. This matches P3\'s', file=buf)
    print('  "data-model-level, not plugin-architecture-level" wording.',
          file=buf)
    print('- B\' is the outlier: it requires the vendor to ship a plugin', file=buf)
    print('  (per-vendor schema class). The per-vendor schema goes through', file=buf)
    print('  USD\'s plugin registration mechanism (plugInfo.json,',
          file=buf)
    print('  PXR_PLUGINPATH_NAME), and the class name occupies a slot in', file=buf)
    print('  the global TfType namespace.', file=buf)
    print('- B\' also surfaces a *base-property-sharing* effect in this run:', file=buf)
    print('  applying both WindchillSourceIdAPI and IFCSourceIdAPI to one', file=buf)
    print('  prim gives only ONE `sourceId:primaryId` slot (the base is', file=buf)
    print('  shared via `prepend apiSchemas`). Per-vendor extensions can', file=buf)
    print('  still coexist (each vendor\'s own additional properties remain', file=buf)
    print('  distinct), but the *base identifier* is not naturally', file=buf)
    print('  one-per-vendor in this expression of B\'.', file=buf)
    print('- For A, C, D the vendor identity is a dict key — two vendors', file=buf)
    print('  coexist as separate sub-dictionaries with no schema work.',
          file=buf)
    print('- For B and D-label the vendor identity is an ApplyAPI instance', file=buf)
    print('  name — two vendors coexist as two schema instances on one', file=buf)
    print('  prim, again with no schema work.', file=buf)
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
