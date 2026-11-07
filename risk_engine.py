"""Single source of truth for portfolio risk calculations.
Additive module: does not alter existing app behavior until explicitly imported.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

CONFIDENCE_LEVELS = (0.95, 0.975, 0.99)

def calculate_weights(holdings: pd.DataFrame) -> pd.DataFrame:
    required = {'pool', 'exposure_mm'}
    missing = required - set(holdings.columns)
    if missing:
        raise ValueError(f"Holdings missing columns: {sorted(missing)}")
    out = holdings.copy()
    total = out['exposure_mm'].sum()
    if total <= 0:
        raise ValueError('Total exposure must be positive.')
    out['calculated_weight'] = out['exposure_mm'] / total
    return out

def calculate_portfolio_losses(holdings: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    h = calculate_weights(holdings)
    assets = h['pool'].tolist()
    missing = [c for c in assets if c not in returns.columns]
    if missing:
        raise ValueError(f"Returns missing pool columns: {missing}")
    out = returns.copy()
    weights = h['calculated_weight'].to_numpy(dtype=float)
    value_mm = float(h['exposure_mm'].sum())
    out['portfolio_return'] = out[assets].to_numpy(dtype=float) @ weights
    out['portfolio_loss_mm'] = -value_mm * out['portfolio_return']
    return out

def historical_var_cvar(losses, confidence: float = 0.99) -> dict:
    if confidence not in CONFIDENCE_LEVELS:
        raise ValueError(f"Confidence must be one of {CONFIDENCE_LEVELS}")
    x = pd.Series(losses, dtype=float).dropna().to_numpy()
    if x.size == 0:
        raise ValueError('Loss series is empty.')
    var = float(np.quantile(x, confidence, method='linear'))
    tail = x[x >= var]
    return {'confidence': confidence, 'var_mm': var,
            'cvar_mm': float(tail.mean()), 'tail_count': int(tail.size)}

def regime_statistics(loss_data: pd.DataFrame, regime: str, confidence: float = 0.99) -> dict:
    x = loss_data.loc[loss_data['regime'].eq(regime), 'portfolio_loss_mm'].dropna()
    risk = historical_var_cvar(x, confidence)
    return {**risk, 'regime': regime, 'observations': int(x.size),
            'volatility_mm': float(x.std(ddof=1))}

def correlation_matrix(returns: pd.DataFrame, holdings: pd.DataFrame, regime: str) -> pd.DataFrame:
    assets = holdings['pool'].tolist()
    return returns.loc[returns['regime'].eq(regime), assets].corr()

def run_audits(holdings: pd.DataFrame, loss_data: pd.DataFrame) -> dict[str, bool]:
    h = calculate_weights(holdings)
    return {
        'Weights sum to 100%': bool(np.isclose(h['calculated_weight'].sum(), 1.0)),
        'Initial regime has 250 observations': int(loss_data['regime'].eq('Initial').sum()) == 250,
        'Updated regime has 250 observations': int(loss_data['regime'].eq('Updated').sum()) == 250,
        'No missing portfolio losses': bool(loss_data['portfolio_loss_mm'].notna().all()),
    }
