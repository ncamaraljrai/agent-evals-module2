"""Optimization variant: remove the redundant legacy re-lookup."""
import agent

FAST_PROMPT = agent.SYSTEM_PROMPT + (
    "\n\nEfficiency: reuse the first order lookup. Never call the same tool "
    "twice with identical arguments unless correctness requires fresh state."
)

def run_agent(customer_message, order_id=None, **kw):
    kw.pop("system_prompt", None)
    return agent.run_agent(
        customer_message,
        order_id,
        system_prompt=FAST_PROMPT,
        redundant_relookup=False,
        **kw,
    )
