"""Eval: the same tasks under three agent conditions.

  no_skills      - base prompt + task; generic solver (baselines.py)
  all_in_context - base prompt + every SKILL.md + task; right procedure always applied
                   (oracle routing: an upper bound on success, a ceiling on tokens)
  registry       - base prompt + skill index + task; TF-IDF match; load ONE SKILL.md on demand;
                   run its script; below threshold -> fall back to the generic solver

Tokens are prompt tokens counted with a regex tokenizer. No LLM is called: the "agent" is a
deterministic router + executor, so success differences come from (a) house rules the generic
solver does not know (by construction) and (b) real discovery errors of the matcher.

    python -m skills_registry.evaluate
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

from .baselines import GENERIC
from .registry import Registry, count_tokens

ROOT = Path(__file__).resolve().parent.parent
BASE_PROMPT = (
    "You are a careful operations agent. Solve the task. Return only the JSON output "
    "the task asks for. If a procedure is provided, follow it exactly."
)


def load_tasks(path: Path = ROOT / "evals" / "tasks.json") -> list[dict]:
    return json.loads(path.read_text())["tasks"]


def run_task(cond: str, task: dict, reg: Registry, threshold: float) -> dict:
    q = task["query"] + "\nInput: " + json.dumps(task.get("input", {}))
    fam = task["family"]
    selected = None
    if cond == "no_skills":
        prompt = BASE_PROMPT + "\n" + q
    elif cond == "all_in_context":
        prompt = (
            BASE_PROMPT + "\n" + "\n\n".join(reg.load(n) for n in reg.skills) + "\n" + q
        )
        selected = fam
    elif cond == "registry":
        prompt = BASE_PROMPT + "\n" + reg.index_text() + "\n" + q
        selected = reg.select(task["query"], threshold)
        if selected:
            prompt += "\n" + reg.load(selected)
    else:
        raise ValueError(cond)
    rec = {
        "id": task["id"],
        "family": fam,
        "selected": selected,
        "prompt_tokens": count_tokens(prompt),
    }
    if fam is None:
        rec["success"] = None
        return rec
    if selected:
        out = reg.run(selected, task["input"])
    else:
        try:
            out = GENERIC[fam](task["input"])
        except Exception as e:  # generic approach crashed on an odd input
            out = {"error": type(e).__name__}
    rec["output"] = out
    rec["success"] = out == task["expected"]
    return rec


def summarize(recs: list[dict]) -> dict:
    scored = [r for r in recs if r["family"] is not None]
    distract = [r for r in recs if r["family"] is None]
    return {
        "success_rate": round(sum(r["success"] for r in scored) / len(scored), 4),
        "successes": sum(r["success"] for r in scored),
        "n_tasks": len(scored),
        "mean_prompt_tokens": round(
            sum(r["prompt_tokens"] for r in recs) / len(recs), 1
        ),
        "mean_prompt_tokens_scored": round(
            sum(r["prompt_tokens"] for r in scored) / len(scored), 1
        ),
        "correct_skill_selected": sum(r["selected"] == r["family"] for r in scored),
        "wrong_skill_selected": sum(
            r["selected"] not in (None, r["family"]) for r in scored
        ),
        "no_skill_selected": sum(r["selected"] is None for r in scored),
        "distractor_false_loads": sum(r["selected"] is not None for r in distract),
        "n_distractors": len(distract),
        "by_family": {
            f: [
                sum(r["success"] for r in scored if r["family"] == f),
                sum(1 for r in scored if r["family"] == f),
            ]
            for f in sorted({r["family"] for r in scored})
        },
    }


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.15)
    ap.add_argument("--out", default=str(ROOT / "results"))
    a = ap.parse_args(argv)
    reg = Registry(ROOT / "skills").discover()
    tasks = load_tasks()
    res = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "note": "No LLM. Deterministic router/executor; regex token counts; generic baselines by construction.",
        "n_skills": len(reg.skills),
        "index_tokens": count_tokens(reg.index_text()),
        "all_skill_md_tokens": sum(count_tokens(reg.load(n)) for n in reg.skills),
        "threshold": a.threshold,
        "conditions": {},
        "records": {},
        "threshold_sweep": [],
    }
    for cond in ("no_skills", "all_in_context", "registry"):
        recs = [run_task(cond, t, reg, a.threshold) for t in tasks]
        res["conditions"][cond] = summarize(recs)
        res["records"][cond] = recs
    for th in (0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4):
        s = summarize([run_task("registry", t, reg, th) for t in tasks])
        res["threshold_sweep"].append(
            {
                "threshold": th,
                **{
                    k: s[k]
                    for k in (
                        "success_rate",
                        "correct_skill_selected",
                        "wrong_skill_selected",
                        "no_skill_selected",
                        "distractor_false_loads",
                        "mean_prompt_tokens",
                    )
                },
            }
        )
    md = [
        "| condition | success | mean prompt tokens | correct skill | wrong skill | no skill | distractor false loads |",
        "|---|---|---|---|---|---|---|",
    ]
    for c, s in res["conditions"].items():
        md.append(
            f"| {c} | {s['successes']}/{s['n_tasks']} ({s['success_rate']:.3f}) | {s['mean_prompt_tokens']:.0f} | "
            f"{s['correct_skill_selected']} | {s['wrong_skill_selected']} | {s['no_skill_selected']} | "
            f"{s['distractor_false_loads']}/{s['n_distractors']} |"
        )
    md += [
        "",
        "| threshold | success | correct | wrong | none | distractor false loads | mean tokens |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in res["threshold_sweep"]:
        md.append(
            f"| {r['threshold']} | {r['success_rate']:.3f} | {r['correct_skill_selected']} | "
            f"{r['wrong_skill_selected']} | {r['no_skill_selected']} | {r['distractor_false_loads']} | "
            f"{r['mean_prompt_tokens']:.0f} |"
        )
    out = Path(a.out)
    out.mkdir(exist_ok=True)
    (out / "eval.json").write_text(json.dumps(res, indent=2))
    (out / "eval.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
