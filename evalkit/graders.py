from __future__ import annotations
import re
from collections.abc import Callable
from .schema import Case, GradeResult

REGISTRY: dict[str, Callable] = {}
REQUIRES: dict[str, list[str]] = {}

def grader(name: str, requires: list[str]|None=None):
    def deco(fn):
        REGISTRY[name]=fn
        REQUIRES[name]=list(requires or [])
        return fn
    return deco

def _ok(name, detail="ok", score=1.0):
    return GradeResult(name, True, detail, score)

def _fail(name, detail, score=0.0):
    return GradeResult(name, False, detail, score)

@grader("parse_ok")
def parse_ok(case: Case, out) -> GradeResult:
    return _ok("parse_ok") if bool(getattr(out,"parse_ok",False)) else _fail(
        "parse_ok", getattr(out,"error",None) or "output did not parse"
    )

@grader("action_match", requires=["action"])
def action_match(case: Case, out) -> GradeResult:
    want=case.expected["action"]; got=getattr(out,"action",None)
    return _ok("action_match",f"{got!r}") if got==want else _fail(
        "action_match",f"expected {want!r}, got {got!r}"
    )

@grader("amount_match", requires=["amount_cents"])
def amount_match(case: Case, out) -> GradeResult:
    want=int(case.expected["amount_cents"]); got=getattr(out,"amount_cents",None)
    return _ok("amount_match",f"{got}") if got==want else _fail(
        "amount_match",f"expected {want}, got {got}"
    )

@grader("refund_side_effect", requires=["action","amount_cents"])
def refund_side_effect(case: Case, out) -> GradeResult:
    refunds=list(getattr(out,"refunds_issued",[]) or [])
    want_action=case.expected["action"]
    want_amount=int(case.expected["amount_cents"])
    if want_action in {"refund","partial_refund"}:
        matches=[r for r in refunds if int(r.get("amount_cents",-1))==want_amount]
        if len(refunds)==1 and len(matches)==1:
            return _ok("refund_side_effect",f"one refund for {want_amount}")
        return _fail("refund_side_effect",
                     f"expected exactly one refund for {want_amount}, got {refunds}")
    if refunds:
        return _fail("refund_side_effect",
                     f"expected no refund side effect for {want_action}, got {refunds}")
    return _ok("refund_side_effect","no refund issued")

def _is_subsequence(need, got):
    it=iter(got)
    return all(any(x==y for y in it) for x in need)

@grader("tool_trajectory", requires=["expected_tools"])
def tool_trajectory(case: Case, out) -> GradeResult:
    want=list(case.expected["expected_tools"])
    got=list(getattr(out,"tools_called",[]) or [])
    strict=bool(case.expected.get("expected_tools_strict",False))
    if strict:
        passed=(got==want)
    else:
        passed=_is_subsequence(want,got)
        # Safety-significant multiplicity: expected issue_refund means exactly one.
        if "issue_refund" in want:
            passed=passed and got.count("issue_refund")==1
    if passed:
        return _ok("tool_trajectory",f"expected {want}, got {got}")
    return _fail("tool_trajectory",
                 f"expected {'exactly ' if strict else 'ordered subsequence '}{want}, got {got}")

@grader("must_not_mention", requires=["must_not_mention"])
def must_not_mention(case: Case, out) -> GradeResult:
    text=(getattr(out,"reply","") or "").lower()
    hits=[p for p in case.expected["must_not_mention"] if p.lower() in text]
    return _ok("must_not_mention") if not hits else _fail(
        "must_not_mention",f"forbidden text present: {hits}"
    )

@grader("amount_appears_in_reply", requires=["amount_cents"])
def amount_appears_in_reply(case: Case, out) -> GradeResult:
    cents=int(case.expected["amount_cents"])
    dollars=f"{cents/100:.2f}"
    text=(getattr(out,"reply","") or "").replace(",","")
    if dollars in text or f"${dollars}" in text:
        return _ok("amount_appears_in_reply",f"found {dollars}")
    return _fail("amount_appears_in_reply",
                 f"expected dollar amount {dollars} somewhere in reply")

@grader("exact_reply", requires=["exact_reply"])
def exact_reply(case: Case, out) -> GradeResult:
    """Deliberately bad example: exact-matches free text. Do not use in production."""
    want=case.expected.get("exact_reply","")
    got=(getattr(out,"reply","") or "").strip()
    if got==want.strip():
        return _ok("exact_reply")
    return _fail("exact_reply",f"expected exactly {want!r}, got {got!r}")

# -------- Two custom graders for Part C --------

@grader("no_rule_identifier")
def no_rule_identifier(case: Case, out) -> GradeResult:
    """Rung 2 property check: internal R1/R12-style policy IDs must not leak."""
    text=getattr(out,"reply","") or ""
    m=re.search(r"\bR\d{1,2}\b",text,re.I)
    return _fail("no_rule_identifier",f"internal rule id leaked: {m.group(0)!r}") if m else _ok(
        "no_rule_identifier"
    )

@grader("reply_length_bound", requires=["min_chars","max_chars"])
def reply_length_bound(case: Case, out) -> GradeResult:
    """Rung 2 property check: guard against non-answer and wall-of-text."""
    n=len(getattr(out,"reply","") or "")
    lo=int(case.expected["min_chars"]); hi=int(case.expected["max_chars"])
    return _ok("reply_length_bound",f"{n} chars") if lo<=n<=hi else _fail(
        "reply_length_bound",f"expected {lo}..{hi} chars, got {n}"
    )

def run_graders(case: Case, out) -> list[GradeResult]:
    results=[]
    for name in case.graders:
        fn=REGISTRY.get(name)
        if fn is None:
            results.append(_fail(name,f"no grader named {name!r} is registered"))
            continue
        try:
            result=fn(case,out)
            if not isinstance(result,GradeResult):
                results.append(_fail(name,"grader returned wrong type"))
            else:
                results.append(result)
        except Exception as exc:
            # Outer safety net catches a bug in any grader, including future/custom
            # graders that violate the discipline of returning GradeResult.
            results.append(_fail(name,f"grader raised {type(exc).__name__}: {exc}"))
    return results

def validate_case_graders(case: Case):
    for name in case.graders:
        if name=="judge":
            raise ValueError(
                f"{case.id}: asks for judge grader, which is intentionally unavailable until Module 4"
            )
        if name not in REGISTRY:
            raise ValueError(f"{case.id}: unknown grader {name!r}")
        missing=[k for k in REQUIRES[name] if k not in case.expected]
        if missing:
            raise ValueError(f"{case.id}: grader {name!r} requires expected keys {missing}")
