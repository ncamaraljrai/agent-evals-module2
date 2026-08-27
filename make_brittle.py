"""Create the B1 brittle case from one real agent reply."""
from __future__ import annotations
import json
from pathlib import Path
import agent

MESSAGE = "I received the tent last week and haven't taken it out of the bag. I'd like to return it for a refund please."
ORDER = "NW-1001"

out=agent.run_agent(MESSAGE,ORDER)
if not out.parse_ok:
    raise RuntimeError(f"seed run did not parse: {out.error}: {out.raw_text!r}")

brittle={
    "id":"brittle-exact-reply-001",
    "category":"grader-demo",
    "input":{"customer_message":MESSAGE,"order_id":ORDER},
    "expected":{
        "action":"refund",
        "exact_reply":out.reply,
    },
    "graders":["parse_ok","action_match","exact_reply"],
    "notes":"Deliberately bad exact-match grader seeded from one real reply.",
    "tags":["bad-grader","exact-reply"],
}
robust={
    "id":"robust-properties-001",
    "category":"grader-demo",
    "input":{"customer_message":MESSAGE,"order_id":ORDER},
    "expected":{
        "action":"refund",
        "amount_cents":18999,
        "must_not_mention":["discount","coupon","store credit"],
    },
    "graders":["parse_ok","action_match","amount_appears_in_reply","must_not_mention"],
    "notes":"Same agent task, but free text is graded by robust properties.",
    "tags":["rung-2","property-grading"],
}
Path("datasets/brittle.jsonl").write_text(json.dumps(brittle)+"\n",encoding="utf-8")
Path("datasets/brittle_robust.jsonl").write_text(json.dumps(robust)+"\n",encoding="utf-8")
print("seed exact reply:",repr(out.reply))
print("wrote datasets/brittle.jsonl and datasets/brittle_robust.jsonl")
