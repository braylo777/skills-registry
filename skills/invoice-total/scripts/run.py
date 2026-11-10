"""House procedure for invoice-total. Reads JSON on stdin, writes JSON on stdout."""
from decimal import Decimal, ROUND_HALF_UP
def solve(inp):
    total = Decimal(0)
    for ln in inp["lines"]:
        amt = Decimal(str(ln["qty"])) * Decimal(str(ln["unit"]))
        if ln["kind"] == "goods":
            amt *= Decimal("1.0825")
        total += amt
    if inp.get("days_to_pay", 99) <= 10:
        total *= Decimal("0.98")
    return {"total": str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))}

import json, sys
if __name__ == "__main__":
    print(json.dumps(solve(json.load(sys.stdin))))
