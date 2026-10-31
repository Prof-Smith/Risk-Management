from statistics import NormalDist


def run_case(case: dict, volatility: float, correlation: float) -> dict:
    confidence = float(case["baseline"]["confidence"])
    horizon = float(case["baseline"]["horizon_days"])
    risk_limit = float(case["baseline"]["risk_limit"])
    z = abs(NormalDist().inv_cdf(1 - confidence))
    diversification_penalty = 1 + 0.55 * correlation
    daily_volatility = volatility / (252 ** 0.5)
    var = z * daily_volatility * (horizon ** 0.5) * diversification_penalty
    expected_shortfall = var * 1.22
    usage = 100 * expected_shortfall / risk_limit
    return {
        "volatility": volatility,
        "correlation": correlation,
        "var": var,
        "expected_shortfall": expected_shortfall,
        "limit_usage": usage,
        "breach": usage >= 100,
    }
