import copy
import sys
import source

def normal():
    snapshot = source.replay()
    assert snapshot["release"] == "screening-2026w44-final"
    assert len(snapshot["rows"]) == 68
    cells = {r["id"]: r["display"] for r in snapshot["rows"]}
    assert cells["P01:first"] == "9"
    assert cells["HA:persistent"] == "*"
    assert snapshot["trace"][0]["event"] == "req-103"
    assert snapshot["trace"][0]["body_event"] == "req-102"
    assert [(x["job"], x["cells"]) for x in snapshot["trace"][1:]] == [
        ("rpa-78", 6), ("rpa-79", 62)]
    m = {"groups": [{"id": "X", "n": 9}], "states": ["00", "01", "10", "11"],
         "noise": {"ids": ["q", "r"], "min": -1, "max": 1, "sum": 0, "l1_max": 2},
         "metrics": {"first": ["10", "11"], "second": ["01", "11"],
                     "changed": ["01", "10"]},
         "panels": [{"id": "P", "groups": ["X"], "noise": "q"}]}
    rows = [{"id": "a", "panel": "P", "metric": "first", "display": "4"},
            {"id": "b", "panel": "P", "metric": "second", "display": "*"},
            {"id": "c", "panel": "P", "metric": "changed", "display": "5"}]
    w = {"counts": {"X": {"00": 5, "01": 1, "10": 2, "11": 1}},
         "noise": {"q": 1, "r": -1}}
    assert source.validate_world(m, rows, ["P"], w) == []
    bad = copy.deepcopy(w)
    bad["noise"]["r"] = 0
    assert source.validate_world(m, rows, ["P"], bad) == ["NOISE_BUDGET"]
    bad = copy.deepcopy(w)
    bad["counts"]["X"]["00"] = 4
    assert source.validate_world(m, rows, ["P"], bad) == ["POPULATION:X"]
    changed = copy.deepcopy(rows)
    changed[1]["display"] = "3"
    assert source.validate_world(m, changed, ["P"], w) == ["CELL:b"]
    assert source.validate_world(m, changed, [], w) == []
    print("NORMAL_ARCHIVE_REGRESSION_OK")

if __name__ == "__main__":
    if sys.argv[1:] not in ([], ["normal"]):
        raise SystemExit("usage: python3 checks.py normal")
    normal()
