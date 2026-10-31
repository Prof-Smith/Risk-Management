from __future__ import annotations
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

# Self-contained risk engine. Keeping these functions in app.py avoids deployment
# failures when only the entry-point file is updated in Streamlit Community Cloud.
APP_ROOT = Path(__file__).resolve().parent
DATA_ROOT = APP_ROOT / "data"

def _build_fallback_data():
    """Create the same deterministic synthetic case data if CSV files are absent."""
    holdings = pd.DataFrame([
        ['Prime RMBS AAA',1400,0.012,0.030],
        ['Alt-A RMBS AAA',1000,0.020,0.055],
        ['Subprime 2006-2 AAA',900,0.030,0.090],
        ['Subprime 2006-2 BBB',600,0.055,0.180],
        ['Subprime 2007-1 BBB-',500,0.075,0.280],
        ['CDO Mezzanine Residual',800,0.085,0.350],
    ], columns=['pool','exposure_mm','calm_annual_vol','crisis_annual_vol'])
    holdings['weight'] = holdings.exposure_mm / holdings.exposure_mm.sum()
    rng = np.random.default_rng(2007)
    n = len(holdings)
    calm_corr = np.full((n,n),.22); np.fill_diagonal(calm_corr,1)
    crisis_corr = np.full((n,n),.62); crisis_corr[2:,2:] = .82; np.fill_diagonal(crisis_corr,1)
    calm_vol = holdings.calm_annual_vol.to_numpy()/np.sqrt(252)
    crisis_vol = holdings.crisis_annual_vol.to_numpy()/np.sqrt(252)
    calm = rng.multivariate_normal(np.full(n,.00012),np.outer(calm_vol,calm_vol)*calm_corr,250)
    crisis = rng.multivariate_normal(np.full(n,-.0009),np.outer(crisis_vol,crisis_vol)*crisis_corr,250)
    jump_days = rng.choice(np.arange(250),size=18,replace=False)
    for j,mag in zip(jump_days,rng.uniform(.010,.035,size=18)):
        crisis[j] -= mag*np.array([.25,.45,.70,.95,1.10,1.25])
    dates = pd.date_range('2006-07-03',periods=500,freq='B')
    returns = pd.DataFrame(np.vstack([calm,crisis]),columns=holdings.pool)
    returns.insert(0,'date',dates); returns.insert(1,'regime',['Initial']*250+['Updated']*250)
    proxy = pd.DataFrame({'date':dates,'proxy_price':np.r_[100*np.exp(np.cumsum(rng.normal(0,.0015,250))),100*np.exp(np.cumsum(rng.normal(-.004,.012,250)))]})
    proxy['proxy_price'] = proxy.proxy_price/proxy.proxy_price.iloc[0]*100
    return holdings, returns, proxy

def load_data():
    files = [DATA_ROOT/'mortgage_pool_holdings.csv', DATA_ROOT/'mortgage_pool_returns.csv', DATA_ROOT/'external_market_proxy.csv']
    if all(f.exists() for f in files):
        return (pd.read_csv(files[0]), pd.read_csv(files[1],parse_dates=['date']), pd.read_csv(files[2],parse_dates=['date']))
    return _build_fallback_data()

def portfolio_losses(holdings,returns,regime):
    x = returns[returns.regime.eq(regime)][holdings.pool].to_numpy()
    weights = holdings.weight.to_numpy()
    return -(x @ weights) * holdings.exposure_mm.sum()

def historical_var_cvar(losses,confidence=.99):
    var = float(np.quantile(losses,confidence))
    tail = losses[losses >= var]
    return {'var':var,'cvar':float(tail.mean()),'mean':float(losses.mean()),'vol':float(losses.std(ddof=1)),'tail_n':int(len(tail))}

def covariance_tables(holdings,returns,regime):
    x = returns[returns.regime.eq(regime)][holdings.pool]
    return x.cov()*252, x.corr()

def rolling_vol(holdings,returns,window=30):
    x = returns[holdings.pool].to_numpy() @ holdings.weight.to_numpy()
    return pd.Series(x,index=returns.date).rolling(window).std()*np.sqrt(252)

st.set_page_config(page_title='Blackridge Mortgage Regime Lab',page_icon='◈',layout='wide',initial_sidebar_state='collapsed')
H,R,P=load_data();SCENES=['intro','eric','peter','regime','tuld','sale','assignment'];TIMES=['INTRO','4:17 PM','6:08 PM','9:10 PM','12:16 AM','8:00 AM','ASSIGNMENT']
for k,v in {'accepted':False,'scene':'intro','confidence':.99,'video':'https://youtu.be/BLYCx_AOgUs'}.items():st.session_state.setdefault(k,v)
CHAR={'Eric Dale':('eric','Former Head of Risk','#526777'),'Peter Sullivan':('peter','Quantitative Risk Analyst','#168C86'),'Seth Bregman':('seth','Associate Risk Analyst','#3B8EBA'),'Sarah Robertson':('sarah','Chief Risk Officer','#B7872B'),'Jared Cohen':('jared','Head of Structured Credit','#42735B'),'Will Emerson':('will','Head of Trading','#A56632'),'Sam Rogers':('sam','Head of Portfolio Management','#245B77'),'John Tuld':('john','Chief Executive Officer','#173F5F')}
st.markdown('''<style>.block-container{max-width:1380px;padding-top:.4rem;padding-bottom:1rem}.eyebrow{color:#0F7890;font-size:.7rem;font-weight:800;letter-spacing:.14em}.title{font:700 1.8rem Georgia;color:#102A43;margin:.05rem 0}.copy{font:1rem/1.45 Georgia;max-width:1080px}.comic{border:1.5px solid #153B56;border-radius:12px;background:#fff;padding:.5rem;box-shadow:3px 4px 0 #D9E2E7}.bubble{border:1.5px solid #153B56;border-radius:13px;background:white;padding:.6rem;font:italic .88rem/1.3 Georgia;min-height:70px}.role{font-size:.65rem;color:#60788A;text-transform:uppercase}.calc{border-left:4px solid #D69C35;background:#FFF8E8;padding:.65rem;border-radius:6px}.stButton>button{font-weight:750}[data-testid="stMetricValue"]{font-size:1.35rem}</style>''',unsafe_allow_html=True)

def portrait(name,state='neutral'):return f"assets/portraits/{CHAR[name][0]}_{state}.png"
def panel(name,text,state='neutral'):
 st.markdown(f"<div class='comic' style='border-color:{CHAR[name][2]}'>",unsafe_allow_html=True);st.image(portrait(name,state),width='stretch');st.markdown(f"**{name}**<br><span class='role'>{CHAR[name][1]}</span><div class='bubble'>{text}</div></div>",unsafe_allow_html=True)
def exchange(a,ta,sa,b,tb,sb):
 x,y=st.columns(2,gap='small')
 with x:panel(a,ta,sa)
 with y:panel(b,tb,sb)
def style(fig,title,h=330):
 fig.update_layout(title=title,height=h,margin=dict(l=35,r=20,t=55,b=40),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#FCFBF8',legend=dict(orientation='h',y=1.08),font=dict(color='#102A43',size=10),uirevision='mortgage');fig.update_yaxes(gridcolor='rgba(120,120,120,.12)');return fig
def goto(s):st.session_state.scene=s;st.rerun()
def nav(n=None):
 a,b=st.columns([5,1]);i=SCENES.index(st.session_state.scene)
 if i and a.button('← Previous'):goto(SCENES[i-1])
 if n and b.button('Continue →',type='primary',width='stretch'):goto(n)
def timeline():
 i=SCENES.index(st.session_state.scene);st.progress((i+1)/len(SCENES));cs=st.columns(len(SCENES))
 for j,(c,t) in enumerate(zip(cs,TIMES)):c.caption(('● ' if i==j else '')+t)
def header(k,t,c):st.markdown(f"<div class='eyebrow'>{k}</div><div class='title'>{t}</div><div class='copy'>{c}</div>",unsafe_allow_html=True)
def density(losses,color,name):
 h,e=np.histogram(losses,bins=75,density=True);ker=np.array([1,2,4,6,4,2,1],float);ker/=ker.sum();h=np.convolve(h,ker,'same');x=(e[:-1]+e[1:])/2
 return go.Scatter(x=x,y=h,name=name,line=dict(color=color,width=3,shape='spline'),fill='tozeroy',fillcolor='rgba(15,120,144,.13)' if color=='#0F7890' else 'rgba(199,71,75,.13)')
def compare_chart(conf):
 a=portfolio_losses(H,R,'Initial');b=portfolio_losses(H,R,'Updated');ma=historical_var_cvar(a,conf);mb=historical_var_cvar(b,conf);fig=go.Figure([density(a,'#0F7890','Initial regime'),density(b,'#C7474B','Updated regime')]);fig.add_vline(x=ma['var'],line_dash='dash',line_color='#0F7890',annotation_text=f"Initial VaR ${ma['var']:.1f}m");fig.add_vline(x=mb['var'],line_dash='dash',line_color='#C7474B',annotation_text=f"Updated VaR ${mb['var']:.1f}m");fig.add_vrect(x0=mb['var'],x1=float(np.quantile(b,.999)),fillcolor='rgba(199,71,75,.07)',line_width=0);fig.update_xaxes(title='One-day portfolio loss ($m)');fig.update_yaxes(title='Density');return style(fig,'Mortgage portfolio loss distribution: before and after the regime change',360),ma,mb

if not st.session_state.accepted:
 st.markdown("<div class='eyebrow'>BEFORE THE CASE</div>",unsafe_allow_html=True);st.title('Educational Use, Historical Context, and Attribution');st.warning('This is an original fictional teaching case inspired by the organizational structure of Margin Call (2011). The film does not identify the firm, disclose its actual holdings, or provide a replicable risk model. Mortgage pools, returns, valuations, calculations, dialogue, and outcomes in this lab are synthetic.');st.info('Historical context comes from Federal Reserve and BIS materials on subprime mortgages, ABX pricing, liquidity, and widening spreads. The case uses that context to construct a transparent VaR/CVaR exercise; it does not claim to reproduce the film’s hidden model.');ok=st.checkbox('I understand the fictional and educational nature of the case.');
 if st.button('Enter the case',type='primary',disabled=not ok):st.session_state.accepted=True;st.rerun()
 st.stop()

st.markdown("<div class='eyebrow'>BLACKRIDGE CAPITAL · MORTGAGE RISK LAB</div>",unsafe_allow_html=True);st.title('One Night Inside the Tail');timeline();st.divider();scene=st.session_state.scene

if scene=='intro':
 header('INTRO · HISTORICAL BRIDGE','Risk management before the model breaks','Begin with the risk-management introduction, then meet the team and the mortgage pools carried on Blackridge’s balance sheet.')
 l,r=st.columns([1.55,1]);
 with l:st.video(st.session_state.video)
 with r:
  st.markdown('### Learning focus');st.markdown('- Mortgage-backed security pools and tranche risk\n- External market proxies and stale marks\n- Volatility and correlation regime change\n- Historical VaR and CVaR\n- Model risk and fire-sale consequences')
 st.caption('The embedded video was supplied for the course introduction.');nav('eric')
elif scene=='eric':
 header('4:17 PM · RISK FLOOR','Eric’s unfinished model','Eric has been comparing Blackridge’s mortgage book with external market evidence. The synthetic proxy price falls sharply as the observed volatility of similar products rises.')
 l,r=st.columns([1.7,1])
 with l:
  vol=rolling_vol(H,R);fig=go.Figure();fig.add_trace(go.Scatter(x=P.date,y=P.proxy_price,name='External proxy price',line=dict(color='#C7474B',width=3)));fig.add_trace(go.Scatter(x=vol.index,y=vol*100,name='Portfolio annualized volatility (%)',yaxis='y2',line=dict(color='#0F7890',width=3)));fig.update_layout(yaxis2=dict(overlaying='y',side='right',title='Annualized volatility (%)'));st.plotly_chart(style(fig,'External pricing weakens as modeled volatility changes',350),width='stretch',config={'displayModeBar':False})
 with r:exchange('Eric Dale','Similar mortgage credit is repricing outside the firm. If those prices contain information, our historical window is no longer describing today’s market.','concerned','Sarah Robertson','External prices can reveal a regime change, but only if the model maps them to our holdings consistently.','concerned')
 nav('peter')
elif scene=='peter':
 header('6:08 PM · QUANT DESK','Peter completes the regime update','Peter repairs Eric’s model by integrating the updated covariance structure across the mortgage pools. Students can inspect the initial and updated correlation matrices.')
 a,b=st.columns(2);_,c0=covariance_tables(H,R,'Initial');_,c1=covariance_tables(H,R,'Updated')
 for col,corr,title in [(a,c0,'Initial correlation'),(b,c1,'Updated correlation')]:
  with col:
   fig=go.Figure(go.Heatmap(z=corr.values,x=[x.replace('Subprime ','SP ') for x in corr.columns],y=[x.replace('Subprime ','SP ') for x in corr.index],zmin=-1,zmax=1,colorscale='RdBu_r',colorbar=dict(title='ρ')));st.plotly_chart(style(fig,title,340),width='stretch',config={'displayModeBar':False})
 exchange('Seth Bregman','The assets did not change overnight. Why did portfolio risk change so much?','concerned','Peter Sullivan','Because volatility and dependence changed. The same exposures now generate a different loss distribution.','decisive');nav('regime')
elif scene=='regime':
 header('9:10 PM · RISK ROOM','The regime change multiplies tail risk','Compute the initial and updated one-day historical VaR and CVaR from the supplied pool-return data. Change only the confidence level; the return histories remain fixed.')
 conf=st.select_slider('Confidence level',options=[.95,.975,.99],value=st.session_state.confidence,format_func=lambda x:f'{x:.1%}');st.session_state.confidence=conf
 fig,m0,m1=compare_chart(conf);m=st.columns(6);m[0].metric('Initial VaR',f"${m0['var']:.1f}m");m[1].metric('Updated VaR',f"${m1['var']:.1f}m",f"×{m1['var']/m0['var']:.1f}",delta_color='inverse');m[2].metric('Initial CVaR',f"${m0['cvar']:.1f}m");m[3].metric('Updated CVaR',f"${m1['cvar']:.1f}m",f"×{m1['cvar']/m0['cvar']:.1f}",delta_color='inverse');m[4].metric('Initial vol',f"${m0['vol']:.1f}m");m[5].metric('Updated vol',f"${m1['vol']:.1f}m")
 st.plotly_chart(fig,width='stretch',config={'displayModeBar':False});nav('tuld')
elif scene=='tuld':
 header('12:16 AM · EXECUTIVE COMMITTEE','The model reaches Tuld','The updated model shows that the firm’s tail exposure no longer fits the old regime. Tuld concludes that the existing business model cannot survive an orderly repricing of the mortgage book.')
 exchange('Peter Sullivan','The updated covariance matrix pushes both the threshold and the average tail loss sharply higher.','decisive','John Tuld','If the market has stopped clearing at our marks, the firm must act before every holder reaches the same conclusion.','decisive')
 st.markdown("<div class='calc'><b>Historical-fiction bridge:</b> the movie establishes an unfinished risk analysis, Peter’s completion of it, senior escalation, and a liquidation decision. The specific mortgage pools and calculations here are the course’s fictional reconstruction.</div>",unsafe_allow_html=True);nav('sale')
elif scene=='sale':
 header('8:00 AM · TRADING FLOOR','Sam executes the fire sale','The desk marks the mortgage pools to synthetic liquidation discounts. The exercise connects market-risk estimates to realized execution losses and damaged market relationships.')
 discounts=np.array([.06,.12,.20,.32,.45,.55]);sale=H[['pool','exposure_mm']].copy();sale['discount_pct']=discounts*100;sale['sale_price_mm']=sale.exposure_mm*(1-discounts);sale['loss_mm']=sale.exposure_mm-sale.sale_price_mm
 fig=go.Figure(go.Bar(y=sale.pool,x=sale.loss_mm,orientation='h',marker_color=['#0F7890','#2E8292','#778F8F','#D69C35','#C96A45','#C7474B'],text=[f'${x:.0f}m' for x in sale.loss_mm],textposition='outside'));fig.update_xaxes(title='Synthetic liquidation loss ($m)');st.plotly_chart(style(fig,'Fire-sale loss by mortgage pool',350),width='stretch',config={'displayModeBar':False})
 exchange('Sam Rogers','The model tells us the tail. The market tells us the price. Selling everything converts model uncertainty into a realized loss.','concerned','Will Emerson','The deeper the discount, the faster the book moves and the more trust the desk destroys.','decisive');nav('assignment')
elif scene=='assignment':
 header('ASSIGNMENT · ANALYST MEMO','Reconstruct the model change','Students calculate initial and updated VaR/CVaR, explain the regime change, and evaluate the liquidation order using the supplied data.')
 st.markdown('''### Required analysis
1. Use `mortgage_pool_holdings.csv` to calculate portfolio weights.  
2. Use the first 250 observations in `mortgage_pool_returns.csv` to calculate initial 95%, 97.5%, and 99% historical VaR and CVaR.  
3. Repeat the calculations using the final 250 updated-regime observations.  
4. Calculate annualized volatility and the initial and updated correlation matrices.  
5. Report the multiple by which VaR and CVaR changed.  
6. Use `external_market_proxy.csv` to explain why Eric would question the original calibration.  
7. Evaluate the synthetic liquidation discounts and recommend an order of sale.  
8. Identify one model limitation and state what evidence would reverse the recommendation.

### Deliverable
Submit the completed workbook or notebook and a **750–1,000 word risk-committee memorandum**. The memorandum must explain the regime change in plain language, cite the initial and updated VaR/CVaR values, distinguish modeled tail loss from realized fire-sale loss, and address the ethical and franchise consequences of liquidating the book.''')
 c1,c2,c3=st.columns(3);c1.download_button('Download holdings',H.to_csv(index=False),'mortgage_pool_holdings.csv','text/csv',width='stretch');c2.download_button('Download returns',R.to_csv(index=False),'mortgage_pool_returns.csv','text/csv',width='stretch');c3.download_button('Download external proxy',P.to_csv(index=False),'external_market_proxy.csv','text/csv',width='stretch')
 st.markdown('### Core formulas');st.latex(r'L_t=-V_0\sum_i w_i r_{i,t}');st.latex(r'VaR_c=Q_c(L)');st.latex(r'CVaR_c=E[L\mid L\ge VaR_c]')
