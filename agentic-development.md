# AI-Assisted Development in aarUSD

Technology has never been about devaluing human labor.  It is about placing
the highest value on human time -- and empowering everyone, through tools,
skills, and opportunity, to make the most of that time.

This brief describes how I use an AI coding agent when contributing to
OpenUSD.  The goal is not to produce code faster.  It is to spend more of my
time on what matters most for a standards codebase: correctness,
documentation quality, and the judgment calls that determine whether a
contribution helps or harms the ecosystem.

Every line that lands in a PR is my responsibility, as if I wrote it by hand.

---

## The Work

One sentence launched the project: "usdValidation is the current C++ based
validation framework; the previous one was Python based.  We no longer have
the ability to implement validations in Python.  Let's make that possible
again."

From that prompt, the agent autonomously:
- Read the C++ registration interface, existing bindings, and GIL-safety
  patterns used elsewhere in USD
- Designed four `RegisterXxxValidator` Python methods mirroring the C++ API
- Wrote `wrapRegistry.cpp` (three GIL-safe wrappers), a six-test Python test
  suite, and README documentation
- Built a proof-of-concept validator checking `metersPerUnit`/`upAxis`
  consistency across composition arcs

I did not specify function names, signatures, or which overloads to expose.
My role: goal-setting, acceptance testing, code review, and the domain
judgment calls described below.

### Iteration: Pixar review feedback

Pixar's review noted that `RegisterPluginValidator` bindings were missing.
This is the registration path where metadata comes from `plugInfo.json`
rather than being constructed at call time; it is how most shipped validators
are actually discovered and loaded.

The reviewer also suggested a notice handler for runtime dynamic
registration.  I scoped those as separate concerns: plugin bindings are
required for the PR; the notice handler is a registry-level feature that
belongs in a follow-up.

From that direction, the agent (Opus):
- Explored the full C++ `UsdValidationRegistry` API, identified the
  distinction between `RegisterValidator` (explicit metadata) and
  `RegisterPluginValidator` (name-only; metadata from `plugInfo.json`)
- Added four `RegisterPlugin*Validator` methods plus
  `RegisterPluginValidatorSuite` to the Python bindings
- Noted that `UsdValidationFixer` had no Python constructor (`no_init`), so
  deferred the optional fixers parameter to a follow-up (see below)
- Added four plugin registration tests, including metadata verification
  (confirming the doc string and keywords come from `plugInfo.json`, not
  from the caller)
- Updated the README with a decision guide: when to use explicit vs. plugin
  registration
- Built `testUsdValidationPyPlugin`, an end-to-end test plugin with
  `"Type": "python"` plugInfo.json and `__init__.py` registration,
  proving the full lazy-load chain works for Python validators
- Updated the README with a "How Python plugin validators are
  triggered" section covering the lazy-load flow, directory structure,
  and example `plugInfo.json` + `__init__.py`
- Converted the POC layer-stack validator from explicit registration
  to a proper Python-type plugin (`layerStackValidator/` package with
  its own `plugInfo.json` and `__init__.py` calling
  `RegisterPluginStageValidator`)

The end-to-end tests verified the full plugin lifecycle:
1. Metadata discoverable from `plugInfo.json` before any code loads
   (`GetValidatorMetadata` returned name, doc, keywords)
2. `GetOrLoadValidatorByName` triggers `plugin->Load()`, which does
   `import <module_name>`, running `__init__.py` registration code
3. The Python validator appears alongside C++ validators in keyword
   queries -- from the outside, indistinguishable from a C++
   implementation
4. Kitchen_set (230 layers): all agree on upAxis=Z, no conflicts
5. Deliberately mismatched stages correctly produce warnings

The progression from explicit to plugin registration on the POC
branch demonstrates both paths working and illustrates the
practical difference: explicit registration is simpler for scripts
and prototyping; plugin registration gives discoverability and lazy
loading for shipped validators.  The implementation language is an
invisible detail.

### How plugin registration is triggered

For C++ plugins, `TF_REGISTRY_FUNCTION(UsdValidationRegistry)` runs
automatically when the shared library is loaded.  For Python, the
equivalent is top-level code in the plugin module's `__init__.py`.

USD's Plug system already supports `"Type": "python"` plugins.  When
`plugin->Load()` is called for a Python plugin, it runs
`import <module_name>` via `TfPyRunSimpleString`.  All module-level
code executes at that point, including `RegisterPluginValidator`
calls.  This is the same mechanism used for `Tf.Type.Define()`, kind
registry extensions, and usdview plugins throughout USD.

The intended lazy-load flow for a Python validator plugin:

1. `plugInfo.json` declares `"Type": "python"`, `"Name":
   "myPyValidators"`, with validator metadata in `Info.Validators`
2. Registry parses metadata at startup; validators are discoverable
   by keyword and schema type before any code loads
3. Client calls `GetOrLoadValidatorByName("myPyValidators:CheckX")`
4. Registry sees `metadata.pluginPtr`; calls `pluginPtr->Load()`
5. Plug system does `import myPyValidators`
6. `myPyValidators/__init__.py` calls
   `registry.RegisterPluginStageValidator("myPyValidators:CheckX", fn)`
7. Validator is registered and returned to the caller

**This flow has been tested end-to-end.**  The PR branch includes
`testUsdValidationPyPlugin`, a test plugin with `"Type": "python"` in
its `plugInfo.json` and registration code in `__init__.py`.  The test
verifies: metadata is discoverable before any code loads (step 2);
`GetOrLoadValidatorByName` triggers `plugin->Load()` which imports
the module and runs the registration (steps 3-7); the validator
executes correctly; and keyword queries find the plugin validators.

The POC layer-stack validator was then converted from explicit
registration (`RegisterStageValidator` with caller-provided metadata)
to a proper Python-type plugin: a `layerStackValidator/` package with
its own `plugInfo.json` and `__init__.py` calling
`RegisterPluginStageValidator`.  All 9 tests pass, including two new
ones for metadata discoverability and keyword query.

### Iteration: Python fixer support

The previous plugin-bindings pass had explicitly noted that
`UsdValidationFixer` was not constructible from Python (`no_init`) and
deferred the work.  With the validator and plugin-registration paths
proven, the natural next step was enabling Python fixers so that a
validator plugin can ship both the check and the fix in one package.

The direction was again one sentence: "How much work would it be to
implement Python support for usdValidation fixers?"  After an
architecture assessment (~30 minutes of autonomous exploration), the
agent confirmed the work was mechanical: the same `TfPyObjWrapper` +
`TfPyLock` + `PyErr_Clear()` GIL-safety pattern used for validators
applies identically to fixer callables.

From that assessment, the agent (Opus):
- Added `_WrapFixerImplFn` and `_WrapFixerCanApplyFn` in
  `wrapFixer.cpp`, following the validator wrapper pattern exactly
- Exposed `ValidationFixer.__init__` via `make_constructor`, accepting
  Python callables for `fixerImplFn` and `canApplyFn` with optional
  `keywords` and `errorName`
- Added `_ExtractFixers` helper in `wrapRegistry.cpp` to convert a
  Python list to `std::vector<UsdValidationFixer>`
- Added an optional `fixers` parameter (default `None`) to all six
  `Register*Validator` methods; fully backward-compatible
- Wrote a comprehensive test suite (`testUsdValidationFixerPyRegister.py`)
  covering construction, registration, retrieval by name/keyword/error,
  `CanApplyFix`/`ApplyFix` round-trips, and backward compatibility
- Added real fixers to the POC layer-stack validator: `MetersPerUnitFixer`
  propagates the root layer's `metersPerUnit` to disagreeing layers;
  `UpAxisFixer` does the same for `upAxis`
- Extended the POC test suite with fixer tests: verify fixers are
  registered, apply correctly, and re-validation produces zero errors

The agent also added an "Adding fixers in Python" section to the
README with code examples covering construction, registration,
retrieval, and the `CanApplyFix`/`ApplyFix` workflow.  Every Python
code snippet in the README (both the existing validator examples and
the new fixer examples) was extracted and run against the built
binaries to verify correctness before committing.

Worth noting: during the plugin-bindings pass, the agent had flagged
that `UsdValidationFixer` lacked a Python constructor and that
exposing the optional fixers parameter on the registration methods
would be premature.  I (the human) read that note but did not
internalize it.  It took a Pixar reviewer asking "is there a reason
you did not implement fixers?" for me to realize the gap had already
been identified -- by my own agent -- and I had simply missed it.
The agent's judgment was correct at the time (fixers were not
blocking the validator PR), but I failed to scope it as a planned
follow-up.  This is an honest example of the human not keeping up
with the agent's observations; the reviewer caught what I should
have tracked.

The fixer implementation is a good example of the pattern this document
describes: the agent handled the mechanical extension (wrappers, bindings,
tests, documentation) while the human decision was about *when* to do
the work (after plugin registration was proven) and *what fixers to
build* for the POC (propagate root value vs. other strategies like
removing the opinion).

---

## Where Human Judgment Mattered

Each item below is a moment where the agent did useful mechanical work but a
human decision shaped whether the result was correct for a standards codebase.

### 1. Reframing the problem, not naming the fix

- Agent used `GetLayerStack()` for the PoC validator (covers sublayers only)
- Tested on Kitchen_set; agent itself reported 1 layer via `GetLayerStack()`
  vs. 230 via `GetUsedLayers()` -- but rationalized the narrow scope as
  sufficient
- My input was one question: "Think about what the maintainer of Kitchen_set
  needs to care about if someone else adds a new object to the kitchen"
- Agent immediately connected the dots: referenced/payloaded assets slip
  through `GetLayerStack()` entirely; one-line fix to `GetUsedLayers()`

**The human's job is not to know every API signature.  It is to understand
the real-world scenario well enough to ask the question that reframes the
problem.**

### 2. Semantic API correctness in documentation

- Agent used `prim.GetName()` (empty-name check) to detect pseudo-root prims
- Code worked, but `IsPseudoRoot()` is the purpose-built API
- This appeared in a README example, its prose, and a test -- three places
  users would copy from
- In a standards codebase, examples are normative; readers treat them as the
  specification for how to use the framework

**Focus review on whether the API being called directly expresses intent.  If
a more specific API exists (`IsPseudoRoot()`, `IsAbstractPrim()`,
`IsLoaded()`), it should be used.**

### 3. Knowing when not to fix

- Agent identified `PyErr_Clear()` as redundant after
  `TfPyConvertPythonExceptionToTfErrors()` (which already clears error state)
- Technically correct, but the same sequence appears in `TfPyCall<T>` and
  elsewhere in USD
- I chose: "Let's match the existing pattern"
- Codebase consistency outweighed theoretical cleanliness

**Not every correct observation should become a change.  In new code that
reviewers will compare against adjacent files, matching the existing pattern
is often more valuable than local optimization.**

### 4. Calibrating the investment

- README code examples were not tested during the session that wrote them
- Next day, different session, I asked the agent to verify them
- Agent's first instinct: build a formal doctest infrastructure
- I scaled back: throwaway test script, verify, revert
  - The broader question (many USD docs have breakable snippets) is a
    project-wide issue, not a single-module scaffolding problem
- Smoke-test confirmed all five examples worked; surfaced one test-ordering
  bug along the way

**Run documentation snippets before the PR.  But calibrate: a throwaway
script you revert is usually enough.  Formal doc-testing is a project-level
investment.**

### 5. Reining in over-applied patterns

- Asked the agent to prefer token constants over raw strings
- Agent applied the rule broadly, including extracting single-use error
  strings (`"MissingDefaultPrim"`) into named module-level constants
- I rolled that back: an inline string used once is fine
- Recurring dynamic: agent applies rules uniformly; human recognizes where
  uniform application crosses into over-engineering

**When giving a style correction, expect it to be applied everywhere.  Review
for cases where the rule does not improve clarity.**

### 6. Reading existing code first -- and scoping review

- **Writing phase:** agent consistently read adjacent code before writing
  - Read `wrapValidator.cpp` before touching `wrapRegistry.cpp`
  - Read existing tests and C++ validators before writing new ones
  - This produced code matching existing conventions without correction
- **Review phase:** agent's search scope sometimes drifted
  - Asked to audit for `GetName()`/`IsPseudoRoot()`, it searched the entire
    `usdValidation` tree instead of the specific commit
  - Redirecting it to `git diff` was a single sentence

**The agent pattern-matches well when writing.  During review, direct its
attention to the relevant changeset.**

### 7. Coding conventions benefit agents too

- Corrections over the sessions: `Tf` not `TF` in prose; no em-dashes;
  token constants over raw strings; inline single-use error strings; comments
  for human reviewers
- Had to point the agent to the project's contributing guidelines -- it did
  not find them on its own
- Each correction was saved to a persistent file; one-time investment,
  recovered in every future session

One view is that agent-written code is re-generatable, so conventions do not
matter.  That breaks down in two places:
- This code must pass human review before merging; inconsistent style creates
  friction unrelated to correctness
- Conventions benefit agents themselves -- the agent's strongest capability
  was reading adjacent code and matching patterns; if every session produces
  a slightly different style, that pattern-matching degrades

**Consistent conventions keep the codebase legible to the next agent, not
just the next human.**

### 8. Branch discipline

- Experimental work (layer-stack validator) went on a `poc/` branch
- PR for the core registration feature stays clean
- POC demonstrates capability without coupling to the reviewed API change

**Standard branch hygiene applies regardless of who or what produced the
code.**

### 9. Testing on real data

- Running the validator on Kitchen_set took minutes; taught more than another
  hour of unit-test design
- The structural insight (1 local layer, 229 referenced layers) directly
  motivated the `GetUsedLayers()` fix

**For any validator, schema change, or tool, run it against a non-trivial
real asset before submitting the PR.**

### 10. Scoping reviewer feedback into separable pieces

- Pixar's review asked for two things: `RegisterPluginValidator` bindings
  and a notice handler for dynamic registration
- The notice handler is a valid enhancement, but it is a C++ framework
  change to the registry itself; it affects all registration paths (C++ and
  Python), not just the Python bindings
- No notice infrastructure exists in usdValidation today; adding one is a
  design discussion, not a mechanical addition
- I scoped the PR to plugin bindings only and noted the notice handler as a
  follow-up
- The agent, when asked whether Python validators are usable without the
  notice handler, correctly analyzed the gap: the notice is about
  *discovery* (a UI caching a validator list would not learn about a new
  one), not *functionality* (register, query, validate all work)

**When a reviewer asks for multiple things, evaluate whether they are
separable.  Bundling a framework-level design change into an API-surface PR
risks delaying both.  Separate what can ship now from what needs its own
design discussion.**

### 11. Writing for the next developer, not just the next reviewer

- Pixar's feedback implicitly raised a question: how should someone else
  reason about which registration path to use?
- The agent added a decision guide to the README: a table comparing explicit
  vs. plugin registration on metadata source, discoverability, lazy loading,
  and use case
- This was not requested in the review; it was the natural response to "how
  would another developer reason about this"
- The guide makes the two paths self-documenting rather than requiring
  someone to read the C++ headers to understand when each applies

**Documentation that only describes *how* is incomplete.  The harder
question is *when* and *why*.  A decision guide at the point of use saves
every future reader from rediscovering the reasoning.**

### 12. The build-and-test loop is improving but still directed

- In the initial sessions, the agent did not independently build or run
  tests after writing code; I had to ask explicitly
- In the plugin-bindings session, the agent built, copied artifacts, ran all
  tests, caught a metadata accessor bug (`GetDoc()` vs. `doc` attribute),
  fixed it, re-ran to green, and ran the existing test suite for regression;
  all without prompting beyond "let's build and test"
- The remaining manual step: I still had to say "let's build and test"
  rather than the agent proposing it after completing the implementation
- Platform-specific mechanics (copying `.pyd` and `.dll` to `_install/`,
  updating the installed `plugInfo.json`) were handled correctly from
  persistent memory of the build environment

**The build-and-test loop has shifted from "agent needs step-by-step
instructions" to "agent needs a prompt to start but handles the mechanics."
The next step is the agent proposing the build at natural checkpoints.**

---

## On Writing This Document

This brief is itself a collaboration artifact shaped by the same dynamics it
describes.

- The implementation agent (Sonnet) wrote the first draft from a compressed
  context window -- not from the raw exchanges
- A different model (Opus) revised it the next day, working from the Sonnet
  draft rather than the original conversation
- Much nuance was lost in this telephone game: the draft overstated my role
  in API design, described the build loop as agent-initiated, and flattened
  Socratic exchanges into declarative statements about what I "pointed out"
- Recovering accuracy required going back to the session transcripts and
  fact-checking claims against what was actually said

If this document argues that human judgment is essential, it should
demonstrate that judgment by being accurate about where the human's
contribution was small and where the agent worked autonomously.  Overstating
the human role would undermine the point.

---

## Practical Limitations

**Context does not survive model switches.**
- Early sessions used Sonnet (implementation) and Opus (review/iteration)
- Sonnet tracked a test failure backlog in working memory but never persisted
  it; Opus had no knowledge of those results
- Recovery required searching through Sonnet's raw transcript

**Persistent memory narrows the gap across sessions.**
- The plugin-bindings session (Opus) picked up the full build environment,
  test invocation patterns, and coding conventions from persistent memory
  files written during earlier sessions
- It did not need to rediscover the `_install/` directory layout, the
  DLL-loading subprocess trick, or the `metadata.doc` vs. `GetDoc()` API
  style; it read memory, verified against current state, and proceeded
- The initial investment in writing those memories (one-time, earlier
  sessions) paid off in zero ramp-up time

**Any workflow that spans sessions or models must persist state to files, not
rely on in-context memory.**

---

## Toward Asynchronous Operation

*This section is aspirational.  The current practice is close human
supervision at every step.  I include it because the scaffolding would also
benefit any remote collaboration workflow, human or otherwise.*

**Core idea:** the agent publishes a live status document and pauses at
defined checkpoints.  The contributor reads the status, leaves guidance, and
the agent resumes.  No real-time presence required.

**Artifacts:**

| Artifact | Location | Purpose |
|---|---|---|
| `TASK.md` | repo root (gitignored) | Task spec; written by contributor |
| `STATUS.md` | repo root (gitignored) | Continuously updated by agent |
| `GUIDANCE.md` | repo root (gitignored) | Contributor writes direction here |
| feature branch | `feature/<name>` | All work on a branch; `dev` untouched |

**Checkpoint categories:**

| Category | What happens |
|---|---|
| Design gate | Pause, write design summary, wait for approval |
| API surface change | Always escalate (bindings and docs are API surface) |
| Build/test failure | Pause, write failure details, wait for guidance |
| Git operations | Commit on feature branches; never touch `dev`/`main`; confirm before PR |
| New public headers | Always escalate |

**Contributor check-in:**
1. Read `STATUS.md` (30 seconds)
2. `git log --oneline` + scan diffs
3. Write `GUIDANCE.md` if direction needed; otherwise agent continues

**Why this is not rubber-stamping.**  The synchronous sessions showed the
important interventions were domain-level, not implementation-level: the
agent handled API names and patterns well by reading existing code.  What
mattered was understanding real-world scenarios, recognizing when intent
trumps implementation detail, knowing when consistency outweighs correctness.
The async model concentrates oversight on exactly these decisions.

**Risks and mitigations:**
- *Agent proceeds past a bad design decision* -- design gates are hard stops;
  task file must be explicit about escalation triggers
- *Status document drifts from reality* -- rewrite STATUS.md from scratch
  after each commit
- *Context window loses details* -- atomic commits with descriptive messages;
  state reconstructable from `git log`
- *Contributor cannot interrupt* -- irreversible operations (PR creation,
  force-push) are always checkpoints, never autonomous

---

## Disclosure

PRs that used AI assistance say so in the description and in the
`Co-Authored-By` trailer on each commit.  Reviewers can use this information
however they see fit.  The contributor has reviewed every line and takes full
responsibility for correctness, API design, and documentation quality.

---

## Quick Reference

```
# Branch naming
# feature/<name>   PR-ready work
# poc/<name>       proof of concept
# fix/<name>       isolated bug fix

# Coding conventions (enforced via persistent agent memory)
# - Tf, not TF, in prose
# - No em-dashes; use semicolons
# - Token constants over raw strings (UsdGeom.Tokens.upAxis, not "upAxis")
# - Inline single-use error strings; no named constants for them
# - Copyright year = current year in new files; leave existing years alone
# - 80-char line limit, K&R braces, PXR_NAMESPACE_USING_DIRECTIVE
```
