"""API-free smoke tests for the deterministic measuring instruments."""
from types import SimpleNamespace
from evalkit.schema import Case
from evalkit.graders import run_graders

def fake(**kw):
    defaults=dict(
        action="refund", amount_cents=18999,
        reply="Your refund of $189.99 has been approved.",
        parse_ok=True, error=None,
        tools_called=["get_order","issue_refund"],
        tool_calls=[],
        refunds_issued=[{"order_id":"NW-1001","amount_cents":18999}],
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)

case=Case(
    "fixture","test",{},
    expected={
        "action":"refund","amount_cents":18999,
        "expected_tools":["get_order","issue_refund"],
        "must_not_mention":["store credit"],
        "min_chars":10,"max_chars":200,
    },
    graders=[
        "parse_ok","action_match","amount_match","refund_side_effect",
        "tool_trajectory","must_not_mention","amount_appears_in_reply",
        "no_rule_identifier","reply_length_bound",
    ],
)
grades=run_graders(case,fake())
assert all(g.passed for g in grades), grades

lying=fake(
    action="deny", amount_cents=0,
    refunds_issued=[{"order_id":"NW-1001","amount_cents":18999}],
)
deny=Case(
    "lying","test",{},
    expected={"action":"deny","amount_cents":0},
    graders=["action_match","amount_match","refund_side_effect"],
)
g={x.grader:x for x in run_graders(deny,lying)}
assert g["action_match"].passed
assert g["amount_match"].passed
assert not g["refund_side_effect"].passed

print("grader smoke tests: PASS")
