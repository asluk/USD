# Brief for the usdGeospatial implementation

**This file is the prompt.** It is the only thing the implementing agent sees.

What it withholds is **implementations**. Seeing how someone else built this tells
you how to build it, and the point of the exercise is an implementation derived
from the specification alone.

What it gives you is everything else: what correct means, and the scenes and
datasets an existing implementation is measured on. Running the same cases is
what makes the two comparable. Set your own tolerances and design your own checks
— those are yours, and where you choose differently we learn something.

---

## What to build

`usdGeospatial` — a codeless OpenUSD schema for coordinate reference systems, plus
a runtime that resolves it, implementing the behavior described in the proposal
below.

## The specification

The proposal is the only specification. Read all of it, and `Runtime behavior`
inside `Runtime coordinate transformation` most closely — that section states what
any implementation has to produce, deliberately without assuming an evaluation
architecture.

Source: `asluk/OpenUSD-proposals`, branch `geospatial-runtime-description`, file
`proposals/geospatial_coordinate_reference_systems/README.md`.

Where the proposal is silent, it is silent on purpose or by oversight, and you
cannot tell which from inside. **Do not decide it quietly.** Implement what lets
you proceed, mark it, and report it as a question. A list of the places the
specification did not tell you what to do is one of the most valuable things this
build produces.

## What correct means

The proposal states the bar: **independent implementations should agree to within
1 mm at Earth-surface magnitudes**, and that figure is chosen rather than measured,
so treat it as the requirement it is. Everything below follows from being able to
demonstrate that.

**The authority is closed-form geodesy.** Correctness means agreeing with a
closed-form computation of where a point actually is, not with your own earlier
output and not with another runtime. Two implementations agreeing catches
divergence between them, not an error they share.

**Coverage has to span the space, not sample one corner of it.** A result that
holds for one coordinate system says nothing about the next. Test across several
CRS families and across latitudes, including the cases where projections behave
worst — near the equator, at high latitude, and in both hemispheres. Author the
same physical location twice, once in a geographic CRS and once projected, and
check that both resolve to the same place and that each matches closed-form. Cover
a national grid, not only UTM.

**Precision is part of correctness at this scale.** An Earth-surface position is
about 6.4 × 10⁶ m from the geocentre, where float32 spacing is roughly half a
metre. An implementation that carries absolute coordinates in single precision is
wrong by more than the bar before it does any geodesy. Show what your scheme costs
and what the naive one costs, as numbers.

**Being wrong loudly is part of it too.** For each way an asset can be authored
incorrectly, show that the broken version misplaces by a gross distance and the
corrected version lands within tolerance. A suite where everything passes
demonstrates nothing. The proposal's authoring-time invariants are the list to work
from.

Pick your own tolerances and say why each is fair.

## Scenes and datasets to test against

Use these, so results are comparable with an existing implementation. All values
are public; author the scenes yourself from the coordinates below rather than
importing anything.

**Single georeferenced points.** Each location authored twice — once in a
geographic CRS, once in the projected CRS named — then checked against closed-form
geodesy and against each other.

| Location | Projected CRS | lon, lat, height |
|---|---|---|
| NOAA benchmark, New York | UTM 18N, EPSG:32618 | −73.985656, 40.748817, 0 |
| Sydney, southern hemisphere | UTM 56S, EPSG:32756 | 151.214, −33.857, 58 |
| Wellington, national grid | NZTM2000, EPSG:2193 | 174.7762, −41.2865, 5 |
| Quito, equatorial | UTM 17S, EPSG:32717 | −78.4678, −0.1807, 2850 |
| Svalbard, high latitude | UTM 33N, EPSG:32633 | 15.65, 78.22, 10 |

**A multi-CRS scene**, which is where the composition rules bite. Two anchors in
different projected CRSs, a Cartesian subtree under one of them, and a probe point
on a mesh whose vertices are small local offsets:

- World anchor — WGS 84 / UTM 30N, EPSG:32630, position `(708276.91981815, 5706731.7076084, 50)`
- New York anchor — NAD83 / UTM 17N, EPSG:26917, position `(586000, 4515000, 50)`
- A child under the New York anchor at plain Cartesian `(-393.7, -337.3, 0)`
- On that child, a mesh whose far corner vertex is at `(50, 100, 30)`, Z-up

**A real third-party asset, and the case that matters most.** The Deutsche Bahn
railway, Apache-2.0, 1,476 track curves on three geospatial tile ground planes near
Hamburg, around 10.2098, 53.4916. **The asset and its tile imagery sit
beside this brief, in `railway/`** — use that copy, and do not go looking for where
it came from. It is there twice: `deutschebahn-rails-usdgeospatial.usda`, already
converted into the schema you are implementing, and the original beside it in the
earlier schema. Use the converted one; `railway/README.md` records what the
conversion decided and why, which is worth reading because several of those
decisions are ones you would otherwise have to make yourself.

The original is authored latitude-first — its root reads
`(53.4915918, 10.2097897, 49.4831324)` — and the converted copy is swapped to
longitude-first. If you compare the two, that is why.

Treat this one as the headline rather than another row in a table. It is real
survey-derived data, published before the proposal existed and authored in an
earlier NVIDIA geospatial schema. So converting it into the schema you are
implementing is part of the exercise.

That is what makes it the strongest evidence against overfitting in this set:
the data was authored against a different schema by people solving a different
problem, so nothing about it was shaped to suit what you are building. Everything
else on this page can be made to work by building for it; this one cannot.

It is also a **co-registration** proof, which is what makes it convincing to
someone who does not want to read a table of millimetres. The rail curves and the
imagery tiles beneath them are separately georeferenced things that have to come
out in the same place. Rails floating off their tiles, or landing on top of each
other, is visible at a glance. They should be separated by something on the order
of a tile footprint — never coincident, never wildly apart.

**If your implementation has more than one path to a world transform** — say a
render-time path and a query or flatten path — this asset is where they have to be
shown to agree, on the same points, to the stated tolerance. Two paths in one
implementation drifting apart on real data is a failure mode that small synthetic
scenes do not catch.

**Go further than this list.** These are the cases one implementation happens to
cover, not a definition of enough. Look for more data, and deliberately look for
cases that would break what you have built — antimeridian crossings, polar
regions, compound and vertical CRSs, datums with an epoch, anything where a
projection is badly behaved. Finding a case these scenes miss is a more useful
result than passing all of them.

## What to deliver

1. **The schema and the runtime.** Codeless schema; a runtime that resolves it.
   An implementation that only works inside a renderer does not satisfy the
   description — the behavior is stated over the composed stage.
2. **Tests, against an independent authority.** Assert against closed-form geodesy,
   not against your own runtime's earlier output and not against a second runtime
   agreeing with the first. Two implementations agreeing catches divergence, not
   shared error. State the tolerance you hold yourself to and why.
   **Include deliberately misconfigured cases** — an asset authored the wrong way
   must be shown to land wrong, by a stated distance. A suite where everything
   passes demonstrates nothing.
3. **A worked example, generated by the code, not written by hand.** One prim in
   the target CRS, one in a different source CRS, walked through the steps with the
   actual numbers your implementation produces. It is for a reader with no
   geospatial background.
4. **A README that carries the story.** What this is, what it proves, how to run
   it. Do not re-argue the design — the proposal owns that, cite it. Cover design
   in one circumstance only: where the proposal left a gap you had to fill to run.
   Name the gap, say what you chose, mark it as owed back to the proposal. No
   marketing register.
5. **A deck derived from the README**, via invisible HTML-comment slide markers in
   the README that a script parses. The README stays the single source; the deck is
   a curated projection of it, never a separate document.
6. **A PR body that is a guided tour of the code.** Minimal. One entry point, three
   or four stops each with a line on why it exists, the two or three places the
   code takes a position, which test backs which claim, and what is deferred. Not a
   file list, not a tour of everything, not a restatement of the README.

## A precedent worth studying — shape, not substance

A comparable contribution already landed in OpenUSD and is in the tree you clone.
Gaussian splats arrived as `ParticleField` and a family of applied API schemas
under `pxr/usd/usdVol`, with per-schema user guides in
`docs/user_guides/schemas/usdVol/`, and a renderer-side example at
`extras/imaging/examples/hdParticleField`.

**Read it for shape.** Where an example runtime sits relative to the schema and how
it is packaged; what documentation shipped alongside; how much of the contribution
is example rather than core; how the whole thing is laid out in the tree. The
schema design itself is not the lesson — the proposal already specifies that. What
you are looking for is a worked answer to how a new representation gets into
OpenUSD in a form the maintainers accept.

**Do not read it for substance.** It solves a different problem, so nothing about
splat kernels or volume rendering transfers. If you find yourself borrowing logic
rather than layout, you have gone too far.

One honest tension to notice rather than paper over: that work extended an existing
schema library instead of creating a new one, and the proposal you are implementing
asks for a new library. If studying the precedent makes you think the proposal has
that wrong, say so in your findings. It may be right and it may not be, and you are
in an unusually good position to have an opinion.

## Constraints

- **Several implementations of this schema already exist publicly, from more than
  one organization. Do not read any of them and do not go looking.** The value of
  this exercise is an implementation derived from the specification alone, so that
  where it differs from the others we learn something about the specification. An
  implementation that has seen the others teaches us nothing.
- **The proposal lists them, in a table called `Prototype implementations`, with
  links.** That is unavoidable — it is part of the document you have to read. Read
  the table as context for who is involved, and **do not follow the links**. The
  same goes for any other repository the proposal references for an implementation.
  If you find yourself reading one of them, stop and say so in your report; that is
  a fact about the run, not a failure to hide.
- **Some of those repositories carry no license.** Nothing may be copied from any
  of them. Author your scenes from public WKT and coordinates, and say where each
  value came from.
- **Do not change the proposal.** If the implementation and the specification
  disagree, the specification wins for now and the disagreement is reported.
- Python and C++ are both acceptable. Say which you chose and why.
- **Work in `asluk/OpenUSD`, on a new branch off `dev`.** Clone it with
  `--single-branch --branch dev`, which fetches only that branch, so the others are
  not in your repository at all. `dev` contains no geospatial code.

  That fork also holds an earlier implementation of this schema, on another branch.
  **Do not fetch, list, check out or read any branch other than `dev` and your
  own.** The single-branch clone means reaching it takes a deliberate act; do not
  take it. This is the one place the setup relies on you rather than on the
  mechanics, and the whole exercise rests on it.

## Definition of done

The schema and runtime exist, the tests pass against closed-form geodesy at a
tolerance you have stated, the misconfigured cases fail by the distances you
report, the worked example is generated, and the README, deck and review guide are
written.

Plus one list: **everywhere the specification did not tell you what to do.** That
list is a deliverable, not an appendix.
