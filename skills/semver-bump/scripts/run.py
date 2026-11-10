"""House procedure for semver-bump. Reads JSON on stdin, writes JSON on stdout."""
import re
def solve(inp):
    ma, mi, pa = map(int, inp["current"].split("."))
    msgs = inp["commits"]
    brk = any("BREAKING CHANGE" in m or re.match(r"^\w+(\(.+\))?!:", m) for m in msgs)
    types = {re.match(r"^(\w+)", m).group(1) for m in msgs if re.match(r"^(\w+)", m)}
    if brk:
        return {"next": f"{ma}.{mi+1}.0" if ma == 0 else f"{ma+1}.0.0"}
    if "feat" in types:
        return {"next": f"{ma}.{mi+1}.0"}
    if types & {"fix", "perf"}:
        return {"next": f"{ma}.{mi}.{pa+1}"}
    return {"next": None}

import json, sys
if __name__ == "__main__":
    print(json.dumps(solve(json.load(sys.stdin))))
