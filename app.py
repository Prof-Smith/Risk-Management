from __future__ import annotations
from pathlib import Path
import base64,numpy as np,pandas as pd,plotly.graph_objects as go,streamlit as st
st.set_page_config(page_title='Blackridge Mortgage Regime Lab',page_icon='◈',layout='wide',initial_sidebar_state='collapsed')
ROOT=Path(__file__).resolve().parent;VIDEO='https://youtu.be/BLYCx_AOgUs'
@st.cache_data(show_spinner=False)
def data():
 h=pd.DataFrame([['Prime RMBS AAA',1400,.012,.030],['Alt-A RMBS AAA',1000,.020,.055],['Subprime 2006-2 AAA',900,.030,.090],['Subprime 2006-2 BBB',600,.055,.180],['Subprime 2007-1 BBB-',500,.075,.280],['CDO Mezzanine Residual',800,.085,.350]],columns=['pool','exposure_mm','calm_vol','crisis_vol']);h['weight']=h.exposure_mm/h.exposure_mm.sum();rng=np.random.default_rng(2007);n=len(h);c0=np.full((n,n),.22);np.fill_diagonal(c0,1);c1=np.full((n,n),.62);c1[2:,2:]=.82;np.fill_diagonal(c1,1);v0=h.calm_vol.values/np.sqrt(252);v1=h.crisis_vol.values/np.sqrt(252);a=rng.multivariate_normal(np.full(n,.00012),np.outer(v0,v0)*c0,250);b=rng.multivariate_normal(np.full(n,-.0009),np.outer(v1,v1)*c1,250)
 for j,m in zip(rng.choice(250,18,False),rng.uniform(.010,.035,18)):b[j]-=m*np.array([.25,.45,.70,.95,1.10,1.25])
 dates=pd.date_range('2006-07-03',periods=500,freq='B');r=pd.DataFrame(np.vstack([a,b]),columns=h.pool);r.insert(0,'date',dates);r.insert(1,'regime',['Initial']*250+['Updated']*250);px=np.r_[100*np.exp(np.cumsum(rng.normal(0,.0015,250))),100*np.exp(np.cumsum(rng.normal(-.004,.012,250)))];px=px/px[0]*100;return h,r,pd.DataFrame({'date':dates,'proxy_price':px})
H,R,P=data();SC=['intro','eric','peter','regime','tuld','sale','assignment'];LAB=['INTRO','4:17','6:08','9:10','12:16','8:00','ASSIGN']
for k,v in {'accepted':False,'scene':'intro','confidence':.99}.items():st.session_state.setdefault(k,v)
st.markdown('''<style>
.block-container{width:calc(100vw - 28px);max-width:none!important;padding:1rem 14px!important}
.eyebrow{color:#0f7890;font-size:.72rem;font-weight:800;letter-spacing:.14em}
.ttl{font:700 1.9rem Georgia;margin:.05rem 0}.copy{font:1rem/1.42 Georgia}
.dialogue{display:flex;gap:1rem;align-items:center;border:1px solid #cbd6dc;border-radius:11px;background:#fff;padding:.85rem;min-height:164px}
.dialogue img{width:142px;height:142px;object-fit:cover;object-position:center 35%;border-radius:11px;flex:none}
.dialogue b{font-size:1.08rem;color:#102a43}.bubble{border-left:5px solid #0f7890;background:#edf5f6;padding:.8rem .9rem;font:italic 1.02rem/1.42 Georgia}
.insight{border:1px solid #cbd6dc;border-radius:11px;background:#fff;padding:18px;min-height:142px;font-size:1.05rem;line-height:1.48;box-shadow:0 3px 10px rgba(16,42,67,.05)}
.insight strong,.insight b{font-size:1.12rem;color:#102a43}
.takeaway-tile{border:1px solid #cbd6dc;border-radius:11px;background:linear-gradient(145deg,#fff,#f3f8f9);padding:18px;min-height:150px;font-size:1.03rem;line-height:1.48}
.takeaway-title{font-size:1.12rem;font-weight:800;color:#102a43;margin-bottom:8px}
.interpretation{border:1px solid #cbd6dc;border-radius:11px;background:#fff;padding:20px;min-height:155px;font-size:1.08rem;line-height:1.5}
.interpretation b{font-size:1.18rem;color:#102a43}
.assignment{border:1px solid #cbd6dc;border-radius:12px;background:#fff;padding:24px;min-height:330px;box-shadow:0 4px 14px rgba(16,42,67,.06)}
.assignment h3{font-size:1.5rem;margin:.1rem 0 .75rem;color:#102a43}.assignment li,.assignment p{font-size:1.12rem;line-height:1.62;margin-bottom:.48rem}
.assignment-note{border-left:6px solid #f3911b;background:#fff8e9;padding:18px 20px;border-radius:8px;font-size:1.08rem;line-height:1.5}
[data-testid="stMetricValue"]{font-size:1.28rem}.stButton>button{font-weight:700}
</style>''',unsafe_allow_html=True)
def header(k,t,c):st.markdown(f"<div class='eyebrow'>{k}</div><div class='ttl'>{t}</div><div class='copy'>{c}</div>",unsafe_allow_html=True)
def goto_scene(x):st.session_state.scene=x;st.rerun()
def nav(n=None):
 a,b=st.columns([6,1]);i=SC.index(st.session_state.scene)
 if i and a.button('← Previous'):goto_scene(SC[i-1])
 if n and b.button('Continue →',type='primary',width='stretch'):goto_scene(n)
def timeline():
 i=SC.index(st.session_state.scene);st.progress((i+1)/7);cs=st.columns(7)
 for j,(c,l) in enumerate(zip(cs,LAB)):c.caption(('● ' if i==j else '')+l)
def portrait(k,s):return ROOT/'assets/expressions'/f'{k}_{s}.jpg'
def talk(name,k,state,text):
 b64=base64.b64encode(portrait(k,state).read_bytes()).decode();st.markdown(f"<div class='dialogue'><img src='data:image/jpeg;base64,{b64}'><div><b>{name}</b><div class='bubble'>{text}</div></div></div>",unsafe_allow_html=True)
def style(f,t,h=390):f.update_layout(title=t,height=h,margin=dict(l=40,r=20,t=50,b=40),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#fcfbf8',font=dict(size=10),legend=dict(orientation='h',y=1.08),uirevision='v5');f.update_yaxes(gridcolor='rgba(120,120,120,.12)');return f
def losses(reg):return -(R[R.regime.eq(reg)][H.pool].values@H.weight.values)*H.exposure_mm.sum()
def stats(x,c):v=float(np.quantile(x,c));return v,float(x[x>=v].mean()),float(x.std(ddof=1))
def density(x,color,name):
 h,e=np.histogram(x,bins=65,density=True);k=np.array([1,2,4,6,4,2,1],float);h=np.convolve(h,k/k.sum(),'same');m=(e[:-1]+e[1:])/2;return go.Scatter(x=m,y=h,name=name,line=dict(color=color,width=3,shape='spline'),fill='tozeroy',fillcolor='rgba(15,120,144,.1)' if color=='#0f7890' else 'rgba(199,71,75,.1)')
if not st.session_state.accepted:
 st.title('Educational Use and Historical Context');st.warning('Original fictional teaching case inspired by Margin Call (2011). Mortgage pools, data, model, dialogue, and liquidation discounts are synthetic.');a,b=st.columns([2.3,1]);
 with a:st.video(VIDEO)
 with b:
  ok=st.checkbox('I understand this is an educational simulation.')
  if st.button('Enter the case',type='primary',disabled=not ok,width='stretch'):st.session_state.accepted=True;st.rerun()
 st.stop()
st.title('One Night Inside the Tail');timeline();st.divider();s=st.session_state.scene
if s=='intro':
 header('INTRO','Meet the room','One consolidated storyboard introduces the eight employees, their positions, and the analytical perspective each person brings to the overnight crisis.')
 st.image(str(ROOT/'assets/blackridge_employee_profiles.png'),width='stretch')
 c1,c2,c3=st.columns(3)
 with c1:st.markdown("<div class='insight'><b>1. Evidence enters</b><br><br>Eric connects external mortgage pricing to a possible failure in the historical calibration. The question is whether outside prices now describe the portfolio better than the firm’s internal marks.</div>",unsafe_allow_html=True)
 with c2:st.markdown("<div class='insight'><b>2. The model changes</b><br><br>Peter integrates updated volatility and dependence into the same mortgage exposures. The holdings stay fixed, but the modeled loss distribution changes.</div>",unsafe_allow_html=True)
 with c3:st.markdown("<div class='insight'><b>3. The firm acts</b><br><br>Tuld escalates the result and Sam converts modeled uncertainty into realized losses. The model becomes an institutional decision.</div>",unsafe_allow_html=True)
 with st.expander('Replay the risk-management introduction'):st.video(VIDEO)
 nav('eric')
elif s=='eric':
 header('4:17 PM · RISK FLOOR','Eric questions the calibration','External prices fall while modeled volatility rises.')
 l,r=st.columns([1.72,1])
 x=R[H.pool].values@H.weight.values;rv=pd.Series(x,index=R.date).rolling(30).std()*np.sqrt(252)*100
 with l:
  f=go.Figure();f.add_trace(go.Scatter(x=P.date,y=P.proxy_price,name='External proxy',line=dict(color='#c7474b',width=3)));f.add_trace(go.Scatter(x=rv.index,y=rv,name='Annualized vol (%)',yaxis='y2',line=dict(color='#0f7890',width=3)));f.update_layout(yaxis2=dict(overlaying='y',side='right'));st.plotly_chart(style(f,'External pricing and volatility',455),width='stretch',config={'displayModeBar':False})
 with r:
  talk('Eric Dale','eric','concerned','The historical window describes yesterday’s market. The external prices suggest a new regime.')
  talk('Sarah Robertson','sarah','concerned','Then the external evidence must map defensibly to the mortgage pools on our books.')
 t1,t2,t3=st.columns(3)
 with t1:st.markdown("<div class='takeaway-tile'><div class='takeaway-title'>Market evidence</div>Comparable mortgage products are repricing before the internal book fully reflects the deterioration.</div>",unsafe_allow_html=True)
 with t2:st.markdown("<div class='takeaway-tile'><div class='takeaway-title'>Model implication</div>A calibration built on the calm period can understate risk when volatility rises and previously separate pools begin moving together.</div>",unsafe_allow_html=True)
 with t3:st.markdown("<div class='takeaway-tile'><div class='takeaway-title'>Takeaway</div>A stable internal mark is not evidence of stable risk. Eric’s task is to decide when external prices should change the model.</div>",unsafe_allow_html=True)
 nav('peter')
elif s=='peter':
 header('6:08 PM · QUANT DESK','Peter updates covariance','The same exposures produce a different distribution when volatility and dependence rise.')
 a,b=st.columns(2)
 for col,reg,title in [(a,'Initial','Initial correlation'),(b,'Updated','Updated correlation')]:
  with col:
   corr=R[R.regime.eq(reg)][H.pool].corr();f=go.Figure(go.Heatmap(z=corr.values,x=[x[:10] for x in corr.columns],y=[x[:10] for x in corr.index],zmin=-1,zmax=1,colorscale='RdBu_r',showscale=True));st.plotly_chart(style(f,title,360),width='stretch',config={'displayModeBar':False})
 x,y=st.columns(2)
 with x:talk('Seth Bregman','seth','concerned','The assets did not change overnight. Why did portfolio risk change?')
 with y:talk('Peter Sullivan','peter','decisive','Volatility and dependence changed. The same holdings now create a different loss distribution.')
 t1,t2,t3=st.columns(3)
 with t1:st.markdown("<div class='takeaway-tile'><div class='takeaway-title'>Initial regime</div>Lower cross-pool dependence creates more diversification. Losses are less likely to arrive together.</div>",unsafe_allow_html=True)
 with t2:st.markdown("<div class='takeaway-tile'><div class='takeaway-title'>Updated regime</div>Correlations rise across the mortgage pools. Diversification weakens precisely when individual asset volatility is also increasing.</div>",unsafe_allow_html=True)
 with t3:st.markdown("<div class='takeaway-tile'><div class='takeaway-title'>Takeaway</div>The portfolio did not change, but the relationships among the assets did. Covariance is the bridge between market stress and portfolio tail risk.</div>",unsafe_allow_html=True)
 nav('regime')
elif s=='regime':
 header('9:10 PM · RISK ROOM','The regime multiplies tail risk','Hover directly over any vertical line to read the measure, dollar estimate, and selected confidence level.')
 st.session_state.confidence=st.select_slider('Confidence level',options=[.95,.975,.99],value=st.session_state.confidence,format_func=lambda x:f'{x:.1%}')
 a,b=losses('Initial'),losses('Updated');v0,c0,sd0=stats(a,st.session_state.confidence);v1,c1,sd1=stats(b,st.session_state.confidence)
 m=st.columns(6)
 for col,(lab,val) in zip(m,[('Initial VaR',v0),('Updated VaR',v1),('Initial CVaR',c0),('Updated CVaR',c1),('Initial vol',sd0),('Updated vol',sd1)]):col.metric(lab,f'${val:.1f}m')
 f=go.Figure([density(a,'#0f7890','Initial density'),density(b,'#c7474b','Updated density')]);ymax=max(max(f.data[0].y),max(f.data[1].y));cl=f'{st.session_state.confidence:.1%}'
 for label,val,color,dash in [('Initial VaR',v0,'#0f7890','dash'),('Updated VaR',v1,'#c7474b','dash'),('Initial CVaR',c0,'#4f94a1','dot'),('Updated CVaR',c1,'#8f2230','dot')]:
  f.add_trace(go.Scatter(x=[val,val],y=[0,ymax],mode='lines',name=label,line=dict(color=color,width=4,dash=dash),customdata=[[label,val,cl],[label,val,cl]],hovertemplate='<b>%{customdata[0]}</b><br>$%{customdata[1]:.1f} million<br>Confidence: %{customdata[2]}<extra></extra>'))
 f.update_layout(hovermode='closest');f.update_xaxes(title='One-day portfolio loss ($m)');st.plotly_chart(style(f,'Mortgage portfolio loss distribution with hoverable VaR and CVaR',455),width='stretch',config={'displayModeBar':False});st.caption('Dashed = VaR. Dotted = CVaR. Hover over a line for the estimate.');nav('tuld')
elif s=='tuld':
 header('12:16 AM · EXECUTIVE COMMITTEE','The model reaches Tuld','Peter compares the original base-case model with the current post-regime-shift model. The same mortgage holdings now produce materially different VaR and CVaR estimates because volatility and cross-pool dependence have changed.')
 base_losses,current_losses=losses('Initial'),losses('Updated')
 base_var,base_cvar,base_vol=stats(base_losses,st.session_state.confidence)
 current_var,current_cvar,current_vol=stats(current_losses,st.session_state.confidence)
 st.markdown('### Base case versus current regime')
 summary=st.columns(6)
 items=[('Base-case VaR',base_var,None),('Current VaR',current_var,current_var/base_var),('Base-case CVaR',base_cvar,None),('Current CVaR',current_cvar,current_cvar/base_cvar),('Base-case vol',base_vol,None),('Current vol',current_vol,current_vol/base_vol)]
 for col,(label,value,multiple) in zip(summary,items):col.metric(label,f'${value:.1f}m',None if multiple is None else f'×{multiple:.1f}',delta_color='inverse')
 left,right=st.columns(2,gap='large')
 with left:
  st.markdown('### VaR: where the tail begins')
  fig=go.Figure(go.Bar(x=['Base case','Current regime'],y=[base_var,current_var],marker_color=['#0f7890','#c7474b'],text=[f'${base_var:.1f}m',f'${current_var:.1f}m'],textposition='outside',customdata=[['Base-case VaR',base_var],['Current-regime VaR',current_var]],hovertemplate='<b>%{customdata[0]}</b><br>$%{customdata[1]:.1f} million<extra></extra>'));fig.update_yaxes(title='One-day loss threshold ($m)',range=[0,current_var*1.28]);st.plotly_chart(style(fig,'VaR comparison: base case vs current regime',355),width='stretch',config={'displayModeBar':False})
  st.markdown(f"<div class='interpretation'><b>Interpretation</b><br><br>At {st.session_state.confidence:.1%} confidence, the loss threshold increases from <b>${base_var:.1f} million</b> to <b>${current_var:.1f} million</b>. The current-regime VaR is <b>{current_var/base_var:.1f} times</b> the base-case estimate.</div>",unsafe_allow_html=True)
 with right:
  st.markdown('### CVaR: what happens inside the tail')
  fig=go.Figure(go.Bar(x=['Base case','Current regime'],y=[base_cvar,current_cvar],marker_color=['#5c99a5','#8f2230'],text=[f'${base_cvar:.1f}m',f'${current_cvar:.1f}m'],textposition='outside',customdata=[['Base-case CVaR',base_cvar],['Current-regime CVaR',current_cvar]],hovertemplate='<b>%{customdata[0]}</b><br>$%{customdata[1]:.1f} million<extra></extra>'));fig.update_yaxes(title='Average loss beyond VaR ($m)',range=[0,current_cvar*1.28]);st.plotly_chart(style(fig,'CVaR comparison: base case vs current regime',355),width='stretch',config={'displayModeBar':False})
  st.markdown(f"<div class='interpretation'><b>Interpretation</b><br><br>Average loss after the portfolio crosses VaR rises from <b>${base_cvar:.1f} million</b> to <b>${current_cvar:.1f} million</b>. Current-regime CVaR is <b>{current_cvar/base_cvar:.1f} times</b> the base-case estimate.</div>",unsafe_allow_html=True)
 a,b=st.columns(2)
 with a:talk('Peter Sullivan','peter','decisive','The holdings are unchanged. The base case and current case diverge because the volatility regime and dependence structure changed.')
 with b:talk('John Tuld','john','decisive','The comparison is the problem: the current book no longer behaves like the book described by the base-case model.')
 st.caption('Base case = first 250 synthetic daily observations. Current regime = final 250 observations after the modeled volatility and correlation shift.')
 nav('sale')
elif s=='sale':
 header('8:00 AM · TRADING FLOOR','Sam executes the fire sale','Synthetic discounts convert modeled risk into realized execution loss.')
 d=np.array([.06,.12,.20,.32,.45,.55]);sale=H.copy();sale['loss']=sale.exposure_mm*d
 f=go.Figure(go.Bar(y=sale.pool,x=sale.loss,orientation='h',marker_color=['#0f7890','#318a98','#7f9692','#d69c35','#ca6a45','#c7474b'],text=[f'${x:.0f}m' for x in sale.loss],textposition='outside'));f.update_xaxes(title='Synthetic liquidation loss ($m)')
 l,r=st.columns([1.72,1])
 with l:st.plotly_chart(style(f,'Fire-sale loss by mortgage pool',475),width='stretch',config={'displayModeBar':False})
 with r:
  talk('Sam Rogers','sam','concerned','The model describes the tail. The fire sale turns uncertainty into a certain loss at today’s distressed prices.')
  st.markdown(f"<div class='takeaway-tile'><div class='takeaway-title'>Sam’s execution problem</div>The synthetic sale realizes <b>${sale['loss'].sum():,.0f} million</b> in losses. Selling quickly may reduce exposure, but deeper discounts transfer value to buyers and can damage the firm’s market relationships.</div>",unsafe_allow_html=True)
 t1,t2,t3=st.columns(3)
 with t1:st.markdown("<div class='takeaway-tile'><div class='takeaway-title'>Modeled loss</div>VaR and CVaR estimate the distribution of potential portfolio losses before the trade occurs.</div>",unsafe_allow_html=True)
 with t2:st.markdown("<div class='takeaway-tile'><div class='takeaway-title'>Realized loss</div>The liquidation discount converts risk into an immediate transaction loss that appears in the firm’s results.</div>",unsafe_allow_html=True)
 with t3:st.markdown("<div class='takeaway-tile'><div class='takeaway-title'>Takeaway</div>Execution is part of risk management. The decision is not only whether to sell, but what price, speed, and franchise damage the firm will accept.</div>",unsafe_allow_html=True)
 nav('assignment')
elif s=='assignment':
 header('ASSIGNMENT','Risk-committee memorandum','Reconstruct the model, quantify the regime change, and evaluate liquidation consequences.')
 a,b=st.columns(2,gap='large')
 with a:st.markdown("<div class='assignment'><h3>Quantitative analysis</h3><ol><li><b>Portfolio construction:</b> Calculate the exposure weight of each mortgage pool and confirm that the weights sum to 100%.</li><li><b>Base-case risk:</b> Calculate 95%, 97.5%, and 99% historical VaR and CVaR using the first 250 observations.</li><li><b>Current-regime risk:</b> Repeat the calculations using the final 250 observations after the modeled regime shift.</li><li><b>Dependence:</b> Compare annualized volatility and the two correlation matrices. Identify the most important changes.</li><li><b>Magnitude:</b> Report the multiples by which VaR, CVaR, and volatility changed.</li></ol></div>",unsafe_allow_html=True)
 with b:st.markdown("<div class='assignment'><h3>Risk judgment</h3><ol><li><b>External evidence:</b> Explain why the market proxy challenges the firm’s original calibration and internal marks.</li><li><b>Interpretation:</b> Distinguish what VaR reveals from what CVaR reveals about the portfolio.</li><li><b>Execution:</b> Evaluate the liquidation order, including the trade-off between speed, price, and market impact.</li><li><b>Model limitation:</b> Identify one assumption that could materially change the findings.</li><li><b>Recommendation:</b> State what the risk committee should do and what evidence would reverse that recommendation.</li></ol></div>",unsafe_allow_html=True)
 st.markdown("<div class='assignment-note'><b>Deliverable:</b> Submit the completed workbook or notebook plus a <b>750–1,000 word risk-committee memorandum</b>. The memorandum must cite the calculated base-case and current-regime VaR/CVaR estimates, explain the regime shift in plain language, distinguish modeled from realized loss, and defend a course of action.</div>",unsafe_allow_html=True)
 st.markdown('### Case data files')
 c1,c2,c3=st.columns(3);c1.download_button('Download mortgage_pool_holdings.csv',H.to_csv(index=False),'mortgage_pool_holdings.csv','text/csv',width='stretch');c2.download_button('Download mortgage_pool_returns.csv',R.to_csv(index=False),'mortgage_pool_returns.csv','text/csv',width='stretch');c3.download_button('Download external_market_proxy.csv',P.to_csv(index=False),'external_market_proxy.csv','text/csv',width='stretch')
