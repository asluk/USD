# Geospatial CRS Prototype — Running TLDR

_Living status doc. Updated as work proceeds. Maintained by claw1 (unattended runs)._
_Last updated: 2026-06-23 ~05:35 UTC._

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
| F.1 | `crs:binding` was a bare rel, not MaterialBindingAPI-like | ✅ | strength (`bindCRSAs` weaker/stronger) + purpose (`crs:binding:<purpose>`) implemented; `test_binding_semantics.py` S1–S4 |

### Binding semantics (F.1) detail
Now mirrors UsdShadeMaterialBindingAPI:
- **Purpose** in the relationship name: `crs:binding` (all-purpose) vs `crs:binding:<purpose>`.
  Purpose-specific wins for that purpose; falls back to all-purpose otherwise.
- **Strength** via `bindCRSAs` relationship metadata: `weakerThanDescendants` (default,
  nearest wins) or `strongerThanDescendants` (ancestor overrides nearer descendant).
  Registered as `SdfMetadata` in `schema/plugInfo.json` (injected by `regen-schema.sh`,
  mirroring how usdShade registers `bindMaterialAs`).
- Still TODO: collection-based binding (`crs:binding:collection:<name>`).

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
1. ~~MaterialBindingAPI strength/purpose parity~~ ✅ done (F.1); **collection-based binding**
   (`crs:binding:collection:<name>`) still open.
2. EPSG-vs-WKT precedence on mismatch (currently WKT authoritative, documented).
3. External-grid / datum-epoch / time-dependent CRS story.

## Changelog
- 2026-06-23 ~05:35 — F.1 binding strength+purpose parity implemented + tested
  (`test_binding_semantics.py` S1–S4); `bindCRSAs` SdfMetadata registered.
- 2026-06-23 ~05:10 — usdGenSchema bootstrapped; schema regenerated canonically (concrete
  CRS bug fixed); `regen-schema.sh` added; full suite re-verified green.
- 2026-06-23 ~05:00 — fixes #1/#2/#3 complete & verified (see `docs/review-fixes-summary.md`).
