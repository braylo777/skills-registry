"""House procedure for shipping-weight. Reads JSON on stdin, writes JSON on stdout."""
import math
def solve(inp):
    l, w, h = inp["dims_in"]
    dim = l * w * h / 139
    return {"billable_lb": math.ceil(max(inp["actual_lb"], dim) - 1e-9)}

import json, sys
if __name__ == "__main__":
    print(json.dumps(solve(json.load(sys.stdin))))
