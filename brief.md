# Brief for the usdGeospatial implementation

**This file is the prompt.** It is the only thing the implementing agent sees.

**The proposal says what to build. This file says what to hand back.** Every rule
about behavior is in the proposal, including the ones it took work to settle, and
nothing here repeats them — where this file looks like it is specifying behavior,
the proposal wins and the disagreement is a bug in this file. What this file owns
is the exercise: the deliverables, the standard the results are held to, the
scenes and datasets to run, and what not to look at.

What it withholds is **implementations**. Seeing how someone else built this tells
you how to build it, and the point of the exercise is an implementation derived
from the specification alone.

The scenes and datasets are the ones an existing implementation is measured on, so
running the same cases makes the two comparable. Set your own tolerances and design
your own checks — those are yours, and where you choose differently we learn
something.

---

## What to build

`usdGeospatial` — a codeless OpenUSD schema for coordinate reference systems, plus
**two independent runtimes** that resolve it, implementing the behavior the
proposal describes.

1. **A runtime outside any renderer.**
2. **A Hydra scene index**, driving resolution through Hydra's own scene-graph and
   invalidation machinery. Not a render delegate calling the first runtime's
   resolver: sharing a geodesy engine is expected, sharing the resolution path is
   not.

Build the first one first, and get the specification-gap list out of it before
starting the second. If you run out of room, that list is what must survive.

Record what the two architectures forced apart — when resolution happens, what is
cached, what invalidates. Where they disagree, report it; the authority for which
one is wrong is below.

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

**A real third-party dataset.** The Deutsche Bahn railway near Hamburg, around
10.2098, 53.4916, Apache-2.0. **It sits beside this brief, in `railway/`** — use
that copy, and do not go looking for where it came from.

What is there is the source data and nothing else. `1kmE4334N3375.geojson` holds
1,473 features — 186 `LineString`, 1,231 `Polygon`, 56 `MultiPolygon` — in
EPSG:4326, longitude-first, each carrying an `object_id`. Three imagery tiles sit
beside it as `quadnode-0.png`, `quadnode-1.png` and `quadnode-4.png`, and their
placements are below. **Author the USD yourself**, as you do for every other scene
on this page.

| Tile | Image | South-west corner, lon/lat/height |
|---|---|---|
| 0 | `quadnode-0.png` | 10.17333984375, 53.470458984375, 49.48313242683307 |
| 1 | `quadnode-1.png` | 10.17333984375, 53.4814453125, 49.48313242683307 |
| 4 | `quadnode-4.png` | 10.1953125, 53.4814453125, 49.48313242683307 |

Each tile is a quad on local east/north axes in metres, corners
`(0, 0)`, `(0, 1222.950439453125)`, `(1458.72119140625, 1222.950439453125)`,
`(1458.72119140625, 0)`, all at height offset −0.283719003200531, with texture
coordinates running `(0,0) (0,1) (1,1) (1,0)` over those corners in that order.
These are quadtree tiles, so the corners are exact tile boundaries rather than
measurements.

It is real-world data, published before the proposal existed, by people solving a
different problem. Nothing about it was shaped to suit what you are building.

**This is where scale and messiness live.** The synthetic scenes above are a
handful of points each. This is a thousand features of surveyed geometry whose
vertices are small local offsets from their own anchors, which exercises the
anchor frame, the offsets, and their composition together rather than testing
anchor placement and assuming the rest.

It is also a **co-registration** case. The rail curves and the imagery tiles
beneath them are separately georeferenced things that have to come out in the same
place. Rails floating off their tiles, or landing on top of each other, is visible
at a glance. They should be separated by something on the order of a tile
footprint — never coincident, never wildly apart.

**Check against the GeoJSON, not against your own USD.** You author the scene, so
comparing it to itself can be satisfied from either end. The GeoJSON holds a
geodetic coordinate for every vertex, which the USD will not. Resolve a vertex,
compute where its GeoJSON coordinate actually is by closed-form geodesy, and
compare.

`railway/README.md` records provenance and how the features map to the imagery.

**Go further than this list.** These are the cases one implementation happens to
cover, not a definition of enough. Look for more data, and deliberately look for
cases that would break what you have built — antimeridian crossings, polar
regions, compound and vertical CRSs, datums with an epoch, anything where a
projection is badly behaved. Finding a case these scenes miss is a more useful
result than passing all of them.

## What to deliver

1. **The schema and both runtimes**, as set out above.
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
4. **Figures, one per claim.** Every claim that can be seen rather than read gets
   a figure generated by the code. At minimum: the co-registration case, the
   misconfigured cases against their corrected versions, the multi-CRS scene, and
   the float32-versus-double comparison — the precision argument is currently a
   number in a table and it is a picture.

   **Where a claim is about the resolved result, produce the figure from both
   implementations, on the same points.** Two architectures landing the same
   geometry in the same place is the strongest thing this exercise can show, and
   two of them drifting apart on real data is a failure mode small synthetic
   scenes do not catch. Where a claim is about one architecture — what it caches,
   when it invalidates — say which one it is about.

   **A figure is generated from the data it is captioned with, or it is not a
   figure.** No diagrams. An illustration of an architecture proves nothing and
   must not be presented where a measurement belongs. The number in a caption is
   the number computed from that figure's own inputs — not a better number from a
   different scene.

   **A figure whose inputs are missing fails the run.** It does not skip, warn, or
   quietly leave the previous version in place. The figures most likely to be
   unavailable are the ones that need both implementations built, which makes them
   the ones that must never silently not happen.
5. **A README that carries the story.** What this is, what it proves, how to run
   it. Do not re-argue the design — the proposal owns that, cite it. Cover design
   in one circumstance only: where the proposal left a gap you had to fill to run.
   Name the gap, say what you chose, mark it as owed back to the proposal. No
   marketing register.
6. **A deck that is the figures.** One claim per slide. The figure is the slide;
   a title and at most one sentence sit under it. If a slide has no figure, it has
   no reason to exist, with the single exception of the gap list.

   **Do not project the README into slides.** A deck generated from prose is
   prose, and it is read rather than seen. Generate it from the same measurements
   the figures come from, so a wrong number cannot survive in one and not the
   other.
7. **A PR body that is a guided tour of the code.** Minimal. One entry point, three
   or four stops each with a line on why it exists, the two or three places the
   code takes a position, which test backs which claim, and what is deferred. Not a
   file list, not a tour of everything, not a restatement of the README.

## One sealed exercise, after the build is done

`railway/sealed/` holds the same Deutsche Bahn data authored in an **earlier,
different** geospatial schema, by the people who published it.

**Do not open it until everything above is finished and your own design is
frozen.** Opened early it will steer you, because it is one organisation's answer
to the same modelling problem and you would read it as a hint. Opened late it
cannot.

Then convert it into your schema and report: what carried over cleanly, what had
no equivalent in either direction, and what you would have done differently had
you seen it first. Whether this schema can carry a model somebody else designed is
a question about the specification, and it is the one question this exercise
cannot ask any other way.

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
- Python and C++ are both acceptable, and the two runtimes need not use the
  same language. Say what you chose for each and why.
- **Work in `asluk/OpenUSD`, on a new branch off `dev`.** Clone it with
  `--single-branch --branch dev`, which fetches only that branch, so the others are
  not in your repository at all. `dev` contains no geospatial code.

  That fork also holds an earlier implementation of this schema, on another branch.
  **Do not fetch, list, check out or read any branch other than `dev` and your
  own.** The single-branch clone means reaching it takes a deliberate act; do not
  take it. This is the one place the setup relies on you rather than on the
  mechanics, and the whole exercise rests on it.

## Definition of done

The schema and both runtimes exist and agree on the same points, the tests pass
against closed-form geodesy at a tolerance you have stated, the misconfigured
cases fail by the distances you report, the worked example and the figures are
generated, the sealed exercise is done and reported, and the README, deck and
review guide are written.

Plus one list: **everywhere the specification did not tell you what to do.** That
list is a deliverable, not an appendix.
