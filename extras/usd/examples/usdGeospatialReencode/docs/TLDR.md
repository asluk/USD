# Geospatial CRS Prototype — Running TLDR

_Living status doc. Updated as work proceeds. Maintained by claw1 (unattended runs)._
_Last updated: 2026-06-23 ~06:10 UTC._

## One-paragraph status
Adversarial review (`docs/codex-review.md`) flagged 3 top weaknesses; **all 3 fixed and
verified with tests that have teeth**. The codeless schema is now generated **canonically
via `usdGenSchema`** (bootstrapped without a full USD build — see below), not hand-authored.
Full test suite green; both authoring paths byte-identical; compliance 0 errors. Everything
local on branch `aluk/geospatial-crs-prototype`; only progress/TLDR docs are pushed.

## usdGenSchema bootstrap (SOLVED)
The usd-core wheel ships `pxr/Usd/usdGenSchema.py` but not as a console script, and omits
the jinja2 codegen templates + base meta-schema. Bootstrap without a full build:
1. jinja2 is in `~/.local` → expose via `PYTHONPATH`.
2. Fetch codegen templates + `usd/schema.usda` base layer from OpenUSD `v26.05`
   (matches usd-core 26.5). The `@usd/schema.usda@` subLayer must resolve next to the
   schema source.
3. Run `python3 .../pxr/Usd/usdGenSchema.py schema.usda <out> -t <templates>`.
4. Substitute `@PLUG_INFO_*@` placeholders for standalone use (Root=`.`, ResourcePath=`resources`).

Reproducible: **`schema/regen-schema.sh`** (auto-fetches templates; `--check` for CI sync).
Lesson caught by canonical gen: a concrete typed schema needs `class Name "TypeName"`;
`class "Name"` silently produces an **abstract** schema. My hand-authored version had this bug.

## Fix status
| # | Weakness | Status | Evidence |
|---|----------|--------|----------|
| 1 | multi-CRS proof circular | ✅ | `multi_crs_example.py` negative control diverges 1,655 km; binding-ignoring resolver → FAIL |
| 2 | "coexists with Xformable" unimplemented | ✅ | `resolve_runtime.py` composes ancestor xforms; `test_ancestor_compose.py` T1/T2/T3 (7,482 km teeth) |
| 3 | schema fiction + axis-order | ✅ | canonical codeless schema, `custom=False` truthful, compliance 0 errors; `docs/axis-order.md`; `verify.py` check E (teeth) |
| F.1 | `crs:binding` was a bare rel, not MaterialBindingAPI-like | ✅ | strength (`bindCRSAs` weaker/stronger) + purpose (`crs:binding:<purpose>`) + collection (`crs:binding:collection:<name>`); `test_binding_semantics.py` S1–S7 |

### Binding semantics (F.1) detail
Now mirrors UsdShadeMaterialBindingAPI in full:
- **Purpose** in the relationship name: `crs:binding` (all-purpose) vs `crs:binding:<purpose>`.
  Purpose-specific wins for that purpose; falls back to all-purpose otherwise.
- **Strength** via `bindCRSAs` relationship metadata: `weakerThanDescendants` (default,
  nearest wins) or `strongerThanDescendants` (ancestor overrides nearer descendant).
  Registered as `SdfMetadata` in `schema/plugInfo.json` (injected by `regen-schema.sh`,
  mirroring how usdShade registers `bindMaterialAs`).
- **Collection-based** binding: `crs:binding:collection:<name>` (two targets: collection
  path + CRS prim). Resolves only for prims that are members of the bound `UsdCollectionAPI`;
  direct bindings beat collection bindings. Token-count grammar matches MaterialBindingAPI.
- Precedence (per prim): purpose direct > all-purpose direct > purpose collection >
  all-purpose collection; nearest-ancestor with strength override across the chain.

## How to run (self-contained; schema auto-registers via `src/_schema_setup.py`)
```
source <geo-usd>/.venv/bin/activate
cd extras/usd/examples/usdGeospatialReencode
python3 src/reencode_georef.py --stride 40 --out out/earth2_georef.usda
python3 src/verify.py out/earth2_georef.usda            # A–E ALL PASS
python3 src/multi_crs_example.py out/multi_crs.usda     # non-circular PASS
python3 src/test_ancestor_compose.py                    # ancestor compose PASS
python3 src/resolve_runtime.py --in out/earth2_georef.usda
bash schema/regen-schema.sh --check                     # schema resources in sync
```

## Open / next (Aaron decides)
1. ~~MaterialBindingAPI strength/purpose/collection parity~~ ✅ done (F.1, S1–S7).
2. ~~EPSG-vs-WKT precedence on mismatch~~ ✅ done (F.5): WKT authoritative, `crs:epsg` a
   hint; `docs/crs-identity-precedence.md` + `verify.py` check F (teeth: mismatch → FAIL).
3. External-grid / datum-epoch / time-dependent CRS story (still open).
4. Possible: ship a real `usdchecker` UsdValidation validator plugin for crs:* prims.

## verify.py checks
A neutrality · B binding/WKT · C geodesy landmarks · D round-trip · E axis-order (authored
WKT, teeth) · F EPSG-vs-WKT precedence (teeth).

## Changelog
- 2026-06-23 ~06:10 — F.5 EPSG-vs-WKT precedence: WKT authoritative; `verify.py` check F
  flags any `crs:epsg` disagreeing with `crs:wkt` (teeth verified). `docs/crs-identity-precedence.md`.
- 2026-06-23 ~05:55 — collection-based binding (S5–S7); full MaterialBindingAPI parity.
- 2026-06-23 ~05:35 — F.1 binding strength+purpose parity (S1–S4).
- 2026-06-23 ~05:10 — usdGenSchema bootstrapped; canonical schema; `regen-schema.sh`.
- 2026-06-23 ~05:00 — fixes #1/#2/#3 complete & verified.
