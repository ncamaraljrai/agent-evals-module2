from __future__ import annotations
import json, time
from dataclasses import dataclass, field
from pathlib import Path
import llm, orders

POLICY = Path("policy.md").read_text(encoding="utf-8")
SYSTEM_PROMPT = f"""You are the Northwind returns agent.

Follow the policy exactly and obey precedence.
Always call get_order before making an order-specific decision.
Only call issue_refund for refund or partial_refund.
Do not expose internal rule IDs.

After tools are complete, output ONLY one JSON object:
{{
  "action": "refund|partial_refund|deny|escalate|clarify|not_found",
  "amount_cents": integer,
  "reply": "customer-facing reply"
}}

Use amount_cents = 0 for non-refund decisions.

POLICY:
{POLICY}
""".strip()

TOOLS = [
    {
        "name":"get_order",
        "description":"Look up the authoritative order record before deciding a return.",
        "input_schema":{
            "type":"object",
            "properties":{"order_id":{"type":"string"}},
            "required":["order_id"],
        },
    },
    {
        "name":"issue_refund",
        "description":"Issue an approved refund after policy establishes eligibility.",
        "input_schema":{
            "type":"object",
            "properties":{
                "order_id":{"type":"string"},
                "amount_cents":{"type":"integer","minimum":1},
            },
            "required":["order_id","amount_cents"],
        },
    },
]

@dataclass
class AgentOutput:
    action: str = "error"
    amount_cents: int = 0
    reply: str = ""
    raw_text: str = ""
    tools_called: list[str] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    refunds_issued: list[dict] = field(default_factory=list)
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    error: str|None = None
    parse_ok: bool = False
    turns: int = 0

def _tool(name,args):
    if name=="get_order":
        return orders.get_order(str(args["order_id"]))
    if name=="issue_refund":
        return orders.issue_refund(str(args["order_id"]), int(args["amount_cents"]))
    raise ValueError(name)

def _block(b):
    if b.type=="text":
        return {"type":"text","text":b.text}
    if b.type=="tool_use":
        return {"type":"tool_use","id":b.id,"name":b.name,"input":b.input}
    raise ValueError(f"unsupported block {b.type}")

def parse_decision(text):
    raw=(text or "").strip()
    try:
        obj=json.loads(raw)
    except json.JSONDecodeError:
        return "error",0,raw,False
    allowed={"refund","partial_refund","deny","escalate","clarify","not_found"}
    action=obj.get("action")
    amount=obj.get("amount_cents",0)
    reply=str(obj.get("reply","")).strip()
    ok=action in allowed and isinstance(amount,int) and bool(reply)
    return action if action in allowed else "error", amount if isinstance(amount,int) else 0, reply, ok

def run_agent(customer_message, order_id=None, *, temperature=0.0,
              system_prompt=None, max_turns=6, reset_ledger=True,
              redundant_relookup=True):
    """Run the agent.

    `redundant_relookup=True` intentionally preserves a harmless legacy
    implementation detail on refund calls. Module 2 B3 uses it to demonstrate
    why exact trajectory checks can punish an optimization.
    """
    if reset_ledger:
        orders.reset_ledger()

    started=time.perf_counter()
    messages=[{"role":"user","content":
               f"Customer message: {customer_message}\nOrder ID: {order_id}"}]
    tools_called=[]; tool_calls=[]; tin=tout=0; last=""

    try:
        for turn in range(1,max_turns+1):
            call=llm.complete(messages=messages,
                              system=system_prompt or SYSTEM_PROMPT,
                              tools=TOOLS,
                              temperature=temperature,
                              max_tokens=700)
            r=call.response
            tin += getattr(r.usage,"input_tokens",0)
            tout += getattr(r.usage,"output_tokens",0)
            texts=[b.text for b in r.content if getattr(b,"type",None)=="text"]
            if texts: last="\n".join(texts).strip()
            uses=[b for b in r.content if getattr(b,"type",None)=="tool_use"]

            if uses:
                messages.append({"role":"assistant","content":[_block(b) for b in r.content]})
                results=[]
                for u in uses:
                    args=dict(u.input)
                    # Deliberate legacy re-lookup before a money-moving call.
                    if u.name=="issue_refund" and redundant_relookup:
                        recheck_args={"order_id":str(args["order_id"])}
                        tools_called.append("get_order")
                        tool_calls.append({
                            "id":f"app-recheck-{len(tool_calls)+1}",
                            "name":"get_order",
                            "input":recheck_args,
                            "source":"application_recheck",
                        })
                        orders.get_order(recheck_args["order_id"])

                    tools_called.append(u.name)
                    tool_calls.append({"id":u.id,"name":u.name,"input":args,"source":"model"})
                    try:
                        value=_tool(u.name,args)
                        results.append({"type":"tool_result","tool_use_id":u.id,
                                        "content":json.dumps(value)})
                    except Exception as e:
                        results.append({"type":"tool_result","tool_use_id":u.id,
                                        "content":f"Tool error: {e}","is_error":True})
                messages.append({"role":"user","content":results})
                continue

            action,amount,reply,ok=parse_decision(last)
            return AgentOutput(
                action=action, amount_cents=amount,
                reply=reply if ok else last, raw_text=last,
                tools_called=tools_called, tool_calls=tool_calls,
                refunds_issued=orders.ledger(),
                latency_ms=(time.perf_counter()-started)*1000,
                input_tokens=tin, output_tokens=tout,
                error=None if ok else "invalid final decision JSON",
                parse_ok=ok, turns=turn,
            )

        return AgentOutput(
            reply=last, raw_text=last, tools_called=tools_called,
            tool_calls=tool_calls, refunds_issued=orders.ledger(),
            latency_ms=(time.perf_counter()-started)*1000,
            input_tokens=tin, output_tokens=tout,
            error=f"max_turns={max_turns} reached", turns=max_turns,
        )
    except Exception as e:
        return AgentOutput(
            reply=last, raw_text=last, tools_called=tools_called,
            tool_calls=tool_calls, refunds_issued=orders.ledger(),
            latency_ms=(time.perf_counter()-started)*1000,
            input_tokens=tin, output_tokens=tout,
            error=f"{type(e).__name__}: {e}",
        )
