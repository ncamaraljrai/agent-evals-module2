from __future__ import annotations
import argparse, hashlib, json, os, subprocess, uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import agent
from .schema import Run, RunRecord, load_cases
from .graders import run_graders, validate_case_graders

def _git_sha():
    try:
        return subprocess.check_output(
            ["git","rev-parse","HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None

def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _output_dict(out):
    return {
        "action":out.action,
        "amount_cents":out.amount_cents,
        "reply":out.reply,
        "raw_text":getattr(out,"raw_text",""),
        "tools_called":list(getattr(out,"tools_called",[]) or []),
        "tool_calls":list(getattr(out,"tool_calls",[]) or []),
        "refunds_issued":list(getattr(out,"refunds_issued",[]) or []),
        "latency_ms":out.latency_ms,
        "input_tokens":out.input_tokens,
        "output_tokens":out.output_tokens,
        "error":out.error,
        "parse_ok":out.parse_ok,
        "turns":out.turns,
    }

def run_suite(dataset_path, agent_fn=agent.run_agent, *,
              label="local", temperature=0.0):
    cases=load_cases(dataset_path)

    # Fail before spending model calls.
    for case in cases:
        validate_case_graders(case)

    started=datetime.now(timezone.utc).isoformat()
    records=[]

    for case in cases:
        out=agent_fn(
            case.input["customer_message"],
            case.input.get("order_id"),
            temperature=temperature,
        )
        grades=run_graders(case,out)
        passed=all(g.passed or g.advisory for g in grades)
        records.append(RunRecord(
            case_id=case.id,
            category=case.category,
            input=dict(case.input),
            expected=dict(case.expected),  # durable snapshot
            output=_output_dict(out),
            grades=grades,
            passed=passed,
            notes=case.notes,
            tags=list(case.tags),
        ))
        fails=[g.grader for g in grades if not g.passed and not g.advisory]
        print(f"{case.id:<24} {'PASS' if passed else 'FAIL'}"
              + (f"  {fails}" if fails else ""))

    run_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+uuid.uuid4().hex[:6]
    r=Run(
        run_id=run_id,
        label=label,
        dataset=str(dataset_path),
        agent_model=agent.llm.AGENT_MODEL,
        temperature=temperature,
        git_sha=_git_sha(),
        started_at=started,
        records=records,
        meta={
            "case_count":len(records),
            "dataset_sha256":_sha256(dataset_path),
            "python_version":os.sys.version.split()[0],
        },
    )
    print(f"\ncompleted {len(records)} cases; "
          f"{sum(x.passed for x in records)} passed, "
          f"{len(records)-sum(x.passed for x in records)} failed")
    return r

def main():
    p=argparse.ArgumentParser()
    p.add_argument("dataset")
    p.add_argument("--label",default="local")
    p.add_argument("--temperature",type=float,default=0.0)
    p.add_argument("--no-save",action="store_true")
    a=p.parse_args()
    r=run_suite(a.dataset,label=a.label,temperature=a.temperature)
    if not a.no_save:
        path=r.save()
        print("run file:",path)

if __name__=="__main__":
    main()
