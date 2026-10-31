from services.simulation_engine import run_case


def find_reversal(case: dict, correlation: float) -> float:
    low, high = 0.1, 150.0
    for _ in range(60):
        midpoint = (low + high) / 2
        if run_case(case, midpoint, correlation)["breach"]:
            high = midpoint
        else:
            low = midpoint
    return high
