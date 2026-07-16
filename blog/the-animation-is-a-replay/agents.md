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
human version runs four discrete-event engines across six live execution paths:
four in the browser, plus native Rust and native SimPy behind an HTTP API. You
do not need a browser. You need the rules, the schema, the adapters, and the
verified numbers. All inline below.

The human page also runs a fifth library for a different purpose: salabim
26.0.8 executes a six-hour factory model inside Pyodide, then its own animation
engine and Pillow 11.2.1 render 61 WebP frames. That is a genuine built-in
animation path, not another Fig. 3 conformance row.

The governing rules, extending the predecessor document's "the diagram is never
the source of truth":

> **1. A simulation's virtual clock is not the viewer's wall clock. Run the
> simulation at full CPU speed, record an event log, and render every animation
> as a replay of that log at a chosen speed. Never couple engine stepping to
> rendering.**
>
> **2. The event log, not the engine, is the interface. Keep the layers
> model → engine → event log → presentation strictly separated. Engines then
> become swappable, which the reference implementation proves by swapping four
> and moving two of them across the browser/server boundary.**
>
> **3. Determinism belongs to the executable semantics: engine + model + RNG +
> seed + serializer → identical log (hash it to prove it). Different engines
> agree statistically, not event by event. The same engine on two runtimes may
> agree exactly, but verify that empirically rather than assuming it.**

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
1 reviewer, exponential 30 min; half-open horizon [0, 14 days), or [0, 20,160
min). Events at or beyond the cutoff do not belong in the log.

Closed form: coding cost/item = 45/(1-p) = 60 agent-min → coding capacity
72/day; review capacity 1440/30 = 48/day < 57.6/day arrivals → **review is the
constraint; predicted throughput 48/day**.

## Verified results (build-time, 2026-07-16, this droplet + headless Chrome)

Conformance band from 200 SimPy replications (seeds 1000-1199):
**mean 47.27, sd 1.89, 3σ band [41.59, 52.95]** deploys/day.

| Engine | Runtime | Deploys/day (seed 42) | Review util | Wall ms (14 sim-days) | Client payload | In band |
|---|---|---|---|---|---|---|
| ts-kernel (hand-rolled) | Node 22 and Chrome | 46.79 | 0.984 | 13.5 | 0 (inline) | yes |
| rust-wasm 0.1.0 (hand-rolled, PCG32) | wasm in Node and Chrome | 44.79 | 0.960 | 11.8 | ~53 KB | yes |
| replay-kernel 0.1.0 (hand-rolled, PCG32) | native x86-64 shared library behind this site's API | 44.79 | 0.960 | ~11 live service | ~36.1 KB compressed log | yes |
| simscript 1.0.37 | Node and Chrome | 46.50 | 0.994 | 186.2 | ~34 KB | yes |
| simpy 4.1.2 | CPython 3.12.3 behind this site's FastAPI service | 46.21 | 0.987 | ~25 warmed; 60-93 ms measured HTTP round trip | ~38.4 KB compressed log | yes |
| simpy 4.1.2 | CPython 3.13 via Pyodide in Chrome | 46.21 | 0.987 | ~101 after boot | ~5.2 MB compressed, opt-in | yes |

Cross-runtime determinism results (same seed 42):
- ts-kernel: Node hash == Chrome hash (`dab40e83…`).
- replay-kernel: Node-wasm == Chrome-wasm == native x86-64 through the live API
  (`406362c5…`), byte-for-byte across all 5,014 seed-42 events. The native
  shared library was built with rustc 1.95.0. Native libm can differ from wasm
  in the last ulp, so treat this equality as measured for this workload rather
  than guaranteed for every seed and platform.
- simscript: Node hash == Chrome hash (`35ce159e…`).
- simpy: native CPython 3.12.3 behind the live API == build-time native CPython
  == Pyodide/CPython 3.13 (`3dab9d60…`). The browser computes the server log's
  hash itself. This workload is bit-identical across the tested glibc/emscripten
  runtimes; do not assume that generalizes.
- Six execution paths produce four hashes: no two different engines share one,
  while both the Rust and SimPy runtime pairs repeat theirs exactly. All six sit
  inside the band. At p = 0.5 coding and review capacities are both 48/day;
  coding is strictly the constraint only above 0.5.

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

**Native engine API** (`server/app.py`; both models imported or loaded rather
than copied):
- `POST /blog/the-animation-is-a-replay/api/run/simpy` with `{"seed":42}`.
- `POST /blog/the-animation-is-a-replay/api/run/rust` with `{"seed":42}`.
- Return the canonical event log plus runtime identity and engine wall time.
  Never return only trusted summary statistics; the browser derives throughput,
  utilization, queue depth, and SHA-256 from the received log.
- The fixed 14-day model limits work. Validate seeds to `0..999999999`, cap each
  client at 30 runs/minute, stop a run after 2 seconds, disable response caching,
  and gzip logs above 1 KB.
- SimPy seed 42 returns 5,276 events, ~240 KB JSON / ~38.4 KB gzip,
  46.21 deploys/day, and hash `3dab9d60…`.
- Native Rust is the same crate as the wasm row, compiled as a persistent
  `cdylib`. A two-function C ABI returns an owned JSON string and frees it after
  Python copies the bytes. Seed 42 returns 5,014 events, ~228 KB JSON /
  ~36.1 KB gzip, 44.79 deploys/day, and hash `406362c5…`.
- Keep engine routes isomorphic. Consumers should not change when a producer is
  added or moved.

**SimScript** gotchas (cost one debugging cycle each; version 1.0.37, npm
"latest" - a 3.x version string circulates but does not exist):
- Its run loop yields to `requestAnimationFrame` every `yieldInterval` ms
  (default 250). For headless/synchronous runs set `sim.maxTimeStep = 0` AND
  `sim.yieldInterval = Infinity`, then await `stateChanged` until
  `SimulationState.Finished` - `start()` resolving does not mean finished.
- Seed its `RandomVar`s explicitly (constructor seed argument); distinct streams
  per purpose (interarrival, service, fail-draw) keep adapters comparable.
- `EntityGenerator` halves the first sampled interarrival when `startTime` is
  omitted. Sample the first interval yourself and pass it as `startTime` to
  match the full exponential first arrival used by the other adapters.
- `timeEnd` is checked after the next future-event entry executes, so SimScript
  may overshoot. Filter the emitted log to `e.t < horizonMin`; stats consumers
  should enforce the same cutoff defensively.

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

**salabim animation in Pyodide** (also strictly opt-in; reuses the SimPy
worker, then adds the ~1.06 MB Pyodide Pillow wheel and ~1.35 MB pure-Python
salabim wheel):

- salabim detects Pyodide, disables its greenlet-based yieldless mode, and
  forces `blind_animation=True`. It does not put a Tk window in the browser.
  It advances the model headlessly and asks Pillow to record the native
  animation objects into an artifact.
- The verified seed-42 figure is 640×360, 61 frames at 10 fps, six simulated
  hours shown in six playback seconds. It contains 18 arrivals, 5 rework
  loops, and 11 deployments. The light WebP is ~1.09 MB; the dark WebP is
  ~1.06 MB.
- Keep this path next to, not in place of, the event-log replayer. salabim's
  built-in animation buys queues, resources, monitors, and a renderer. The
  event-log path buys a presentation layer that is engine-independent,
  scrubbable, diffable, and shareable.

Minimal model and render path (the page's fully styled source is
`salabim_animation.py`):

```python
import json, random
from pathlib import Path
import salabim as sim

P = {"arrivalMean": 25, "codeMean": 45, "ciTime": 10, "failP": 0.25,
     "agents": 3, "reviewers": 1, "reviewMean": 30, "horizonMin": 360}

def render_salabim(seed, theme="light"):
    rng = random.Random(seed)
    out = Path(f"/tmp/factory-{seed}-{theme}.webp")
    env = sim.Environment(
        random_seed=seed, blind_animation=True, yieldless=False,
        time_unit="minutes")
    coding = sim.Resource("coding", capacity=3, env=env)
    review = sim.Resource("review", capacity=1, env=env)
    ci_active = sim.Queue("ci active", env=env)
    deployed = sim.Queue("deployed", env=env)

    class Item(sim.Component):
        def process(self):
            while True:
                yield self.request(coding)
                yield self.hold(rng.expovariate(1 / P["codeMean"]))
                self.release(coding)
                self.enter(ci_active)
                yield self.hold(P["ciTime"])
                self.leave(ci_active)
                if rng.random() < P["failP"]:
                    continue
                break
            yield self.request(review)
            yield self.hold(rng.expovariate(1 / P["reviewMean"]))
            self.release(review)
            self.enter(deployed)
            yield self.passivate()

    class Arrivals(sim.Component):
        def process(self):
            while True:
                yield self.hold(rng.expovariate(1 / P["arrivalMean"]))
                Item()

    Arrivals()
    env.animation_parameters(
        width=640, height=360, x0=0, y0=0, x1=640,
        speed=60, fps=10, show_time=False, show_menu_buttons=False,
        video=str(out), video_repeat=1)
    sim.AnimateQueue(coding.requesters(), x=24, y=245, direction="e")
    sim.AnimateQueue(coding.claimers(), x=164, y=245, direction="e")
    sim.AnimateQueue(ci_active, x=315, y=245, direction="e")
    sim.AnimateQueue(review.requesters(), x=424, y=245, direction="e")
    sim.AnimateQueue(review.claimers(), x=480, y=190, direction="e")
    sim.AnimateQueue(deployed, x=548, y=245, direction="e")
    env.animate(True)
    env.run(till=P["horizonMin"])
    env.video_close()
    return json.dumps({"path": str(out), "bytes": out.stat().st_size})
```

Worker handoff:

```js
await pyodide.loadPackage("pillow");
await micropip.install("salabim==26.0.8");
pyodide.runPython(salabimSource);
const meta = JSON.parse(
  pyodide.runPython(`render_salabim(${seed}, ${JSON.stringify(theme)})`));
const bytes = pyodide.FS.readFile(meta.path);
const buffer = bytes.buffer.slice(
  bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
self.postMessage({ id, ok: true, result: { meta, buffer } }, [buffer]);
```

The main thread wraps `buffer` in `new Blob([buffer], {type:"image/webp"})`.
If the CDN or wheel load fails, retain the static explanation and the working
event-log replay. Never leave an empty media box.

**Rust → wasm**: hand-rolled kernel + PCG32, `wasm-bindgen` exports taking
primitive params, `wasm-pack build --target web` for the page and
`--target nodejs` for build-time reference logs. Note wasm-pack drops a
`.gitignore` containing `*` into the output dir; delete it or your artifacts
silently never commit.

**Rust → native server**: build the same crate as a `cdylib`; load it once at
service startup with `ctypes.CDLL`; set explicit argument and return types; copy
the returned JSON bytes; always call `replay_kernel_string_free` in `finally`.
Do not spawn a CLI process per request just to cross a language boundary.

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
| Want built-in animation/monitoring in Python | salabim; the human post demonstrates its real Pyodide/Pillow render path |
| The model is a queueing network | Ciw |
| Browser is the runtime, adopt not build | SimScript; or SimPy via Pyodide (opt-in weight) |
| Own + embed the core (browser and native from one source) | hand-rolled Rust → native + WASM (this post's crate) |
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
9. If demonstrating a built-in animator, run the real renderer and label where
   it executes. A JavaScript lookalike teaches nothing about the library.
10. Treat a server as another event-log producer. Validate and hash its returned
   log in the consumer instead of trusting server-calculated presentation data.

## Self-test (answers below)

1. Your renderer needs the current queue depth. Where does it get it?
2. Same seed, two different engines, different hashes - bug or expected? What
   about the Rust or SimPy browser/server runtime pairs?
3. An engine lands at 40.1 deploys/day at the default parameters. What does that
   mean, given the band [41.59, 52.95]?
4. Why generate the Rust reference log from the wasm build instead of native?
5. What two properties make a replay shareable and diffable?
6. salabim can animate the model directly. Does that invalidate the event-log
   replay rule?

Answers: (1) By folding the event log up to t; if it must ask the engine, the
layering is broken. (2) Different engines should differ event by event and agree
statistically. Both runtime pairs match exactly for the verified seed-42
workload because each pair shares its engine, model, RNG, seed, and serializer;
verify rather than generalize. (3) A semantics divergence in that engine's
model - a real bug, findable because the band exists; investigate the adapter,
not the band. (4) wasm float semantics are identical across platforms, so the
bundled hash matches every browser; native libm may differ in the last ulp even
though this native run did not. (5) Seed + params in the header (regenerable)
and canonical serialization with a stable hash (identity). (6) No. Built-in
animation is useful and the post demonstrates it honestly; it simply puts
presentation inside the engine's vocabulary. Keep the event-log seam when you
need another renderer, arbitrary-speed replay, scrubbing, diffing, or sharing.

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
