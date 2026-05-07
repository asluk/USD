#!/usr/bin/env python3
"""
Principle-Derived Scoring for Source Identifier Approaches A, B, C, and D.

Scoring dimensions are derived from the eight authorized design
principles in proposal 105
(PixarAnimationStudios/OpenUSD-proposals#105 Principles section)
plus the explicit risks (uncurated proliferation, premature
standardization, adoption fragmentation, scope creep).

Earlier scoring (preserved as `vendor_adoption_analysis_legacy.py`)
used eight dimensions that Claude invented across the comparison
work — initially on the `aluk/source-identifiers-comparison` base
branch (April 2026 A/B/C) and subsequently augmented for D on
`aluk/source-identifiers-rev2`. Those dimensions did not derive from
proposal 105's authorized principles, and the D-augmented version
biased toward D along axes D happens to lead on by construction.
This re-derivation replaces the entire ad-hoc lineage in favor of
dimensions drawn from the proposal's authorized framing. The header
of `vendor_adoption_analysis_legacy.py` documents the regression in
detail.

Aaron's 2026-05-07 call on the distribution-friction tension: scored
as conditional — currently heavy because schema-distribution depends
on the substrate the AOUSD Build Interest Group is actively scoping
(aousd/build-ig-initiatives#28 hosted-binaries epic, plugin
registration via importlib, conda-forge / PyPI distribution),
trending lighter as those initiatives land. The trajectory is noted
in the methodology and in the score for Minimal disruption.

Per-dimension scores are 1–5 against published anchors; totals are
reported but the anchors and per-mechanism justifications are the
primary reading. The numerical totals are illustrative of how the
mechanisms trade off across the principles, not a verdict.
"""

import json
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


DIMENSIONS = [
    {
        "principle": "Separation of concerns",
        "principle_id": 1,
        "question": (
            "Does the mechanism keep identifier metadata distinct "
            "from USD path semantics, and within the identifier "
            "package does it cleanly separate the content types real "
            "source systems bundle (identity strings, controlled-"
            "vocabulary classification facets, heterogeneous typed "
            "fields)?"
        ),
        "anchors": {
            5: "Clean separation of all three content types into distinct slots; nothing overflows into a non-segregated container.",
            4: "Two of three content types separated; the third has a clean fallback within the same mechanism.",
            3: "Two-way separation; the third content type either has no slot or must overflow to a non-segregated container.",
            2: "One container holds everything, or the separation is misaligned with how source systems actually bundle.",
            1: "Identifier metadata bleeds into USD path semantics or other un-related machinery.",
        },
    },
    {
        "principle": "Industry agnosticism",
        "principle_id": 2,
        "question": (
            "Does the mechanism admit any industry's full identifier-"
            "package shape (identity + classification + heterogeneous "
            "typed fields, per the field census) without per-industry "
            "engineering?"
        ),
        "anchors": {
            5: "Admits any package shape across the four verticals surveyed; no per-industry engineering required.",
            4: "Admits the surface in three of four verticals; the fourth requires modest accommodation.",
            3: "Admits identity + one of the other two content types; the missing one has to be carried by an unrelated mechanism.",
            2: "Admits a fixed common subset; per-industry engineering required to carry anything else.",
            1: "Industry-specific.",
        },
    },
    {
        "principle": "Vendor extensibility",
        "principle_id": 3,
        "question": (
            "Can a vendor, standards body, or consortium declare its "
            "own identifier scheme without central approval before "
            "deployment? Does the mechanism support a tiered "
            "lifecycle (vendor → multi-vendor → core) without "
            "requiring re-authoring at each stage?"
        ),
        "anchors": {
            5: "Ship today, no approval. Tiered lifecycle is registry-level (a spec document) rather than a re-authoring pass.",
            4: "Ship today, no approval, but promotion to a multi-vendor or core tier requires re-authoring.",
            3: "Ship today via a fallback path; the canonical path requires central approval.",
            2: "Central approval (schema ratification, plugin distribution) required to ship at all.",
            1: "Single-vendor lock-in.",
        },
    },
    {
        "principle": "Composability",
        "principle_id": 4,
        "question": (
            "Does the mechanism participate in USD's composition "
            "model with the granularity authors expect — overrides "
            "of single fields without disturbing siblings?"
        ),
        "anchors": {
            5: "Per-field composition with no shadowing or naive-tool hazards.",
            4: "Effectively equivalent to per-field for non-timevarying strings, which is the regime identifier metadata lives in (per the composition_test experiments).",
            3: "Per-field for some content types; element-wise dictionary semantics for others.",
            2: "Element-wise only, with shadowing hazards for tools that rewrite whole containers.",
            1: "Composition is unpredictable or undefined.",
        },
    },
    {
        "principle": "Discoverability",
        "principle_id": 5,
        "question": (
            "Can tools discover that a prim carries source "
            "identifiers and at what granularity, without parsing "
            "metadata dictionaries or having prior knowledge of a "
            "pipeline-specific convention?"
        ),
        "anchors": {
            5: "Per-facet discovery from `apiSchemas` alone — consumer can answer `which facets of which systems are present?` without parsing.",
            4: "Per-system discovery from `apiSchemas`; per-facet requires a parse.",
            3: "Discovery is possible from `apiSchemas` for some content types and parse-based for others.",
            2: "Discovery requires parsing metadata dictionaries; no schema surface exposes presence.",
            1: "Discovery requires prior knowledge of pipeline-specific conventions.",
        },
    },
    {
        "principle": "External queryability",
        "principle_id": 6,
        "question": (
            "Does the mechanism support tractable external indexes "
            "for `given external identifier, find prim` queries "
            "without forcing full-stage scans?"
        ),
        "anchors": {
            5: "Schema-targeted validators + per-facet structure enables narrow validator targeting; external index construction is straightforward.",
            4: "Schema-targeted validators (`plugInfo.json schemaTypes`) work; index construction requires schema-aware traversal.",
            3: "Stage traversal with parse-based dictionary inspection; tractable but requires walking every prim.",
            2: "Stage traversal plus per-prim convention checks; index construction is per-domain.",
            1: "External indexes are intractable without out-of-band metadata.",
        },
    },
    {
        "principle": "Round-trip fidelity",
        "principle_id": 7,
        "question": (
            "Do source identifier strings (including characters not "
            "valid in USD prim names) survive a round-trip through "
            "USD without loss?"
        ),
        "anchors": {
            5: "Identifier strings are stored verbatim as UTF-8 strings; any character set survives.",
            4: "Identifier strings survive but require an explicit container choice (e.g. `assetInfo` vs property).",
            3: "Most characters survive; some require transcoding.",
            2: "Identifier strings undergo transformation that has to be inverted on read.",
            1: "Identifiers can be lost or silently corrupted on round-trip.",
        },
    },
    {
        "principle": "Minimal disruption",
        "principle_id": 8,
        "question": (
            "Does the mechanism build on USD's existing strengths "
            "without new core surface, schema ratification, or "
            "plugin-architecture changes? Schema-distribution cost is "
            "scored conditionally per Aaron's 2026-05-07 call — "
            "currently elevated as the AOUSD Build IG epic is "
            "scoping the substrate, trending lighter as those "
            "initiatives land."
        ),
        "anchors": {
            5: "No new core surface, no schema ratification, no plugin distribution. Pure convention on existing USD machinery.",
            4: "Reuses an existing core schema in an extended use case; no new plugin distribution but the reuse stretches the original schema's intent.",
            3: "New core surface or new ratified schema, but distribution piggybacks on existing OpenUSD-core distribution.",
            2: "New ratified schema requiring full plugin-distribution matrix (DCC × USD release × Python × OS × runtime × build flavor) — currently elevated; trajectory expected to lighten as the AOUSD Build IG epic lands.",
            1: "New ratified schema plus composition-engine or USD-core changes.",
        },
    },
]


def score_a():
    """Approach A: assetInfo dictionaries (status quo, refined)."""
    return {
        "name": "A — assetInfo dictionaries",
        "scores": {
            "Separation of concerns": (3, "One assetInfo dict container holds identity + classification + any heterogeneous typed fields together; no slot-level separation by content type."),
            "Industry agnosticism": (5, "Freeform dicts admit any package shape without per-industry engineering."),
            "Vendor extensibility": (5, "Vendor adds a sub-dict key today; no central approval. Tiered lifecycle is convention promotion in the AOUSD Domains Registry — a spec document, not a re-author."),
            "Composability": (4, "Element-wise dict composition; effectively equivalent to per-field for non-timevarying strings (per composition_test experiments). Tools that rewrite the whole dict can shadow base-layer keys."),
            "Discoverability": (2, "No `apiSchemas` instance announces presence; consumers must parse `assetInfo` for the `sourceIds` key."),
            "External queryability": (3, "Stage traversal with dict inspection at each prim; tractable but parse-based."),
            "Round-trip fidelity": (5, "Identifier strings stored verbatim; any UTF-8 survives."),
            "Minimal disruption": (5, "No new core surface; no schema ratification; no plugin distribution. Convenience API is optional and follows the `UsdModelAPI` precedent."),
        },
    }


def score_b():
    """Approach B: multi-apply schema with four typed properties."""
    return {
        "name": "B — Multi-apply schema (typed common fields)",
        "scores": {
            "Separation of concerns": (3, "Typed properties separate identity-flavored fields from USD path, but classification and heterogeneous typed metadata have no slot — they default to companion schemas or `customData`, which is a non-segregated container."),
            "Industry agnosticism": (2, "Fixed four-property surface (`primaryId`, `revision`, `domain`, `label`) admits a common subset only; everything outside requires per-industry companion schemas."),
            "Vendor extensibility": (2, "Schema ratification + plugin distribution are required for a vendor's domain-specific fields; the `domain` token can be added today, but the carrying schema cannot ship without a ratification path."),
            "Composability": (4, "Per-property composition is the cleanest available mechanism; effectively equivalent to A/C/D for non-timevarying strings."),
            "Discoverability": (4, "`apiSchemas` surfaces per-system instances (`SourceIdSchemaAPI:windchill`); per-facet structure is not exposed because there are no per-facet typed properties."),
            "External queryability": (4, "Schema-targeted validators work via `plugInfo.json schemaTypes`. Index construction is straightforward for the four common fields."),
            "Round-trip fidelity": (5, "Schema property values are strings; any UTF-8 survives."),
            "Minimal disruption": (2, "New ratified schema + plugin distribution across the AOUSD Build IG matrix. Currently elevated; trajectory expected to lighten as the IG epic lands."),
        },
    }


def score_c():
    """Approach C: refinement of B (B + assetInfo overflow)."""
    return {
        "name": "C — Refinement of B (B + assetInfo overflow)",
        "scores": {
            "Separation of concerns": (4, "Typed properties for the four common fields + freeform dict overflow for everything else. Two-way separation; the heterogeneous typed surface is admitted via overflow rather than a typed slot, but no content type bleeds into a non-segregated container."),
            "Industry agnosticism": (5, "Overflow tier admits any package shape, including the heterogeneous typed surface AAS / IFC / SAP / URDF / ShotGrid bundle."),
            "Vendor extensibility": (4, "Overflow tier is zero-coordination ship-today; promotion of a stable field to a typed schema property requires central approval (schema versioning bump + redistribution)."),
            "Composability": (4, "Per-property composition for typed fields + element-wise dict for overflow; effectively equivalent to A/B/D for non-timevarying strings."),
            "Discoverability": (4, "`apiSchemas` surfaces per-system instances; overflow contents require a parse."),
            "External queryability": (4, "Schema-targeted validators + parse for overflow; same shape as B/D for the typed tier."),
            "Round-trip fidelity": (5, "Schema property + dict values are strings; any UTF-8 survives."),
            "Minimal disruption": (2, "New ratified schema + plugin distribution across the AOUSD Build IG matrix, same as B; carries dict overflow on top. Currently elevated; trajectory expected to lighten as the IG epic lands."),
        },
    }


def score_d():
    """Approach D: refinement of B (UsdSemanticsLabelsAPI + assetInfo identity)."""
    return {
        "name": "D — Refinement of B (Labels + Identity, no new schema)",
        "scores": {
            "Separation of concerns": (3, "Identity strings in `assetInfo` + classification facets in `SemanticsLabelsAPI` token arrays = clean two-way separation. The third content type (heterogeneous typed fields) has no slot; in practice it overflows to `assetInfo` or `customData`, which mixes content types."),
            "Industry agnosticism": (3, "Carries identity + classification cleanly across all four verticals; misses the heterogeneous typed surface (timestamps, numeric measures with units, composite typed references, polymorphic AAS Property values) that surfaces in every vertical surveyed."),
            "Vendor extensibility": (5, "Vendor applies `SemanticsLabelsAPI:<system>:<facet>` today; no central approval. Tiered lifecycle is registry-level facet addition — a spec document."),
            "Composability": (4, "Per-property composition for label token arrays + element-wise dict for `assetInfo` identity; effectively equivalent to A/B/C for non-timevarying strings."),
            "Discoverability": (5, "`apiSchemas` surfaces per-facet instances (`SemanticsLabelsAPI:revit:familyType`, `SemanticsLabelsAPI:revit:mark`); consumers can answer `which facets of which systems are present` from the apiSchemas list directly."),
            "External queryability": (4, "Schema-targeted validators + per-facet structure enables narrow validator targeting; index construction over labels is straightforward."),
            "Round-trip fidelity": (5, "Identifier strings in `assetInfo` + label token arrays both UTF-8; any character set survives."),
            "Minimal disruption": (4, "Reuses `UsdSemanticsLabelsAPI` (already in OpenUSD 24.11+); no new schema ratification, no new plugin distribution. The reuse extends `SemanticsLabelsAPI` beyond its original semantic-labels intent, which is a stretch worth flagging but does not commit the AOUSD Build IG matrix."),
        },
    }


def main():
    approaches = [score_a(), score_b(), score_c(), score_d()]
    output = {
        "methodology": {
            "framing": (
                "Scoring dimensions derived from the eight authorized "
                "design principles in proposal 105. Earlier scoring "
                "constructed eight ad-hoc dimensions after a leaning "
                "toward Approach D had taken shape; that scoring is "
                "preserved in `vendor_adoption_analysis_legacy.py` and "
                "is retracted."
            ),
            "scoring_anchors": "Per-dimension 1-5 anchors are published in DIMENSIONS below; per-mechanism justifications cite evidence from the field census and stress tests.",
            "distribution_friction_call": (
                "Aaron's 2026-05-07 call on schema-distribution cost: "
                "currently elevated as the AOUSD Build IG epic is "
                "scoping the substrate (hosted binaries, plugin "
                "registration, conda-forge/PyPI), trending lighter as "
                "those initiatives land. Reflected in Minimal "
                "disruption scoring for B and C."
            ),
            "what_the_totals_mean": (
                "Numerical totals are illustrative of how the "
                "mechanisms trade off across principles, not a "
                "verdict. The anchors and per-mechanism "
                "justifications are the primary reading."
            ),
        },
        "dimensions": DIMENSIONS,
        "approaches": approaches,
    }

    # Compute totals
    for approach in output["approaches"]:
        approach["total"] = sum(score for score, _ in approach["scores"].values())

    out_path = os.path.join(OUTPUT_DIR, "vendor_adoption_analysis.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print a compact table
    dim_names = [d["principle"] for d in DIMENSIONS]
    print("Principle-derived scoring (max 40):")
    print()
    header = f"{'Dimension':<32}" + "".join(f"  {name:<3}" for name in ["A", "B", "C", "D"])
    print(header)
    print("-" * len(header))
    for dim in dim_names:
        row = f"{dim:<32}"
        for approach in output["approaches"]:
            row += f"  {approach['scores'][dim][0]:<3}"
        print(row)
    print("-" * len(header))
    totals = f"{'Total':<32}"
    for approach in output["approaches"]:
        totals += f"  {approach['total']:<3}"
    print(totals)
    print()
    print(f"Output: {out_path}")
    print()
    print("Note: numerical totals are illustrative. Per-dimension")
    print("anchors and per-mechanism justifications are the primary")
    print("reading; see the JSON output for both.")


if __name__ == "__main__":
    main()
