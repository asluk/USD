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

### 10. The build-and-test loop is not automatic

- Agent did not independently build or run tests after writing code
- I had to ask explicitly; when it ran a subset, I had to clarify: "I mean
  all tests available in the repository"
- Build phase consumed significant session time: Windows DLL loading, stale
  `.pyd` files, `os.add_dll_directory` on Python 3.8+
- "Run tests early and often" was aspirational, not automatic

**Explicitly request builds and full test runs at checkpoints.  Budget time
for platform-specific issues the agent will need to debug.**

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
- Sessions used Sonnet (implementation) and Opus (review/iteration)
- Sonnet tracked a test failure backlog in working memory but never persisted
  it; Opus had no knowledge of those results
- Recovery required searching through Sonnet's raw transcript

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
