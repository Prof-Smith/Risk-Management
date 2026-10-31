from pathlib import Path
import yaml, pandas as pd
ROOT=Path(__file__).resolve().parents[1]/'cases'/'northstar_private_credit'
def load_case():
    with open(ROOT/'case.yml',encoding='utf-8') as f: case=yaml.safe_load(f)
    with open(ROOT/'scenarios.yml',encoding='utf-8') as f: scenarios=yaml.safe_load(f)['scenarios']
    evidence=pd.read_csv(ROOT/'evidence.csv')
    return case,scenarios,evidence

def calculate(case, scenario):
    b=case['baseline']; a=scenario['assumptions']
    debt=b['senior_debt_mm']+a.get('revolver_draw_mm',0)-a.get('principal_paydown_mm',0)
    ebitda=b['ebitda_mm']*(1+a.get('revenue_growth_pct',0)/100)*(a.get('ebitda_margin_pct',16)/16)
    cash_interest=debt*a.get('cash_rate_pct',b['cash_rate_pct'])/100
    pik=debt*a.get('pik_rate_pct',0)/100
    leverage=debt/max(ebitda,0.1)
    coverage=ebitda/max(cash_interest,0.1)
    pd=a.get('probability_default_pct',b['probability_default_pct'])/100
    recovery=a.get('recovery_pct',b['recovery_pct'])/100
    expected_loss=b['outstanding_mm']*pd*(1-recovery)
    bid=a.get('secondary_bid_pct_of_par', max(45,100-(pd*105)-(1-recovery)*30))
    liquidity=max(0,17-a.get('revolver_draw_mm',0)+a.get('new_equity_mm',0))
    return {'debt':debt,'ebitda':ebitda,'cash_interest':cash_interest,'pik':pik,'leverage':leverage,'coverage':coverage,'pd':pd*100,'recovery':recovery*100,'expected_loss':expected_loss,'bid':bid,'liquidity':liquidity,'breach':expected_loss>b['risk_limit_expected_loss_mm']}

def reversal_pd(case,recovery_pct):
    b=case['baseline']; lgd=1-recovery_pct/100
    return 100*b['risk_limit_expected_loss_mm']/(b['outstanding_mm']*max(lgd,.001))
