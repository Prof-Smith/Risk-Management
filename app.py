from __future__ import annotations
from pathlib import Path
import numpy as np, pandas as pd, plotly.graph_objects as go, streamlit as st
st.set_page_config(page_title='Blackridge Mortgage Regime Lab',page_icon='◈',layout='wide',initial_sidebar_state='collapsed')
ROOT=Path(__file__).resolve().parent

def build_data():
    h=pd.DataFrame([
      ['Prime RMBS AAA',1400,.012,.030],['Alt-A RMBS AAA',1000,.020,.055],['Subprime 2006-2 AAA',900,.030,.090],
      ['Subprime 2006-2 BBB',600,.055,.180],['Subprime 2007-1 BBB-',500,.075,.280],['CDO Mezzanine Residual',800,.085,.350]],columns=['pool','exposure_mm','calm_vol','crisis_vol'])
    h['weight']=h.exposure_mm/h.exposure_mm.sum(); rng=np.random.default_rng(2007);n=len(h)
    c0=np.full((n,n),.22);np.fill_diagonal(c0,1);c1=np.full((n,n),.62);c1[2:,2:]=.82;np.fill_diagonal(c1,1)
    v0=h.calm_vol.to_numpy()/np.sqrt(252);v1=h.crisis_vol.to_numpy()/np.sqrt(252)
    a=rng.multivariate_normal(np.full(n,.00012),np.outer(v0,v0)*c0,250)
    b=rng.multivariate_normal(np.full(n,-.0009),np.outer(v1,v1)*c1,250)
    for j,mag in zip(rng.choice(250,18,False),rng.uniform(.010,.035,18)): b[j]-=mag*np.array([.25,.45,.70,.95,1.10,1.25])
    dates=pd.date_range('2006-07-03',periods=500,freq='B');r=pd.DataFrame(np.vstack([a,b]),columns=h.pool);r.insert(0,'date',dates);r.insert(1,'regime',['Initial']*250+['Updated']*250)
    proxy=np.r_[100*np.exp(np.cumsum(rng.normal(0,.0015,250))),100*np.exp(np.cumsum(rng.normal(-.004,.012,250)))];proxy=proxy/proxy[0]*100
    p=pd.DataFrame({'date':dates,'proxy_price':proxy});return h,r,p
H,R,P=build_data()
SCENES=['intro','eric','peter','regime','tuld','sale','assignment'];LABELS=['INTRO','4:17','6:08','9:10','12:16','8:00','ASSIGN']
for k,v in {'accepted':False,'scene':'intro','confidence':.99}.items():st.session_state.setdefault(k,v)
PEOPLE=[('Eric Dale','eric','Model risk'),('Peter Sullivan','peter','Quantitative risk'),('Seth Bregman','seth','Analyst interpretation'),('Sarah Robertson','sarah','Governance'),('Jared Cohen','jared','Structured credit'),('Will Emerson','will','Execution'),('Sam Rogers','sam','Portfolio management'),('John Tuld','john','Executive synthesis')]
st.markdown('''<style>
.block-container{max-width:1280px;padding-top:.25rem;padding-bottom:.35rem}.eyebrow{color:#0f7890;font-size:.68rem;font-weight:800;letter-spacing:.13em}.ttl{font:700 1.65rem Georgia;margin:0;color:#102a43}.copy{font: .94rem/1.35 Georgia;max-width:1050px}.card{border:1px solid #cad6dc;border-radius:9px;background:white;padding:.35rem}.speech{border-left:4px solid #0f7890;background:#eef6f7;padding:.55rem .7rem;border-radius:6px;font:italic .84rem/1.3 Georgia}.stButton>button{font-weight:700}[data-testid="stMetricValue"]{font-size:1.22rem}.element-container{margin-bottom:.1rem}h1{font-size:1.8rem!important;margin:.05rem 0!important}div[data-testid="stImage"] img{max-height:135px;object-fit:cover;border-radius:8px}.stProgress{margin-bottom:0}
</style>''',unsafe_allow_html=True)
def header(k,t,c):st.markdown(f"<div class='eyebrow'>{k}</div><div class='ttl'>{t}</div><div class='copy'>{c}</div>",unsafe_allow_html=True)
def goto(x):st.session_state.scene=x;st.rerun()
def nav(n=None):
 a,b=st.columns([6,1]);i=SCENES.index(st.session_state.scene)
 if i and a.button('← Previous'):goto(SCENES[i-1])
 if n and b.button('Continue →',type='primary',width='stretch'):goto(n)
def timeline():
 i=SCENES.index(st.session_state.scene);st.progress((i+1)/7);cs=st.columns(7)
 for j,(c,l) in enumerate(zip(cs,LABELS)):c.caption(('● ' if i==j else '')+l)
def portrait(key):return str(ROOT/'assets/portraits'/f'{key}.jpg')
def dialogue(name,key,text):
 c1,c2=st.columns([1,2.4]);
 with c1:st.image(portrait(key),width='stretch')
 with c2:st.markdown(f"**{name}**");st.markdown(f"<div class='speech'>{text}</div>",unsafe_allow_html=True)
def style(fig,title,h=285):
 fig.update_layout(title=dict(text=title,font=dict(size=16)),height=h,margin=dict(l=35,r=15,t=48,b=35),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#fcfbf8',font=dict(size=10,color='#102a43'),legend=dict(orientation='h',y=1.08),uirevision='compact');fig.update_yaxes(gridcolor='rgba(120,120,120,.12)');return fig
def losses(reg):return -(R[R.regime.eq(reg)][H.pool].to_numpy()@H.weight.to_numpy())*H.exposure_mm.sum()
def stats(x,c):
 v=float(np.quantile(x,c));tail=x[x>=v];return v,float(tail.mean()),float(x.std(ddof=1))
def dens(x,color,name):
 h,e=np.histogram(x,bins=65,density=True);ker=np.array([1,2,4,6,4,2,1],float);h=np.convolve(h,ker/ker.sum(),'same');m=(e[:-1]+e[1:])/2
 return go.Scatter(x=m,y=h,name=name,line=dict(color=color,width=3,shape='spline'),fill='tozeroy',fillcolor='rgba(15,120,144,.10)' if color=='#0f7890' else 'rgba(199,71,75,.10)')
if not st.session_state.accepted:
 st.title('Educational Use and Historical Context');st.warning('Original fictional teaching case inspired by the organizational structure of Margin Call (2011). Mortgage pools, data, model, dialogue, and liquidation discounts are synthetic.');ok=st.checkbox('I understand this is an educational simulation.');
 if st.button('Enter',type='primary',disabled=not ok):st.session_state.accepted=True;st.rerun()
 st.stop()
st.title('One Night Inside the Tail');timeline();st.divider();s=st.session_state.scene
if s=='intro':
 header('INTRO','Meet the room','A compact cast strip defines the analytical role of each participant before the case begins.')
 cols=st.columns(4,gap='small')
 for i,(name,key,focus) in enumerate(PEOPLE):
  with cols[i%4]:
   with st.container(border=True):st.image(portrait(key),width='stretch');st.markdown(f"**{name}**  \
{focus}")
 st.caption('Video introduction: use the supplied course video before beginning the 4:17 p.m. scene.');nav('eric')
elif s=='eric':
 header('4:17 PM · RISK FLOOR','Eric questions the calibration','External prices for similar mortgage credit fall while modeled portfolio volatility rises.')
 l,r=st.columns([1.8,1])
 with l:
  x=R[H.pool].to_numpy()@H.weight.to_numpy();rv=pd.Series(x,index=R.date).rolling(30).std()*np.sqrt(252)*100
  fig=go.Figure();fig.add_trace(go.Scatter(x=P.date,y=P.proxy_price,name='External proxy',line=dict(color='#c7474b',width=3)));fig.add_trace(go.Scatter(x=rv.index,y=rv,name='Annualized vol (%)',yaxis='y2',line=dict(color='#0f7890',width=3)));fig.update_layout(yaxis2=dict(overlaying='y',side='right'));st.plotly_chart(style(fig,'External pricing and volatility',300),width='stretch',config={'displayModeBar':False})
 with r:dialogue('Eric Dale','eric','The historical window still describes yesterday’s market. The external prices suggest a new regime.');dialogue('Sarah Robertson','sarah','Then the mapping from external evidence to our holdings must be defensible.')
 nav('peter')
elif s=='peter':
 header('6:08 PM · QUANT DESK','Peter updates covariance','The same exposures produce a different distribution when volatility and dependence rise.')
 a,b=st.columns(2)
 for col,reg,title in [(a,'Initial','Initial correlation'),(b,'Updated','Updated correlation')]:
  corr=R[R.regime.eq(reg)][H.pool].corr();
  with col:
   fig=go.Figure(go.Heatmap(z=corr.values,x=[x[:11] for x in corr.columns],y=[x[:11] for x in corr.index],zmin=-1,zmax=1,colorscale='RdBu_r',showscale=False));st.plotly_chart(style(fig,title,255),width='stretch',config={'displayModeBar':False})
 x,y=st.columns(2)
 with x:dialogue('Seth Bregman','seth','The assets did not change overnight. Why did portfolio risk change?')
 with y:dialogue('Peter Sullivan','peter','Volatility and dependence changed. The same holdings now create a different loss distribution.')
 nav('regime')
elif s=='regime':
 header('9:10 PM · RISK ROOM','The regime multiplies tail risk','Change only the confidence level. The two return histories remain fixed.')
 st.session_state.confidence=st.select_slider('Confidence level',options=[.95,.975,.99],value=st.session_state.confidence,format_func=lambda x:f'{x:.1%}')
 a,b=losses('Initial'),losses('Updated');v0,c0,sd0=stats(a,st.session_state.confidence);v1,c1,sd1=stats(b,st.session_state.confidence)
 m=st.columns(6)
 for col,(lab,val) in zip(m,[('Initial VaR',v0),('Updated VaR',v1),('Initial CVaR',c0),('Updated CVaR',c1),('Initial vol',sd0),('Updated vol',sd1)]):col.metric(lab,f'${val:.1f}m')
 fig=go.Figure([dens(a,'#0f7890','Initial'),dens(b,'#c7474b','Updated')]);fig.add_vline(x=v0,line_dash='dash',line_color='#0f7890');fig.add_vline(x=v1,line_dash='dash',line_color='#c7474b');fig.update_xaxes(title='One-day portfolio loss ($m)');st.plotly_chart(style(fig,'Mortgage portfolio loss distribution',310),width='stretch',config={'displayModeBar':False});nav('tuld')
elif s=='tuld':
 header('12:16 AM · EXECUTIVE COMMITTEE','The model reaches Tuld','The updated risk estimate no longer fits the old business assumptions.')
 a,b=st.columns(2)
 with a:dialogue('Peter Sullivan','peter','Updated volatility and correlation push both VaR and CVaR sharply higher.')
 with b:dialogue('John Tuld','john','If the market no longer clears near our marks, delay compounds the problem.')
 nav('sale')
elif s=='sale':
 header('8:00 AM · TRADING FLOOR','Sam executes the fire sale','Synthetic discounts convert modeled risk into realized execution loss.')
 d=np.array([.06,.12,.20,.32,.45,.55]);sale=H.copy();sale['loss']=sale.exposure_mm*d
 fig=go.Figure(go.Bar(y=sale.pool,x=sale.loss,orientation='h',marker_color=['#0f7890','#318a98','#7f9692','#d69c35','#ca6a45','#c7474b'],text=[f'${x:.0f}m' for x in sale.loss],textposition='outside'));fig.update_xaxes(title='Synthetic liquidation loss ($m)')
 l,r=st.columns([1.8,1])
 with l:st.plotly_chart(style(fig,'Fire-sale loss by pool',300),width='stretch',config={'displayModeBar':False})
 with r:dialogue('Sam Rogers','sam','The model describes the tail. The sale turns uncertainty into a realized loss.');dialogue('Will Emerson','will','Faster execution requires deeper discounts and damages market relationships.')
 nav('assignment')
elif s=='assignment':
 header('ASSIGNMENT','Analyst memo','Calculate initial and updated VaR/CVaR and explain the regime change.')
 st.markdown('''1. Calculate weights from the six mortgage pools.  
2. Calculate 95%, 97.5%, and 99% historical VaR and CVaR for each 250-day regime.  
3. Compare annualized volatility and correlation matrices.  
4. Explain why external pricing could invalidate the original calibration.  
5. Evaluate the fire-sale order and distinguish modeled loss from realized loss.  
6. Submit a 750–1,000 word risk-committee memorandum.''')
 c1,c2=st.columns(2);c1.download_button('Download holdings',H.to_csv(index=False),'mortgage_pool_holdings.csv','text/csv',width='stretch');c2.download_button('Download returns',R.to_csv(index=False),'mortgage_pool_returns.csv','text/csv',width='stretch')
