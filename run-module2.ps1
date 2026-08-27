$ErrorActionPreference="Stop"
New-Item -ItemType Directory -Force -Path results | Out-Null

Write-Host "A1 schema sanity"
python -c "from evalkit.schema import Case,GradeResult; print(Case('x','happy',{}))" |
  Tee-Object results\00-schema.txt

Write-Host "A3 load dataset"
python -c "from evalkit.schema import load_cases; cs=load_cases('datasets/mini.jsonl'); print(len(cs), [c.id for c in cs])" |
  Tee-Object results\01-load.txt

Write-Host "A4 normal mini suite"
python -m evalkit.runner datasets/mini.jsonl --label local |
  Tee-Object results\02-mini.txt

Write-Host "B1 seed brittle dataset"
python make_brittle.py | Tee-Object results\03-brittle-seed.txt

1..5 | ForEach-Object {
  python -m evalkit.runner datasets/brittle.jsonl --label "brittle-$_" |
    Tee-Object "results\04-brittle-$_.txt"
}

1..5 | ForEach-Object {
  python -m evalkit.runner datasets/brittle_robust.jsonl --label "robust-$_" |
    Tee-Object "results\05-robust-$_.txt"
}

Write-Host "B2 lying agent"
python -c "import lying_agent; from evalkit.runner import run_suite; r=run_suite('datasets/mini.jsonl', lying_agent.run_agent, label='lying'); print('run file:',r.save())" |
  Tee-Object results\06-lying.txt

Write-Host "B3 strict trajectory: base"
python -m evalkit.runner datasets/strict_trajectory.jsonl --label strict-base |
  Tee-Object results\07-strict-base.txt

Write-Host "B3 strict trajectory: caching"
python -c "import caching_agent; from evalkit.runner import run_suite; r=run_suite('datasets/strict_trajectory.jsonl', caching_agent.run_agent, label='strict-cache'); print('run file:',r.save())" |
  Tee-Object results\08-strict-cache.txt

Write-Host "B3 fixed semantic trajectory: caching"
python -c "import caching_agent; from evalkit.runner import run_suite; r=run_suite('datasets/strict_trajectory_fixed.jsonl', caching_agent.run_agent, label='fixed-cache'); print('run file:',r.save())" |
  Tee-Object results\09-fixed-cache.txt

Write-Host "C1 extended mini with custom graders"
python -m evalkit.runner datasets/mini_extended.jsonl --label extended |
  Tee-Object results\10-extended.txt

Write-Host "Latest run report"
python read_latest_run.py | Tee-Object results\11-latest-report.txt

Write-Host ""
Write-Host "Done. Review results\ and runs\, then populate lab-notes.md."
