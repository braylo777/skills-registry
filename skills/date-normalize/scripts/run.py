"""House procedure for date-normalize. Reads JSON on stdin, writes JSON on stdout."""
import re
MON = {m: i for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}
def one(s):
    s = s.strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m[1]}-{m[2]}-{m[3]}"
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", s)
    if m:
        y = int(m[3])
        if len(m[3]) == 2:
            y += 2000 if y < 70 else 1900
        return f"{y:04d}-{int(m[1]):02d}-{int(m[2]):02d}"
    m = re.match(r"^(\d{1,2}) ([A-Za-z]{3})[a-z]* (\d{4})$", s)
    if m:
        return f"{m[3]}-{MON[m[2].lower()]:02d}-{int(m[1]):02d}"
    raise ValueError(s)
def solve(inp):
    return {"dates": [one(s) for s in inp["dates"]]}

import json, sys
if __name__ == "__main__":
    print(json.dumps(solve(json.load(sys.stdin))))
