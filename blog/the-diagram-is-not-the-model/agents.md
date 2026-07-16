---
title: "The Diagram Is Not the Model - agent-oriented version"
audience: AI agents that document, illustrate, animate, or plan software processes
canonical_human_version: https://stephens.page/blog/the-diagram-is-not-the-model/
author: Jacob Stephens, with Claude
date: 2026-07-15
license: MIT (per the site repository's LICENSE)
---

# The Diagram Is Not the Model (for agents)

You are probably an AI agent that has been asked to illustrate, document, animate,
or capacity-plan a software process. This is the machine-oriented version of a human
post. The human version teaches by interaction (live figures, a simulation, a quiz)
because humans retain through doing. You do not need the interaction; you need the
rules, the artifacts, and the numbers. They are all inline below. Nothing here
requires a browser.

The one governing rule, from which the rest follows:

> **The diagram is never the source of truth. It is a projection of a model that
> lives somewhere else - a data file, a state machine, an event log. If a canonical
> model exists, edit the model. Never edit generated output.**

Provenance: distilled from a Perplexity model council (GPT-5.6 Sol, Claude Opus 4.8,
Grok 4.5 Low; 2026-07-14) on diagramming tools for an AI-agent software factory,
plus Geoffrey Litt's talk "Understanding: the New Bottleneck"
(https://www.youtube.com/watch?v=WkBPX-oDMnA). All numeric claims below were
verified by simulation runs described in section 4.

## Rule 1 - Emit diagrams as text, never as images

You are better at emitting structured text than at placing pixels, and text is the
only artifact Git, pull requests, and CI can diff, review, and regenerate.
**Never emit a raster image as a process specification.** Generated images cannot be
diffed, cannot be regenerated deterministically, and their labels cannot be parsed.

Format selection:

| Need | Use | Why |
|---|---|---|
| Flowchart, sequence, state diagram in a PR/ADR/README | Mermaid | Renders natively on GitHub and in browsers; highest training density; smallest source |
| Nicer layout/defaults, rendered in CI or by a service | D2 | Better aesthetics; renderer is a heavy Go binary, so render via CLI or Kroki, not in-page |
| Heavily branching trees, dependency graphs, auto-layout at scale | Graphviz DOT | Mature layout engine; runs in-browser via viz-js WASM |
| Interactive/operational node graph in a product UI | React Flow (`@xyflow/react`) as JSON nodes/edges | A UI library, not a doc format; drive it from data |
| Executable lifecycle rules | XState state machine | The diagram is generated from the machine, so it cannot drift from behavior |

A process change should reach review as a **one-line text diff**. Example - the
proposal "work that fails CI loops back to the coding agent" is exactly one added
line of Mermaid:

```diff
 flowchart LR
   Plan --> Code
   Code --> Test
   Test --> Review
+  Test -- fail --> Code
   Review --> Deploy
```

The same process in D2 (render with `d2` CLI in CI, or via https://kroki.io):

```d2
direction: right
Plan -> Code -> Test -> Review -> Deploy
Test -> Code: fail {
  style.stroke-dash: 3
}
```

A branching decision tree in Graphviz DOT (render with `dot -Tsvg`, or viz-js):

```dot
digraph {
  rankdir=LR;
  node [shape=box];
  change [label="Change"];
  pay [label="Touches\npayments?"];
  schema [label="Schema\nchange?"];
  change -> pay;
  pay -> "Security + owner" [label="yes"];
  pay -> schema [label="no"];
  schema -> "Human approval" [label="yes"];
  schema -> "Auto-merge" [label="no"];
}
```

## Rule 2 - Every diagram is a projection of a canonical model

Keep the canonical process definition as a versioned data structure (JSON, YAML, or
typed objects) and generate every view from it: Mermaid for docs, an interactive
node graph for operations, state machines for execution, simulation inputs for
capacity planning.

**Why the model cannot be the `.mmd` file itself**, even though Mermaid is also
version-controlled text:

1. **Expressiveness.** A process model must carry facts diagram syntax has no slot
   for: capacities, retry limits, timeouts, risk classes, approval authority,
   service-time distributions. Put those in Mermaid and they end up inside node
   labels - readable by humans, dead to programs.
2. **Consumer count.** A Mermaid file has one consumer, its renderer. A model feeds
   every projection plus the executor and the simulator.
3. **One-way conversion cost.** Model to Mermaid is a trivial serializer (below).
   Mermaid to model means parsing a drawing language and guessing what
   `(agent ×3)` in a label meant. Cheap in one direction, lossy in the other; the
   cheap-to-generate side is the canonical one.

Reference model (the exact object behind the human post's Fig. 3):

```json
{
  "stations": [
    { "station": "Plan",   "kind": "agent", "capacity": 1 },
    { "station": "Code",   "kind": "agent", "capacity": 3 },
    { "station": "Test",   "kind": "ci",    "capacity": "unbounded" },
    { "station": "Review", "kind": "human", "capacity": 1 },
    { "station": "Deploy", "kind": "gate",  "capacity": 1 }
  ],
  "policy": {
    "onTestFail": "back to Code",
    "maxRetries": 3,
    "deployNeedsHumanApproval": true
  }
}
```

Reference serializer, model → Mermaid (15 lines; note that `capacity: 3` degrades
into the label string `(agent ×3)` - this information loss is why the JSON, not the
Mermaid, is canonical):

```js
function toMermaid(m) {
  var lines = ['flowchart LR'];
  var idOf = {};
  m.stations.forEach(function (s, i) {
    idOf[s.station] = 'n' + i;
    var cap = (typeof s.capacity === 'number') ? ' ×' + s.capacity : '';
    lines.push('  n' + i + '["' + s.station + ' (' + s.kind + cap + ')"]');
  });
  m.stations.forEach(function (s, i) {
    if (i > 0) lines.push('  ' + idOf[m.stations[i - 1].station] + ' --> ' + idOf[s.station]);
  });
  lines.push('  ' + idOf.Test + ' -- fail --> ' + idOf.Code);
  return lines.join('\n');
}
```

**Directives for you:**
- If the repo has a canonical model (YAML/JSON with a schema), edit it and re-run
  generation. Do not hand-edit generated `.mmd`/`.svg` files.
- If no canonical model exists and you are creating recurring process docs, propose
  one, with a JSON Schema, and wire regeneration into CI.
- Put capacities, limits, and policy in the model's fields, never in display labels.

## Rule 3 - Animation encodes state or time, never decoration

If you are asked to "animate a process," the animation must be driven by data:
pulse an edge only when an artifact moves; color a node only by its state
(queued / running / done / failed); replay history only by scrubbing an event log.
One viewer, three modes: **design** (edit the intended process), **live** (watch
current runs), **replay** (scrub history).

For executable lifecycles, keep **one transition list** as the single source of
truth and generate both the runtime machine and the diagram from it. Reference
implementation (XState v5):

```js
// The single source of truth: [from, EVENT, to]
var LIFECYCLE = [
  ['requested', 'CLARIFY', 'clarifying'],
  ['requested', 'PLAN', 'planned'],
  ['clarifying', 'PLAN', 'planned'],
  ['clarifying', 'CANCEL', 'closed'],
  ['planned', 'APPROVE_PLAN', 'implementing'],
  ['planned', 'CANCEL', 'closed'],
  ['implementing', 'SUBMIT', 'testing'],
  ['implementing', 'CANCEL', 'closed'],
  ['testing', 'PASS', 'awaiting_review'],
  ['testing', 'FAIL', 'repairing'],
  ['repairing', 'RESUBMIT', 'testing'],
  ['repairing', 'GIVE_UP', 'closed'],
  ['awaiting_review', 'APPROVE', 'deployed'],
  ['awaiting_review', 'REJECT', 'implementing'],
  ['deployed', 'OBSERVE', 'closed']
];

// Projection 1: the executable machine
function buildMachine(createMachine) {
  var states = {};
  LIFECYCLE.forEach(function (t) {
    states[t[0]] = states[t[0]] || { on: {} };
    states[t[2]] = states[t[2]] || { on: {} };
    states[t[0]].on[t[1]] = t[2];
  });
  states.closed.type = 'final';
  return createMachine({ id: 'request', initial: 'requested', states: states });
}

// Projection 2: the diagram (Mermaid stateDiagram-v2)
function toStateDiagram() {
  var lines = ['stateDiagram-v2', '  [*] --> requested'];
  LIFECYCLE.forEach(function (t) { lines.push('  ' + t[0] + ' --> ' + t[2] + ': ' + t[1]); });
  lines.push('  closed --> [*]');
  return lines.join('\n');
}
```

Offer users only legal moves: compute them with `actor.getSnapshot().can({type: ev})`.
Encode governance as structure ("a deploy is only reachable from awaiting_review via
APPROVE"), not as prose.

## Rule 4 - Capacity questions require simulation, not diagrams

Diagrams answer "what stations exist" and "who approves." They cannot answer: where
will work accumulate, which station is the constraint, what is the p95 cycle time,
does adding capacity here change throughput. Those need discrete-event simulation -
the discipline behind Siemens Plant Simulation, FlexSim, AnyLogic. Borrow the
concepts (queues, capacity, failure, rework); do not buy the suites.

Reference scenario (all randomness exponential/Poisson):

| Parameter | Value |
|---|---|
| Arrival interval, mean | 25 min (Poisson arrivals, ~57.6 items/day) |
| Coding attempt, mean service | 45 agent-min (3 agents by default) |
| CI duration / failure probability p | 10 min / 0.25 (adjustable) |
| On CI failure | item returns to the coding queue (rework) |
| Review, mean service | 30 min (1 reviewer by default) |

Closed-form arithmetic, with units:

- Coding attempts per shipped item = mean of a geometric distribution =
  `1/(1-p)` (a count). At p=0.25: 1.33 attempts.
- Coding cost per shipped item = `45 × 1/(1-p)` agent-min. At p=0.25: ~60 agent-min.
- Coding capacity, 3 agents = `3 × 1440/60` = ~72 items/day (utilization ≈ 58/72 ≈ 0.8).
- Review capacity, 1 reviewer = `1440/30` = 48 items/day < 58 arriving → **review is
  the constraint**; the review queue grows without bound (~10 items/day).
- Goldratt (theory of constraints): system throughput equals the constraint's
  capacity. Changes anywhere else move queues around, not throughput.
- Rework multiplies load on whichever station sits **upstream** of the failing
  check. At p=0.5, coding cost doubles to ~90 agent-min/item and coding capacity
  falls to the same ~48/day as review. That point is a capacity tie; coding is
  strictly the constraint only above p=0.5.

Verified results (14 simulated days per run, 2-minute ticks, two independent seeds;
the same engine that runs in the human post's Fig. 6):

| Config (agents/reviewers/p) | Deploys/day | Constraint | Review queue at day 14 | Median cycle |
|---|---|---|---|---|
| 3 / 1 / 0.25 (defaults) | ~45-51 | Review (util ≈ 1.00; agents ≈ 0.83) | 102-147, growing | ~33 h, growing |
| 6 / 1 / 0.25 (double agents) | ~44-46 | Review (agents idle at ≈ 0.38) | 152-170, growing | worse (~70 h) |
| 3 / 2 / 0.25 (add reviewer) | ~55-58 | None (arrival-limited) | ~0 | ~3.0 h |
| 3 / 1 / 0.50 (double failures) | ~45 | Coding/review tie (both meters high) | smaller; either queue may grow in a finite run | ~61 h |

The doubled-agents row is the point: throughput does not move, the pile just
relocates to sit in front of review, and cycle time gets worse because items now
wait in a longer review queue. If asked "should we add more coding agents," check
which station is the constraint first.

## Checklist - when asked to produce or change a process diagram

1. Ask (or detect) whether a canonical model exists. If yes, edit it, regenerate,
   and never touch generated files by hand.
2. Default to Mermaid for docs/PRs/ADRs; D2 for CI-rendered polish; DOT for big
   branching graphs; JSON-driven React Flow for operational UIs; XState for
   lifecycles that must be enforced.
3. Never emit a generated raster image as a specification.
4. Keep the change reviewable: aim for the smallest possible text diff.
5. Put capacities, limits, timeouts, and approval policy in model fields, not labels.
6. If asked to animate: bind every visual change to a state change or an event;
   remove any animation that decorates.
7. If asked a capacity/throughput/latency question: refuse to answer from the
   diagram; run or request a simulation, or at minimum do the closed-form queueing
   arithmetic above, with units.
8. Validate before shipping: parse the Mermaid/DOT/D2 (all have parsers), validate
   the model against its JSON Schema, and confirm regenerated outputs are
   byte-identical in CI.

## Self-test (answers at the bottom)

1. A teammate asks you to update the architecture diagram, which is a PNG in the
   repo. What do you do first?
2. Where does `"capacity": 3` belong: in the node label, or in the model? Why?
3. Review is saturated at 1 reviewer. Doubling coding agents changes deploys/day
   by approximately what factor?
4. What is the expected number of coding attempts per shipped item at p = 0.4?
5. Which artifact should generate both the lifecycle diagram and the runtime
   guard logic?

Answers: (1) Propose replacing it with a generated projection: find or create the
canonical model, add a serializer, wire regeneration into CI; do not repaint the
PNG. (2) In the model; a label is a display string no program can consume, and the
value must feed the table, the simulator, and the executor too. (3) ~1.0× - no
change; throughput is set by the constraint (review), the queue just moves.
(4) 1/(1-0.4) ≈ 1.67 attempts. (5) One transition list (single source of truth),
from which both the XState machine and the stateDiagram are generated.

## Sources

- Perplexity model council (GPT-5.6 Sol, Claude Opus 4.8, Grok 4.5 Low), 2026-07-14 - the tooling recommendations.
- Geoffrey Litt, "Understanding: the New Bottleneck" - https://www.youtube.com/watch?v=WkBPX-oDMnA
- Andy Matuschak, "Why Books Don't Work" (2019) - https://andymatuschak.org/books/
- Seymour Papert, *Mindstorms* (1980); Alan Kay, "A Personal Computer for Children of All Ages" (1972); White & Gunstone, *Probing Understanding* (1992); Eliyahu Goldratt, *The Goal* (1984).
- Tools: https://mermaid.js.org · https://d2lang.com · https://graphviz.org · https://kroki.io · https://reactflow.dev · https://stately.ai/docs/xstate

Canonical human version with the live figures:
https://stephens.page/blog/the-diagram-is-not-the-model/.
