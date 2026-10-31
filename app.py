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
.block-container{width:calc(100vw - 28px);max-width:none!important;padding:1.0rem 14px .65rem!important}.eyebrow{color:#0f7890;font-size:.68rem;font-weight:800;letter-spacing:.13em}.ttl{font:700 clamp(1.35rem,2vw,1.72rem) Georgia;margin:.05rem 0;color:#102a43}.copy{font:.92rem/1.35 Georgia;max-width:none;margin-bottom:.35rem}.cast-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.cast-card{display:flex;align-items:center;gap:10px;border:1px solid #cbd6dc;border-radius:10px;background:#fff;padding:9px 10px;min-height:96px;box-shadow:0 2px 8px rgba(16,42,67,.06)}.cast-card img{width:72px;height:72px;object-fit:cover;object-position:center 35%;border-radius:50%;border:2px solid #dce7eb;flex:none}.cast-name{font-weight:800;color:#102a43;line-height:1.1}.cast-role{font-size:.67rem;color:#60788a;text-transform:uppercase;margin-top:3px}.cast-focus{font:italic .77rem/1.2 Georgia;color:#31546a;margin-top:5px}.dialogue{display:flex;gap:.55rem;align-items:center;border:1px solid #cbd6dc;border-radius:9px;background:white;padding:.42rem;min-height:112px}.dialogue img{width:92px;height:92px;object-fit:cover;object-position:center 35%;border-radius:50%;border:2px solid #dce7eb;flex:none}.bubble{border-left:4px solid #0f7890;background:#edf5f6;padding:.5rem .6rem;border-radius:5px;font:italic .82rem/1.28 Georgia}.role{font-size:.63rem;color:#60788a;text-transform:uppercase}.stButton>button{font-weight:700}[data-testid="stMetricValue"]{font-size:1.18rem}.element-container{margin-bottom:.08rem}h1{font-size:1.78rem!important;margin:.05rem 0!important}.stProgress{margin-bottom:0}.stTabs [data-baseweb="tab"]{height:32px}@media(max-width:900px){.block-container{width:100%;padding-left:10px!important;padding-right:10px!important}.cast-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
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
    return f"<div class='cast-card'><img src='data:image/jpeg;base64,{b64}' alt='Editorial sketch of {name}'><div><div class='cast-name'>{name}</div><div class='cast-role'>{dict((x[1],x[2]) for x in PEOPLE)[key]}</div><div class='cast-focus'>{focus}</div></div></div>"

def style(fig,title,h=278):
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
    header('INTRO','Meet the room','Each role enters with a scene-specific neutral, concerned, or decisive expression. The full video remains available below the cast.')
    cards=''.join(cast_card(name,key,focus) for name,key,focus in PEOPLE)
    st.markdown(f"<div class='cast-grid'>{cards}</div>",unsafe_allow_html=True)
    with st.expander('Replay the risk-management introduction'):st.video(VIDEO_URL)
    nav('eric')
elif s=='eric':
    header('4:17 PM · RISK FLOOR','Eric questions the calibration','External prices fall while modeled volatility rises.')
    l,r=st.columns([1.8,1])
    with l:
        x=R[H.pool].to_numpy()@H.weight.to_numpy();rv=pd.Series(x,index=R.date).rolling(30).std()*np.sqrt(252)*100
        fig=go.Figure();fig.add_trace(go.Scatter(x=P.date,y=P.proxy_price,name='External proxy',line=dict(color='#c7474b',width=3)));fig.add_trace(go.Scatter(x=rv.index,y=rv,name='Annualized vol (%)',yaxis='y2',line=dict(color='#0f7890',width=3)));fig.update_layout(yaxis2=dict(overlaying='y',side='right'));st.plotly_chart(style(fig,'External pricing and volatility',292),width='stretch',config={'displayModeBar':False})
    with r:talk('Eric Dale','eric','concerned','The historical window describes yesterday’s market. The external prices suggest a new regime.');talk('Sarah Robertson','sarah','concerned','Then the mapping from external evidence to our holdings must be defensible.')
    nav('peter')
elif s=='peter':
    header('6:08 PM · QUANT DESK','Peter updates covariance','The same exposures produce a different distribution when volatility and dependence rise.')
    a,b=st.columns(2)
    for col,reg,title in [(a,'Initial','Initial correlation'),(b,'Updated','Updated correlation')]:
        corr=R[R.regime.eq(reg)][H.pool].corr()
        with col:
            fig=go.Figure(go.Heatmap(z=corr.values,x=[x[:10] for x in corr.columns],y=[x[:10] for x in corr.index],zmin=-1,zmax=1,colorscale='RdBu_r',showscale=False));st.plotly_chart(style(fig,title,225),width='stretch',config={'displayModeBar':False})
    x,y=st.columns(2)
    with x:talk('Seth Bregman','seth','concerned','The assets did not change overnight. Why did portfolio risk change?')
    with y:talk('Peter Sullivan','peter','decisive','Volatility and dependence changed. The same holdings now create a different loss distribution.')
    nav('regime')
elif s=='regime':
    header('9:10 PM · RISK ROOM','The regime multiplies tail risk','Change the confidence level. The two return histories remain fixed.')
    st.session_state.confidence=st.select_slider('Confidence level',options=[.95,.975,.99],value=st.session_state.confidence,format_func=lambda x:f'{x:.1%}')
    a,b=losses('Initial'),losses('Updated');v0,c0,sd0=stats(a,st.session_state.confidence);v1,c1,sd1=stats(b,st.session_state.confidence)
    m=st.columns(6)
    for col,(lab,val) in zip(m,[('Initial VaR',v0),('Updated VaR',v1),('Initial CVaR',c0),('Updated CVaR',c1),('Initial vol',sd0),('Updated vol',sd1)]):col.metric(lab,f'${val:.1f}m')
    fig=go.Figure([dens(a,'#0f7890','Initial'),dens(b,'#c7474b','Updated')]);fig.add_vline(x=v0,line_dash='dash',line_color='#0f7890');fig.add_vline(x=v1,line_dash='dash',line_color='#c7474b');fig.update_xaxes(title='One-day portfolio loss ($m)');st.plotly_chart(style(fig,'Mortgage portfolio loss distribution',298),width='stretch',config={'displayModeBar':False});nav('tuld')
elif s=='tuld':
    header('12:16 AM · EXECUTIVE COMMITTEE','The model reaches Tuld','The updated estimate no longer fits the old business assumptions.')
    a,b=st.columns(2)
    with a:talk('Peter Sullivan','peter','decisive','Updated volatility and correlation push both VaR and CVaR sharply higher.')
    with b:talk('John Tuld','john','decisive','If the market no longer clears near our marks, delay compounds the problem.')
    nav('sale')
elif s=='sale':
    header('8:00 AM · TRADING FLOOR','Sam executes the fire sale','Synthetic discounts convert modeled risk into realized execution loss.')
    d=np.array([.06,.12,.20,.32,.45,.55]);sale=H.copy();sale['loss']=sale.exposure_mm*d
    fig=go.Figure(go.Bar(y=sale.pool,x=sale.loss,orientation='h',marker_color=['#0f7890','#318a98','#7f9692','#d69c35','#ca6a45','#c7474b'],text=[f'${x:.0f}m' for x in sale.loss],textposition='outside'));fig.update_xaxes(title='Synthetic liquidation loss ($m)')
    l,r=st.columns([1.8,1])
    with l:st.plotly_chart(style(fig,'Fire-sale loss by pool',292),width='stretch',config={'displayModeBar':False})
    with r:talk('Sam Rogers','sam','concerned','The model describes the tail. The sale turns uncertainty into a realized loss.');talk('Will Emerson','will','decisive','Faster execution requires deeper discounts and damages market relationships.')
    nav('assignment')
elif s=='assignment':
    header('ASSIGNMENT','Analyst memo','Calculate initial and updated VaR/CVaR and explain the regime change.')
    st.markdown('''1. Calculate weights for the six pools.  
2. Calculate 95%, 97.5%, and 99% historical VaR and CVaR for each 250-day regime.  
3. Compare volatility and correlation matrices.  
4. Explain why external pricing could invalidate the calibration.  
5. Evaluate the sale order and distinguish modeled from realized loss.  
6. Submit a 750–1,000 word risk-committee memorandum.''')
    c1,c2,c3=st.columns(3);c1.download_button('Holdings CSV',H.to_csv(index=False),'mortgage_pool_holdings.csv','text/csv',width='stretch');c2.download_button('Returns CSV',R.to_csv(index=False),'mortgage_pool_returns.csv','text/csv',width='stretch');c3.download_button('Proxy CSV',P.to_csv(index=False),'external_market_proxy.csv','text/csv',width='stretch')
