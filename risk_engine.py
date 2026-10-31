import numpy as np
import pandas as pd


def apply_software_shock(df, severity):
    """One coherent shock: AI-driven repricing of software and correlated private debt."""
    x = df.copy()
    s = severity / 100
    software = x.sector.eq('Software')

    # The selected shock directly changes the portfolio loss model inputs.
    x.loc[software, 'pd'] *= 1 + 2.4 * s
    x.loc[software, 'lgd'] += 0.15 * s
    x.loc[software, 'mark'] -= 18 * s

    # Spillovers to all holdings through tighter conditions and correlation.
    x['pd'] *= 1 + 0.30 * s
    x['lgd'] += 0.04 * s
    x['mark'] -= 3 * s

    x['pd'] = x.pd.clip(upper=.60)
    x['lgd'] = x.lgd.clip(upper=.85)
    x['mark'] = x['mark'].clip(lower=45)
    return x


def simulate_losses(df, severity=0, confidence=.95, simulations=30000, seed=47):
    """Simulate loss from correlated defaults plus current valuation markdowns."""
    rng = np.random.default_rng(seed)
    common_loading = .30 + .35 * severity / 100
    common = rng.standard_normal(simulations)
    losses = np.zeros(simulations)
    contribution = {}

    for _, loan in df.iterrows():
        idio = rng.standard_normal(simulations)
        latent = common_loading * common + np.sqrt(1-common_loading**2) * idio
        threshold = np.quantile(rng.standard_normal(250000), loan.pd)
        default = latent < threshold
        lgd = np.clip(loan.lgd + rng.normal(0, .08, simulations), .05, .95)
        default_loss = default * loan.exposure * lgd
        markdown = max(0, (100-loan['mark'])/100 * loan.exposure)
        loan_loss = default_loss + markdown
        losses += loan_loss
        contribution[loan.asset] = float(loan_loss[loan_loss >= np.quantile(losses, confidence)].mean()) if np.any(loan_loss) else 0

    var = float(np.quantile(losses, confidence))
    tail = losses[losses >= var]
    cvar = float(tail.mean())
    probability_exceeding_cvar = float(np.mean(losses >= cvar))
    tail_width = cvar - var

    # Conditional average contribution in portfolio-tail scenarios.
    tail_mask = losses >= var
    tail_contrib = {}
    rng2 = np.random.default_rng(seed)
    common2 = rng2.standard_normal(simulations)
    loan_arrays = {}
    recomputed = np.zeros(simulations)
    for _, loan in df.iterrows():
        idio = rng2.standard_normal(simulations)
        latent = common_loading * common2 + np.sqrt(1-common_loading**2) * idio
        threshold = np.quantile(rng2.standard_normal(250000), loan.pd)
        default = latent < threshold
        lgd = np.clip(loan.lgd + rng2.normal(0, .08, simulations), .05, .95)
        arr = default * loan.exposure * lgd + max(0,(100-loan['mark'])/100*loan.exposure)
        loan_arrays[loan.asset] = arr
        recomputed += arr
    mask = recomputed >= np.quantile(recomputed, confidence)
    for name, arr in loan_arrays.items():
        tail_contrib[name] = float(arr[mask].mean())

    return {
        'losses': losses,
        'var': var,
        'cvar': cvar,
        'tail_width': tail_width,
        'probability_exceeding_cvar': probability_exceeding_cvar,
        'tail_contribution': pd.Series(tail_contrib).sort_values(ascending=False),
        'correlation_loading': common_loading,
    }
