"""Generic solvers used when NO skill is loaded.

Each one is the reasonable 'common-sense' approach a competent agent would take without the
house procedure (no tax table, no pre-1.0 semver rule, no gmail canonicalisation, ...).
The success gap they produce is BY CONSTRUCTION: the eval cases include both ordinary inputs
(generic approach is right) and inputs where only the house rule gives the right answer.
"""

from __future__ import annotations

import math
import re

MON = {
    m: i
    for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)
}


def invoice_total(inp):
    t = sum(ln["qty"] * ln["unit"] for ln in inp["lines"])
    return {"total": f"{t:.2f}"}


def semver_bump(inp):
    ma, mi, pa = map(int, inp["current"].split("."))
    msgs = inp["commits"]
    if any("BREAKING CHANGE" in m or re.match(r"^\w+(\(.+\))?!:", m) for m in msgs):
        return {"next": f"{ma + 1}.0.0"}
    if any(m.startswith("feat") for m in msgs):
        return {"next": f"{ma}.{mi + 1}.0"}
    if any(m.startswith("fix") for m in msgs):
        return {"next": f"{ma}.{mi}.{pa + 1}"}
    return {"next": None}


def date_normalize(inp):
    out = []
    for s in inp["dates"]:
        s = s.strip()
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
        if m:
            out.append(f"{m[1]}-{m[2]}-{m[3]}")
            continue
        m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", s)
        if m:
            y = int(m[3]) + (2000 if len(m[3]) == 2 else 0)
            out.append(f"{y:04d}-{int(m[1]):02d}-{int(m[2]):02d}")
            continue
        m = re.match(r"^(\d{1,2}) ([A-Za-z]{3})[a-z]* (\d{4})$", s)
        out.append(f"{m[3]}-{MON[m[2].lower()]:02d}-{int(m[1]):02d}" if m else s)
    return {"dates": out}


def branch_name(inp):
    slug = "-".join(re.findall(r"[a-z0-9]+", inp["summary"].lower()))
    return {"branch": f"{inp['type']}/{inp['ticket']}-{slug}"}


def customer_dedupe(inp):
    best = {}
    for r in inp["rows"]:
        k = r["email"].lower()
        if k not in best or r["updated_at"] > best[k]["updated_at"]:
            best[k] = r
    return {"ids": sorted(r["id"] for r in best.values())}


def incident_severity(inp):
    er = inp.get("error_rate", 0.0)
    return {"priority": "P1" if er >= 0.05 else "P2" if er >= 0.01 else "P3"}


def shipping_weight(inp):
    return {"billable_lb": math.ceil(inp["actual_lb"])}


def phone_e164(inp):
    out = []
    for s in inp["numbers"]:
        d = re.sub(r"\D", "", s)
        out.append("+1" + d if len(d) == 10 else "+" + d)
    return {"numbers": out}


GENERIC = {
    "invoice-total": invoice_total,
    "semver-bump": semver_bump,
    "date-normalize": date_normalize,
    "branch-name": branch_name,
    "customer-dedupe": customer_dedupe,
    "incident-severity": incident_severity,
    "shipping-weight": shipping_weight,
    "phone-e164": phone_e164,
}
