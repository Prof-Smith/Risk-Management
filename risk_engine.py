import numpy as np
import pandas as pd


def apply_scenario(df, scenario):
    x=df.copy()
    if scenario=='Software disruption':
        m=x.sector.eq('Software'); x.loc[m,'pd']*=2.8; x.loc[m,'lgd']+=.14; x.loc[m,'mark']-=14; x.loc[m,'coverage']-=.35; x.loc[m,'spread']+=3.2
    elif scenario=='Higher for longer':
        x['pd']*=1.35; x['coverage']-=.22; x['spread']+=1.5; x['mark']-=4; x['duration']*=.96
    elif scenario=='Consumer slowdown':
        m=x.sector.isin(['Consumer','Logistics']); x.loc[m,'pd']*=2.0; x.loc[m,'lgd']+=.09; x.loc[m,'mark']-=9; x.loc[m,'coverage']-=.28
    elif scenario=='Liquidity run':
        x['days_to_liquidate']*=1.8; x['mark']-=3; x['spread']+=1.0
    elif scenario=='Combined stress':
        x['pd']*=1.7; x['lgd']+=.10; x['mark']-=8; x['coverage']-=.30; x['spread']+=2.0; x['days_to_liquidate']*=1.7
        m=x.sector.eq('Software'); x.loc[m,'pd']*=1.6; x.loc[m,'mark']-=8
    x['pd']=x.pd.clip(upper=.60); x['lgd']=x.lgd.clip(upper=.85); x['coverage']=x.coverage.clip(lower=.45); x['mark']=x.mark.clip(lower=45)
    return x


def metrics(df, nav=1250, confidence=.95, seed=47):
    d=df.copy(); total=d.exposure.sum(); w=d.exposure/total
    d['expected_loss']=d.exposure*d.pd*d.lgd
    d['economic_value']=d.exposure*d['mark']/100
    d['valuation_gap']=d.exposure-d.economic_value
    d['liq_haircut']=np.minimum(.35,.015+d.days_to_liquidate/900+d.spread/500)
    d['liquidity_value']=d.economic_value*(1-d.liq_haircut)
    expected_loss=d.expected_loss.sum()
    hhi=float((w*w).sum())
    weighted_pd=float((w*d.pd).sum())
    weighted_lgd=float((w*d.lgd).sum())
    weighted_duration=float((w*d.duration).sum())
    concentration_addon=max(0,(hhi-.125))*total*.28
    rng=np.random.default_rng(seed)
    # latent common credit factor plus idiosyncratic loss states
    sims=30000; common=rng.standard_normal(sims)
    losses=np.zeros(sims)
    for _,r in d.iterrows():
        latent=.48*common+np.sqrt(1-.48**2)*rng.standard_normal(sims)
        threshold=np.quantile(rng.standard_normal(200000),r.pd)
        default=latent<threshold
        severity=np.clip(r.lgd+rng.normal(0,.08,sims),.05,.95)
        mtm=np.maximum(0,(100-r['mark'])/100*r.exposure)
        losses += default*r.exposure*severity + mtm
    losses += concentration_addon
    var=float(np.quantile(losses,confidence)); cvar=float(losses[losses>=var].mean())
    return {'detail':d,'total_exposure':total,'expected_loss':expected_loss,'weighted_pd':weighted_pd,'weighted_lgd':weighted_lgd,'duration':weighted_duration,'hhi':hhi,'var':var,'cvar':cvar,'losses':losses,'economic_value':d.economic_value.sum(),'liquidity_value':d.liquidity_value.sum(),'valuation_gap':d.valuation_gap.sum()}


def cash_run(metrics, redemption_pct, cash=75, line=62.5, income=11.25, gate_pct=5, nav=1250):
    requested=nav*redemption_pct/100; payable=min(requested,nav*gate_pct/100); sources=cash+line+income
    sale_need=max(0,payable-sources); portfolio_discount=1-metrics['liquidity_value']/max(metrics['economic_value'],1)
    forced_loss=sale_need*portfolio_discount; ending=max(0,sources-payable-forced_loss)
    return {'requested':requested,'payable':payable,'sources':sources,'sale_need':sale_need,'forced_loss':forced_loss,'ending_cash':ending,'discount':portfolio_discount}
