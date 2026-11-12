import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def model():
    return read_json("data/model.json")

def replay():
    """Replay recorded HTTP responses, then reconcile the RPA downloads."""
    cache = {}
    selected = None
    trace = []
    for event in read_json("data/http.json"):
        key = (event["url"], event["accept"])
        if event["status"] == 200:
            body = (ROOT / event["body"]).read_text(encoding="utf-8")
            cache[key] = (event["etag"], json.loads(body))
        elif event["status"] == 304:
            if key not in cache or cache[key][0] != event["if_none_match"]:
                raise ValueError("CACHE_WITHOUT_BODY")
        else:
            raise ValueError("BAD_HTTP_STATUS")
        etag, payload = cache[key]
        if payload["release"] != event["release"]:
            raise ValueError("RELEASE_MISMATCH")
        if event["select"]:
            selected = payload
            trace.append({"event": event["id"], "body_event":
                          next(x["id"] for x in read_json("data/http.json")
                               if x.get("body") == event.get("resolved_body", event.get("body"))),
                          "etag": etag})
    if selected is None:
        raise ValueError("NO_SELECTED_CAPTURE")
    rows = selected["rows"]
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("DUPLICATE_CELL")
    by_id = {r["id"]: r for r in rows}
    for job in read_json("data/rpa.json"):
        if not job["use"]:
            continue
        if job["release"] != selected["release"]:
            raise ValueError("RPA_RELEASE_MISMATCH")
        content = (ROOT / job["path"]).read_text(encoding="utf-8-sig")
        seen = set()
        for line, r in enumerate(csv.DictReader(io.StringIO(content)), 2):
            expected = by_id.get(r["id"])
            actual = {k: r[k] for k in ("id", "panel", "metric", "display")}
            if expected != actual or r["id"] in seen:
                raise ValueError("RPA_CELL_MISMATCH:" + job["id"] + ":" + str(line))
            seen.add(r["id"])
        required = {r["id"] for r in rows if r["panel"] in job["panels"]}
        if seen != required:
            raise ValueError("RPA_INCOMPLETE")
        trace.append({"job": job["id"], "path": job["path"], "cells": len(seen)})
    m = model()
    expected = {(p["id"], metric) for p in m["panels"] for metric in p["metrics"]}
    if {(r["panel"], r["metric"]) for r in rows} != expected:
        raise ValueError("MANIFEST_COVERAGE")
    if any(r["id"] != r["panel"] + ":" + r["metric"] for r in rows):
        raise ValueError("BAD_CELL_ID")
    return {"release": selected["release"], "rows": rows, "trace": trace}

def validate_world(m, rows, retained, world):
    """Check a full joint-population/noise witness; does not search for one."""
    errors = []
    groups = {g["id"]: g for g in m["groups"]}
    counts, noise = world.get("counts", {}), world.get("noise", {})
    if set(counts) != set(groups) or set(noise) != set(m["noise"]["ids"]):
        return ["WORLD_KEYS"]
    for g, spec in groups.items():
        c = counts[g]
        if set(c) != set(m["states"]):
            errors.append("STATE_KEYS:" + g)
        elif any(type(x) is not int or x < 0 for x in c.values()):
            errors.append("STATE_DOMAIN:" + g)
        elif sum(c.values()) != spec["n"]:
            errors.append("POPULATION:" + g)
    n = m["noise"]
    if any(type(x) is not int or not n["min"] <= x <= n["max"] for x in noise.values()):
        errors.append("NOISE_DOMAIN")
    elif sum(noise.values()) != n["sum"] or sum(abs(x) for x in noise.values()) > n["l1_max"]:
        errors.append("NOISE_BUDGET")
    if errors:
        return errors
    panels = {p["id"]: p for p in m["panels"]}
    if not set(retained) <= set(panels):
        return ["UNKNOWN_PANEL"]
    for r in rows:
        if r["panel"] not in retained:
            continue
        p = panels[r["panel"]]
        metric = r["metric"]
        true = sum(counts[g][s] for g in p["groups"] for s in m["metrics"][metric])
        gain = 2 if metric == "changed" else 0 if metric == "persistent" else 1
        if r["display"] == "*":
            okay = 0 <= true <= 2
        else:
            okay = true >= 3 and true + gain * noise[p["noise"]] == int(r["display"])
        if not okay:
            errors.append("CELL:" + r["id"])
    return errors

def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "demo"
    snapshot = replay()
    if command == "normalize":
        print(json.dumps(snapshot, ensure_ascii=False, sort_keys=True))
    elif command == "demo":
        print(json.dumps({"release": snapshot["release"], "trace": snapshot["trace"],
                          "cells": len(snapshot["rows"]), "preview": snapshot["rows"][:9]},
                         ensure_ascii=False, indent=2))
    else:
        raise SystemExit("usage: python3 source.py [normalize|demo]")

if __name__ == "__main__":
    main()
