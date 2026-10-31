from __future__ import annotations
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from data_portfolio import portfolio_data
from risk_engine import apply_software_shock, simulate_losses

st.set_page_config(page_title='Northstar VaR & CVaR Shock Lab',page_icon='◈',layout='wide',initial_sidebar_state='collapsed')
BASE=portfolio_data()
STEPS=['portfolio','shock','tail','decision']
LABELS=['1. Portfolio','2. Shock','3. Tail anatomy','4. Decision']
for k,v in {'step':'portfolio','severity':50,'confidence':.95,'notes':{},'decision':None}.items():
    st.session_state.setdefault(k,v.copy() if isinstance(v,dict) else v)

st.markdown('''<style>
.block-container{max-width:1420px;padding-top:1rem}.eyebrow{color:#168c86;font-size:.78rem;font-weight:800;letter-spacing:.13em}.story{font-size:1.16rem;line-height:1.55;max-width:1050px}[data-testid="stMetricValue"]{font-size:1.65rem}</style>''',unsafe_allow_html=True)

def style(fig,title,h=420):
    fig.update_layout(title=title,height=h,margin=dict(l=35,r=25,t=65,b=45),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',legend=dict(orientation='h',y=1.08),hovermode='closest')
    fig.update_yaxes(gridcolor='rgba(128,128,128,.15)');return fig

def goto(s):st.session_state.step=s;st.rerun()
def progress():
    i=STEPS.index(st.session_state.step);st.progress((i+1)/4);cols=st.columns(4)
    for j,(c,l) in enumerate(zip(cols,LABELS)):c.markdown(f'**{l}**' if i==j else l)
def nav(next_step=None):
    a,b=st.columns([4,1]);i=STEPS.index(st.session_state.step)
    if i and a.button('← Back'):goto(STEPS[i-1])
    if next_step and b.button('Continue →',type='primary',use_container_width=True):goto(next_step)
def note(key,prompt):
    with st.form('note_'+key):
        t=st.text_area(prompt,value=st.session_state.notes.get(key,''),height=85)
        if st.form_submit_button('Save learning note'):
            st.session_state.notes[key]=t.strip();st.success('Saved to the final record.')
def distribution_chart(base,stress):
    fig=go.Figure()
    for result,name,color in [(base,'Before shock','#18A7A0'),(stress,'After shock','#D45B5B')]:
        h,e=np.histogram(result['losses'],bins=90,density=True);x=(e[:-1]+e[1:])/2
        fig.add_trace(go.Scatter(x=x,y=h,name=name,line=dict(color=color,width=3),fill='tozeroy',opacity=.38))
    fig.add_vline(x=stress['var'],line_color='#E4B45B',line_width=3,annotation_text=f"VaR ${stress['var']:.0f}m")
    fig.add_vline(x=stress['cvar'],line_color='#D45B5B',line_width=3,annotation_text=f"CVaR ${stress['cvar']:.0f}m")
    fig.add_vrect(x0=stress['var'],x1=max(stress['losses']),fillcolor='#D45B5B',opacity=.08,line_width=0,annotation_text='Tail losses')
    fig.update_xaxes(title='One-year simulated portfolio loss ($ millions)');fig.update_yaxes(title='Relative frequency')
    return style(fig,'One shock changes the entire loss distribution',470)

st.markdown('<div class="eyebrow">NORTHSTAR PRIVATE DEBT FUND · VAR/CVAR SHOCK LAB</div>',unsafe_allow_html=True)
st.title('One Shock. One Distribution. One Decision.')
st.caption('Fictional loans and synthetic data. The single event is an AI-driven repricing of software credit with spillovers to the broader private-debt portfolio.')
progress();st.divider();step=st.session_state.step

if step=='portfolio':
    st.subheader('The portfolio before the shock')
    st.markdown('<div class="story">Northstar manages eight private loans totaling $800 million. The portfolio appears diversified, but Meridian Cloud is exposed to a potential AI-driven change in software economics. Your task is not to calculate every risk measure. Your task is to understand how one shock changes portfolio VaR and CVaR.</div>',unsafe_allow_html=True)
    cols=st.columns(4);cols[0].metric('Loans','8');cols[1].metric('Total exposure','$800m');cols[2].metric('Software exposure','$80m');cols[3].metric('Simulation trials','30,000')
    fig=go.Figure(go.Bar(x=BASE.asset,y=BASE.exposure,marker_color=['#D45B5B' if s=='Software' else '#18A7A0' for s in BASE.sector],customdata=np.stack([BASE.sector,BASE.pd*100,BASE.lgd*100],axis=1),hovertemplate='<b>%{x}</b><br>Exposure: $%{y:.0f}m<br>Sector: %{customdata[0]}<br>PD: %{customdata[1]:.1f}%<br>LGD: %{customdata[2]:.1f}%<extra></extra>'))
    fig.update_yaxes(title='Exposure ($m)');st.plotly_chart(style(fig,'The loan book: Meridian is the shock origin'),use_container_width=True)
    with st.expander('Calculation setup'):
        st.markdown('Each trial combines **correlated default losses** and **valuation markdowns**. The base case and stressed case use the same portfolio and simulation seed, so the change in the loss distribution comes from the shock assumptions.')
    note('portfolio','Before seeing the shock, what would make one $80 million loan important to portfolio tail risk?');nav('shock')

elif step=='shock':
    st.subheader('The event: software credit reprices')
    st.markdown('<div class="story">AI-native competition weakens software pricing power. Meridian’s default probability and loss severity rise, its mark falls, and correlations increase as lenders reassess similar underwriting assumptions across private debt.</div>',unsafe_allow_html=True)
    severity=st.slider('Shock severity',0,100,st.session_state.severity,5);st.session_state.severity=severity
    stressed_df=apply_software_shock(BASE,severity)
    before=BASE.loc[BASE.asset.eq('Meridian Cloud')].iloc[0];after=stressed_df.loc[stressed_df.asset.eq('Meridian Cloud')].iloc[0]
    c=st.columns(4);c[0].metric('Meridian PD',f"{after.pd:.1%}",delta=f"{after.pd-before.pd:+.1%}",delta_color='inverse');c[1].metric('Meridian LGD',f"{after.lgd:.1%}",delta=f"{after.lgd-before.lgd:+.1%}",delta_color='inverse');c[2].metric('Meridian mark',f"{after['mark']:.1f}",delta=f"{after['mark']-before['mark']:+.1f}");c[3].metric('Common-factor loading',f"{.30+.35*severity/100:.2f}")
    comp=pd.DataFrame({'Input':['PD (%)','LGD (%)','Mark / par'], 'Before':[before.pd*100,before.lgd*100,before['mark']], 'After':[after.pd*100,after.lgd*100,after['mark']]})
    fig=go.Figure();fig.add_trace(go.Bar(x=comp.Input,y=comp.Before,name='Before',marker_color='#18A7A0'));fig.add_trace(go.Bar(x=comp.Input,y=comp.After,name='After',marker_color='#D45B5B'));fig.update_layout(barmode='group');st.plotly_chart(style(fig,'The shock changes only the inputs needed for the loss simulation'),use_container_width=True)
    with st.expander('Shock mechanics'):
        st.markdown('The shock increases Meridian’s **PD**, increases **LGD**, lowers the **mark**, and raises common-factor dependence. Small spillovers also affect the rest of the portfolio. Those changes feed directly into the simulated loss distribution.')
    note('shock','Which changed input should matter most for VaR, and which should matter most for CVaR? Explain.');nav('tail')

elif step=='tail':
    st.subheader('What the shock does to VaR and CVaR')
    confidence=st.select_slider('Confidence level',options=[.90,.95,.975,.99],value=st.session_state.confidence,format_func=lambda x:f'{x:.1%}');st.session_state.confidence=confidence
    base=simulate_losses(BASE,0,confidence);stressed_df=apply_software_shock(BASE,st.session_state.severity);stress=simulate_losses(stressed_df,st.session_state.severity,confidence)
    c=st.columns(5);c[0].metric('VaR before',f"${base['var']:.1f}m");c[1].metric('VaR after',f"${stress['var']:.1f}m",delta=f"+${stress['var']-base['var']:.1f}m",delta_color='inverse');c[2].metric('CVaR before',f"${base['cvar']:.1f}m");c[3].metric('CVaR after',f"${stress['cvar']:.1f}m",delta=f"+${stress['cvar']-base['cvar']:.1f}m",delta_color='inverse');c[4].metric('Tail gap',f"${stress['tail_width']:.1f}m")
    st.plotly_chart(distribution_chart(base,stress),use_container_width=True)
    left,right=st.columns([1.4,1])
    with left:
        tc=stress['tail_contribution'].sort_values();fig=go.Figure(go.Bar(y=tc.index,x=tc.values,orientation='h',marker_color=['#D45B5B' if n=='Meridian Cloud' else '#18A7A0' for n in tc.index]));fig.update_xaxes(title='Average contribution in VaR-tail scenarios ($m)');st.plotly_chart(style(fig,'Who contributes to losses beyond VaR?',365),use_container_width=True)
    with right:
        st.markdown('### Read the result')
        st.write(f"At **{confidence:.1%} confidence**, VaR is the loss threshold of **${stress['var']:.1f} million**.")
        st.write(f"CVaR is the average loss once that threshold is crossed: **${stress['cvar']:.1f} million**.")
        st.write(f"The distance between them is **${stress['tail_width']:.1f} million**. That gap describes the severity beyond the threshold.")
        st.info('VaR answers: “Where does the tail begin?” CVaR answers: “How bad is the tail once we are in it?”')
    with st.expander('Core calculations'):
        st.latex(r"VaR_c(L)=\inf\{\ell:P(L\leq \ell)\geq c\}")
        st.latex(r"CVaR_c(L)=E[L\mid L\geq VaR_c(L)]")
        st.write('All additional outputs on this page, including the tail gap and borrower contributions, are derived from the same stressed loss distribution.')
    note('tail','What does CVaR reveal that VaR alone would miss in this scenario?');nav('decision')

elif step=='decision':
    st.subheader('Make the portfolio decision')
    stressed_df=apply_software_shock(BASE,st.session_state.severity);stress=simulate_losses(stressed_df,st.session_state.severity,st.session_state.confidence)
    st.markdown('<div class="story">The committee does not need a second dashboard. The committee needs a decision based on the change in the tail.</div>',unsafe_allow_html=True)
    decision=st.radio('Portfolio action',['Keep the portfolio unchanged','Reduce Meridian exposure','Reduce Meridian and related software risk','Increase the fund risk buffer'],horizontal=True);st.session_state.decision=decision
    reversal=st.number_input('Maximum acceptable CVaR ($m)',min_value=0.0,value=float(round(stress['cvar'],1)),step=5.0)
    note('decision','State the recommendation, cite VaR and CVaR, explain the tail contribution, and state the CVaR level that would reverse the decision.')
    st.markdown('### Learning record')
    record=pd.DataFrame([{'Stage':k.title(),'Reasoning':v} for k,v in st.session_state.notes.items() if v])
    if not record.empty:st.dataframe(record,use_container_width=True,hide_index=True)
    output={'shock':'AI-driven software credit repricing','severity':st.session_state.severity,'confidence':st.session_state.confidence,'var':round(stress['var'],2),'cvar':round(stress['cvar'],2),'tail_gap':round(stress['tail_width'],2),'decision':decision,'maximum_acceptable_cvar':reversal,'tail_contribution':{k:round(float(v),2) for k,v in stress['tail_contribution'].items()},'learning_notes':st.session_state.notes}
    st.download_button('Download VaR/CVaR committee record',json.dumps(output,indent=2),file_name='northstar_var_cvar_record.json',mime='application/json',type='primary')
