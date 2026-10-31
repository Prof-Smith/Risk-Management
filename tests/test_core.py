from services.case_loader import load_case
from services.reversal_engine import find_reversal
from services.simulation_engine import run_case


def test_case_loads():
    assert load_case("portfolio_tail_risk")["id"] == "portfolio_tail_risk"


def test_stress_increases_risk():
    case = load_case("portfolio_tail_risk")
    base = run_case(case, 18.0, 0.25)
    stress = run_case(case, 36.0, 0.85)
    assert stress["expected_shortfall"] > base["expected_shortfall"]


def test_reversal_is_positive():
    case = load_case("portfolio_tail_risk")
    assert find_reversal(case, 0.25) > 0
