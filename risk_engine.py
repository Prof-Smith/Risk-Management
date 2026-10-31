import numpy as np
import pandas as pd

def apply_ghostline_shock(df,severity):
    x=df.copy(); s=severity/100; ghost=x.asset.eq('Ghostline Systems'); adjacent=x.asset.eq('CipherWorks')
    x.loc[ghost,'pd']*=1+2.4*s; x.loc[ghost,'lgd']+=.15*s; x.loc[ghost,'mark']-=18*s
    x.loc[adjacent,'pd']*=1+.65*s; x.loc[adjacent,'lgd']+=.05*s; x.loc[adjacent,'mark']-=5*s
    x['pd']*=1+.18*s; x['lgd']+=.025*s; x['mark']-=2*s
    x['pd']=x.pd.clip(upper=.60); x['lgd']=x.lgd.clip(upper=.85); x['mark']=x['mark'].clip(lower=45)
    return x

def simulate_losses(df,severity=0,confidence=.95,simulations=30000,seed=47):
    rng=np.random.default_rng(seed); loading=.30+.35*severity/100; common=rng.standard_normal(simulations)
    arrays={}; total=np.zeros(simulations)
    for _,loan in df.iterrows():
        idio=rng.standard_normal(simulations); latent=loading*common+np.sqrt(1-loading**2)*idio
        threshold=np.quantile(rng.standard_normal(250000),loan.pd); default=latent<threshold
        lgd=np.clip(loan.lgd+rng.normal(0,.08,simulations),.05,.95)
        loss=default*loan.exposure*lgd+max(0,(100-loan['mark'])/100*loan.exposure)
        arrays[loan.asset]=loss; total+=loss
    var=float(np.quantile(total,confidence)); mask=total>=var; cvar=float(total[mask].mean())
    contribution=pd.Series({k:float(v[mask].mean()) for k,v in arrays.items()}).sort_values(ascending=False)
    return {'losses':total,'var':var,'cvar':cvar,'tail_gap':cvar-var,'tail_contribution':contribution,'loading':loading}
