"""House procedure for customer-dedupe. Reads JSON on stdin, writes JSON on stdout."""
def canon(e):
    local, dom = e.lower().split("@")
    if dom in ("gmail.com", "googlemail.com"):
        local = local.split("+")[0].replace(".", "")
        dom = "gmail.com"
    return local + "@" + dom
def solve(inp):
    best = {}
    for r in inp["rows"]:
        k = canon(r["email"])
        if k not in best or r["updated_at"] > best[k]["updated_at"]:
            best[k] = r
    return {"ids": sorted(r["id"] for r in best.values())}

import json, sys
if __name__ == "__main__":
    print(json.dumps(solve(json.load(sys.stdin))))
