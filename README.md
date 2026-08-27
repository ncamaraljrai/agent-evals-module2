# Module 2 — Build the Eval Harness

This is a complete runnable scaffold for the **Module 2 Lab: Build the Eval Harness**.

## Source caveat

The lab references `03-eval-harness.md` and the official Module 1 agent fixture,
but those files were not included with the supplied attachment. The package
therefore reconstructs a compatible harness from the lab's explicit
requirements. It preserves the important semantics:

- four-part cases;
- deterministic grader registry with declared required keys;
- durable JSON run files;
- output and side-effect/trajectory grading;
- deliberately bad `exact_reply`;
- a lying-agent demonstration;
- an over-specified trajectory demonstration;
- two custom rung-2 graders.

If you later receive the official script listing, compare/replace the
reconstructed files before final course submission if exact fixture parity is
required.

## Setup — Windows PowerShell

```powershell
cd agent-evals-module2
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Add your own `ANTHROPIC_API_KEY` to `.env`.

## Smoke tests

```powershell
python -c "from evalkit.schema import Case, GradeResult; print(Case('x','happy',{}))"
python -c "from evalkit.schema import load_cases; cs=load_cases('datasets/mini.jsonl'); print(len(cs), [c.id for c in cs])"
```

## Run the full lab evidence workflow

```powershell
.\run-module2.ps1
```

This writes:
- raw terminal evidence to `results/`;
- durable eval run artifacts to `runs/`.

Then fill the **RUN REQUIRED** fields in `lab-notes.md` from the actual evidence.

## Measurement honesty

The package does not fabricate model outputs, latency, pass rates, grader
failures, or money moved. The conceptual answers are pre-written where they
can be derived from the specification; API-dependent observations are marked
for completion after the real run.
# agent-evals-module2
