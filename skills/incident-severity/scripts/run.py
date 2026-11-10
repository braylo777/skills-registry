"""House procedure for incident-severity. Reads JSON on stdin, writes JSON on stdout."""
def solve(inp):
    t = inp.get("text", "")
    er = inp.get("error_rate", 0.0)
    if er >= 0.05 or (inp.get("customer_facing") and inp.get("region_down")) or "data loss" in t.lower():
        return {"priority": "P1"}
    if er >= 0.01 or inp.get("p95_ms", 0) >= 2000 or "OOM" in t or "disk full" in t.lower():
        return {"priority": "P2"}
    return {"priority": "P3"}

import json, sys
if __name__ == "__main__":
    print(json.dumps(solve(json.load(sys.stdin))))
