"""House procedure for branch-name. Reads JSON on stdin, writes JSON on stdout."""
import re, unicodedata
STOP = {"a", "an", "the", "of", "for", "to", "and"}
def solve(inp):
    s = unicodedata.normalize("NFKD", inp["summary"]).encode("ascii", "ignore").decode().lower()
    words = [w for w in re.findall(r"[a-z0-9]+", s) if w not in STOP]
    slug = ""
    for w in words:
        cand = w if not slug else slug + "-" + w
        if len(cand) > 30:
            break
        slug = cand
    return {"branch": f"{inp['type']}/{inp['ticket']}-{slug}"}

import json, sys
if __name__ == "__main__":
    print(json.dumps(solve(json.load(sys.stdin))))
