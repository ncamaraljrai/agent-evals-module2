import json, glob, os
paths=glob.glob("runs/*.json")
if not paths:
    raise SystemExit("No run files found.")
path=max(paths,key=os.path.getmtime)
d=json.load(open(path,encoding="utf-8"))
print(path,d["agent_model"],d["meta"])
for r in d["records"]:
    fails=[(g["grader"],g["detail"]) for g in r["grades"] if not g["passed"]]
    print(f'{r["case_id"]:<28} {"PASS" if r["passed"] else "FAIL"}  {fails}')
