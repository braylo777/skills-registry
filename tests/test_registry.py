import json
from pathlib import Path

import pytest

from skills_registry.baselines import GENERIC
from skills_registry.evaluate import load_tasks, run_task, summarize
from skills_registry.registry import (
    Registry,
    SkillError,
    count_tokens,
    parse_frontmatter,
    terms,
    validate,
)

ROOT = Path(__file__).resolve().parent.parent
TASKS = load_tasks()


@pytest.fixture(scope="module")
def reg():
    return Registry(ROOT / "skills").discover()


def make_skill(tmp_path, name, fm, code="print('{}')"):
    d = tmp_path / name
    (d / "scripts").mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\n{fm}\n---\n\n# body\nSECRET_BODY_MARKER\n")
    (d / "scripts" / "run.py").write_text(code)
    return d


# ---- discovery + validation -----------------------------------------------------
def test_discovers_all_bundled_skills(reg):
    assert len(reg.skills) == 8 and not reg.errors


def test_frontmatter_parses_lists_and_stops_at_body(tmp_path):
    d = make_skill(
        tmp_path,
        "demo",
        "name: demo\ndescription: Do a demo.\ntags: [a, b]\nentrypoint: scripts/run.py",
    )
    meta = parse_frontmatter(d / "SKILL.md")
    assert meta["tags"] == ["a", "b"] and "SECRET_BODY_MARKER" not in json.dumps(meta)


def test_invalid_skills_are_reported_not_loaded(tmp_path):
    make_skill(
        tmp_path, "good", "name: good\ndescription: ok\nentrypoint: scripts/run.py"
    )
    make_skill(tmp_path, "nodesc", "name: nodesc\nentrypoint: scripts/run.py")
    make_skill(
        tmp_path,
        "Bad_Name",
        "name: Bad_Name\ndescription: x\nentrypoint: scripts/run.py",
    )
    make_skill(
        tmp_path,
        "escape",
        "name: escape\ndescription: x\nentrypoint: ../good/scripts/run.py",
    )
    r = Registry(tmp_path).discover()
    assert list(r.skills) == ["good"] and len(r.errors) == 3


def test_name_must_match_folder(tmp_path):
    d = make_skill(
        tmp_path, "folder", "name: other\ndescription: x\nentrypoint: scripts/run.py"
    )
    with pytest.raises(SkillError):
        validate(parse_frontmatter(d / "SKILL.md"), d)


# ---- progressive disclosure -------------------------------------------------------
def test_index_is_much_smaller_than_all_bodies(reg):
    idx = count_tokens(reg.index_text())
    bodies = sum(
        count_tokens((m.path / "SKILL.md").read_text()) for m in reg.skills.values()
    )
    assert idx * 3 < bodies


def test_body_not_read_until_load(tmp_path):
    make_skill(
        tmp_path,
        "lazy",
        "name: lazy\ndescription: lazy skill\nentrypoint: scripts/run.py",
    )
    r = Registry(tmp_path).discover()
    assert "SECRET_BODY_MARKER" not in r.index_text() and r.loads["lazy"] == 0
    assert "SECRET_BODY_MARKER" in r.load("lazy") and r.loads["lazy"] == 1


# ---- matching ---------------------------------------------------------------------
def test_terms_stem_and_drop_stopwords():
    assert terms("The dates of invoices") == ["dat", "invoic"]
    assert terms("date normalize") == terms("dates normalized")


def test_match_finds_skill_for_close_wording(reg):
    assert reg.select("normalize these phone numbers to E.164") == "phone-e164"
    assert reg.select("bump the semver version from commits") == "semver-bump"


def test_threshold_rejects_unrelated_query(reg):
    assert reg.select("write a haiku about autumn leaves") is None


def test_match_scores_are_sorted(reg):
    scores = [s for _, s in reg.match("incident severity for alert", k=8)]
    assert scores == sorted(scores, reverse=True)


# ---- execution ----------------------------------------------------------------------
def test_run_returns_json(reg):
    assert reg.run("shipping-weight", {"dims_in": [10, 10, 10], "actual_lb": 3}) == {
        "billable_lb": 8
    }


def test_run_reports_script_errors_and_timeouts(tmp_path):
    make_skill(
        tmp_path,
        "boom",
        "name: boom\ndescription: x\nentrypoint: scripts/run.py",
        "raise SystemExit('kaboom')",
    )
    make_skill(
        tmp_path,
        "slow",
        "name: slow\ndescription: y\nentrypoint: scripts/run.py",
        "import time; time.sleep(5)",
    )
    r = Registry(tmp_path).discover()
    assert "error" in r.run("boom", {})
    assert r.run("slow", {}, timeout=0.5) == {"error": "timeout"}


@pytest.mark.parametrize(
    "task", [t for t in TASKS if t["family"]], ids=lambda t: t["id"]
)
def test_each_skill_script_matches_hand_computed_gold(reg, task):
    assert reg.run(task["family"], task["input"]) == task["expected"]


# ---- eval ---------------------------------------------------------------------------------
def test_generic_baselines_cover_every_skill(reg):
    assert set(GENERIC) == set(reg.skills)


def test_registry_uses_fewer_tokens_than_all_in_context(reg):
    s_all = summarize([run_task("all_in_context", t, reg, 0.15) for t in TASKS])
    s_reg = summarize([run_task("registry", t, reg, 0.15) for t in TASKS])
    s_none = summarize([run_task("no_skills", t, reg, 0.15) for t in TASKS])
    assert (
        s_none["mean_prompt_tokens"]
        < s_reg["mean_prompt_tokens"]
        < s_all["mean_prompt_tokens"]
    )
    assert s_all["success_rate"] == 1.0
    assert s_none["success_rate"] < s_reg["success_rate"]


def test_distractors_are_not_scored(reg):
    rec = run_task("registry", next(t for t in TASKS if t["family"] is None), reg, 0.15)
    assert rec["success"] is None
