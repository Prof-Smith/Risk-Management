from __future__ import annotations
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from data_portfolio import portfolio_data
from risk_engine import apply_ghostline_shock, simulate_losses

st.set_page_config(page_title='Blackridge: One Night Inside the Tail',page_icon='◈',layout='wide',initial_sidebar_state='collapsed')
BASE=portfolio_data(); SCENES=['intro','cold_open','baseline','shock','reveal','interrogation','tail','committee']; TIMES=['INTRO','4:17 PM','6:08 PM','7:35 PM','9:10 PM','10:48 PM','12:16 AM','1:03 AM']
for k,v in {'accepted':False,'scene':'intro','severity':60,'confidence':.95,'sim_steps':10000}.items():st.session_state.setdefault(k,v)
CHAR={'John Tuld':('john','Chief Executive Officer','#173F5F'),'Eric Dale':('eric','Former Head of Risk','#526777'),'Sarah Robertson':('sarah','Chief Risk Officer','#B7872B'),'Sam Rogers':('sam','Head of Portfolio Management','#245B77'),'Peter Sullivan':('peter','Quantitative Risk Analyst','#168C86'),'Seth Bregman':('seth','Associate Risk Analyst','#3B8EBA'),'Will Emerson':('will','Head of Trading & Portfolio Solutions','#A56632'),'Jared Cohen':('jared','Head of Private Credit','#42735B')}

st.markdown('''<style>
.block-container{max-width:1360px;padding-top:.35rem;padding-bottom:.7rem}.eyebrow{color:#174868;font-size:.68rem;font-weight:800;letter-spacing:.14em}.scene-title{font-family:Georgia,serif;font-size:1.65rem;font-weight:700;color:#102A43;margin:.03rem 0 .12rem}.scene-copy{font-family:Georgia,serif;font-size:.96rem;line-height:1.38;max-width:1080px}.comic{border:1.5px solid #183B56;border-radius:12px;background:linear-gradient(145deg,#fff,#f2f6f8);padding:.5rem;box-shadow:3px 4px 0 #DCE5EA;height:100%}.comic-name{font-weight:900;color:#102A43;font-size:.9rem}.comic-role{font-size:.62rem;color:#60788A;text-transform:uppercase;letter-spacing:.06em}.bubble{background:white;color:#102A43;border:1.5px solid #183B56;border-radius:13px;padding:.58rem .7rem;margin-top:.35rem;font-family:Georgia,serif;font-size:.84rem;line-height:1.27;min-height:68px}.calc{border-left:4px solid #D69C35;background:#FFF9EC;color:#40351E;padding:.55rem .75rem;border-radius:6px;font-size:.82rem}.stButton>button{border-radius:7px;font-weight:750}[data-testid="stMetricValue"]{font-size:1.28rem}[data-testid="stMetricLabel"]{font-size:.72rem}.stProgress{margin-bottom:0}h1{font-size:1.9rem!important;margin:.03rem 0!important}.stForm{border:0!important;padding:0!important}div[data-testid="stImage"] img{width:100%;height:auto;aspect-ratio:1/1;object-fit:cover;object-position:50% 42%;border-radius:10px}.element-container{margin-bottom:.15rem}
</style>''',unsafe_allow_html=True)

def style(fig,title,h=320):
    fig.update_layout(title=dict(text=title,font=dict(size=17,color='#102A43')),height=h,margin=dict(l=32,r=22,t=55,b=38),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#FBFCFD',font=dict(color='#102A43',size=10),legend=dict(orientation='h',y=1.08,x=.01),hoverlabel=dict(bgcolor='#102A43',font_color='white'),transition_duration=250,uirevision='blackridge')
    fig.update_xaxes(showgrid=False,zeroline=False);fig.update_yaxes(gridcolor='rgba(128,128,128,.12)',zeroline=False);return fig
@st.cache_data(show_spinner=False)
def sim(severity,confidence,trials=30000,seed=47):return simulate_losses(apply_ghostline_shock(BASE,severity),severity,confidence,simulations=trials,seed=seed)
@st.cache_data(show_spinner=False)
def convergence(confidence,max_trials):
    checkpoints=np.unique(np.geomspace(300,max_trials,28).astype(int));v=[];c=[]
    for n in checkpoints:
        r=sim(0,confidence,int(n),47);v.append(r['var']);c.append(r['cvar'])
    return checkpoints,np.array(v),np.array(c)
def portrait(name,state):return f"assets/portraits/{CHAR[name][0]}_{state}.png"
def panel(name,text,state='neutral'):
    color=CHAR[name][2];st.markdown(f"<div class='comic' style='border-color:{color}'>",unsafe_allow_html=True);st.image(portrait(name,state),width='stretch');st.markdown(f"<div class='comic-name'>{name}</div><div class='comic-role'>{CHAR[name][1]}</div><div class='bubble' style='border-color:{color}'>{text}</div></div>",unsafe_allow_html=True)
def exchange(a,ta,sa,b,tb,sb):
    x,y=st.columns(2,gap='small')
    with x:panel(a,ta,sa)
    with y:panel(b,tb,sb)
def goto(s):st.session_state.scene=s;st.rerun()
def nav(n=None):
    a,b=st.columns([5,1]);i=SCENES.index(st.session_state.scene)
    if i>0 and a.button('← Previous',key=f'prev_{scene}'):goto(SCENES[i-1])
    if n and b.button('Continue →',type='primary',width='stretch',key=f'next_{scene}'):goto(n)
def timeline():
    i=SCENES.index(st.session_state.scene);st.progress((i+1)/len(SCENES));cs=st.columns(8)
    for j,(c,t) in enumerate(zip(cs,TIMES)):c.caption(('● ' if i==j else '')+t)
def header(k,t,c):st.markdown(f"<div class='eyebrow'>{k}</div><div class='scene-title'>{t}</div><div class='scene-copy'>{c}</div>",unsafe_allow_html=True)
def smooth_density(losses,bins=120):
    lo=max(0,float(np.quantile(losses,.002)))
    hi=float(np.quantile(losses,.997))
    h,e=np.histogram(losses,bins=bins,range=(lo,hi),density=True)
    kernel=np.array([1,2,4,7,10,12,10,7,4,2,1],dtype=float);kernel/=kernel.sum()
    h=np.convolve(h,kernel,mode='same')
    return (e[:-1]+e[1:])/2,h
def dist_chart(base,stress):
    fig=go.Figure()
    for color,fill,name,r in [('#168C86','rgba(22,140,134,.16)','Before shock',base),('#C7474B','rgba(199,71,75,.14)','After shock',stress)]:
        x,h=smooth_density(r['losses']);fig.add_trace(go.Scatter(x=x,y=h,name=name,line=dict(color=color,width=3,shape='spline'),fill='tozeroy',fillcolor=fill,hovertemplate=f'{name}<br>Loss: $%{{x:.1f}}m<extra></extra>'))
    ymax=max(max(fig.data[0].y),max(fig.data[1].y));
    fig.add_vrect(x0=stress['var'],x1=float(np.max(stress['losses'])),fillcolor='rgba(199,71,75,.07)',line_width=0)
    fig.add_annotation(x=stress['var'],y=ymax*.9,text=f"VaR<br>${stress['var']:.1f}m",showarrow=True,arrowhead=2,arrowcolor='#D69C35',bgcolor='#FFF7E6',bordercolor='#D69C35')
    fig.add_annotation(x=stress['cvar'],y=ymax*.62,text=f"CVaR<br>${stress['cvar']:.1f}m",showarrow=True,arrowhead=2,arrowcolor='#C7474B',bgcolor='#FFF0F1',bordercolor='#C7474B')
    fig.update_xaxes(title='Simulated portfolio loss ($ millions)',range=[0,np.quantile(stress['losses'],.997)]);fig.update_yaxes(title='Smoothed density');return style(fig,'Portfolio loss profile: baseline versus stressed',345)
def convergence_chart(confidence,n):
    cp,v,c=convergence(confidence,n);fig=go.Figure();fig.add_trace(go.Scatter(x=cp,y=v,name='VaR',line=dict(color='#D69C35',width=3,shape='spline')));fig.add_trace(go.Scatter(x=cp,y=c,name='CVaR',line=dict(color='#C7474B',width=3,shape='spline')));fig.add_hline(y=v[-1],line_dash='dot',line_color='#D69C35');fig.add_hline(y=c[-1],line_dash='dot',line_color='#C7474B');fig.update_xaxes(title='Cumulative simulation trials',type='log');fig.update_yaxes(title='Estimated loss ($m)');return style(fig,'Monte Carlo estimates settle as trials accumulate',300)
def sensitivity_chart(confidence):
    levels=list(range(0,101,10));v=[];c=[]
    for s in levels:r=sim(s,confidence,12000,47);v.append(r['var']);c.append(r['cvar'])
    fig=go.Figure();fig.add_trace(go.Scatter(x=levels,y=v,name='VaR',line=dict(color='#D69C35',width=3,shape='spline')));fig.add_trace(go.Scatter(x=levels,y=c,name='CVaR',line=dict(color='#C7474B',width=3,shape='spline'),fill='tonexty',fillcolor='rgba(199,71,75,.10)'));fig.add_vline(x=st.session_state.severity,line_dash='dash',line_color='#173F5F');fig.update_xaxes(title='Shock severity');fig.update_yaxes(title='Loss ($m)');return style(fig,'Tail severity widens as assumptions deteriorate',300)

if not st.session_state.accepted:
    st.markdown("<div class='eyebrow'>BEFORE THE EXPERIENCE</div>",unsafe_allow_html=True);st.title('Educational Use and Attribution');st.warning('This is an original fictional teaching simulation inspired by the organizational tension of Margin Call (2011), written and directed by J. C. Chandor. No film dialogue or scenes are reproduced, and the experience is not affiliated with or endorsed by the film or its participants.');st.info('Blackridge Capital, all portfolio companies, character commentary, assumptions, and modeled outcomes are fictional. VaR and CVaR are produced by a simplified instructional Monte Carlo model, not a production risk system or investment recommendation.');ok=st.checkbox('I understand the fictional educational nature of the simulation.');
    if st.button('Enter Blackridge',type='primary',disabled=not ok):st.session_state.accepted=True;st.session_state.scene='intro';st.rerun()
    st.stop()

st.markdown("<div class='eyebrow'>BLACKRIDGE CAPITAL · SPECIAL SITUATIONS CREDIT FUND IV</div>",unsafe_allow_html=True);st.title('One Night Inside the Tail');timeline();st.divider();scene=st.session_state.scene

if scene=='intro':
    header('INTRO · THE PEOPLE IN THE ROOM','Meet Blackridge','Eight professionals move one model from an unfinished file to the executive committee. The portraits change expression as the analytical stakes rise.')
    intro=[('Eric Dale','Model risk and stale marks'),('Peter Sullivan','Monte Carlo, VaR, and CVaR'),('Seth Bregman','Questions and interpretation'),('Sarah Robertson','Validation and governance'),('Jared Cohen','Credit and contagion'),('Will Emerson','Execution and liquidity'),('Sam Rogers','Portfolio judgment'),('John Tuld','Executive synthesis')]
    for row in range(2):
        cols=st.columns(4,gap='small')
        for j,col in enumerate(cols):
            n,line=intro[row*4+j]
            with col:
                with st.container(border=True):
                    st.image(portrait(n,'neutral'),width='stretch')
                    st.markdown(f"**{n}**")
                    st.caption(CHAR[n][1])
                    st.markdown(f"*{line}*")
    nav('cold_open')
elif scene=='cold_open':
    header('4:17 PM · RISK FLOOR','The last file out of the building','Eric leaves behind GHOSTLINE_TAIL_RECALIBRATION_v17_FINAL. Peter sees that the model changes not only the loan, but the assumptions connecting the entire book.')
    exchange('Eric Dale','Ghostline kept its mark because no one had been forced to price it.','concerned','Peter Sullivan','You changed the mark, default assumptions, and dependence structure. This is a portfolio model.','concerned');nav('baseline')
elif scene=='baseline':
    header('6:08 PM · QUANT DESK','Build the world before the shock','Submit the controls once. The model remains stable while the chart updates, avoiding a full rerun on every slider movement.')
    with st.form('baseline_controls'):
        c1,c2=st.columns(2);confidence=c1.select_slider('Confidence level',options=[.90,.95,.975,.99],value=st.session_state.confidence,format_func=lambda x:f'{x:.1%}');n=c2.select_slider('Monte Carlo trials',options=[1000,2500,5000,10000,20000,30000],value=st.session_state.sim_steps);apply=st.form_submit_button('Run Monte Carlo',type='primary')
        if apply:st.session_state.confidence=confidence;st.session_state.sim_steps=n
    base=sim(0,st.session_state.confidence,st.session_state.sim_steps,47);m=st.columns(3);m[0].metric('Trials',f"{st.session_state.sim_steps:,}");m[1].metric('VaR',f"${base['var']:.1f}m");m[2].metric('CVaR',f"${base['cvar']:.1f}m")
    l,r=st.columns([1.7,1]);
    with l:st.plotly_chart(convergence_chart(st.session_state.confidence,st.session_state.sim_steps),width='stretch',config={'displayModeBar':False})
    with r:exchange('Seth Bregman','Why do the estimates move when trials accumulate?','concerned','Peter Sullivan','Sampling noise falls as the simulation grows. The estimates settle.','decisive')
    nav('shock')
elif scene=='shock':
    header('7:35 PM · MARKET ALERT','The market moves. The mark does not.','Submit one coherent software-credit shock. Ghostline PD, LGD, mark, and common dependence move together.')
    with st.form('shock_controls'):
        sev=st.slider('Shock severity',0,100,st.session_state.severity,5);apply=st.form_submit_button('Apply shock',type='primary')
        if apply:st.session_state.severity=sev
    stressed=apply_ghostline_shock(BASE,st.session_state.severity);b=BASE[BASE.asset.eq('Ghostline Systems')].iloc[0];a=stressed[stressed.asset.eq('Ghostline Systems')].iloc[0];m=st.columns(4);m[0].metric('PD',f"{a.pd:.1%}",f"{a.pd-b.pd:+.1%}",delta_color='inverse');m[1].metric('LGD',f"{a.lgd:.1%}",f"{a.lgd-b.lgd:+.1%}",delta_color='inverse');m[2].metric('Mark',f"{a['mark']:.1f}",f"{a['mark']-b['mark']:+.1f}");m[3].metric('Common loading',f"{.30+.35*st.session_state.severity/100:.2f}")
    l,r=st.columns([1.7,1]);
    with l:st.plotly_chart(sensitivity_chart(st.session_state.confidence),width='stretch',config={'displayModeBar':False})
    with r:exchange('Eric Dale','The market moved. Ghostline’s private mark did not.','concerned','Peter Sullivan','Same book. New assumptions. Now rerun the distribution.','decisive')
    nav('reveal')
elif scene=='reveal':
    header('9:10 PM · RISK ROOM','The tail opens','The redesigned visualization uses smooth density curves, direct VaR/CVaR callouts, a focused x-axis, and a shaded tail without chart clutter.')
    base=sim(0,st.session_state.confidence,30000,47);stress=sim(st.session_state.severity,st.session_state.confidence,30000,47);m=st.columns(4);m[0].metric('VaR before',f"${base['var']:.1f}m");m[1].metric('VaR after',f"${stress['var']:.1f}m",f"+${stress['var']-base['var']:.1f}m",delta_color='inverse');m[2].metric('CVaR before',f"${base['cvar']:.1f}m");m[3].metric('CVaR after',f"${stress['cvar']:.1f}m",f"+${stress['cvar']-base['cvar']:.1f}m",delta_color='inverse')
    l,r=st.columns([1.75,1]);
    with l:st.plotly_chart(dist_chart(base,stress),width='stretch',config={'displayModeBar':False})
    with r:exchange('Seth Bregman','The threshold moved. The stressed curve also stretches farther right.','concerned','Peter Sullivan','VaR locates the boundary. CVaR measures severity after the boundary is crossed.','decisive')
    nav('interrogation')
elif scene=='interrogation':
    header('10:48 PM · CHIEF RISK OFFICE','Interrogate the assumptions','Sarah asks whether the tail survives less severe assumptions. Peter responds with the complete sensitivity curve.')
    l,r=st.columns([1.7,1]);
    with l:st.plotly_chart(sensitivity_chart(st.session_state.confidence),width='stretch',config={'displayModeBar':False})
    with r:exchange('Sarah Robertson','A severe result is not automatically credible. Does it survive challenge?','concerned','Peter Sullivan','The widening gap persists across shock levels. That is the model’s central evidence.','decisive')
    nav('tail')
elif scene=='tail':
    header('12:16 AM · PRIVATE CREDIT FLOOR','Who owns the tail?','Borrower contributions show whether Ghostline remains isolated or hidden dependence pulls CipherWorks into the same tail.')
    stress=sim(st.session_state.severity,st.session_state.confidence,30000,47);tc=stress['tail_contribution'].sort_values();fig=go.Figure(go.Bar(y=tc.index,x=tc.values,orientation='h',marker=dict(color=['#C7474B' if n in ['Ghostline Systems','CipherWorks'] else '#168C86' for n in tc.index],line=dict(color='white',width=1)),text=[f'${v:.1f}m' for v in tc.values],textposition='outside'));fig.update_xaxes(title='Average borrower loss beyond portfolio VaR ($m)')
    l,r=st.columns([1.7,1]);
    with l:st.plotly_chart(style(fig,'Contribution inside the stressed tail',325),width='stretch',config={'displayModeBar':False})
    with r:exchange('Jared Cohen','If Ghostline owns the tail, the risk is specific. If CipherWorks follows, the book has hidden dependence.','concerned','Will Emerson','The model identifies the source. Execution determines what can actually be changed.','decisive')
    nav('committee')
elif scene=='committee':
    header('1:03 AM · EXECUTIVE COMMITTEE','The model reaches the room','The experience closes with an analytical briefing. The changing cast expressions mark the shift from uncertainty to explanation.')
    stress=sim(st.session_state.severity,st.session_state.confidence,30000,47);top=stress['tail_contribution'].index[0];m=st.columns(4);m[0].metric('Shock',f"{st.session_state.severity}/100");m[1].metric('VaR',f"${stress['var']:.1f}m");m[2].metric('CVaR',f"${stress['cvar']:.1f}m");m[3].metric('Largest contributor',top)
    exchange('Sam Rogers','We manage portfolios, not charts. Explain what the evidence supports.','concerned','John Tuld','Give me the distribution before, the distribution after, and the conclusion between them.','decisive')
    if st.button('Restart the night'):st.session_state.scene='intro';st.rerun()
