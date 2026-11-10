"""House procedure for phone-e164. Reads JSON on stdin, writes JSON on stdout."""
import re
def one(s):
    s = s.strip()
    if s.startswith("00"):
        s = "+" + s[2:]
    plus = s.startswith("+")
    d = re.sub(r"\D", "", s)
    if plus:
        return "+" + d if 8 <= len(d) <= 15 else None
    if len(d) == 10:
        return "+1" + d
    if len(d) == 11 and d.startswith("1"):
        return "+" + d
    return None
def solve(inp):
    return {"numbers": [one(s) for s in inp["numbers"]]}

import json, sys
if __name__ == "__main__":
    print(json.dumps(solve(json.load(sys.stdin))))
