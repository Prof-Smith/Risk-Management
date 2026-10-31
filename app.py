from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from data_portfolio import portfolio_data
from risk_engine import apply_ghostline_shock, simulate_losses

st.set_page_config(page_title='Blackridge: One Night Inside the Tail',page_icon='◈',layout='wide',initial_sidebar_state='collapsed')
BASE=portfolio_data()
SCENES=['cold_open','handoff','baseline','shock','reveal','interrogation','tail','committee']
TIMES=['4:17 PM','5:02 PM','6:08 PM','7:35 PM','9:10 PM','10:48 PM','12:16 AM','1:03 AM']
DEFAULTS={'scene':'cold_open','severity':60,'confidence':.95}
for k,v in DEFAULTS.items(): st.session_state.setdefault(k,v)

CHAR={
 'John Tuld':('john_tuld.png','Chief Executive Officer','#173F5F'),
 'Eric Dale':('eric_dale.png','Former Head of Risk','#526777'),
 'Sarah Robertson':('sarah_robertson.png','Chief Risk Officer','#B7872B'),
 'Sam Rogers':('sam_rogers.png','Head of Portfolio Management','#245B77'),
 'Peter Sullivan':('peter_sullivan.png','Quantitative Risk Analyst','#168C86'),
 'Seth Bregman':('seth_bregman.png','Associate Risk Analyst','#3B8EBA'),
 'Will Emerson':('will_emerson.png','Head of Trading & Portfolio Solutions','#A56632'),
 'Jared Cohen':('jared_cohen.png','Head of Private Credit','#42735B'),
}

st.markdown('''<style>
.block-container{max-width:1450px;padding-top:.8rem;padding-bottom:3rem}.eyebrow{color:#174868;font-size:.76rem;font-weight:800;letter-spacing:.15em}.scene-title{font-family:Georgia,serif;font-size:2.05rem;font-weight:700;color:#102A43;margin:.2rem 0 .25rem}.scene-copy{font-family:Georgia,serif;font-size:1.14rem;line-height:1.6;max-width:1050px}.comic{border:2px solid #183B56;border-radius:14px;background:#F8FAFC;padding:.8rem;box-shadow:5px 6px 0 #D6E0E7;height:100%}.comic-name{font-weight:900;color:#102A43;letter-spacing:.04em}.comic-role{font-size:.78rem;color:#60788A;text-transform:uppercase;letter-spacing:.08em}.bubble{position:relative;background:white;color:#102A43;border:2px solid #183B56;border-radius:18px;padding:1rem 1.15rem;margin-top:.7rem;font-family:Georgia,serif;font-size:1.02rem;line-height:1.45}.bubble:before{content:'';position:absolute;top:-13px;left:28px;border-width:0 12px 13px;border-style:solid;border-color:transparent transparent #183B56}.bubble:after{content:'';position:absolute;top:-9px;left:30px;border-width:0 10px 11px;border-style:solid;border-color:transparent transparent white}.caption-box{background:#102A43;color:white;padding:.75rem 1rem;border-radius:7px;font-family:Georgia,serif;letter-spacing:.02em}.calc-bridge{border-left:5px solid #D69C35;background:#FFF9EC;color:#40351E;padding:.9rem 1rem;border-radius:7px}.stButton>button{border-radius:8px;font-weight:750}[data-testid="stMetricValue"]{font-size:1.6rem}
</style>''',unsafe_allow_html=True)

def style(fig,title,h=420):
    fig.update_layout(title=dict(text=title,font=dict(size=20,family='Arial')),height=h,margin=dict(l=35,r=25,t=70,b=45),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(color='#102A43'),legend=dict(orientation='h',y=1.08),hoverlabel=dict(bgcolor='#102A43',font_color='white'))
    fig.update_xaxes(showgrid=False,zeroline=False);fig.update_yaxes(gridcolor='rgba(128,128,128,.16)',zeroline=False);return fig

def portrait(name): return f"assets/characters/{CHAR[name][0]}"
def panel(name,text):
    color=CHAR[name][2]
    with st.container(border=False):
        st.markdown(f"<div class='comic' style='border-color:{color};box-shadow:5px 6px 0 {color}33'>",unsafe_allow_html=True)
        st.image(portrait(name),use_container_width=True)
        st.markdown(f"<div class='comic-name'>{name}</div><div class='comic-role'>{CHAR[name][1]}</div><div class='bubble' style='border-color:{color}'>{text}</div></div>",unsafe_allow_html=True)
def exchange(left_name,left_text,right_name,right_text):
    a,b=st.columns(2,gap='large')
    with a: panel(left_name,left_text)
    with b: panel(right_name,right_text)
def goto(s): st.session_state.scene=s; st.rerun()
def nav(next_scene=None):
    a,b=st.columns([4,1]);i=SCENES.index(st.session_state.scene)
    if i and a.button('← Previous panel'):goto(SCENES[i-1])
    if next_scene and b.button('Turn the page →',type='primary',use_container_width=True):goto(next_scene)
def timeline():
    i=SCENES.index(st.session_state.scene);st.progress((i+1)/len(SCENES));cols=st.columns(8)
    for j,(c,t) in enumerate(zip(cols,TIMES)):c.caption(('● ' if i==j else '')+t)
def dist_chart(base,stress):
    fig=go.Figure()
    colors=[('#168C86','Before shock',base),('#C7474B','After shock',stress)]
    for color,name,r in colors:
        h,e=np.histogram(r['losses'],bins=100,density=True);x=(e[:-1]+e[1:])/2
        fig.add_trace(go.Scatter(x=x,y=h,name=name,mode='lines',line=dict(color=color,width=3),fill='tozeroy',fillcolor=color+'25'))
    fig.add_vrect(x0=stress['var'],x1=max(stress['losses']),fillcolor='#C7474B',opacity=.09,line_width=0,annotation_text='Tail beyond VaR',annotation_position='top left')
    fig.add_vline(x=stress['var'],line_color='#D69C35',line_width=3,annotation_text=f"VaR ${stress['var']:.1f}m",annotation_position='top')
    fig.add_vline(x=stress['cvar'],line_color='#C7474B',line_width=3,annotation_text=f"CVaR ${stress['cvar']:.1f}m",annotation_position='bottom')
    fig.update_xaxes(title='Simulated portfolio loss ($ millions)');fig.update_yaxes(title='Relative frequency')
    return style(fig,'The shock shifts the distribution and deepens the tail',490)
def exceedance_chart(base,stress):
    fig=go.Figure()
    for color,name,r in [('#168C86','Before shock',base),('#C7474B','After shock',stress)]:
        x=np.sort(r['losses']);y=1-np.arange(1,len(x)+1)/len(x)
        fig.add_trace(go.Scatter(x=x,y=y,name=name,line=dict(color=color,width=3)))
    fig.update_yaxes(type='log',title='Probability loss is exceeded',tickformat='.1%');fig.update_xaxes(title='Loss threshold ($ millions)')
    return style(fig,'Loss exceedance curve: how quickly extreme losses become rare',390)
def sensitivity_curve(conf):
    levels=list(range(0,101,10));vars_= [];cvars=[]
    for s in levels:
        r=simulate_losses(apply_ghostline_shock(BASE,s),s,conf,simulations=12000,seed=47);vars_.append(r['var']);cvars.append(r['cvar'])
    fig=go.Figure();fig.add_trace(go.Scatter(x=levels,y=vars_,name='VaR',line=dict(color='#D69C35',width=4)));fig.add_trace(go.Scatter(x=levels,y=cvars,name='CVaR',line=dict(color='#C7474B',width=4),fill='tonexty',fillcolor='rgba(199,71,75,.10)'))
    fig.add_vline(x=st.session_state.severity,line_dash='dash',line_color='#173F5F',annotation_text='Current shock')
    fig.update_xaxes(title='Shock severity');fig.update_yaxes(title='Loss ($ millions)')
    return style(fig,'Sensitivity: the tail opens as the shock intensifies',390)

def scene_header(kicker,title,copy):
    st.markdown(f"<div class='eyebrow'>{kicker}</div><div class='scene-title'>{title}</div><div class='scene-copy'>{copy}</div>",unsafe_allow_html=True)

st.markdown("<div class='eyebrow'>BLACKRIDGE CAPITAL · SPECIAL SITUATIONS CREDIT FUND IV</div>",unsafe_allow_html=True)
st.title('One Night Inside the Tail')
st.caption('An original fictional teaching simulation inspired by the organizational tension of Margin Call (2011). No film dialogue is reproduced. All firms, data, commentary, and modeled events are fictional.')
timeline();st.divider();scene=st.session_state.scene

if scene=='cold_open':
    scene_header('4:17 PM · RISK FLOOR','The last file out of the building','Every borrower is current. Blackridge reports no crisis. Eric Dale leaves behind one unfinished model and a warning that the portfolio may be stable only because the market has not forced a new price.')
    exchange('Eric Dale','Ghostline did not keep its value because the business was unchanged. Ghostline kept its value because no one had been forced to price it.','Peter Sullivan','You changed the mark, the default assumptions, and the dependence structure. You were not modeling one loan. You were modeling what the loan reveals.')
    st.markdown("<div class='caption-box'>FILE RECEIVED: GHOSTLINE_TAIL_RECALIBRATION_v17_FINAL</div>",unsafe_allow_html=True)
    nav('handoff')

elif scene=='handoff':
    scene_header('5:02 PM · MODEL TERMINAL','Eight loans, four altered assumptions','Peter opens the Blackridge book. Ghostline is only $80 million of an $800 million portfolio, but the unfinished model links the software shock to PD, LGD, valuation marks, and common-factor dependence.')
    left,right=st.columns([1.6,1])
    with left:
        fig=go.Figure(go.Bar(x=BASE.asset,y=BASE.exposure,marker_color=['#C7474B' if n=='Ghostline Systems' else '#168C86' for n in BASE.asset],text=BASE.exposure,texttemplate='$%{text:.0f}m',textposition='outside'))
        fig.update_yaxes(title='Exposure ($m)');st.plotly_chart(style(fig,'The Blackridge loan book',420),use_container_width=True)
    with right:
        st.markdown("<div class='calc-bridge'><b>MECHANICS</b><br><br>Ghostline PD ↑<br>Ghostline LGD ↑<br>Ghostline mark ↓<br>Common dependence ↑</div>",unsafe_allow_html=True)
        panel('Seth Bregman','Ghostline is ten percent of the book. What would make one loan control the tail?')
    nav('baseline')

elif scene=='baseline':
    scene_header('6:08 PM · QUANT DESK','Build the world before the shock','Peter and Seth establish the baseline. The confidence level changes where the tail begins; it does not change the underlying simulated losses.')
    confidence=st.select_slider('Confidence level',options=[.90,.95,.975,.99],value=st.session_state.confidence,format_func=lambda x:f'{x:.1%}');st.session_state.confidence=confidence
    base=simulate_losses(BASE,0,confidence);cols=st.columns(3);cols[0].metric('Simulation trials','30,000');cols[1].metric('Baseline VaR',f"${base['var']:.1f}m");cols[2].metric('Baseline CVaR',f"${base['cvar']:.1f}m")
    exchange('Seth Bregman','Every borrower is current. What exactly are we looking for?','Peter Sullivan','Not a default. A change in the distribution. VaR marks the boundary. CVaR tells us what happens after we cross it.')
    st.markdown("<div class='calc-bridge'><b>CALCULATION BRIDGE</b><br>VaR = selected percentile of portfolio losses. CVaR = average portfolio loss conditional on being beyond VaR.</div>",unsafe_allow_html=True)
    nav('shock')

elif scene=='shock':
    scene_header('7:35 PM · MARKET ALERT','The market moves. The mark does not.','AI-native competition pressures enterprise-software pricing. Public software credit reprices. Ghostline remains privately marked near par. Eric asks which signal the model should trust.')
    severity=st.slider('AI-driven software-credit shock severity',0,100,st.session_state.severity,5);st.session_state.severity=severity
    stressed=apply_ghostline_shock(BASE,severity);b=BASE[BASE.asset.eq('Ghostline Systems')].iloc[0];a=stressed[stressed.asset.eq('Ghostline Systems')].iloc[0]
    cols=st.columns(4);cols[0].metric('Ghostline PD',f"{a.pd:.1%}",f"{a.pd-b.pd:+.1%}",delta_color='inverse');cols[1].metric('Ghostline LGD',f"{a.lgd:.1%}",f"{a.lgd-b.lgd:+.1%}",delta_color='inverse');cols[2].metric('Ghostline mark',f"{a['mark']:.1f}",f"{a['mark']-b['mark']:+.1f}");cols[3].metric('Common loading',f"{.30+.35*severity/100:.2f}")
    exchange('Eric Dale','The market moved. Ghostline’s mark did not. Decide which one the model should believe.','Peter Sullivan','Same portfolio. Same simulation seed. Different economic assumptions. The comparison is the result.')
    nav('reveal')

elif scene=='reveal':
    scene_header('9:10 PM · RISK ROOM','The tail opens','The stressed simulation changes more than one number. The entire loss distribution moves, the VaR threshold shifts, and losses beyond the threshold become more severe.')
    base=simulate_losses(BASE,0,st.session_state.confidence);stress=simulate_losses(apply_ghostline_shock(BASE,st.session_state.severity),st.session_state.severity,st.session_state.confidence)
    cols=st.columns(5);cols[0].metric('VaR before',f"${base['var']:.1f}m");cols[1].metric('VaR after',f"${stress['var']:.1f}m",f"+${stress['var']-base['var']:.1f}m",delta_color='inverse');cols[2].metric('CVaR before',f"${base['cvar']:.1f}m");cols[3].metric('CVaR after',f"${stress['cvar']:.1f}m",f"+${stress['cvar']-base['cvar']:.1f}m",delta_color='inverse');cols[4].metric('Tail gap',f"${stress['tail_gap']:.1f}m")
    tab1,tab2=st.tabs(['Distribution','Exceedance curve'])
    with tab1:st.plotly_chart(dist_chart(base,stress),use_container_width=True)
    with tab2:st.plotly_chart(exceedance_chart(base,stress),use_container_width=True)
    exchange('Seth Bregman','The VaR threshold moved.','Peter Sullivan','The losses beyond the threshold moved farther. CVaR is showing how severe the tail becomes once the boundary is crossed.')
    nav('interrogation')

elif scene=='interrogation':
    scene_header('10:48 PM · CHIEF RISK OFFICE','Interrogate the model, not the drama','Sarah does not accept a severe result simply because it is severe. The same shock slider now acts as a sensitivity test across the entire VaR and CVaR curve.')
    st.plotly_chart(sensitivity_curve(st.session_state.confidence),use_container_width=True)
    exchange('Sarah Robertson','A dramatic result still has to survive a reasonable change in assumptions.','Peter Sullivan','The gap between VaR and CVaR widens as shock severity rises. That is the part of the story the threshold alone cannot tell.')
    st.markdown("<div class='calc-bridge'><b>ONE SHOCK, FOUR LINKS</b><br>PD raises default frequency. LGD raises loss severity. The mark adds immediate loss. Dependence makes adverse outcomes arrive together.</div>",unsafe_allow_html=True)
    nav('tail')

elif scene=='tail':
    scene_header('12:16 AM · PRIVATE CREDIT FLOOR','Who owns the tail?','Jared and Will move the argument from distribution-level risk to borrower-level contribution. If Ghostline dominates, the problem may be specific. If CipherWorks and the rest of the book follow, the portfolio is revealing hidden dependence.')
    stress=simulate_losses(apply_ghostline_shock(BASE,st.session_state.severity),st.session_state.severity,st.session_state.confidence);tc=stress['tail_contribution'].sort_values()
    fig=go.Figure(go.Bar(y=tc.index,x=tc.values,orientation='h',marker_color=['#C7474B' if n in ['Ghostline Systems','CipherWorks'] else '#168C86' for n in tc.index],text=[f'${v:.1f}m' for v in tc.values],textposition='outside'))
    fig.update_xaxes(title='Average borrower loss in portfolio scenarios beyond VaR ($m)');st.plotly_chart(style(fig,'Contribution inside the stressed tail',450),use_container_width=True)
    exchange('Jared Cohen','If Ghostline owns the tail, manage Ghostline. If CipherWorks and the rest of the book follow it, manage the portfolio.','Will Emerson','The chart tells us where the risk comes from. It does not tell us what a sale would cost or whether the market can absorb it.')
    nav('committee')

elif scene=='committee':
    scene_header('1:03 AM · EXECUTIVE COMMITTEE','The model reaches the room','The story ends with an analytical briefing rather than a participant decision. The committee receives the two distributions, the tail metrics, and the borrower contribution evidence.')
    stress=simulate_losses(apply_ghostline_shock(BASE,st.session_state.severity),st.session_state.severity,st.session_state.confidence);top=stress['tail_contribution'].index[0]
    cols=st.columns(4);cols[0].metric('Shock severity',f"{st.session_state.severity}/100");cols[1].metric('Stressed VaR',f"${stress['var']:.1f}m");cols[2].metric('Stressed CVaR',f"${stress['cvar']:.1f}m");cols[3].metric('Largest contributor',top)
    exchange('Sam Rogers','We manage portfolios, not spreadsheets. Tell the committee what risk the fund is carrying and what the analysis can support.','John Tuld','Give me the distribution before the shock, the distribution after the shock, and the conclusion between them.')
    st.markdown("<div class='caption-box'>GHOSTLINE STARTED THE SHOCK. THE DISTRIBUTION REVEALED THE PORTFOLIO.</div>",unsafe_allow_html=True)
    st.info('No decision form, recommendation input, scoring, or reversal-condition input is included. The app ends at the analytical briefing so the class discussion can continue outside the interface.')
    if st.button('Restart the night'):st.session_state.scene='cold_open';st.rerun()
