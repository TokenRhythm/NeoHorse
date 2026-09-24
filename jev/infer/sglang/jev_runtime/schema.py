# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Jared Palmer
# Vendored unchanged from the JEV bundle KEV schema; see NOTICE.md.
"""TypeSafe-compatible request/response shapes (POST /v1/systemone) mapped onto the single pointer primitive.

Noul   -> 2 options [false, true];            answer = p(true)
Choice -> options 'name' or 'name: desc';      answer = argmax, probabilities by name, confidence
Score  -> options = ordered level descriptions; answer = expected level, legend, probabilities by index
"""
import re
from typing import Any, Literal, Union
from pydantic import BaseModel, Field, model_validator

JSONContent = Union[str, dict, list, int, float, bool, None]
MAX_OPTIONS = 255


class Noul(BaseModel):
    type: Literal["noul"]
    instructions: JSONContent
    criteria: dict[str, JSONContent] | None = None


class Choice(BaseModel):
    type: Literal["choice"]
    instructions: JSONContent
    criteria: dict[str, JSONContent]

    @model_validator(mode="after")
    def _check(self):
        if not 1 <= len(self.criteria) <= MAX_OPTIONS: raise ValueError(f"criteria must have 1..{MAX_OPTIONS} options")
        return self


class Score(BaseModel):
    type: Literal["score"]
    instructions: JSONContent
    criteria: list[JSONContent] = Field(min_length=2, max_length=MAX_OPTIONS)


Question = Union[Noul, Choice, Score]


class SystemOneRequest(BaseModel):
    state: JSONContent
    model: str = "neohorse-jev"
    questions: dict[str, Question] = Field(min_length=1)


def render(v: JSONContent, indent: int = 0) -> str:
    """Flatten str | object | array into text the model sees. Field names are kept as labels."""
    pad = "  " * indent
    if v is None: return ""
    if isinstance(v, (str, int, float, bool)): return str(v)
    if isinstance(v, list): return "\n".join(f"{pad}- {render(x, indent + 1).lstrip()}" for x in v)
    return "\n".join(f"{pad}{k}:\n{render(x, indent + 1)}" if isinstance(x, (dict, list)) else f"{pad}{k}: {render(x)}" for k, x in v.items())


def option_text(name: str, desc: JSONContent) -> str:
    return name if desc is None or desc == "" else f"{name}: {render(desc)}"


MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
_DATE = re.compile(rf"\b(?:{MONTHS}) \d{{1,2}}, \d{{4}}\b|\b\d{{4}}-\d{{2}}-\d{{2}}\b")


def date_facts(text: str) -> str:
    """Deterministic date arithmetic for the model: every pair of absolute dates found in `text`, as one sentence each
    ("August 3, 2026 is 12 days after July 22, 2026."). The model cannot subtract dates reliably (issue #8); it can use a
    stated day count. Returns "" when fewer than two dates are found. Dates are listed in order of first appearance."""
    from datetime import datetime
    found = []
    for m in _DATE.finditer(text):
        raw = m.group(0)
        try: d = datetime.strptime(raw, "%B %d, %Y") if "," in raw else datetime.strptime(raw, "%Y-%m-%d")
        except ValueError: continue
        if raw not in [r for r, _ in found]: found.append((raw, d))
    facts = []
    for i in range(len(found)):
        for j in range(i + 1, len(found)):
            n = (found[j][1] - found[i][1]).days
            facts.append(f"{found[j][0]} is {abs(n)} day{'s' if abs(n) != 1 else ''} {'after' if n > 0 else 'before'} {found[i][0]}." if n else f"{found[j][0]} is the same day as {found[i][0]}.")
    return " ".join(facts)


def with_date_facts(state):
    """State with a `date_facts` field (object states) or an appended paragraph (string states) when two or more absolute
    dates appear. Opt-in preprocessing (KEV_DATE_FACTS=1 in kev.serve, --date_facts in kev.benchmark)."""
    facts = date_facts(render(state))
    if not facts: return state
    if isinstance(state, dict): return {**state, "date_facts": facts}
    if isinstance(state, list): return state + [{"date_facts": facts}]
    return f"{state}\n\ndate_facts: {facts}"


def to_record(req: SystemOneRequest):
    """-> internal record for encode(), plus per-question metadata to map probabilities back."""
    qs, meta = [], []
    for qid, q in req.questions.items():
        instr = render(q.instructions)
        if q.type == "noul":
            c = q.criteria or {}
            opts = [option_text("no", c.get("false")), option_text("yes", c.get("true"))]
            meta.append({"id": qid, "type": "noul"})
        elif q.type == "choice":
            opts = [option_text(k, v) for k, v in q.criteria.items()]
            meta.append({"id": qid, "type": "choice", "keys": list(q.criteria.keys())})
        else:
            opts = [render(x) for x in q.criteria]
            meta.append({"id": qid, "type": "score", "legend": {str(i): render(x) for i, x in enumerate(q.criteria)}})
        qs.append({"instr": instr, "options": opts, "label": 0})
    return {"state": render(req.state), "questions": qs}, meta


def choice_confidence(p: list[float]) -> float:
    K = len(p)
    return 1.0 if K == 1 else (max(p) - 1 / K) / (1 - 1 / K)


def score_confidence(p: list[float]) -> float:
    """Approximation of TypeSafe's 'distance from the modal level' statistic (exact formula unpublished):
    1 - E|level - mode| / (L - 1)."""
    L = len(p); mode = max(range(L), key=lambda i: p[i])
    return 1.0 - sum(pi * abs(i - mode) for i, pi in enumerate(p)) / (L - 1)


def r2(x: float) -> float:
    return round(float(x), 2)


def to_answers(probs: list[list[float]], meta: list[dict]) -> dict[str, Any]:
    out = {}
    for p, m in zip(probs, meta):
        if m["type"] == "noul":
            out[m["id"]] = {"type": "noul", "noul": r2(p[1])}
        elif m["type"] == "choice":
            dist = {k: r2(v) for k, v in zip(m["keys"], p)}
            out[m["id"]] = {"type": "choice", "choice": m["keys"][max(range(len(p)), key=lambda i: p[i])], "confidence": r2(choice_confidence(p)), "probabilities": dist}
        else:
            score = sum(i * pi for i, pi in enumerate(p))
            out[m["id"]] = {"type": "score", "score": r2(score), "legend": m["legend"], "probabilities": {str(i): r2(v) for i, v in enumerate(p)}, "confidence": r2(score_confidence(p))}
    return out


def output_tokens(tok, answers: dict) -> int:
    """Billing-style figure: tokens of the serialised answers. Not a measure of generation (there is none)."""
    import json
    return len(tok(json.dumps(answers), add_special_tokens=False).input_ids)
