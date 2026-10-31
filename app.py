from __future__ import annotations
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from data_portfolio import portfolio_data
from risk_engine import apply_ghostline_shock, simulate_losses

st.set_page_config(page_title='Blackridge: One Night Inside the Tail',page_icon='◈',layout='wide',initial_sidebar_state='collapsed')
BASE=portfolio_data()
SCENES=['intro','cold_open','baseline','shock','reveal','interrogation','tail','committee']
TIMES=['INTRO','4:17 PM','6:08 PM','7:35 PM','9:10 PM','10:48 PM','12:16 AM','1:03 AM']
for k,v in {'accepted':False,'scene':'intro','severity':60,'confidence':.95,'sim_steps':2500}.items():st.session_state.setdefault(k,v)
CHAR={
 'John Tuld':('john_tuld.png','Chief Executive Officer','#173F5F'), 'Eric Dale':('eric_dale.png','Former Head of Risk','#526777'),
 'Sarah Robertson':('sarah_robertson.png','Chief Risk Officer','#B7872B'), 'Sam Rogers':('sam_rogers.png','Head of Portfolio Management','#245B77'),
 'Peter Sullivan':('peter_sullivan.png','Quantitative Risk Analyst','#168C86'), 'Seth Bregman':('seth_bregman.png','Associate Risk Analyst','#3B8EBA'),
 'Will Emerson':('will_emerson.png','Head of Trading & Portfolio Solutions','#A56632'), 'Jared Cohen':('jared_cohen.png','Head of Private Credit','#42735B')}

st.markdown('''<style>
.block-container{max-width:1380px;padding-top:.45rem;padding-bottom:1rem}.eyebrow{color:#174868;font-size:.7rem;font-weight:800;letter-spacing:.14em}.scene-title{font-family:Georgia,serif;font-size:1.78rem;font-weight:700;color:#102A43;margin:.05rem 0 .15rem}.scene-copy{font-family:Georgia,serif;font-size:1rem;line-height:1.42;max-width:1080px}.comic{border:2px solid #183B56;border-radius:11px;background:#F8FAFC;padding:.55rem;box-shadow:4px 4px 0 #D6E0E7;height:100%}.comic-name{font-weight:900;color:#102A43;font-size:.92rem}.comic-role{font-size:.66rem;color:#60788A;text-transform:uppercase;letter-spacing:.06em}.bubble{background:white;color:#102A43;border:2px solid #183B56;border-radius:14px;padding:.65rem .75rem;margin-top:.4rem;font-family:Georgia,serif;font-size:.88rem;line-height:1.32}.caption-box{background:#102A43;color:white;padding:.55rem .8rem;border-radius:6px;font-family:Georgia,serif}.calc-bridge{border-left:4px solid #D69C35;background:#FFF9EC;color:#40351E;padding:.65rem .8rem;border-radius:6px;font-size:.86rem}.stButton>button{border-radius:7px;font-weight:750}[data-testid="stMetricValue"]{font-size:1.35rem}[data-testid="stMetricLabel"]{font-size:.75rem}div[data-testid="stImage"] img{max-height:180px;object-fit:cover}.stTabs [data-baseweb="tab"]{height:32px}.stProgress{margin-bottom:.1rem}h1{font-size:2rem!important;margin:.05rem 0!important}h3{font-size:1.1rem!important}
</style>''',unsafe_allow_html=True)

def style(fig,title,h=330):
    fig.update_layout(title=dict(text=title,font=dict(size=17)),height=h,margin=dict(l=30,r=20,t=52,b=35),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(color='#102A43',size=11),legend=dict(orientation='h',y=1.08),hoverlabel=dict(bgcolor='#102A43',font_color='white'))
    fig.update_xaxes(showgrid=False,zeroline=False);fig.update_yaxes(gridcolor='rgba(128,128,128,.14)',zeroline=False);return fig
def portrait(name):return f"assets/characters/{CHAR[name][0]}"
def panel(name,text):
    color=CHAR[name][2];st.markdown(f"<div class='comic' style='border-color:{color}'>",unsafe_allow_html=True);st.image(portrait(name),width='stretch');st.markdown(f"<div class='comic-name'>{name}</div><div class='comic-role'>{CHAR[name][1]}</div><div class='bubble' style='border-color:{color}'>{text}</div></div>",unsafe_allow_html=True)
def exchange(a,ta,b,tb):
    x,y=st.columns(2,gap='medium')
    with x:panel(a,ta)
    with y:panel(b,tb)
def goto(s):st.session_state.scene=s;st.rerun()
def nav(n=None):
    a,b=st.columns([5,1]);i=SCENES.index(st.session_state.scene)
    if i>0 and a.button('← Previous'):goto(SCENES[i-1])
    if n and b.button('Continue →',type='primary',width='stretch'):goto(n)
def timeline():
    i=SCENES.index(st.session_state.scene);st.progress((i+1)/len(SCENES));cs=st.columns(8)
    for j,(c,t) in enumerate(zip(cs,TIMES)):c.caption(('● ' if i==j else '')+t)
def header(k,t,c):st.markdown(f"<div class='eyebrow'>{k}</div><div class='scene-title'>{t}</div><div class='scene-copy'>{c}</div>",unsafe_allow_html=True)
def dist_chart(base,stress):
    fig=go.Figure()
    for color,fill,name,r in [('#168C86','rgba(22,140,134,.16)','Before shock',base),('#C7474B','rgba(199,71,75,.14)','After shock',stress)]:
        h,e=np.histogram(r['losses'],bins=85,density=True);x=(e[:-1]+e[1:])/2;fig.add_trace(go.Scatter(x=x,y=h,name=name,mode='lines',line=dict(color=color,width=3),fill='tozeroy',fillcolor=fill))
    fig.add_vrect(x0=stress['var'],x1=float(np.max(stress['losses'])),fillcolor='rgba(199,71,75,.09)',line_width=0)
    fig.add_vline(x=stress['var'],line_color='#D69C35',line_width=3,annotation_text=f"VaR ${stress['var']:.1f}m")
    fig.add_vline(x=stress['cvar'],line_color='#C7474B',line_width=3,annotation_text=f"CVaR ${stress['cvar']:.1f}m")
    fig.update_xaxes(title='Portfolio loss ($m)');fig.update_yaxes(title='Relative frequency');return style(fig,'Before and after: the tail opens',350)
def mc_convergence(severity,confidence,n):
    checkpoints=np.unique(np.linspace(250,n,42,dtype=int));vars_,cvars_=[],[]
    df=apply_ghostline_shock(BASE,severity)
    for k in checkpoints:
        r=simulate_losses(df,severity,confidence,simulations=int(k),seed=47);vars_.append(r['var']);cvars_.append(r['cvar'])
    fig=go.Figure();fig.add_trace(go.Scatter(x=checkpoints,y=vars_,name='VaR estimate',line=dict(color='#D69C35',width=3)));fig.add_trace(go.Scatter(x=checkpoints,y=cvars_,name='CVaR estimate',line=dict(color='#C7474B',width=3)))
    fig.update_xaxes(title='Monte Carlo trials');fig.update_yaxes(title='Estimated loss ($m)');return style(fig,'Monte Carlo convergence as trials accumulate',320)
def sensitivity(conf):
    levels=range(0,101,10);va=[];cv=[]
    for s in levels:
        r=simulate_losses(apply_ghostline_shock(BASE,s),s,conf,simulations=10000,seed=47);va.append(r['var']);cv.append(r['cvar'])
    fig=go.Figure();fig.add_trace(go.Scatter(x=list(levels),y=va,name='VaR',line=dict(color='#D69C35',width=3)));fig.add_trace(go.Scatter(x=list(levels),y=cv,name='CVaR',line=dict(color='#C7474B',width=3),fill='tonexty',fillcolor='rgba(199,71,75,.10)'));fig.add_vline(x=st.session_state.severity,line_dash='dash',line_color='#173F5F',annotation_text='Current shock');fig.update_xaxes(title='Shock severity');fig.update_yaxes(title='Loss ($m)');return style(fig,'Assumptions change the tail',320)

# Disclaimer gate before any story content.
if not st.session_state.accepted:
    st.markdown("<div class='eyebrow'>BEFORE THE EXPERIENCE</div>",unsafe_allow_html=True);st.title('Educational Use and Attribution')
    st.warning('This application is an original, fictional teaching simulation inspired by the organizational tension of Margin Call (2011), written and directed by J. C. Chandor. It does not reproduce film dialogue or scenes and is not affiliated with or endorsed by the film, its cast, creators, producers, or distributors.')
    st.info('Blackridge Capital, Ghostline Systems, all portfolio companies, character commentary, financial data, assumptions, and modeled outcomes are fictional. VaR and CVaR results come from a simplified instructional Monte Carlo model and are not investment advice, valuation opinions, or production risk estimates.')
    accepted=st.checkbox('I understand that this is a fictional educational simulation.')
    if st.button('Enter Blackridge',type='primary',disabled=not accepted):st.session_state.accepted=True;st.session_state.scene='intro';st.rerun()
    st.stop()

st.markdown("<div class='eyebrow'>BLACKRIDGE CAPITAL · SPECIAL SITUATIONS CREDIT FUND IV</div>",unsafe_allow_html=True);st.title('One Night Inside the Tail');timeline();st.divider();scene=st.session_state.scene

if scene=='intro':
    header('INTRO · THE PEOPLE IN THE ROOM','Meet Blackridge','Eight professionals carry the model from an unfinished risk file to the executive committee. Each character owns a different interpretation of the same VaR/CVaR evidence.')
    cols=st.columns(4,gap='small')
    intro=[('Eric Dale','Model risk and stale marks'),('Peter Sullivan','Monte Carlo, VaR, and CVaR'),('Seth Bregman','Questions and interpretation'),('Sarah Robertson','Validation and governance'),('Jared Cohen','Credit and contagion'),('Will Emerson','Execution and liquidity'),('Sam Rogers','Portfolio judgment'),('John Tuld','Executive synthesis')]
    for i,(n,line) in enumerate(intro):
        with cols[i%4]:
            st.image(portrait(n),width='stretch');st.markdown(f"**{n}**  \
{CHAR[n][1]}  \
*{line}*")
    nav('cold_open')

elif scene=='cold_open':
    header('4:17 PM · RISK FLOOR','The last file out of the building','Every borrower is current. Eric Dale leaves behind GHOSTLINE_TAIL_RECALIBRATION_v17_FINAL and a warning that the portfolio may be stable only because the market has not forced a new price.')
    exchange('Eric Dale','Ghostline did not keep its value because the business was unchanged. Ghostline kept its value because no one had been forced to price it.','Peter Sullivan','You changed the mark, default assumptions, and dependence structure. This model is about what the loan reveals.')
    nav('baseline')

elif scene=='baseline':
    header('6:08 PM · QUANT DESK','Build the world before the shock','Peter and Seth run the Monte Carlo model. Increase the trial count to see VaR and CVaR estimates stabilize, then change the confidence level to move the tail threshold.')
    c1,c2=st.columns(2);confidence=c1.select_slider('Confidence level',options=[.90,.95,.975,.99],value=st.session_state.confidence,format_func=lambda x:f'{x:.1%}');n=c2.select_slider('Monte Carlo trials',options=[1000,2500,5000,10000,20000,30000],value=st.session_state.sim_steps)
    st.session_state.confidence=confidence;st.session_state.sim_steps=n
    base=simulate_losses(BASE,0,confidence,simulations=n,seed=47);m=st.columns(3);m[0].metric('Trials',f'{n:,}');m[1].metric('VaR estimate',f"${base['var']:.1f}m");m[2].metric('CVaR estimate',f"${base['cvar']:.1f}m")
    left,right=st.columns([1.65,1])
    with left:st.plotly_chart(mc_convergence(0,confidence,n),width='stretch')
    with right:exchange('Seth Bregman','Why do the estimates move when we add trials?','Peter Sullivan','Sampling noise falls as the simulation grows. Confidence changes the threshold; trial count changes estimate stability.')
    nav('shock')

elif scene=='shock':
    header('7:35 PM · MARKET ALERT','The market moves. The mark does not.','One shock slider changes Ghostline PD, LGD, mark, and common-factor dependence through a fixed scenario mapping.')
    severity=st.slider('Software-credit shock severity',0,100,st.session_state.severity,5);st.session_state.severity=severity
    stressed=apply_ghostline_shock(BASE,severity);b=BASE[BASE.asset.eq('Ghostline Systems')].iloc[0];a=stressed[stressed.asset.eq('Ghostline Systems')].iloc[0]
    m=st.columns(4);m[0].metric('Ghostline PD',f"{a.pd:.1%}",f"{a.pd-b.pd:+.1%}",delta_color='inverse');m[1].metric('Ghostline LGD',f"{a.lgd:.1%}",f"{a.lgd-b.lgd:+.1%}",delta_color='inverse');m[2].metric('Ghostline mark',f"{a['mark']:.1f}",f"{a['mark']-b['mark']:+.1f}");m[3].metric('Common loading',f"{.30+.35*severity/100:.2f}")
    st.plotly_chart(sensitivity(st.session_state.confidence),width='stretch')
    nav('reveal')

elif scene=='reveal':
    header('9:10 PM · RISK ROOM','The tail opens','The stressed distribution changes VaR, CVaR, and the severity beyond the threshold. The chart code now uses Plotly-compatible RGBA fill colors.')
    base=simulate_losses(BASE,0,st.session_state.confidence);stress=simulate_losses(apply_ghostline_shock(BASE,st.session_state.severity),st.session_state.severity,st.session_state.confidence)
    m=st.columns(5);m[0].metric('VaR before',f"${base['var']:.1f}m");m[1].metric('VaR after',f"${stress['var']:.1f}m",f"+${stress['var']-base['var']:.1f}m",delta_color='inverse');m[2].metric('CVaR before',f"${base['cvar']:.1f}m");m[3].metric('CVaR after',f"${stress['cvar']:.1f}m",f"+${stress['cvar']-base['cvar']:.1f}m",delta_color='inverse');m[4].metric('Tail gap',f"${stress['tail_gap']:.1f}m")
    left,right=st.columns([1.65,1])
    with left:st.plotly_chart(dist_chart(base,stress),width='stretch')
    with right:exchange('Seth Bregman','The VaR threshold moved.','Peter Sullivan','The losses beyond it moved farther. CVaR measures what happens after the threshold is crossed.')
    nav('interrogation')

elif scene=='interrogation':
    header('10:48 PM · CHIEF RISK OFFICE','Interrogate the model','Sarah challenges whether the result survives less severe assumptions.')
    left,right=st.columns([1.7,1])
    with left:st.plotly_chart(sensitivity(st.session_state.confidence),width='stretch')
    with right:exchange('Sarah Robertson','A severe result is not automatically a credible result.','Peter Sullivan','The widening gap between VaR and CVaR shows how the tail changes as assumptions intensify.')
    nav('tail')

elif scene=='tail':
    header('12:16 AM · PRIVATE CREDIT FLOOR','Who owns the tail?','The contribution chart converts the portfolio tail into borrower-level evidence.')
    stress=simulate_losses(apply_ghostline_shock(BASE,st.session_state.severity),st.session_state.severity,st.session_state.confidence);tc=stress['tail_contribution'].sort_values()
    fig=go.Figure(go.Bar(y=tc.index,x=tc.values,orientation='h',marker_color=['#C7474B' if n in ['Ghostline Systems','CipherWorks'] else '#168C86' for n in tc.index],text=[f'${v:.1f}m' for v in tc.values],textposition='outside'));fig.update_xaxes(title='Average loss beyond portfolio VaR ($m)')
    left,right=st.columns([1.65,1])
    with left:st.plotly_chart(style(fig,'Contribution inside the stressed tail',340),width='stretch')
    with right:exchange('Jared Cohen','If Ghostline owns the tail, the risk is specific. If CipherWorks follows, the book contains hidden dependence.','Will Emerson','The model identifies the source of risk. It does not tell us the execution price.')
    nav('committee')

elif scene=='committee':
    header('1:03 AM · EXECUTIVE COMMITTEE','The model reaches the room','The experience ends with an analytical briefing rather than a participant decision.')
    stress=simulate_losses(apply_ghostline_shock(BASE,st.session_state.severity),st.session_state.severity,st.session_state.confidence);top=stress['tail_contribution'].index[0]
    m=st.columns(4);m[0].metric('Shock severity',f"{st.session_state.severity}/100");m[1].metric('Stressed VaR',f"${stress['var']:.1f}m");m[2].metric('Stressed CVaR',f"${stress['cvar']:.1f}m");m[3].metric('Largest contributor',top)
    exchange('Sam Rogers','We manage portfolios, not spreadsheets. Explain what the evidence can support.','John Tuld','Give the committee the distribution before, the distribution after, and the conclusion between them.')
    if st.button('Restart the night'):st.session_state.scene='intro';st.rerun()
