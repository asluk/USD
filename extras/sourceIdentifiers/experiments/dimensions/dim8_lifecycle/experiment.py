"""Dim 8 driver — content migration & compatibility.

PR #105 Principle 3 (vendor extensibility) — for carrier-types (a) and (b).
Operational concern downstream of mechanism plurality — for carrier-type (c).

Scenarios:
  1. forward     — author N=3 prims under X, rewrite under new carrier in new layer
  2. coexist     — both old + new forms on one stage; can both be enumerated?
  3. roundtrip   — c only: X -> Y -> X; what survives both hops?

Cross-approach scenarios (carrier c) are orchestrated here by invoking
the probe multiple times against different approaches, coordinating via
temp layer files written to a shared directory.
"""
import io
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _harness import (APPROACHES, run_all_approaches, run_probe, write_report,
                      DIMENSIONS_ROOT)

DIM_DIR = Path(__file__).resolve().parent
PROBE = DIM_DIR / 'probe.py'

# Storage-primitive-transition representatives for carrier (c).
# Not all 20 ordered pairs — chosen to cover storage-shape transitions.
# A/C/D-identifier-half are storage-equivalent (dict shape), so transitions
# among them are mostly trivial dict renames; we exercise A<->C and A<->D
# implicitly via A<->B and A<->Bprime.
CROSS_APPROACH_PAIRS = [
    ('A', 'B'),       # dict -> typed-attr
    ('B', 'A'),       # typed-attr -> dict
    ('A', 'Bprime'),  # dict -> schema-class
    ('Bprime', 'A'),  # schema-class -> dict
    ('B', 'Bprime'),  # typed-attr -> schema-class
    ('A', 'C'),       # dict -> dict-with-bridge (near-identity)
    ('A', 'D'),       # dict -> dict + labels (identifier half)
]


# ----------------------------------------------------------------------
# Per-approach forward/coexist scenarios (a + b)
# ----------------------------------------------------------------------

def run_forward_coexist():
    """Run forward_a, forward_b, coexist_a, coexist_b for each approach.
    Additionally run the *_label variants for D's label half."""
    results = {ap: {} for ap in APPROACHES}
    for mode in ('forward_a', 'forward_b', 'coexist_a', 'coexist_b'):
        per_approach = run_all_approaches(PROBE, mode)
        for ap in APPROACHES:
            results[ap][mode] = per_approach[ap]
    # D label half: separate modes, only D handles them
    for mode in ('forward_a_label', 'forward_b_label',
                 'coexist_a_label', 'coexist_b_label'):
        results['D'][mode] = run_probe(PROBE, 'D', mode)
    return results


# ----------------------------------------------------------------------
# Cross-approach forward + roundtrip (c)
# ----------------------------------------------------------------------

def run_cross_approach():
    """For each (src, dst) pair: src authors, dst rewrites, src reads back.

    Coordinates via a shared temp dir of layer files + json snapshots.
    Each step is a subprocess with PXR_PLUGINPATH_NAME pinned to that
    step's approach.
    """
    forward_c = {}     # {pair_label: {...}}
    roundtrip_c = {}   # {pair_label: {...}}
    coexist_c = {}     # {pair_label: {...}}

    with tempfile.TemporaryDirectory() as td:
        for src, dst in CROSS_APPROACH_PAIRS:
            pair_label = f'{src}->{dst}'

            v1 = os.path.join(td, f'{src}_{dst}_v1.usda')
            v2 = os.path.join(td, f'{src}_{dst}_v2.usda')
            v3 = os.path.join(td, f'{src}_{dst}_v3.usda')

            # Step 1: src authors v1.
            r1 = run_probe(PROBE, src, 'author_for_c', v1)
            # Step 2: dst rewrites v1 -> v2.
            r2 = run_probe(PROBE, dst, 'rewrite_for_c', v1, v2)
            # Step 3: src rewrites v2 -> v3 (round-trip back to source approach).
            r3 = run_probe(PROBE, src, 'rewrite_for_c', v2, v3)

            forward_c[pair_label] = {
                'src': src,
                'dst': dst,
                'src_author': r1,
                'dst_rewrite': r2,
            }
            roundtrip_c[pair_label] = {
                'src': src,
                'dst': dst,
                'src_author': r1,
                'dst_rewrite': r2,
                'src_rewrite_back': r3,
                'roundtrip_preserved': _compare_snapshots(r1, r3),
            }

            # Coexist (c): hand v1 (src approach) and v2 (dst approach) to
            # a neutral subprocess (one of the approaches, but reading raw
            # layer text — the snapshot files left by the probe — without
            # depending on any plugin's schemas).
            r_neutral = run_probe(PROBE, src, 'neutral_read', v1, v2)
            coexist_c[pair_label] = {
                'src_layer': v1,
                'dst_layer': v2,
                'neutral_read': r_neutral,
                'both_layers_readable_without_plugin_load': _both_readable(r_neutral),
            }

    return forward_c, roundtrip_c, coexist_c


def _compare_snapshots(author_result, rewriteback_result):
    """Compare snapshot before hop1 to snapshot after hop2 (back to src)."""
    if 'error' in (author_result.get('result') or {}):
        return {'comparable': False, 'reason': 'author_failed'}
    if 'error' in (rewriteback_result.get('result') or {}):
        return {'comparable': False, 'reason': 'rewriteback_failed'}
    a = (author_result.get('result') or {}).get('snapshot', {})
    b = (rewriteback_result.get('result') or {}).get('snapshot', {})
    matches = []
    diffs = []
    extras_lost_total = []
    for path in sorted(set(a.keys()) | set(b.keys())):
        a_entry = a.get(path) or {}
        b_entry = b.get(path) or {}
        av = a_entry.get('value')
        bv = b_entry.get('value')
        if av == bv:
            matches.append(path)
        else:
            diffs.append({'path': path, 'before': av, 'after': bv})
        # Compare extras (dict-keys beyond primaryId) for dict-storage
        # source approaches. If a had extras and b doesn't, those keys
        # were dropped at one of the hops.
        a_extras = a_entry.get('vendor_extras') or {}
        b_extras = b_entry.get('vendor_extras') or {}
        for k in a_extras:
            if k not in b_extras:
                extras_lost_total.append({'path': path, 'lost_key': k})
    return {
        'comparable': True,
        'value_preserved_for_all_prims': not diffs,
        'matches_count': len(matches),
        'diffs': diffs,
        'extras_lost_in_roundtrip': extras_lost_total,
    }


def _both_readable(neutral_result):
    """True if neutral_read observed both layer files."""
    obs = (neutral_result.get('result') or {}).get('observations', [])
    return len(obs) == 2 and all(o.get('layer_lines', 0) > 0 for o in obs)


# ----------------------------------------------------------------------
# Summary rendering
# ----------------------------------------------------------------------

def render_summary(results, forward_c, roundtrip_c, coexist_c):
    buf = io.StringIO()
    print('# Dim 8 — content migration & compatibility (P3 + operational)', file=buf)
    print('', file=buf)
    print('Umbrella question: when carrier choices change — vendor name,', file=buf)
    print('field name, or the approach itself — can content be migrated,', file=buf)
    print('can old + new forms coexist, and what survives the migration?', file=buf)
    print('', file=buf)
    print('Carrier-change types:', file=buf)
    print('', file=buf)
    print('- **(a)** vendor name within one approach (e.g.', file=buf)
    print('  `windchill` -> `multiVendor`).', file=buf)
    print('- **(b)** field name within one vendor (e.g.', file=buf)
    print('  `primaryId` -> `oid`).', file=buf)
    print('- **(c)** the approach itself (X -> Y).', file=buf)
    print('', file=buf)
    print('Cross-approach (c) is exercised on a chosen set of seven', file=buf)
    print('storage-primitive-transition representative ordered pairs', file=buf)
    print('rather than all 20. A/C/D identifier-half share the same dict', file=buf)
    print('storage shape (`assetInfo.source.<vendor>`), so the migration', file=buf)
    print('between dict-shape approaches is dict-key shape preservation', file=buf)
    print('with a schema-token change (the applied schema class is', file=buf)
    print('renamed). The chosen pairs include A->C and A->D for that', file=buf)
    print('shape; the reverse direction (C->A, D->A) is not enumerated.', file=buf)
    print('', file=buf)
    print('**Note on Approach D.** D is a candidate beyond PR #105',
          file=buf)
    print('(Matt Kuruc strawman, per the criteria file). Its mechanism',
          file=buf)
    print('combines an identifier half (assetInfo dict shape, mirroring',
          file=buf)
    print('A) and a label half (`SemanticLabelsAPI` multi-apply,',
          file=buf)
    print('mirroring B). Where a scenario applies to both halves, this',
          file=buf)
    print('summary shows two rows tagged "D (id half)" and "D (label',
          file=buf)
    print('half)"; carrier (c) cross-approach migration is exercised',
          file=buf)
    print('only on the identifier half (label-half cross-approach',
          file=buf)
    print('migration to A/B/B\'/C is not defined by the mechanism).',
          file=buf)
    print('', file=buf)

    # ------------------------------------------------------------------
    # Scenario 1 — forward migration
    # ------------------------------------------------------------------
    print('## Scenario 1 — forward migration', file=buf)
    print('', file=buf)
    print('Author N=3 prims under carrier X, rewrite under carrier Y in a', file=buf)
    print('new layer; observe what the rewrite required.', file=buf)
    print('', file=buf)

    print('### Carrier (a) — vendor name rewrite (`windchill` -> `multiVendor`)',
          file=buf)
    print('', file=buf)
    print('"Lexical mapping" = the rewrite can be expressed as a layer-text', file=buf)
    print('operation on the layer file. "Schema + plugin registration" = the', file=buf)
    print('rewrite touches the schema definition and the plugin\'s TfType', file=buf)
    print('registration, not just the layer text.', file=buf)
    print('', file=buf)
    print('| approach | convention | sites/prim | v1 lines | v2 lines | new vendor visible after rewrite |',
          file=buf)
    print('|---|---|---|---|---|---|', file=buf)

    def render_forward_a(label, row):
        if not row or 'error' in row:
            err = row.get('error', '—') if row else '—'
            print(f'| {label} | ERROR | — | — | — | `{err[:60]}` |', file=buf)
            return
        conv = row.get('convention', '—')
        spp = row.get('sites_per_prim')
        detail = row.get('sites_detail', '')
        if spp is None:
            sites = f'n/a ({detail})' if detail else 'n/a'
        else:
            sites = f'{spp} ({detail})' if detail else str(spp)
        sl = row.get('src_lines', '—')
        dl = row.get('dst_lines', '—')
        visible_list = row.get('new_vendors_visible_after_rewrite', [])
        nv = (', '.join(visible_list) if visible_list
              else 'none (no schema registered for new vendor)')
        print(f'| {label} | `{conv}` | {sites} | {sl} | {dl} | {nv} |', file=buf)

    for ap in APPROACHES:
        row = (results.get(ap, {}).get('forward_a', {}) or {}).get('result', {}) or {}
        if ap == 'D':
            render_forward_a('D (id half)', row)
            lab = (results.get('D', {}).get('forward_a_label', {})
                   or {}).get('result', {}) or {}
            render_forward_a('D (label half)', lab)
        else:
            render_forward_a(ap, row)
    print('', file=buf)

    print('### Carrier (b) — field name rewrite (`primaryId` -> `oid`)', file=buf)
    print('', file=buf)
    print('| approach | convention | v1 lines | v2 lines | note |',
          file=buf)
    print('|---|---|---|---|---|', file=buf)

    def render_forward_b(label, row):
        if not row or 'error' in row:
            err = row.get('error', '—') if row else '—'
            print(f'| {label} | ERROR | — | — | `{err[:60]}` |', file=buf)
            return
        conv = row.get('convention', '—')
        sl = row.get('src_lines', '—')
        dl = row.get('dst_lines', '—')
        note = (row.get('note') or '').replace('|', '\\|')
        print(f'| {label} | `{conv}` | {sl} | {dl} | {note} |', file=buf)

    for ap in APPROACHES:
        row = (results.get(ap, {}).get('forward_b', {}) or {}).get('result', {}) or {}
        if ap == 'D':
            render_forward_b('D (id half)', row)
            lab = (results.get('D', {}).get('forward_b_label', {})
                   or {}).get('result', {}) or {}
            render_forward_b('D (label half)', lab)
        else:
            render_forward_b(ap, row)
    print('', file=buf)

    print('### Carrier (c) — approach rewrite (storage-primitive transitions)',
          file=buf)
    print('', file=buf)
    print('| pair | src lines | dst lines | preserved (sample) | dropped (sample) |',
          file=buf)
    print('|---|---|---|---|---|', file=buf)
    for label, entry in forward_c.items():
        sa = (entry.get('src_author') or {}).get('result') or {}
        dr = (entry.get('dst_rewrite') or {}).get('result') or {}
        if 'error' in sa:
            print(f'| {label} | SRC ERROR | — | — | `{sa["error"][:50]}` |',
                  file=buf)
            continue
        if 'error' in dr:
            print(f'| {label} | {sa.get("src_lines", "—")} | DST ERROR | — | `{dr["error"][:50]}` |',
                  file=buf)
            continue
        sl = sa.get('src_lines', '—')
        dl = dr.get('dst_lines', '—')
        pres = dr.get('preserved') or []
        drop = dr.get('dropped') or []
        pres_summary = f'{len(pres)} prim(s) value-preserved' if pres else 'none'
        drop_summary = (', '.join(sorted(set(d['dropped_key'] for d in drop)))
                        if drop else 'none')
        print(f'| {label} | {sl} | {dl} | {pres_summary} | {drop_summary} |',
              file=buf)
    print('', file=buf)

    # ------------------------------------------------------------------
    # Scenario 2 — coexistence
    # ------------------------------------------------------------------
    print('## Scenario 2 — coexistence', file=buf)
    print('', file=buf)
    print('Author both old + new forms on one stage (different prims for', file=buf)
    print("(a); same prim's vendor dict / same prim's schema for (b)).", file=buf)
    print('Observe whether both resolve under a single read pass and', file=buf)
    print("whether tooling can enumerate both without prior knowledge of", file=buf)
    print('the specific token names.', file=buf)
    print('', file=buf)

    print('Carrier (b) for B and B\' authors the renamed field as a',
          file=buf)
    print('custom attribute on the prim — present in the layer but not',
          file=buf)
    print('in the schema-declared property table; A/C/D author the',
          file=buf)
    print('renamed field as a dict key.', file=buf)
    print('', file=buf)
    print('### Carrier (a) — both vendor names on one stage', file=buf)
    print('', file=buf)
    print('| approach | both resolve under one read pass | enumerable w/o prior vendor knowledge | all vendors visible |',
          file=buf)
    print('|---|---|---|---|', file=buf)

    def render_coexist_a(label, row):
        if not row or 'error' in row:
            err = row.get('error', '—') if row else '—'
            print(f'| {label} | ERROR | — | `{err[:60]}` |', file=buf)
            return
        br = 'yes' if row.get('both_resolve_under_one_read_pass') else 'no'
        en = 'yes' if row.get('enumerable_without_prior_vendor_knowledge') else 'no'
        av = ', '.join(row.get('all_vendors_visible', []))
        print(f'| {label} | {br} | {en} | {av} |', file=buf)

    for ap in APPROACHES:
        row = (results.get(ap, {}).get('coexist_a', {}) or {}).get('result', {}) or {}
        if ap == 'D':
            render_coexist_a('D (id half)', row)
            lab = (results.get('D', {}).get('coexist_a_label', {})
                   or {}).get('result', {}) or {}
            render_coexist_a('D (label half)', lab)
        else:
            render_coexist_a(ap, row)
    print('', file=buf)

    print('### Carrier (b) — both field names on one prim', file=buf)
    print('', file=buf)
    print('| approach | both resolve under one read pass | enumerable w/o prior field knowledge | note |',
          file=buf)
    print('|---|---|---|---|', file=buf)

    def render_coexist_b(label, row):
        if not row or 'error' in row:
            err = row.get('error', '—') if row else '—'
            print(f'| {label} | ERROR | — | `{err[:60]}` |', file=buf)
            return
        br = 'yes' if row.get('both_resolve_under_one_read_pass') else 'no'
        en = 'yes' if row.get('enumerable_without_prior_field_knowledge') else 'no'
        note = (row.get('note') or '').replace('|', '\\|')
        print(f'| {label} | {br} | {en} | {note} |', file=buf)

    for ap in APPROACHES:
        row = (results.get(ap, {}).get('coexist_b', {}) or {}).get('result', {}) or {}
        if ap == 'D':
            render_coexist_b('D (id half)', row)
            lab = (results.get('D', {}).get('coexist_b_label', {})
                   or {}).get('result', {}) or {}
            render_coexist_b('D (label half)', lab)
        else:
            render_coexist_b(ap, row)
    print('', file=buf)

    print('### Carrier (c) — both approaches\' layers on disk, read neutrally',
          file=buf)
    print('', file=buf)
    print('Note: each subprocess only has one approach\'s plugin loaded,',
          file=buf)
    print('so "two approaches on one stage" cannot be tested under a',
          file=buf)
    print('single Usd.Stage. Instead, src and dst each author their own',
          file=buf)
    print('layer file; a neutral reader (no schema-specific decoding)',
          file=buf)
    print('reads both layers and reports the schema tokens it finds.',
          file=buf)
    print('', file=buf)
    print('| pair | both layers readable | src tokens in layer | dst tokens in layer |',
          file=buf)
    print('|---|---|---|---|', file=buf)
    for label, entry in coexist_c.items():
        nr = (entry.get('neutral_read') or {}).get('result') or {}
        obs = nr.get('observations', [])
        if not obs or 'error' in nr:
            err = nr.get('error', 'no observations')
            print(f'| {label} | ERROR | — | `{err[:50]}` | |', file=buf)
            continue
        br = 'yes' if entry.get('both_layers_readable_without_plugin_load') else 'no'
        src_tokens = ', '.join(obs[0].get('applied_schema_tokens_in_layer', [])
                                if len(obs) > 0 else [])
        dst_tokens = ', '.join(obs[1].get('applied_schema_tokens_in_layer', [])
                                if len(obs) > 1 else [])
        print(f'| {label} | {br} | {src_tokens} | {dst_tokens} |', file=buf)
    print('', file=buf)

    # ------------------------------------------------------------------
    # Scenario 3 — round-trip (c only)
    # ------------------------------------------------------------------
    print('## Scenario 3 — round-trip (carrier c only)', file=buf)
    print('', file=buf)
    print('X -> Y -> X across three layers. Carrier (a) and (b) round-trip', file=buf)
    print('within one approach goes back to the same source schema on both', file=buf)
    print('ends, so this scenario only enumerates cross-approach (c) pairs.',
          file=buf)
    print('', file=buf)
    print('| pair (X -> Y -> X) | primaryId preserved | matches | diffs | extras lost at hop1 |',
          file=buf)
    print('|---|---|---|---|---|', file=buf)
    for label, entry in roundtrip_c.items():
        rp = entry.get('roundtrip_preserved') or {}
        if not rp.get('comparable'):
            reason = rp.get('reason', '—')
            print(f'| {label} | ERROR | — | `{reason}` | — |', file=buf)
            continue
        ok = 'yes' if rp.get('value_preserved_for_all_prims') else 'no'
        matches = rp.get('matches_count', 0)
        diffs = rp.get('diffs') or []
        if not diffs:
            diff_summary = 'none'
        else:
            diff_summary = '; '.join(
                f"{d['path']}: {d['before']!r}->{d['after']!r}" for d in diffs)
        extras_lost = rp.get('extras_lost_in_roundtrip') or []
        if not extras_lost:
            extras_summary = 'none'
        else:
            keys_lost = sorted({e['lost_key'] for e in extras_lost})
            extras_summary = ', '.join(keys_lost)
        print(f'| {label} | {ok} | {matches} | {diff_summary} | {extras_summary} |',
              file=buf)
    print('', file=buf)

    # ------------------------------------------------------------------
    # Criteria mapping
    # ------------------------------------------------------------------
    print('## Criteria mapping', file=buf)
    print('', file=buf)
    print('- **Carrier (a)** — vendor name within one approach — touches',
          file=buf)
    print('  **PR #105 Principle 3** (vendor extensibility; tiered',
          file=buf)
    print('  lifecycle vendor -> multi-vendor -> core). Vendor-name',
          file=buf)
    print('  evolution is the operation the tiered lifecycle names.',
          file=buf)
    print('- **Carrier (b)** — field name within one vendor — is not',
          file=buf)
    print('  directly named in PR #105\'s principles. The probe measures',
          file=buf)
    print('  the mechanism\'s response (where the renamed field lives,',
          file=buf)
    print('  whether it stays in UsdPrimDefinition) as data.',
          file=buf)
    print('- **Carrier (c)** — approach itself — is not named in PR #105.',
          file=buf)
    print('  It is an operational concern downstream of mechanism',
          file=buf)
    print('  plurality.', file=buf)
    print('', file=buf)

    # ------------------------------------------------------------------
    # Observations (descriptive only, no verdicts)
    # ------------------------------------------------------------------
    print('## Observations', file=buf)
    print('', file=buf)
    print('- For A, C, D identifier-half, both the vendor token (carrier a)', file=buf)
    print('  and the field name (carrier b) are dict keys; both rewrites',
          file=buf)
    print('  are layer-text operations (one site per prim).', file=buf)
    print('- For B, the vendor token is a multi-apply schema instance', file=buf)
    print('  name appearing in the apiSchemas list and as the middle',
          file=buf)
    print('  segment of each authored typed-property name. Carrier (a)',
          file=buf)
    print('  is a layer-text rewrite at two sites per prim in this probe',
          file=buf)
    print('  (apiSchemas entry + the authored `primaryId` property). The',
          file=buf)
    print('  site count scales by +1 per additional authored typed',
          file=buf)
    print('  property; B declares four (primaryId, revision, domain,',
          file=buf)
    print('  label). Carrier (b) authors the renamed field as a custom',
          file=buf)
    print('  attribute on the prim — carries the value, not present in',
          file=buf)
    print('  UsdPrimDefinition.', file=buf)
    print("- For B' (Bprime), the vendor token is the schema class name",
          file=buf)
    print("  itself, which lives in the schema definition and the",
          file=buf)
    print("  plugin's TfType registration. Carrier (a) requires declaring",
          file=buf)
    print('  and registering a new schema class before any prim can',
          file=buf)
    print('  reference it. Carrier (b) lands the renamed field as a',
          file=buf)
    print('  custom attribute on the prim (same shape as B\'s carrier b).',
          file=buf)
    print('- D label-half: carrier (a) is a layer-text rewrite at two',
          file=buf)
    print('  sites per prim (apiSchemas entry + property name segment).',
          file=buf)
    print('  Because the SemanticLabelsAPI template is multi-apply over',
          file=buf)
    print('  `__INSTANCE_NAME__`, the site count does not scale with the',
          file=buf)
    print('  number of authored kinds the same way B\'s scales with the',
          file=buf)
    print('  number of authored typed properties — the template is one',
          file=buf)
    print('  property regardless of how many kind instances apply.',
          file=buf)
    print('  Carrier (b) renames the kind segment; the new instance',
          file=buf)
    print('  still matches the multi-apply template, so it appears in',
          file=buf)
    print('  UsdPrimDefinition (whereas B/B\' carrier (b) lands as a',
          file=buf)
    print('  custom attribute).', file=buf)
    print('- Cross-approach probes author A as the dict-storage source',
          file=buf)
    print('  with `primaryId` plus extra dict-keyed metadata (`extra`,',
          file=buf)
    print('  `pdmTag`). Destinations whose storage is typed-property',
          file=buf)
    print("  (B, B') drop the extra keys at the destination-rewrite",
          file=buf)
    print('  step; this surfaces in the `dropped` column of carrier (c)',
          file=buf)
    print('  forward and the `extras lost at hop1` column of round-trip.',
          file=buf)
    print('- The neutral-read coexistence row for carrier (c) reports', file=buf)
    print('  what raw layer text + snapshot files carry; it does not', file=buf)
    print('  require any specific approach\'s plugin to be loaded.', file=buf)
    print("- B' (Bprime) layer text carries the vendor identity inside",
          file=buf)
    print('  the schema class name itself (e.g. `WindchillSourceIdAPI`);',
          file=buf)
    print('  a separate vendor token does not appear as a string literal',
          file=buf)
    print('  in the layer. Other approaches surface the vendor token as',
          file=buf)
    print('  a literal string in the layer (dict key or multi-apply',
          file=buf)
    print('  instance suffix).', file=buf)
    print('- A and D both name their identifier-half schema',
          file=buf)
    print('  `SourceIdentifiersAPI`. Per the criteria file, D is a',
          file=buf)
    print('  proposal candidate beyond PR #105 (Matt Kuruc strawman); the',
          file=buf)
    print('  shared name is a design choice in that strawman, not a PR',
          file=buf)
    print('  #105 design. Neutral layer-text inspection does not',
          file=buf)
    print("  distinguish A's authoring from D's identifier-half authoring",
          file=buf)
    print('  on this surface alone.', file=buf)
    print('', file=buf)

    return buf.getvalue()


def main():
    # 1. forward + coexist for carriers (a) and (b) per approach
    fc_results = run_forward_coexist()
    # 2. forward + coexist + roundtrip for carrier (c)
    forward_c, roundtrip_c, coexist_c = run_cross_approach()

    full = {
        'per_approach': fc_results,
        'cross_approach_forward': forward_c,
        'cross_approach_roundtrip': roundtrip_c,
        'cross_approach_coexist': coexist_c,
    }
    write_report(DIM_DIR, full)
    (DIM_DIR / 'summary.md').write_text(
        render_summary(fc_results, forward_c, roundtrip_c, coexist_c),
        encoding='utf-8')
    print(f'Wrote {DIM_DIR / "report.json"}')
    print(f'Wrote {DIM_DIR / "summary.md"}')


if __name__ == '__main__':
    main()
