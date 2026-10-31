from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='Blackridge Mortgage Regime Lab',page_icon='◈',layout='wide',initial_sidebar_state='collapsed')
ROOT=Path(__file__).resolve().parent
VIDEO_URL='https://youtu.be/BLYCx_AOgUs'

@st.cache_data(show_spinner=False)
def build_data():
    h=pd.DataFrame([
      ['Prime RMBS AAA',1400,.012,.030],['Alt-A RMBS AAA',1000,.020,.055],['Subprime 2006-2 AAA',900,.030,.090],
      ['Subprime 2006-2 BBB',600,.055,.180],['Subprime 2007-1 BBB-',500,.075,.280],['CDO Mezzanine Residual',800,.085,.350]],columns=['pool','exposure_mm','calm_vol','crisis_vol'])
    h['weight']=h.exposure_mm/h.exposure_mm.sum();rng=np.random.default_rng(2007);n=len(h)
    c0=np.full((n,n),.22);np.fill_diagonal(c0,1);c1=np.full((n,n),.62);c1[2:,2:]=.82;np.fill_diagonal(c1,1)
    v0=h.calm_vol.to_numpy()/np.sqrt(252);v1=h.crisis_vol.to_numpy()/np.sqrt(252)
    calm=rng.multivariate_normal(np.full(n,.00012),np.outer(v0,v0)*c0,250)
    crisis=rng.multivariate_normal(np.full(n,-.0009),np.outer(v1,v1)*c1,250)
    for j,mag in zip(rng.choice(250,18,False),rng.uniform(.010,.035,18)):crisis[j]-=mag*np.array([.25,.45,.70,.95,1.10,1.25])
    dates=pd.date_range('2006-07-03',periods=500,freq='B');r=pd.DataFrame(np.vstack([calm,crisis]),columns=h.pool);r.insert(0,'date',dates);r.insert(1,'regime',['Initial']*250+['Updated']*250)
    proxy=np.r_[100*np.exp(np.cumsum(rng.normal(0,.0015,250))),100*np.exp(np.cumsum(rng.normal(-.004,.012,250)))];proxy=proxy/proxy[0]*100
    return h,r,pd.DataFrame({'date':dates,'proxy_price':proxy})
H,R,P=build_data()
SCENES=['intro','eric','peter','regime','tuld','sale','assignment'];LABELS=['INTRO','4:17','6:08','9:10','12:16','8:00','ASSIGN']
for k,v in {'accepted':False,'scene':'intro','confidence':.99}.items():st.session_state.setdefault(k,v)
PEOPLE=[('Eric Dale','eric','Model risk'),('Peter Sullivan','peter','Quantitative risk'),('Seth Bregman','seth','Interpretation'),('Sarah Robertson','sarah','Governance'),('Jared Cohen','jared','Structured credit'),('Will Emerson','will','Execution'),('Sam Rogers','sam','Portfolio judgment'),('John Tuld','john','Executive synthesis')]

st.markdown('''<style>
.block-container{width:calc(100vw - 28px);max-width:none!important;padding:1rem 14px .7rem!important}.eyebrow{color:#0f7890;font-size:.72rem;font-weight:800;letter-spacing:.14em}.ttl{font:700 clamp(1.5rem,2.2vw,1.95rem) Georgia;margin:.05rem 0;color:#102a43}.copy{font:1rem/1.42 Georgia;max-width:none;margin-bottom:.55rem}.cast-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.cast-card{display:flex;flex-direction:column;align-items:flex-start;border:1px solid #cbd6dc;border-radius:12px;background:linear-gradient(145deg,#fff,#f3f7f8);padding:13px;min-height:250px;box-shadow:0 5px 16px rgba(16,42,67,.08)}.cast-card img{width:100%;height:158px;object-fit:cover;object-position:center 30%;border-radius:9px;border:1px solid #dce7eb}.cast-name{font-weight:850;color:#102a43;font-size:1rem;line-height:1.1;margin-top:10px}.cast-role{font-size:.68rem;color:#60788a;text-transform:uppercase;margin-top:4px}.cast-focus{font:italic .85rem/1.25 Georgia;color:#31546a;margin-top:7px}.dialogue{display:flex;gap:.75rem;align-items:center;border:1px solid #cbd6dc;border-radius:11px;background:white;padding:.65rem;min-height:145px}.dialogue img{width:122px;height:122px;object-fit:cover;object-position:center 32%;border-radius:10px;border:2px solid #dce7eb;flex:none}.bubble{border-left:4px solid #0f7890;background:#edf5f6;padding:.68rem .78rem;border-radius:6px;font:italic .92rem/1.36 Georgia}.role{font-size:.66rem;color:#60788a;text-transform:uppercase}.insight-card{border:1px solid #cbd6dc;border-radius:11px;background:#fff;padding:16px;min-height:145px;box-shadow:0 4px 14px rgba(16,42,67,.06)}.insight-title{font-weight:850;color:#102a43;font-size:1.02rem}.insight-copy{font:1rem/1.45 Georgia;color:#27485d;margin-top:8px}.assignment-card{border:1px solid #cbd6dc;border-radius:12px;background:#fff;padding:18px;min-height:175px;box-shadow:0 4px 14px rgba(16,42,67,.05)}.assignment-card h3{margin:.1rem 0 .5rem;font-size:1.18rem}.assignment-card p,.assignment-card li{font-size:1rem;line-height:1.5}.stButton>button{font-weight:700}[data-testid="stMetricValue"]{font-size:1.28rem}.element-container{margin-bottom:.12rem}h1{font-size:1.9rem!important;margin:.05rem 0!important}.stProgress{margin-bottom:0}.stTabs [data-baseweb="tab"]{height:34px}@media(max-width:1000px){.block-container{width:100%;padding-left:10px!important;padding-right:10px!important}.cast-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.cast-card img{height:135px}}
</style>''',unsafe_allow_html=True)

def path(key,state):return str(ROOT/'assets/expressions'/f'{key}_{state}.jpg')
def header(k,t,c):st.markdown(f"<div class='eyebrow'>{k}</div><div class='ttl'>{t}</div><div class='copy'>{c}</div>",unsafe_allow_html=True)
def goto(x):st.session_state.scene=x;st.rerun()
def nav(n=None):
    a,b=st.columns([6,1]);i=SCENES.index(st.session_state.scene)
    if i and a.button('← Previous',key=f'p{i}'):goto(SCENES[i-1])
    if n and b.button('Continue →',type='primary',width='stretch',key=f'n{i}'):goto(n)
def timeline():
    i=SCENES.index(st.session_state.scene);st.progress((i+1)/7);cs=st.columns(7)
    for j,(c,l) in enumerate(zip(cs,LABELS)):c.caption(('● ' if i==j else '')+l)
def talk(name,key,state,text):
    import base64
    raw=Path(path(key,state)).read_bytes();b64=base64.b64encode(raw).decode()
    st.markdown(f"<div class='dialogue'><img src='data:image/jpeg;base64,{b64}'><div><b>{name}</b><div class='role'>{dict((x[1],x[2]) for x in PEOPLE)[key]}</div><div class='bubble'>{text}</div></div></div>",unsafe_allow_html=True)
def cast_card(name,key,focus):
    import base64
    raw=Path(path(key,'neutral')).read_bytes();b64=base64.b64encode(raw).decode()
    descriptions={
      'eric':'Connects external mortgage pricing to a possible model-calibration failure.',
      'peter':'Repairs the covariance model and translates the regime change into VaR and CVaR.',
      'seth':'Asks the questions that expose the difference between assets and assumptions.',
      'sarah':'Challenges whether the revised model is credible, governed, and decision useful.',
      'jared':'Interprets the mortgage pools as a structured-credit business, not isolated securities.',
      'will':'Turns risk analysis into execution mechanics and fire-sale pricing.',
      'sam':'Balances modeled tail loss, realized loss, client trust, and franchise consequences.',
      'john':'Demands a concise explanation of what changed and what the firm must do next.'}
    role=dict((x[1],x[2]) for x in PEOPLE)[key]
    return f"<div class='cast-card'><img src='data:image/jpeg;base64,{b64}' alt='Editorial sketch of {name}'><div class='cast-name'>{name}</div><div class='cast-role'>{role}</div><div class='cast-focus'>{descriptions[key]}</div></div>"

def style(fig,title,h=390):
    fig.update_layout(title=dict(text=title,font=dict(size=15)),height=h,margin=dict(l=40,r=18,t=45,b=34),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#fcfbf8',font=dict(size=9,color='#102a43'),legend=dict(orientation='h',y=1.08),uirevision='v2');fig.update_yaxes(gridcolor='rgba(120,120,120,.12)');return fig
def losses(reg):return -(R[R.regime.eq(reg)][H.pool].to_numpy()@H.weight.to_numpy())*H.exposure_mm.sum()
def stats(x,c):
    v=float(np.quantile(x,c));tail=x[x>=v];return v,float(tail.mean()),float(x.std(ddof=1))
def dens(x,color,name):
    h,e=np.histogram(x,bins=65,density=True);ker=np.array([1,2,4,6,4,2,1],float);h=np.convolve(h,ker/ker.sum(),'same');m=(e[:-1]+e[1:])/2
    return go.Scatter(x=m,y=h,name=name,line=dict(color=color,width=3,shape='spline'),fill='tozeroy',fillcolor='rgba(15,120,144,.10)' if color=='#0f7890' else 'rgba(199,71,75,.10)')

if not st.session_state.accepted:
    st.markdown("<div class='eyebrow'>BEFORE THE CASE</div>",unsafe_allow_html=True);st.title('Educational Use and Historical Context')
    st.warning('Original fictional teaching case inspired by the organizational structure of Margin Call (2011). Mortgage pools, data, model, dialogue, and liquidation discounts are synthetic.')
    a,b=st.columns([2.4,1]);
    with a:st.video(VIDEO_URL)
    with b:
        st.markdown('**Before entering**');st.write('Watch the risk-management introduction, then acknowledge the fictional educational nature of the simulation.');ok=st.checkbox('I understand this is an educational simulation.');
        if st.button('Enter the case',type='primary',disabled=not ok,width='stretch'):st.session_state.accepted=True;st.rerun()
    st.stop()

st.title('One Night Inside the Tail');timeline();st.divider();s=st.session_state.scene
if s=='intro':
    header('INTRO','Meet the room','Each role enters with a scene-specific expression and a distinct analytical responsibility in the case.')
    cards=''.join(cast_card(name,key,focus) for name,key,focus in PEOPLE)
    st.markdown(f"<div class='cast-grid'>{cards}</div>",unsafe_allow_html=True)
    st.markdown('### How to read the story')
    c1,c2,c3=st.columns(3)
    with c1:st.markdown("<div class='insight-card'><div class='insight-title'>1. Evidence enters</div><div class='insight-copy'>Eric connects external mortgage-market pricing to a possible failure in the firm’s historical calibration.</div></div>",unsafe_allow_html=True)
    with c2:st.markdown("<div class='insight-card'><div class='insight-title'>2. The model changes</div><div class='insight-copy'>Peter updates volatility and dependence, producing a new distribution for the same mortgage exposures.</div></div>",unsafe_allow_html=True)
    with c3:st.markdown("<div class='insight-card'><div class='insight-title'>3. The firm acts</div><div class='insight-copy'>Tuld escalates the result and Sam converts model risk into realized fire-sale losses.</div></div>",unsafe_allow_html=True)
    with st.expander('Replay the risk-management introduction'):st.video(VIDEO_URL)
    nav('eric')
elif s=='eric':
    header('4:17 PM · RISK FLOOR','Eric questions the calibration','External prices fall while modeled volatility rises. The visual is intentionally deep enough for the audience to read the timing of the break.')
    l,r=st.columns([1.8,1])
    with l:
        x=R[H.pool].to_numpy()@H.weight.to_numpy();rv=pd.Series(x,index=R.date).rolling(30).std()*np.sqrt(252)*100
        fig=go.Figure();fig.add_trace(go.Scatter(x=P.date,y=P.proxy_price,name='External proxy',line=dict(color='#c7474b',width=3)));fig.add_trace(go.Scatter(x=rv.index,y=rv,name='Annualized vol (%)',yaxis='y2',line=dict(color='#0f7890',width=3)));fig.update_layout(yaxis2=dict(overlaying='y',side='right',title='Annualized volatility (%)'));st.plotly_chart(style(fig,'External pricing and volatility: proxy price versus modeled volatility',455),width='stretch',config={'displayModeBar':False})
    with r:talk('Eric Dale','eric','concerned','The historical window describes yesterday’s market. The external prices suggest a new regime.');talk('Sarah Robertson','sarah','concerned','Then the mapping from external evidence to our holdings must be defensible.')
    q1,q2,q3=st.columns(3)
    with q1:st.markdown("<div class='insight-card'><div class='insight-title'>What changed?</div><div class='insight-copy'>The external proxy falls while rolling portfolio volatility rises sharply around the modeled break.</div></div>",unsafe_allow_html=True)
    with q2:st.markdown("<div class='insight-card'><div class='insight-title'>Why it matters</div><div class='insight-copy'>A calm-period model will understate losses if the market has entered a different volatility regime.</div></div>",unsafe_allow_html=True)
    with q3:st.markdown("<div class='insight-card'><div class='insight-title'>Audience question</div><div class='insight-copy'>At what point does external price evidence become more credible than an internal mark?</div></div>",unsafe_allow_html=True)
    nav('peter')
elif s=='peter':
    header('6:08 PM · QUANT DESK','Peter updates covariance','The same exposures produce a different distribution when volatility and dependence rise. Larger heat maps let the audience compare clusters directly.')
    a,b=st.columns(2)
    for col,reg,title in [(a,'Initial','Initial correlation'),(b,'Updated','Updated correlation')]:
        corr=R[R.regime.eq(reg)][H.pool].corr()
        with col:
            fig=go.Figure(go.Heatmap(z=corr.values,x=[x[:10] for x in corr.columns],y=[x[:10] for x in corr.index],zmin=-1,zmax=1,colorscale='RdBu_r',showscale=True,colorbar=dict(title='ρ',len=.75)));st.plotly_chart(style(fig,title,360),width='stretch',config={'displayModeBar':False})
    x,y=st.columns(2)
    with x:talk('Seth Bregman','seth','concerned','The assets did not change overnight. Why did portfolio risk change?')
    with y:talk('Peter Sullivan','peter','decisive','Volatility and dependence changed. The same holdings now create a different loss distribution.')
    c1,c2=st.columns(2)
    with c1:st.markdown("<div class='insight-card'><div class='insight-title'>Initial regime</div><div class='insight-copy'>Lower and more dispersed correlations allow the mortgage pools to offset one another more often.</div></div>",unsafe_allow_html=True)
    with c2:st.markdown("<div class='insight-card'><div class='insight-title'>Updated regime</div><div class='insight-copy'>Correlations rise together, weakening diversification precisely when losses become larger.</div></div>",unsafe_allow_html=True)
    nav('regime')
elif s=='regime':
    header('9:10 PM · RISK ROOM','The regime multiplies tail risk','Change the confidence level. The two return histories remain fixed.')
    st.session_state.confidence=st.select_slider('Confidence level',options=[.95,.975,.99],value=st.session_state.confidence,format_func=lambda x:f'{x:.1%}')
    a,b=losses('Initial'),losses('Updated');v0,c0,sd0=stats(a,st.session_state.confidence);v1,c1,sd1=stats(b,st.session_state.confidence)
    m=st.columns(6)
    for col,(lab,val) in zip(m,[('Initial VaR',v0),('Updated VaR',v1),('Initial CVaR',c0),('Updated CVaR',c1),('Initial vol',sd0),('Updated vol',sd1)]):col.metric(lab,f'${val:.1f}m')
    fig=go.Figure([dens(a,'#0f7890','Initial'),dens(b,'#c7474b','Updated')]);fig.add_vline(x=v0,line_dash='dash',line_color='#0f7890');fig.add_vline(x=v1,line_dash='dash',line_color='#c7474b');fig.update_xaxes(title='One-day portfolio loss ($m)');st.plotly_chart(style(fig,'Mortgage portfolio loss distribution: old regime versus updated regime',430),width='stretch',config={'displayModeBar':False});nav('tuld')
elif s=='tuld':
    header('12:16 AM · EXECUTIVE COMMITTEE','The model reaches Tuld','Peter reduces the regime change to two measures: where the tail begins and how severe losses become after the threshold is crossed.')
    la,lb=losses('Initial'),losses('Updated');v0,c0,sd0=stats(la,st.session_state.confidence);v1,c1,sd1=stats(lb,st.session_state.confidence)
    left,right=st.columns(2,gap='large')
    with left:
        st.markdown('### Value at Risk: where the tail begins')
        m1,m2=st.columns(2);m1.metric('Initial VaR',f'${v0:.1f}m');m2.metric('Updated VaR',f'${v1:.1f}m',f'×{v1/v0:.1f}',delta_color='inverse')
        fig=go.Figure(go.Bar(x=['Initial regime','Updated regime'],y=[v0,v1],marker_color=['#0f7890','#c7474b'],text=[f'${v0:.1f}m',f'${v1:.1f}m'],textposition='outside'));fig.update_yaxes(title='One-day loss threshold ($m)');st.plotly_chart(style(fig,'VaR comparison',340),width='stretch',config={'displayModeBar':False})
        st.markdown("<div class='insight-card'><div class='insight-title'>Interpretation</div><div class='insight-copy'>The loss threshold moves from the calm-regime estimate to a level many times larger under the updated data.</div></div>",unsafe_allow_html=True)
    with right:
        st.markdown('### Conditional VaR: what happens inside the tail')
        m1,m2=st.columns(2);m1.metric('Initial CVaR',f'${c0:.1f}m');m2.metric('Updated CVaR',f'${c1:.1f}m',f'×{c1/c0:.1f}',delta_color='inverse')
        fig=go.Figure(go.Bar(x=['Initial regime','Updated regime'],y=[c0,c1],marker_color=['#6aa6b0','#8f2230'],text=[f'${c0:.1f}m',f'${c1:.1f}m'],textposition='outside'));fig.update_yaxes(title='Average loss beyond VaR ($m)');st.plotly_chart(style(fig,'CVaR comparison',340),width='stretch',config={'displayModeBar':False})
        st.markdown("<div class='insight-card'><div class='insight-title'>Interpretation</div><div class='insight-copy'>The problem is not only a higher threshold. Average losses after crossing that threshold have also multiplied.</div></div>",unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:talk('Peter Sullivan','peter','decisive','Updated volatility and correlation move both the boundary and the severity beyond it.')
    with b:talk('John Tuld','john','decisive','If both the threshold and the tail have broken the old assumptions, delay compounds the problem.')
    nav('sale')
elif s=='sale':
    header('8:00 AM · TRADING FLOOR','Sam executes the fire sale','Synthetic discounts convert modeled risk into realized execution loss. The larger chart gives the audience room to compare position size and discount severity.')
    d=np.array([.06,.12,.20,.32,.45,.55]);sale=H.copy();sale['loss']=sale.exposure_mm*d
    fig=go.Figure(go.Bar(y=sale.pool,x=sale.loss,orientation='h',marker_color=['#0f7890','#318a98','#7f9692','#d69c35','#ca6a45','#c7474b'],text=[f'${x:.0f}m' for x in sale.loss],textposition='outside'));fig.update_xaxes(title='Synthetic liquidation loss ($m)')
    l,r=st.columns([1.75,1])
    with l:st.plotly_chart(style(fig,'Fire-sale loss by mortgage pool',475),width='stretch',config={'displayModeBar':False})
    with r:talk('Sam Rogers','sam','concerned','The model describes the tail. The sale turns uncertainty into a realized loss.');talk('Will Emerson','will','decisive','Faster execution requires deeper discounts and damages market relationships.')
    x1,x2,x3=st.columns(3)
    with x1:st.markdown(f"<div class='insight-card'><div class='insight-title'>Total realized loss</div><div class='insight-copy'>${sale['loss'].sum():,.0f} million under the synthetic liquidation schedule.</div></div>",unsafe_allow_html=True)
    with x2:st.markdown("<div class='insight-card'><div class='insight-title'>Largest source</div><div class='insight-copy'>The CDO mezzanine residual produces the largest dollar loss because the position is large and the discount is deepest.</div></div>",unsafe_allow_html=True)
    with x3:st.markdown("<div class='insight-card'><div class='insight-title'>Audience question</div><div class='insight-copy'>Does an immediate sale protect the firm, or transfer uncertainty into a certain and reputationally costly loss?</div></div>",unsafe_allow_html=True)
    nav('assignment')
elif s=='assignment':
    header('ASSIGNMENT','Risk-committee memorandum','Reconstruct the initial model, quantify the regime change, and evaluate the consequences of liquidating the mortgage book.')
    a,b=st.columns([1.15,1],gap='large')
    with a:st.markdown("<div class='assignment-card'><h3>Required quantitative analysis</h3><ol><li>Calculate exposure weights for the six mortgage pools.</li><li>Calculate 95%, 97.5%, and 99% historical VaR and CVaR for each 250-day regime.</li><li>Calculate annualized portfolio volatility for both regimes.</li><li>Produce and interpret the initial and updated correlation matrices.</li><li>Report the multiples by which VaR and CVaR changed.</li></ol></div>",unsafe_allow_html=True)
    with b:st.markdown("<div class='assignment-card'><h3>Required risk judgment</h3><ol><li>Explain why external market pricing could invalidate the original calibration.</li><li>Distinguish modeled tail loss from realized fire-sale loss.</li><li>Evaluate the order of liquidation and its franchise consequences.</li><li>Identify one model limitation and one reversal condition.</li><li>Submit a 750–1,000 word risk-committee memorandum.</li></ol></div>",unsafe_allow_html=True)
    st.markdown('### Case data files')
    c1,c2,c3=st.columns(3)
    with c1:
        st.markdown("<div class='assignment-card'><h3>Mortgage Pool Holdings</h3><p>Exposure, calm volatility, crisis volatility, and portfolio weight for each of the six pools.</p></div>",unsafe_allow_html=True);st.download_button('Download mortgage_pool_holdings.csv',H.to_csv(index=False),'mortgage_pool_holdings.csv','text/csv',width='stretch')
    with c2:
        st.markdown("<div class='assignment-card'><h3>Mortgage Pool Returns</h3><p>Five hundred synthetic daily observations divided into initial and updated 250-day regimes.</p></div>",unsafe_allow_html=True);st.download_button('Download mortgage_pool_returns.csv',R.to_csv(index=False),'mortgage_pool_returns.csv','text/csv',width='stretch')
    with c3:
        st.markdown("<div class='assignment-card'><h3>External Market Proxy</h3><p>Synthetic external price series used to motivate Eric’s challenge to the original calibration.</p></div>",unsafe_allow_html=True);st.download_button('Download external_market_proxy.csv',P.to_csv(index=False),'external_market_proxy.csv','text/csv',width='stretch')
    st.markdown('### Core formulas')
    f1,f2,f3=st.columns(3);f1.latex(r'L_t=-V_0\sum_i w_ir_{i,t}');f2.latex(r'VaR_c=Q_c(L)');f3.latex(r'CVaR_c=E[L\mid L\ge VaR_c]')
