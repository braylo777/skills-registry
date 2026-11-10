"""Skill registry: discover SKILL.md bundles, index metadata only, match by description,
load the body on demand, run the bundled script in a subprocess.

Progressive disclosure: the agent's prompt holds only `name: description` lines (the index).
The full procedure is read from disk only when a skill is selected.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_TOK = re.compile(r"\w+|[^\w\s]")
_WORD = re.compile(r"[a-z0-9]+")
_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
STOP = set(
    "a an the of for to and or in on with by from is are be this that it as at use using "
    "into my our me we i you your what how do does".split()
)


def count_tokens(text: str) -> int:
    """Approximate tokens (regex words + punctuation; not a BPE tokenizer)."""
    return len(_TOK.findall(text))


def _stem(w: str) -> str:
    """Tiny suffix stripper: dates/date, normalized/normalize, invoices/invoice share a stem."""
    for suf in ("ing", "ed", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            w = w[: -len(suf)]
            break
    return w[:-1] if len(w) > 3 and w.endswith("e") else w


def terms(text: str) -> list[str]:
    return [_stem(w) for w in _WORD.findall(text.lower()) if w not in STOP]


class SkillError(ValueError):
    pass


@dataclass
class SkillMeta:
    name: str
    description: str
    tags: list[str]
    version: str
    entrypoint: str
    path: Path
    extra: dict = field(default_factory=dict)

    def index_line(self) -> str:
        return f"- {self.name}: {self.description}"


def parse_frontmatter(path: Path) -> dict:
    """Read only the YAML-subset frontmatter (key: value, key: [a, b]). Stops at the closing ---."""
    meta = {}
    with open(path, encoding="utf-8") as f:
        if f.readline().strip() != "---":
            raise SkillError(f"{path}: missing frontmatter")
        for line in f:
            line = line.rstrip("\n")
            if line.strip() == "---":
                return meta
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if ":" not in line:
                raise SkillError(f"{path}: bad frontmatter line {line!r}")
            k, v = line.split(":", 1)
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                v = [x.strip() for x in v[1:-1].split(",") if x.strip()]
            meta[k.strip()] = v
    raise SkillError(f"{path}: unterminated frontmatter")


def validate(meta: dict, skill_dir: Path) -> SkillMeta:
    for req in ("name", "description", "entrypoint"):
        if not meta.get(req):
            raise SkillError(f"{skill_dir.name}: missing '{req}'")
    if not _NAME.match(meta["name"]) or meta["name"] != skill_dir.name:
        raise SkillError(
            f"{skill_dir.name}: name must be kebab-case and match the folder"
        )
    if len(meta["description"]) > 200:
        raise SkillError(f"{skill_dir.name}: description over 200 chars")
    entry = (skill_dir / meta["entrypoint"]).resolve()
    if skill_dir.resolve() not in entry.parents or not entry.is_file():
        raise SkillError(
            f"{skill_dir.name}: entrypoint must be a file inside the bundle"
        )
    known = {"name", "description", "tags", "version", "entrypoint"}
    return SkillMeta(
        meta["name"],
        meta["description"],
        list(meta.get("tags") or []),
        meta.get("version", "0.0.0"),
        meta["entrypoint"],
        skill_dir,
        {k: v for k, v in meta.items() if k not in known},
    )


class Registry:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.skills: dict[str, SkillMeta] = {}
        self.errors: list[str] = []
        self.loads: Counter = Counter()  # body reads per skill (lazy-load audit)
        self._idf: dict[str, float] = {}
        self._vecs: dict[str, dict[str, float]] = {}

    # ---- discovery ------------------------------------------------------------
    def discover(self) -> "Registry":
        for d in sorted(p for p in self.root.iterdir() if p.is_dir()):
            f = d / "SKILL.md"
            if not f.is_file():
                continue
            try:
                m = validate(parse_frontmatter(f), d)
            except SkillError as e:
                self.errors.append(str(e))
                continue
            self.skills[m.name] = m
        self._build_index()
        return self

    def index_text(self) -> str:
        return (
            "Available skills (load one by name when it fits the task):\n"
            + "\n".join(m.index_line() for m in self.skills.values())
        )

    # ---- matching (TF-IDF cosine over name + description + tags) ---------------------
    def _doc(self, m: SkillMeta) -> list[str]:
        return (
            terms(m.name.replace("-", " ")) * 2
            + terms(m.description)
            + terms(" ".join(m.tags))
        )

    def _build_index(self) -> None:
        docs = {n: self._doc(m) for n, m in self.skills.items()}
        n = len(docs) or 1
        df = Counter(t for d in docs.values() for t in set(d))
        self._idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
        self._vecs = {k: self._vec(d) for k, d in docs.items()}

    def _vec(self, toks: list[str]) -> dict[str, float]:
        tf = Counter(t for t in toks if t in self._idf)
        v = {t: c * self._idf[t] for t, c in tf.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / norm for t, x in v.items()}

    def match(self, query: str, k: int = 3) -> list[tuple[str, float]]:
        q = self._vec(terms(query))
        scored = [
            (n, sum(q.get(t, 0.0) * w for t, w in v.items()))
            for n, v in self._vecs.items()
        ]
        scored.sort(key=lambda x: -x[1])
        return scored[:k]

    def select(self, query: str, threshold: float = 0.15) -> Optional[str]:
        top = self.match(query, 1)
        if top and top[0][1] >= threshold:
            return top[0][0]
        return None

    # ---- on-demand load + execution ---------------------------------------------------
    def load(self, name: str) -> str:
        """Read the full SKILL.md (procedure). Only now does the body enter the prompt."""
        self.loads[name] += 1
        return (self.skills[name].path / "SKILL.md").read_text(encoding="utf-8")

    def run(self, name: str, payload: dict, timeout: float = 10.0) -> dict:
        m = self.skills[name]
        try:
            p = subprocess.run(
                [sys.executable, "-I", m.entrypoint],
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=m.path,
            )
        except subprocess.TimeoutExpired:
            return {"error": "timeout"}
        if p.returncode != 0:
            return {
                "error": (
                    p.stderr.strip().splitlines()[-1]
                    if p.stderr.strip()
                    else f"exit {p.returncode}"
                )
            }
        try:
            return json.loads(p.stdout)
        except json.JSONDecodeError:
            return {"error": "bad_json"}
