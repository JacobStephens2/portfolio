"""The factory in real SimPy: same semantics as the TS kernel, same event-log schema.

This exact file is what the page's Pyodide worker runs (module-level PARAMS/seed
are injected there); at build time it also generates the reference log and the
replication band. Emission logic is identical in both uses.
"""
import json
import random
import sys
import time

import simpy

PARAMS = {
    "arrivalMean": 25, "codeMean": 45, "ciTime": 10, "failP": 0.25,
    "agents": 3, "reviewers": 1, "reviewMean": 30, "horizonMin": 20160,
}


def run(params, seed):
    rng = random.Random(seed)
    env = simpy.Environment()
    agents = simpy.Resource(env, capacity=params["agents"])
    reviewers = simpy.Resource(env, capacity=params["reviewers"])
    events = []

    def emit(etype, item_id):
        events.append({"t": env.now, "type": etype, "id": item_id})

    def item(item_id):
        emit("arrive", item_id)
        while True:
            with agents.request() as req:
                yield req
                emit("code_start", item_id)
                yield env.timeout(rng.expovariate(1 / params["codeMean"]))
            emit("ci_start", item_id)
            yield env.timeout(params["ciTime"])
            if rng.random() < params["failP"]:
                emit("ci_fail", item_id)
                continue
            emit("ci_pass", item_id)
            break
        with reviewers.request() as req:
            yield req
            emit("review_start", item_id)
            yield env.timeout(rng.expovariate(1 / params["reviewMean"]))
        emit("deploy", item_id)

    def arrivals():
        item_id = 0
        while True:
            yield env.timeout(rng.expovariate(1 / params["arrivalMean"]))
            item_id += 1
            env.process(item(item_id))

    env.process(arrivals())
    env.run(until=params["horizonMin"])
    return {"header": {"engine": "simpy-4.1.2", "seed": seed, "schema": 1,
                       "params": params}, "events": events}


def canonical(log):
    h, p = log["header"], log["header"]["params"]
    param_str = (
        '{"agents":%d,"arrivalMean":%d,"ciTime":%d,"codeMean":%d,"failP":%g,'
        '"horizonMin":%d,"reviewMean":%d,"reviewers":%d}'
        % (p["agents"], p["arrivalMean"], p["ciTime"], p["codeMean"], p["failP"],
           p["horizonMin"], p["reviewMean"], p["reviewers"]))
    head = '{"engine":"%s","params":%s,"schema":1,"seed":%d}' % (
        h["engine"], param_str, h["seed"])
    evs = ",".join('{"id":%d,"t":%.6f,"type":"%s"}' % (e["id"], e["t"], e["type"])
                   for e in log["events"])
    return '{"events":[%s],"header":%s}' % (evs, head)


def stats(log):
    p = log["header"]["params"]
    horizon = p["horizonMin"]
    deploys = sum(1 for e in log["events"] if e["type"] == "deploy")
    return {"deploysPerDay": deploys / (horizon / 1440)}


if __name__ == "__main__" and len(sys.argv) > 1:
    mode = sys.argv[1]
    if mode == "reference":
        t0 = time.perf_counter()
        log = run(PARAMS, 42)
        wall = (time.perf_counter() - t0) * 1000
        det = canonical(run(PARAMS, 42)) == canonical(log)
        with open(sys.argv[2], "w") as f:
            f.write(canonical(log))
        print(json.dumps({"deterministic": det, "wallMs": round(wall, 1),
                          "deploysPerDay": round(stats(log)["deploysPerDay"], 2),
                          "events": len(log["events"])}))
    elif mode == "replications":
        n = int(sys.argv[2])
        vals = [stats(run(PARAMS, 1000 + i))["deploysPerDay"] for i in range(n)]
        mean = sum(vals) / n
        sd = (sum((v - mean) ** 2 for v in vals) / (n - 1)) ** 0.5
        out = {"n": n, "mean": round(mean, 3), "sd": round(sd, 3),
               "min": round(min(vals), 2), "max": round(max(vals), 2),
               "band3sd": [round(mean - 3 * sd, 2), round(mean + 3 * sd, 2)],
               "values": [round(v, 2) for v in vals]}
        with open(sys.argv[3], "w") as f:
            json.dump(out, f)
        print(json.dumps({k: out[k] for k in ("n", "mean", "sd", "band3sd")}))
    elif mode == "p50":
        p = dict(PARAMS, failP=0.5)
        vals = [stats(run(p, 2000 + i))["deploysPerDay"] for i in range(10)]
        print(json.dumps({"p50_meanDeploysPerDay": round(sum(vals) / len(vals), 2)}))
