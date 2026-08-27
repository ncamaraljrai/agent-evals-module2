from __future__ import annotations
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

@dataclass
class Case:
    id: str
    category: str
    input: dict
    expected: dict = field(default_factory=dict)
    graders: list[str] = field(default_factory=list)
    notes: str = ""
    tags: list[str] = field(default_factory=list)

@dataclass
class GradeResult:
    grader: str
    passed: bool
    detail: str = ""
    score: float|None = None
    advisory: bool = False

@dataclass
class RunRecord:
    case_id: str
    category: str
    input: dict
    expected: dict
    output: dict
    grades: list[GradeResult]
    passed: bool
    notes: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self):
        d=asdict(self)
        return d

@dataclass
class Run:
    run_id: str
    label: str
    dataset: str
    agent_model: str
    temperature: float
    git_sha: str|None
    started_at: str
    records: list[RunRecord]
    meta: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "run_id":self.run_id,
            "label":self.label,
            "dataset":self.dataset,
            "agent_model":self.agent_model,
            "temperature":self.temperature,
            "git_sha":self.git_sha,
            "started_at":self.started_at,
            "meta":self.meta,
            "records":[r.to_dict() for r in self.records],
        }

    def save(self, directory="runs"):
        p=Path(directory)
        p.mkdir(parents=True,exist_ok=True)
        path=p/f"{self.label}-{self.run_id}.json"
        path.write_text(json.dumps(self.to_dict(),indent=2,ensure_ascii=False),encoding="utf-8")
        return path

def load_cases(path: str|Path) -> list[Case]:
    path=Path(path)
    cases=[]; seen=set()
    for lineno,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip():
            continue
        try:
            d=json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}:{lineno}: invalid JSON: {e}") from e
        case=Case(
            id=d["id"], category=d["category"], input=d["input"],
            expected=d.get("expected",{}), graders=d.get("graders",[]),
            notes=d.get("notes",""), tags=d.get("tags",[]),
        )
        if case.id in seen:
            raise ValueError(f"{path}:{lineno}: duplicate case id {case.id!r}")
        seen.add(case.id); cases.append(case)
    return cases
