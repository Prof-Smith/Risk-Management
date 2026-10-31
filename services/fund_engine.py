import numpy as np
import pandas as pd

SECTORS=['Software','Business services','Healthcare','Consumer','Industrials','Asset-backed']
BASE_WEIGHTS=np.array([.24,.20,.17,.13,.14,.12])
BASE_VOL=np.array([.10,.08,.07,.11,.09,.06])
BASE_MARKS=np.array([99.,98.,99.,96.,97.,99.])


def _corr(rho):
    c=np.full((6,6),rho,dtype=float); np.fill_diagonal(c,1.0); return c


def simulate_fund(nav_mm=1250,shock=0,stale_days=30,draw_pct=0,gating_pct=5,seed=717,n_sims=25000):
    shock=shock/100
    rho=.24+.56*shock
    vol=BASE_VOL*(1+1.9*shock)
    mean=np.array([.020,.018,.016,.015,.017,.014])-np.array([.18,.10,.07,.12,.09,.05])*shock
    cov=np.outer(vol,vol)*_corr(rho)
    rng=np.random.default_rng(seed)
    rets=rng.multivariate_normal(mean,cov,n_sims)
    port=rets@BASE_WEIGHTS
    # additional nonlinear liquidity/valuation gap, increasing with staleness and shock
    stale_gap=(stale_days/90)*(.018+.11*shock)
    run_pressure=(draw_pct/100)*(.06+.16*shock)
    economic=port-stale_gap-run_pressure
    losses=-economic*nav_mm
    var95=float(np.quantile(losses,.95)); cvar95=float(losses[losses>=var95].mean())
    var99=float(np.quantile(losses,.99)); cvar99=float(losses[losses>=var99].mean())
    reported_nav=nav_mm
    economic_nav=nav_mm*(1-stale_gap)-max(0,float(np.median(losses)))
    liquid_cash=nav_mm*.06
    committed_lines=nav_mm*.05
    monthly_income=nav_mm*.009
    redemption_request=nav_mm*draw_pct/100
    payable=min(redemption_request,nav_mm*gating_pct/100)
    liquidity_sources=liquid_cash+committed_lines+monthly_income
    sale_need=max(0,payable-liquidity_sources)
    sale_discount=.04+.25*shock+stale_days/900
    forced_sale_loss=sale_need*sale_discount
    ending_cash=max(0,liquidity_sources-payable)
    unmet=max(0,payable-liquidity_sources-sale_need)
    liabilities=nav_mm*.12+payable
    economic_assets=economic_nav-forced_sale_loss
    coverage=economic_assets/max(liabilities,1)
    return {
        'losses':losses,'var95':var95,'cvar95':cvar95,'var99':var99,'cvar99':cvar99,
        'reported_nav':reported_nav,'economic_nav':economic_nav,'stale_gap':reported_nav-economic_nav,
        'redemption_request':redemption_request,'payable':payable,'cash':liquid_cash,'lines':committed_lines,
        'income':monthly_income,'sale_need':sale_need,'sale_discount':sale_discount,'forced_sale_loss':forced_sale_loss,
        'ending_cash':ending_cash,'unmet':unmet,'coverage':coverage,'rho':rho,'weights':BASE_WEIGHTS,
        'sector_losses':-np.median(rets,axis=0)*nav_mm*BASE_WEIGHTS,
    }


def liquidity_waterfall(result):
    return pd.DataFrame({
        'Step':['Opening cash','Committed lines','Monthly income','Redemptions payable','Forced-sale loss','Ending cash'],
        'Amount':[result['cash'],result['lines'],result['income'],-result['payable'],-result['forced_sale_loss'],result['ending_cash']],
        'Measure':['relative','relative','relative','relative','relative','total']
    })


def mitigation_effects(nav_mm,shock,stale_days,draw_pct,gating_pct,actions):
    adj_shock=shock; adj_stale=stale_days; adj_draw=draw_pct; adj_gate=gating_pct
    cash_add=0
    if 'Independent revaluation' in actions: adj_stale=max(1,stale_days-20)
    if 'Tighten redemption gate' in actions: adj_gate=max(2,gating_pct-2)
    if 'Draw liquidity line early' in actions: cash_add=nav_mm*.03
    if 'Sell public liquid sleeve' in actions: cash_add=nav_mm*.025
    if 'Suspend new originations' in actions: adj_draw=max(0,draw_pct-1)
    r=simulate_fund(nav_mm,adj_shock,adj_stale,adj_draw,adj_gate)
    r['ending_cash']+=cash_add
    return r
