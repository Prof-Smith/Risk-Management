from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent

def load_data():
 h=pd.read_csv(ROOT/'data/mortgage_pool_holdings.csv')
 r=pd.read_csv(ROOT/'data/mortgage_pool_returns.csv',parse_dates=['date'])
 p=pd.read_csv(ROOT/'data/external_market_proxy.csv',parse_dates=['date'])
 return h,r,p

def portfolio_losses(holdings,returns,regime):
 x=returns[returns.regime.eq(regime)][holdings.pool].to_numpy()
 weights=holdings.weight.to_numpy(); exposure=holdings.exposure_mm.sum()
 return -(x@weights)*exposure

def historical_var_cvar(losses,confidence=.99):
 var=float(np.quantile(losses,confidence));tail=losses[losses>=var]
 return {'var':var,'cvar':float(tail.mean()),'mean':float(losses.mean()),'vol':float(losses.std(ddof=1)),'tail_n':int(len(tail))}

def covariance_tables(holdings,returns,regime):
 x=returns[returns.regime.eq(regime)][holdings.pool]
 return x.cov()*252,x.corr()

def rolling_vol(holdings,returns,window=30):
 x=returns[holdings.pool].to_numpy()@holdings.weight.to_numpy()
 return pd.Series(x,index=returns.date).rolling(window).std()*np.sqrt(252)
