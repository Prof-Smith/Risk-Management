from pathlib import Path
import yaml

CASE_ROOT = Path(__file__).resolve().parents[1] / "cases"


def available_cases() -> list[str]:
    return sorted(path.parent.name for path in CASE_ROOT.glob("*/case.yml"))


def load_case(case_id: str) -> dict:
    path = CASE_ROOT / case_id / "case.yml"
    if not path.exists():
        raise FileNotFoundError(f"Case not found: {case_id}")
    with path.open(encoding="utf-8") as stream:
        case = yaml.safe_load(stream)
    required = {"id", "title", "narrative", "decision_prompt", "decision_choices", "baseline", "shock"}
    missing = required.difference(case)
    if missing:
        raise ValueError(f"Case {case_id} is missing: {', '.join(sorted(missing))}")
    return case
