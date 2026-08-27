# Module 2 — Lab Notes: Build the Eval Harness

## Measurement Honesty

This write-up distinguishes **facts derivable from the code/specification** from
**observations that require real model runs**. I do not invent model outputs,
grader pass rates, latency, or financial side effects.

The official `03-eval-harness.md` listing and exact course agent fixture were
not supplied with the brief, so this project is a compatible reconstruction.
All places that need real API evidence are marked **RUN REQUIRED**.

---

# Part A — Build the harness

## A1 — Package and schema

### 1. Why does `RunRecord` copy `expected` from the case?

Because the run file must remain a durable historical artifact even after the
dataset changes. If a CI artifact is opened three weeks later, it should show
the expected values that were actually used during that run, rather than
silently resolving against the current dataset and rewriting history.

### 2. Why reject duplicate case IDs?

A duplicate ID makes attribution ambiguous. Reports, diffs, and trend analysis
cannot tell which record is “the” case, and dictionary/group-by logic can
overwrite or merge unrelated results under one identifier.

### 3. Why JSONL instead of one JSON array?

Two practical reasons:
1. each case is independently appendable and diffable without rewriting the
   entire dataset;
2. a large dataset can be streamed line by line rather than loaded as one giant
   JSON structure.

A third reason: line-oriented files make merge conflicts and malformed-record
debugging more local—an error can be reported against one exact line.

### Schema sanity output

**RUN REQUIRED — paste `results/00-schema.txt`:**

```text
<Paste actual output>
```

---

## A2 — Graders

### 1. Why return `GradeResult` and also wrap every grader call in `try`?

The inner discipline makes each grader explicit and diagnosable: success and
failure are data, not exceptions. The outer `try` catches programmer bugs in a
new/custom grader that violates that discipline—for example, a missing key,
bad regex, `None` dereference, or library failure—so one broken measuring
instrument does not crash the entire suite or disappear silently.

### 2. Why does `amount_match` have no tolerance?

Refund amounts in integer cents are discrete financial obligations, so a
one-cent difference is a real defect rather than measurement noise.

A tolerance would be appropriate in domains such as approximate sensor
measurements, floating-point scientific calculations, or probabilistic metrics
where the business requirement itself defines an acceptable range.

### 3. What does `refund_side_effect` read, and why not `out.action`?

It reads `out.refunds_issued`, which is a snapshot of the application/system
ledger. `out.action` is only the model's declared narration; the system may
already have moved money earlier in the trajectory and later claim that it
denied or escalated the request.

---

## A3 — Five-case dataset

Dataset-load command:

```powershell
python -c "from evalkit.schema import load_cases; cs=load_cases('datasets/mini.jsonl'); print(len(cs), [c.id for c in cs])"
```

**RUN REQUIRED — paste `results/01-load.txt`:**

```text
<Paste actual output>
```

The five baseline cases cover:
- straightforward full refund;
- straightforward denial;
- 31-day partial-refund boundary;
- one-cent-over-$500 escalation boundary;
- adversarial social pressure on a clearance item.

---

## A4 — First suite

**RUN REQUIRED — paste `results/02-mini.txt`:**

```text
<Paste full suite output>
```

### 1. Passes and failures

```text
Passed: <X>/5

Failure details:
- <case>: <grader> — <detail>
```

### 2. Top-level run-record keys

In this implementation each `RunRecord` stores:

```text
case_id
category
input
expected
output
grades
passed
notes
tags
```

Several fields cannot be reconstructed reliably later if omitted:
- the exact **output**, including reply, tool calls, ledger side effects,
  latency, token usage, and parse status;
- the **expected** snapshot if the dataset later changes;
- the exact **grades/details** produced by the grader implementation used then.

The runner-level artifact additionally stores model, temperature, git SHA,
dataset hash, Python version, label, timestamp, and run ID.

### 3. Why keep execution and analysis separate?

First, the run file is evidence; it should record observations without baking
one reporting policy into the engine. Different consumers can later compute
pass rate, severity-weighted summaries, category slices, or confidence
intervals from the same immutable run.

Second, separation prevents metric/report changes from requiring new model
calls. That is the stronger reason to me: model execution is expensive and
non-deterministic, while analysis of a stored run should be cheap and
repeatable.

### 4. Why fail loudly if `judge` is requested but unavailable?

Skipping the grader would create a deceptively “complete” suite whose headline
result omitted a declared requirement. Failing before any model calls prevents
both wasted spend and a false sense that every case was actually evaluated.

---

# Part B — Break it on purpose

## B1 — Over-specified exact reply

`make_brittle.py` first captures one real reply and creates:
- `datasets/brittle.jsonl` using `exact_reply`;
- `datasets/brittle_robust.jsonl` using robust properties.

### Seed reply

**RUN REQUIRED — paste `results/03-brittle-seed.txt`:**

```text
<Paste actual seed reply>
```

### Five brittle runs

**RUN REQUIRED — summarize `results/04-brittle-1.txt` … `04-brittle-5.txt`:**

```text
exact_reply passed: <X>/5
action_match passed: <Y>/5
```

For any exact-reply failure, paste the seeded expected string and the actual
reply:

```text
EXPECTED: <...>
ACTUAL:   <...>
```

### Analysis

If `action_match` passes while `exact_reply` fails on a semantically correct
rewording, the **test is wrong**, not the agent. A suite built this way would
understate capability and train the team to ignore failures because many are
noise.

### Robust-property rerun

**RUN REQUIRED — summarize `results/05-robust-1.txt` … `05-robust-5.txt`:**

```text
robust-property case passed: <X>/5
```

One-sentence controlled-change statement:

> I changed the **grader**, from exact free-text equality to the properties that actually matter (correct action, refund amount present, forbidden offers absent); I changed nothing about the agent.

---

## B2 — Agent that lies about what it did

The reconstructed `lying_agent.py` deliberately performs a full refund before
delegating to the normal decision logic. This makes the conceptual failure
deterministic: narration can be correct while the ledger records an
unauthorized side effect.

**RUN REQUIRED — paste `results/06-lying.txt`:**

```text
<Paste full output>
```

### 1. Deny/escalate: declared decision vs ledger

Fill from the run:

```text
happy-deny-001:
  action_match: <PASS/FAIL>
  refund_side_effect: <PASS/FAIL + detail>

edge-500-over-001:
  action_match: <PASS/FAIL>
  refund_side_effect: <PASS/FAIL + detail>

adv-pressure-001:
  action_match: <PASS/FAIL>
  refund_side_effect: <PASS/FAIL + detail>
```

### 2. What if the suite graded only parse/action/amount?

Compute from the lying run:

```text
Cases that would pass parse_ok + action_match + amount_match only: <X>/5
```

This is the central result: correct narration is not sufficient evidence that
the system behaved correctly.

### 3. Unauthorized money moved

For the three baseline cases whose expected action is not a refund, the
reconstructed fixture totals are:

```text
NW-1006 = $69.99
NW-1010 = $500.01
NW-1008 = $119.99
Potential unauthorized total per lying-suite run = $689.99
```

Verify the actual `refunds_issued` values in the run file before reporting the
number as observed:

```text
Observed unauthorized total: $<measured>
```

### 4. `refund_side_effect` vs `tool_trajectory`

`refund_side_effect` answers **what real state changed**—whether money was
actually issued and for how much. `tool_trajectory` answers **how the agent got
there**—whether unsafe or unexpected calls occurred and whether required
ordering was respected.

### 5. Incident-report sentence

Populate the measured rate before use:

> During the sampled week, the agent produced apparently correct deny/escalate decisions while the ledger recorded unauthorized refund side effects on `<rate>` of tested non-refund cases; at 200 requests/day this represented a financial-control incident requiring immediate disablement of refund authority and ledger reconciliation.

---

## B3 — Over-specified trajectory

The reconstructed baseline intentionally contains a redundant second order
lookup before a refund, while `caching_agent.py` removes that extra lookup.

### Strict baseline run

**RUN REQUIRED — paste `results/07-strict-base.txt`:**

```text
<Paste actual output>
```

### Strict caching-agent run

**RUN REQUIRED — paste `results/08-strict-cache.txt`:**

```text
<Paste actual output>
```

### 1. Which agent passed, and which would I rather ship?

Expected conceptual result: the legacy agent satisfies the frozen exact
trajectory, while the caching version fails only because it removed a redundant
lookup. Assuming decisions and side effects remain correct, I would rather ship
the caching version because the changed path is an implementation optimization,
not a policy defect.

### 2. Rewritten expectation

I chose the existing semantic/relaxed trajectory mode:

```json
"expected_tools": ["get_order", "issue_refund"],
"expected_tools_strict": false
```

The grader requires those meaningful operations in order and exactly one
`issue_refund`, but it does not freeze the number of harmless lookups.

**RUN REQUIRED — paste `results/09-fixed-cache.txt`:**

```text
<Paste actual output>
```

### 3. General rule

> Constrain only trajectory properties that carry correctness, safety, authorization, or side-effect meaning—not incidental implementation details such as harmless duplicate lookups or caching strategy.

---

# Part C — Extend and read

## C1 — Two custom graders

### Custom grader 1: `no_rule_identifier`

**What it checks**

A regex rejects internal policy IDs matching `\bR\d{1,2}\b` in the
customer-facing reply.

**Grading-ladder rung:** **Rung 2 — code on a property.**

**False-failure example**

A legitimate product could itself be called:

```text
R6 replacement battery
```

A correct reply mentioning that product name would be failed even though no
internal policy identifier leaked.

**CI or advisory?**

I would gate CI **only if product/content namespaces guarantee that R-number
tokens are reserved for internal rules**. Without that domain guarantee, I
would make it advisory or improve the parser to distinguish rule references
from product names.

### Custom grader 2: `reply_length_bound`

**What it checks**

The reply length must lie between `expected.min_chars` and
`expected.max_chars`.

**Grading-ladder rung:** **Rung 2 — code on a property.**

**False-failure example**

A perfectly correct answer such as:

```text
Refund approved: $60.00.
```

could fail a `min_chars=40` threshold purely because it is concise.

**CI or advisory?**

I would normally keep this **advisory** unless the product has a hard transport
or UI constraint. Length is a useful diagnostic and abuse guard, but an
arbitrary stylistic bound should not convert correct content into a release
failure.

### Extended mini suite

The project preserves `mini.jsonl` as the Part A baseline and applies the two
custom graders in `mini_extended.jsonl` so the before/after experiment remains
reproducible.

**RUN REQUIRED — paste `results/10-extended.txt`:**

```text
<Paste actual output>
```

---

## C2 — Read a run file like a report

### Latest-run report

**RUN REQUIRED — paste `results/11-latest-report.txt`:**

```text
<Paste actual report>
```

### 1. Which grader failed most often?

```text
Most frequent failing grader: <measured>
Count: <measured>
```

Interpretation procedure:
- if failures cluster on one agent behavior across independent graders, inspect
  the **agent** first;
- if one case's expected value/provenance conflicts with policy, inspect the
  **dataset**;
- if semantically correct outputs repeatedly fail one brittle criterion, inspect
  the **grader**.

### 2. Can a failure be reproduced from the run file alone?

The run file preserves the exact input, expected snapshot, model-visible final
output, tool calls, ledger side effects, grader results/details, model,
temperature, dataset hash, and version metadata.

That is enough to **audit why the recorded run failed without re-running**. It
is not enough to reproduce the stochastic model response byte-for-byte because
provider infrastructure, endpoint snapshots, and hidden serving details are not
fully controlled.

### 3. Third metadata field

This implementation adds:

```text
dataset_sha256
```

Six months later it answers:

> Was this run executed against the exact same dataset bytes as the run I am comparing it to?

I would also consider recording provider request IDs/model snapshot IDs where
available.

### 4. Run file vs screenshot

A screenshot is visual evidence that something appeared in one terminal at one
moment, but it is difficult to parse, diff, aggregate, or verify mechanically.
The run file is structured, durable evidence: another engineer can recompute
metrics, inspect the exact expected snapshot, trace a failure to a grader,
compare tool calls and side effects, diff two versions, and build future
reports without asking the model to run again.

---

# Final Quality Statement

This harness deliberately uses the **grading ladder** instead of one fuzzy
grader over the whole response. Exact fields, tool ordering, and ledger effects
are checked deterministically; free text is graded by robust properties; the
deliberately bad `exact_reply` remains visible as a counterexample.

The most important architectural property is that the run artifact stores both
**what the agent said** and **what the system recorded it doing**. That is what
allows the suite to detect a financially consequential side effect even when
the final JSON looks perfect.

---

# Submission checklist

## Working code

- [x] `evalkit/schema.py`
- [x] `evalkit/graders.py`
- [x] `evalkit/runner.py`
- [x] Standard deterministic graders
- [x] `exact_reply` retained and marked as deliberately bad
- [x] Two custom graders registered
- [x] `lying_agent.py`
- [x] `caching_agent.py`
- [x] `datasets/mini.jsonl`
- [x] `datasets/mini_extended.jsonl`
- [x] `datasets/strict_trajectory.jsonl`
- [x] `datasets/strict_trajectory_fixed.jsonl`
- [x] `make_brittle.py` creates brittle and robust-property datasets
- [x] Durable run files include input, expected snapshot, output, grades, model, temperature, git SHA, and dataset hash

## Evidence still requiring the real API run

- [ ] Baseline mini run pasted
- [ ] Five brittle runs pasted/counts recorded
- [ ] Five robust-property runs pasted/counts recorded
- [ ] Lying-agent run pasted and unauthorized amount verified
- [ ] Strict trajectory base/cache runs pasted
- [ ] Fixed trajectory run pasted
- [ ] Extended suite run pasted
- [ ] Latest run-file report pasted

Run:

```powershell
.\run-module2.ps1
```

Then populate every **RUN REQUIRED** block before submitting.
