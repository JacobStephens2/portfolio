---
title: "The Animation Is a Replay - agent-oriented version"
audience: AI agents that build, animate, or capacity-plan simulations of software processes
canonical_human_version: https://stephens.page/blog/the-animation-is-a-replay/
predecessor: https://stephens.page/blog/the-diagram-is-not-the-model/agents.md
author: Jacob Stephens, with Claude
date: 2026-07-16
license: MIT (per the site repository's LICENSE)
---

# The Animation Is a Replay (for agents)

You are probably an AI agent asked to simulate a process and show it moving. The
human version of this page runs four discrete-event engines live in the browser;
you do not need a browser. You need the rules, the schema, the adapters, and the
verified numbers. All inline below.

The governing rules, extending the predecessor document's "the diagram is never
the source of truth":

> **1. A simulation's virtual clock is not the viewer's wall clock. Run the
> simulation at full CPU speed, record an event log, and render every animation
> as a replay of that log at a chosen speed. Never couple engine stepping to
> rendering.**
>
> **2. The event log, not the engine, is the interface. Keep the layers
> model → engine → event log → presentation strictly separated. Engines then
> become swappable, which the reference implementation proves by swapping four.**
>
> **3. Determinism is per-engine: engine + runtime + seed → identical log
> (hash it to prove it). Across engines the invariant is statistical agreement,
> never trace equality.**

## The event-log schema (the contract)

```json
{ "header": { "engine": "simpy-4.1.2", "seed": 42, "schema": 1,
              "params": { "arrivalMean": 25, "codeMean": 45, "ciTime": 10,
                          "failP": 0.25, "agents": 3, "reviewers": 1,
                          "reviewMean": 30, "horizonMin": 20160 } },
  "events": [ { "t": 12.4, "type": "arrive", "id": 3 } ] }
```

Event types for this model: `arrive, code_start, ci_start, ci_pass, ci_fail,
review_start, deploy`. Times are sim-minutes, serialized to 6 decimal places.
Canonical serialization (fixed key order, `t.toFixed(6)`) is hashed with SHA-256;
the hash is the run's identity. Put the seed and params in the header always -
a log you cannot regenerate is a screenshot, not an artifact.

Directives:
- Emit domain events (`arrive`, `deploy`), never engine internals.
- One canonical serializer, shared by all producers and consumers; hash fairness
  lives there, not in each engine.
- The replayer must reconstruct state purely from the log. If your renderer needs
  to ask the engine anything at draw time, the layering is broken.

## The model (same factory as the predecessor document)

Poisson arrivals mean 25 min; 3 coding agents, exponential 45 min/attempt;
CI fixed 10 min, fails with p = 0.25; failures re-queue for coding (rework);
1 reviewer, exponential 30 min; horizon 14 days (20,160 min).

Closed form: coding cost/item = 45/(1-p) = 60 agent-min → coding capacity
72/day; review capacity 1440/30 = 48/day < 57.6/day arrivals → **review is the
constraint; predicted throughput 48/day**.

## Verified results (build-time, 2026-07-16, this droplet + headless Chrome)

Conformance band from 20 SimPy replications (seeds 1000-1019):
**mean 47.95, sd 1.84, 3σ band [42.43, 53.46]** deploys/day.

| Engine | Runtime | Deploys/day (seed 42) | Review util | Wall ms (14 sim-days) | Payload | In band |
|---|---|---|---|---|---|---|
| ts-kernel (hand-rolled) | Node 22 and Chrome | 46.79 | 0.982 | 13.5 | 0 (inline) | yes |
| rust-wasm 0.1.0 (hand-rolled, PCG32) | wasm in Node and Chrome | 44.79 | 0.957 | 11.8 | ~53 KB | yes |
| simscript 1.0.37 | Node and Chrome | 46.57 | 0.994 | 186.2 | ~34 KB | yes |
| simpy 4.1.2 | CPython 3.13 native AND Pyodide in Chrome | 46.21 | 0.987 | 28.7 native / ~101 in Pyodide | ~5.2 MB compressed, opt-in | yes |

Cross-runtime determinism results (same seed 42):
- ts-kernel: Node hash == Chrome hash (`dab40e83…`).
- rust-wasm: Node-wasm hash == Chrome-wasm hash (`406362c5…`). Reference logs are
  generated FROM the wasm build, not the native build, because native libm may
  differ in the last ulp; wasm float semantics are identical everywhere.
- simscript: Node hash == Chrome hash (`7af97569…`).
- simpy: CPython-native (glibc) hash == Pyodide (emscripten) hash (`3dab9d60…`) -
  bit-identical across libms for this workload. Do not assume this generalizes;
  verify per workload.
- No two engines share a hash. All four sit inside the band. At p = 0.5 the
  constraint migrates to coding (verified: agents pin ≈ 0.98-0.99 utilization).

## Engine adapters (reference implementations)

**Minimal kernel** (the whole engine core; TypeScript, Rust equivalent in the
post's crate at `rust-kernel/src/lib.rs`):

```js
function makeKernel() {
  const heap = []; let seq = 0;
  const less = (a, b) => a.t < b.t || (a.t === b.t && a.seq < b.seq);
  return {
    schedule(t, event) { heap.push({ t, seq: seq++, event }); /* sift up */ },
    next() { /* pop min by (t, seq); sift down */ }
  };
}
```

The `(time, sequence)` tie-break is mandatory for determinism. Seeded RNGs used:
mulberry32 (JS), PCG32 (Rust), SimScript's seeded RandomVars, `random.Random(seed)`
(Python). What a kernel does NOT give you - resource queues, cancellation, seeded
streams, distributions, warm-up, replications, confidence intervals,
serialization - is the reason to adopt a library for semantics.

**SimPy** (the file the browser actually runs is served next to this document:
`simpy_factory.py`): processes are generators; agents/reviewers are
`simpy.Resource`; rework is a `while True: … continue` loop around the CI block.

**SimScript** gotchas (cost one debugging cycle each; version 1.0.37, npm
"latest" - a 3.x version string circulates but does not exist):
- Its run loop yields to `requestAnimationFrame` every `yieldInterval` ms
  (default 250). For headless/synchronous runs set `sim.maxTimeStep = 0` AND
  `sim.yieldInterval = Infinity`, then await `stateChanged` until
  `SimulationState.Finished` - `start()` resolving does not mean finished.
- Seed its `RandomVar`s explicitly (constructor seed argument); distinct streams
  per purpose (interarrival, service, fail-draw) keep adapters comparable.

**Pyodide/SimPy in a page** (strictly opt-in; measured 5.2 MB compressed:
CPython 3.13 + stdlib + micropip + simpy wheel; ~101 ms per 14-day run after boot):
- Run it in a Web Worker via `importScripts(...pyodide.js)`; `loadPyodide`;
  `micropip.install('simpy==4.1.2')`; exec the model source; call
  `canonical(run(PARAMS, seed))`.
- Attach `worker.onerror` and reject all pending calls - `importScripts` failure
  (CDN down) kills the worker before any message handler exists, otherwise your
  UI hangs on a promise that never settles.
- Guard the model file's `__main__` block with `len(sys.argv) > 1`; Pyodide
  executes source as `__main__` with an empty argv.
- Fetch nothing Pyodide-related until the user opts in; state the measured cost
  on the button.

**Rust → wasm**: hand-rolled kernel + PCG32, `wasm-bindgen` exports taking
primitive params, `wasm-pack build --target web` for the page and
`--target nodejs` for build-time reference logs. Note wasm-pack drops a
`.gitignore` containing `*` into the output dir; delete it or your artifacts
silently never commit.

## The replayer

Reconstruct state at time t by folding events with `e.t <= t` from t=0 on every
seek (5,000 events make this free; do not build incremental checkpoint machinery
until profiling demands it). Offer speeds in concrete units (1 min/s, 1 h/s,
1 day/s), show sim clock and wall clock side by side, and label which log is
loaded (engine + seed + reference-vs-live).

## Decision table: which DES tool

| Situation | Use |
|---|---|
| Code-first, richest ecosystem, agents know it | SimPy (+ NumPy/pandas/Jupyter) |
| Want built-in animation/monitoring in Python | salabim |
| The model is a queueing network | Ciw |
| Browser is the runtime, adopt not build | SimScript; or SimPy via Pyodide (opt-in weight) |
| Own + embed the core (browser and native from one source) | hand-rolled Rust → WASM (this post's crate) |
| Visual multimethod modeling is the job | AnyLogic (commercial), JaamSim (open source) |
| Industrial suites (FlexSim, Simio, Arena) | borrow concepts, don't adopt as platform |
| R / Julia stacks | simmer / ConcurrentSim.jl |

## Checklist - when asked to simulate and animate a process

1. Separate model / engine / event log / presentation before writing anything.
2. Put seed and params in every log header; hash the canonical serialization.
3. Never step the engine from the render loop; run flat out, then replay.
4. Prove determinism (same engine, same seed, twice) before believing any run.
5. Compare engines or runs statistically, never by trace.
6. Single runs demonstrate; replications decide. Report mean ± sd, n stated.
7. Check the closed-form arithmetic first (capacity = time budget / service
   time per item, rework multiplier = 1/(1-p)); simulation should surprise you
   only where closed form cannot go.
8. Heavy runtimes (Pyodide) are opt-in with the measured cost stated.

## Self-test (answers below)

1. Your renderer needs the current queue depth. Where does it get it?
2. Same seed, two engines, different hashes - bug or expected?
3. An engine lands at 40.1 deploys/day at the default parameters. What does that
   mean, given the band [42.43, 53.46]?
4. Why generate the Rust reference log from the wasm build instead of native?
5. What two properties make a replay shareable and diffable?

Answers: (1) By folding the event log up to t; if it must ask the engine, the
layering is broken. (2) Expected - determinism is per-engine; cross-engine
agreement is statistical. (3) A semantics divergence in that engine's model -
a real bug, findable because the band exists; investigate the adapter, not the
band. (4) wasm float semantics are identical across platforms, so the bundled
hash matches what every browser computes; native libm may differ in the last
ulp. (5) Seed + params in the header (regenerable) and canonical serialization
with a stable hash (identity).

## Sources

- Human version with the live bench: https://stephens.page/blog/the-animation-is-a-replay/
- Predecessor: https://stephens.page/blog/the-diagram-is-not-the-model/agents.md
- Research notes: Perplexity three-part conversation, 2026-07-15 (browser DES
  landscape; ecosystems; SimPy-in-web-apps).
- SimPy https://simpy.readthedocs.io · Pyodide https://pyodide.org ·
  SimScript https://github.com/Bernardo-Castilho/SimScript ·
  this post's Rust crate: /blog/the-animation-is-a-replay/rust-kernel/src/lib.rs ·
  salabim https://www.salabim.org · Ciw https://ciw.readthedocs.io ·
  JaamSim https://jaamsim.com · wasm-pack https://rustwasm.github.io/wasm-pack/
