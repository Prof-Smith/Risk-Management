from __future__ import annotations
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from data_portfolio import portfolio_data
from risk_engine import apply_ghostline_shock, simulate_losses

st.set_page_config(page_title='Blackridge: One Night Inside the Tail',page_icon='◈',layout='wide',initial_sidebar_state='collapsed')
BASE=portfolio_data(); SCENES=['opening','model','baseline','shock','distribution','challenge','tail','briefing']
LABELS=['4:17 PM','6:08 PM','7:02 PM','7:35 PM','9:10 PM','10:48 PM','12:16 AM','1:03 AM']
for k,v in {'scene':'opening','severity':60,'confidence':.95}.items():st.session_state.setdefault(k,v)
st.markdown('''<style>.block-container{max-width:1440px;padding-top:1rem}.eyebrow{color:#174868;font-weight:800;font-size:.78rem;letter-spacing:.15em}.story{font-size:1.14rem;line-height:1.58;max-width:1050px}.speech{border-left:5px solid #174868;background:#eef3f6;color:#102a43;border-radius:8px;padding:1rem 1.2rem;font-size:1.05rem;line-height:1.5}.name{font-weight:800;color:#0c2e4a}.mechanic{border:1px solid #ccd8df;border-radius:10px;padding:1rem;background:#f8fafb;color:#102a43}[data-testid="stMetricValue"]{font-size:1.65rem}</style>''',unsafe_allow_html=True)

def chart(fig,title,h=420):
    fig.update_layout(title=title,height=h,margin=dict(l=35,r=25,t=65,b=45),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',legend=dict(orientation='h',y=1.08));fig.update_yaxes(gridcolor='rgba(128,128,128,.15)');return fig
def goto(s):st.session_state.scene=s;st.rerun()
def nav(next_scene=None):
    a,b=st.columns([4,1]);i=SCENES.index(st.session_state.scene)
    if i and a.button('← Previous scene'):goto(SCENES[i-1])
    if next_scene and b.button('Continue story →',type='primary',use_container_width=True):goto(next_scene)
def progress():
    i=SCENES.index(st.session_state.scene);st.progress((i+1)/len(SCENES));cs=st.columns(8)
    for j,(c,l) in enumerate(zip(cs,LABELS)):c.caption(('● ' if i==j else '')+l)
def speech(name,role,text):
    st.markdown(f'<div class="speech"><span class="name">{name}</span> · {role}<br>{text}</div>',unsafe_allow_html=True)
def distribution(base,stress):
    fig=go.Figure()
    for r,n,c in [(base,'Before shock','#168c86'),(stress,'After shock','#c7474b')]:
        h,e=np.histogram(r['losses'],bins=90,density=True);x=(e[:-1]+e[1:])/2;fig.add_trace(go.Scatter(x=x,y=h,name=n,line=dict(color=c,width=3),fill='tozeroy',opacity=.35))
    fig.add_vline(x=stress['var'],line_color='#d69c35',line_width=3,annotation_text=f"VaR ${stress['var']:.0f}m")
    fig.add_vline(x=stress['cvar'],line_color='#c7474b',line_width=3,annotation_text=f"CVaR ${stress['cvar']:.0f}m")
    fig.add_vrect(x0=stress['var'],x1=max(stress['losses']),fillcolor='#c7474b',opacity=.07,line_width=0)
    fig.update_xaxes(title='Simulated portfolio loss ($m)');fig.update_yaxes(title='Relative frequency');return chart(fig,'The distribution changes before the marks do',470)

st.markdown('<div class="eyebrow">BLACKRIDGE CAPITAL · SPECIAL SITUATIONS CREDIT FUND IV</div>',unsafe_allow_html=True)
st.title('One Night Inside the Tail')
st.caption('An original fictional teaching simulation inspired by the organizational tension of Margin Call (2011). No film dialogue is reproduced. All companies, data, commentary, and modeled events are fictional.')
progress();st.divider();scene=st.session_state.scene

if scene=='opening':
    st.image('assets/blackridge_cast.png',use_container_width=True)
    st.markdown('<div class="story">Blackridge manages eight private loans totaling $800 million. Every borrower is current. At 4:17 p.m., former Head of Risk Eric Dale leaves behind an unfinished file: <b>GHOSTLINE_TAIL_RECALIBRATION_v17_FINAL</b>.</div>',unsafe_allow_html=True)
    speech('Eric Dale','Former Head of Risk','“Ghostline did not keep its value because the business was unchanged. Ghostline kept its value because no one had been forced to price it.”')
    nav('model')

elif scene=='model':
    st.subheader('The unfinished model')
    l,r=st.columns([1.7,1])
    with l:
        fig=go.Figure(go.Bar(x=BASE.asset,y=BASE.exposure,marker_color=['#c7474b' if x=='Ghostline Systems' else '#168c86' for x in BASE.asset]));fig.update_yaxes(title='Exposure ($m)');st.plotly_chart(chart(fig,'The Blackridge loan book'),use_container_width=True)
    with r:
        st.markdown('<div class="mechanic"><b>Eric changed four assumptions</b><br><br>1. Ghostline PD<br>2. Ghostline LGD<br>3. Ghostline mark<br>4. Common-factor dependence</div>',unsafe_allow_html=True)
        speech('Eric Dale','Former Head of Risk','“The labels say Ghostline is software and CipherWorks is business services. The economics may not respect the labels.”')
    nav('baseline')

elif scene=='baseline':
    st.subheader('Peter rebuilds the base distribution')
    confidence=st.select_slider('Confidence level',options=[.90,.95,.975,.99],value=st.session_state.confidence,format_func=lambda x:f'{x:.1%}');st.session_state.confidence=confidence
    base=simulate_losses(BASE,0,confidence);c=st.columns(3);c[0].metric('Trials','30,000');c[1].metric('Baseline VaR',f"${base['var']:.1f}m");c[2].metric('Baseline CVaR',f"${base['cvar']:.1f}m")
    speech('Seth Bregman','Associate Risk Analyst','“Every borrower is current. What exactly are we looking for?”')
    speech('Peter Sullivan','Quantitative Risk Analyst','“Not a default. A change in the distribution.”')
    st.markdown('<div class="mechanic"><b>Calculation bridge</b><br>VaR locates the loss threshold at the selected confidence level. CVaR is the average loss once the portfolio crosses that threshold.</div>',unsafe_allow_html=True)
    nav('shock')

elif scene=='shock':
    st.subheader('The market moves. The private mark does not.')
    severity=st.slider('AI-driven software-credit shock severity',0,100,st.session_state.severity,5);st.session_state.severity=severity
    stressed=apply_ghostline_shock(BASE,severity);before=BASE[BASE.asset.eq('Ghostline Systems')].iloc[0];after=stressed[stressed.asset.eq('Ghostline Systems')].iloc[0]
    c=st.columns(4);c[0].metric('Ghostline PD',f"{after.pd:.1%}",f"{after.pd-before.pd:+.1%}",delta_color='inverse');c[1].metric('Ghostline LGD',f"{after.lgd:.1%}",f"{after.lgd-before.lgd:+.1%}",delta_color='inverse');c[2].metric('Ghostline mark',f"{after['mark']:.1f}",f"{after['mark']-before['mark']:+.1f}");c[3].metric('Common loading',f"{.30+.35*severity/100:.2f}")
    speech('Eric Dale','Former Head of Risk','“The market moved. Ghostline’s mark did not. Decide which one the model should believe.”')
    speech('Peter Sullivan','Quantitative Risk Analyst','“Same portfolio. Same number of trials. Different economic assumptions.”')
    nav('distribution')

elif scene=='distribution':
    st.subheader('The stressed model')
    base=simulate_losses(BASE,0,st.session_state.confidence);stress_df=apply_ghostline_shock(BASE,st.session_state.severity);stress=simulate_losses(stress_df,st.session_state.severity,st.session_state.confidence)
    c=st.columns(5);c[0].metric('VaR before',f"${base['var']:.1f}m");c[1].metric('VaR after',f"${stress['var']:.1f}m",f"+${stress['var']-base['var']:.1f}m",delta_color='inverse');c[2].metric('CVaR before',f"${base['cvar']:.1f}m");c[3].metric('CVaR after',f"${stress['cvar']:.1f}m",f"+${stress['cvar']-base['cvar']:.1f}m",delta_color='inverse');c[4].metric('Tail gap',f"${stress['tail_gap']:.1f}m")
    st.plotly_chart(distribution(base,stress),use_container_width=True)
    speech('Seth Bregman','Associate Risk Analyst','“The VaR threshold moved.”')
    speech('Peter Sullivan','Quantitative Risk Analyst','“The losses beyond the threshold moved farther. That is what CVaR is showing us.”')
    nav('challenge')

elif scene=='challenge':
    st.subheader('Sarah challenges the assumptions')
    speech('Sarah Robertson','Chief Risk Officer','“A dramatic result still has to survive a reasonable change in assumptions.”')
    st.markdown('<div class="mechanic"><b>One slider, four linked mechanics</b><br><br><b>PD ↑</b> → more simulated defaults<br><b>LGD ↑</b> → larger loss when default occurs<br><b>Mark ↓</b> → immediate valuation loss<br><b>Dependence ↑</b> → more loans deteriorate together</div>',unsafe_allow_html=True)
    severity=st.slider('Challenge the shock severity',0,100,st.session_state.severity,5,key='challenge_severity');st.session_state.severity=severity
    stress=simulate_losses(apply_ghostline_shock(BASE,severity),severity,st.session_state.confidence)
    c=st.columns(3);c[0].metric('Revised VaR',f"${stress['var']:.1f}m");c[1].metric('Revised CVaR',f"${stress['cvar']:.1f}m");c[2].metric('Tail gap',f"${stress['tail_gap']:.1f}m")
    speech('Sarah Robertson','Chief Risk Officer','“Do not show me the most severe model. Show me the model whose assumptions the committee can defend.”')
    nav('tail')

elif scene=='tail':
    st.subheader('Who owns the tail?')
    stress=simulate_losses(apply_ghostline_shock(BASE,st.session_state.severity),st.session_state.severity,st.session_state.confidence);tc=stress['tail_contribution'].sort_values()
    fig=go.Figure(go.Bar(y=tc.index,x=tc.values,orientation='h',marker_color=['#c7474b' if n in ['Ghostline Systems','CipherWorks'] else '#168c86' for n in tc.index]));fig.update_xaxes(title='Average contribution in scenarios beyond portfolio VaR ($m)');st.plotly_chart(chart(fig,'Tail contribution by borrower',430),use_container_width=True)
    speech('Jared Cohen','Head of Private Credit','“If Ghostline owns the tail, manage Ghostline. If CipherWorks and the rest of the book follow it, manage the portfolio.”')
    speech('Will Emerson','Head of Trading & Portfolio Solutions','“A recommendation to reduce Ghostline is incomplete. Who buys it, at what discount, and how much CVaR do we actually remove?”')
    nav('briefing')

elif scene=='briefing':
    st.subheader('The midnight committee briefing')
    stress=simulate_losses(apply_ghostline_shock(BASE,st.session_state.severity),st.session_state.severity,st.session_state.confidence);top=stress['tail_contribution'].index[0]
    c=st.columns(4);c[0].metric('Shock severity',f"{st.session_state.severity}/100");c[1].metric('Stressed VaR',f"${stress['var']:.1f}m");c[2].metric('Stressed CVaR',f"${stress['cvar']:.1f}m");c[3].metric('Largest tail contributor',top)
    speech('Sam Rogers','Head of Portfolio Management','“We manage portfolios, not distributions. Tell me which risk the fund is carrying and what the analysis can support.”')
    speech('John Tuld','Chief Executive Officer','“Give the committee the distribution before the shock, the distribution after the shock, and the conclusion between them.”')
    st.markdown('<div class="story"><b>Closing lesson:</b> Ghostline started the shock. The distribution revealed the portfolio. Blackridge must understand whether the model identified a new risk or finally measured one that was already present.</div>',unsafe_allow_html=True)
    st.info('This version intentionally contains no participant decision, recommendation form, scoring, or reversal threshold. The experience ends with an analytical briefing and the course discussion can occur outside the app.')
    if st.button('Restart story'):st.session_state.scene='opening';st.rerun()
