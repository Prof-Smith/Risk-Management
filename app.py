from __future__ import annotations
import streamlit as st, plotly.graph_objects as go, pandas as pd, numpy as np
from services.case_engine import load_case, calculate, reversal_pd

st.set_page_config(page_title='Northstar Private Debt Lab',page_icon='◈',layout='wide',initial_sidebar_state='collapsed')
case, scenarios, evidence=load_case()
PHASES=['briefing','evidence','decision','scenarios','intervention','defense']
LABELS=['Mandate','Evidence','Commit','Scenario Lab','Sponsor Offer','Board Defense']
for k,v in {'phase':'briefing','initial_decision':None,'final_decision':None,'scenario_index':0,'revealed':[]}.items(): st.session_state.setdefault(k,v)

st.markdown('''<style>
.block-container{max-width:1450px;padding-top:1.4rem}.lab-kicker{color:#55D6CF;font-size:.78rem;letter-spacing:.14em;font-weight:700}.lab-card{border:1px solid #294057;border-radius:12px;padding:1.15rem;background:linear-gradient(145deg,#102235,#0B1828)}.signal{padding:.55rem .8rem;border-left:4px solid #E4B45B;background:#18283A;border-radius:4px}.stButton>button{border-radius:8px;font-weight:700}.small{color:#9FB0BE;font-size:.86rem}</style>''',unsafe_allow_html=True)

def goto(name): st.session_state.phase=name; st.rerun()
def progress():
    idx=PHASES.index(st.session_state.phase); st.progress((idx+1)/len(PHASES)); cols=st.columns(6)
    for i,(c,l) in enumerate(zip(cols,LABELS)):
        c.markdown(f"**{'● ' if i==idx else ''}{l}**" if i<=idx else f"<span style='color:#6E8191'>{l}</span>",unsafe_allow_html=True)
def metric_cards(r):
    c=st.columns(6); vals=[('Leverage',f"{r['leverage']:.1f}×"),('Coverage',f"{r['coverage']:.2f}×"),('PD',f"{r['pd']:.1f}%"),('Recovery',f"{r['recovery']:.0f}%"),('Expected loss',f"${r['expected_loss']:.2f}m"),('Secondary bid',f"{r['bid']:.0f}")]
    for col,(a,b) in zip(c,vals): col.metric(a,b)
def nav(next_phase=None,disable=False):
    left,right=st.columns([4,1])
    if PHASES.index(st.session_state.phase)>0 and left.button('← Previous room'): goto(PHASES[PHASES.index(st.session_state.phase)-1])
    if next_phase and right.button('Continue →',type='primary',use_container_width=True,disabled=disable): goto(next_phase)

st.markdown("<div class='lab-kicker'>NORTHSTAR DIRECT LENDING FUND III  /  INVESTMENT COMMITTEE LAB</div>",unsafe_allow_html=True)
st.title('The Meridian Amendment Decision')
st.caption('A fictional private-debt decision experience. All firms, figures, probabilities, and outcomes are synthetic.')
progress(); st.divider()

p=st.session_state.phase
if p=='briefing':
    a,b=st.columns([1.45,1])
    with a:
        st.subheader('The call arrives at 8:10 a.m.')
        st.markdown(case['narrative'])
        st.markdown("<div class='signal'><b>Your mandate</b><br>"+case['mandate']+"</div>",unsafe_allow_html=True)
        st.warning('The borrower is current. The deterioration is real. The committee must decide before the next interest date.')
    with b:
        st.markdown("<div class='lab-card'><b>BASELINE CREDIT</b><hr>First-lien loan: <b>$80.0m</b><br>Cash coupon: <b>10.75%</b><br>Net leverage: <b>5.4×</b><br>Interest coverage: <b>1.55×</b><br>Fund NAV exposure: <b>6.4%</b><br>Expected-loss limit: <b>$4.5m</b></div>",unsafe_allow_html=True)
    ack=st.checkbox('I accept responsibility for the committee recommendation.')
    nav('evidence',not ack)

elif p=='evidence':
    st.subheader('Evidence room')
    tabs=st.tabs(['Operating trend','Credit dashboard','Deal structure','Information gaps'])
    with tabs[0]:
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=evidence.period,y=evidence.arr_retention_pct,name='ARR retention',line=dict(color='#55D6CF',width=3)))
        fig.add_trace(go.Scatter(x=evidence.period,y=evidence.ebitda_margin_pct,name='EBITDA margin',yaxis='y2',line=dict(color='#E4B45B',width=3)))
        fig.update_layout(height=390,template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',yaxis=dict(title='Retention %'),yaxis2=dict(title='Margin %',overlaying='y',side='right'),legend=dict(orientation='h'))
        st.plotly_chart(fig,use_container_width=True)
    with tabs[1]:
        c1,c2=st.columns(2)
        with c1:
            fig=go.Figure(go.Scatter(x=evidence.period,y=evidence.net_leverage_x,mode='lines+markers',line=dict(color='#D45B5B',width=3))); fig.add_hline(y=5.75,line_dash='dash',line_color='#E4B45B',annotation_text='Covenant')
            fig.update_layout(title='Net leverage',height=360,template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)');st.plotly_chart(fig,use_container_width=True)
        with c2:
            fig=go.Figure(go.Bar(x=evidence.period,y=evidence.liquidity_mm,marker_color=['#18A7A0']*4+['#D45B5B']));fig.update_layout(title='Borrower liquidity ($m)',height=360,template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)');st.plotly_chart(fig,use_container_width=True)
    with tabs[2]: st.markdown('''### Amendment request
- Reduce the cash coupon and introduce PIK interest
- Reset the maximum-leverage covenant
- Preserve revolver access
- Extend the runway without a mandatory paydown

### Lender concern
PIK interest may preserve near-term liquidity while increasing principal and delaying recognition of deterioration.''')
    with tabs[3]: st.markdown('''- No observable market price for the loan
- Recovery depends on enterprise-value and exit-multiple assumptions
- Retention deterioration may be cyclical or structural
- Sponsor willingness to contribute capital is not yet known
- Fund-level redemption needs have not yet been disclosed''')
    st.session_state.decisive_signal=st.radio('Which signal controls your initial view?',['Retention deterioration','Leverage and covenant headroom','Liquidity runway','Interest coverage','Valuation and recovery uncertainty'],horizontal=True)
    st.session_state.evidence_note=st.text_area('Record one evidence-based observation')
    nav('decision',not bool(st.session_state.evidence_note.strip()))

elif p=='decision':
    st.subheader('Decision desk: commit before the scenarios')
    d=st.radio(case['decision_prompt'],case['decision_choices'],horizontal=True,key='initial_choice')
    conf=st.slider('Confidence',0,100,60)
    rationale=st.text_area('Committee rationale',placeholder='State the action, decisive evidence, lender protection, and principal uncertainty.')
    lock=st.checkbox('Lock this initial recommendation')
    if d: st.session_state.initial_decision=d; st.session_state.initial_confidence=conf; st.session_state.initial_rationale=rationale
    nav('scenarios',not(lock and bool(rationale.strip())))

elif p=='scenarios':
    visible=[s for s in scenarios if not s.get('facilitator_only')]
    idx=st.session_state.scenario_index; scenario=visible[idx]; r=calculate(case,scenario)
    st.subheader(f"Scenario {idx+1} of {len(visible)}: {scenario['label']}")
    st.markdown(f"<div class='lab-card'>{scenario['description']}</div>",unsafe_allow_html=True)
    metric_cards(r)
    x=np.linspace(1,30,80); losses=case['baseline']['outstanding_mm']*(x/100)*(1-r['recovery']/100)
    fig=go.Figure(go.Scatter(x=x,y=losses,line=dict(color='#55D6CF',width=4),name='Expected loss'));fig.add_hline(y=case['baseline']['risk_limit_expected_loss_mm'],line_color='#D45B5B',line_width=3,annotation_text='Fund limit');fig.add_vline(x=reversal_pd(case,r['recovery']),line_color='#E4B45B',line_dash='dash',annotation_text='Reversal PD')
    fig.update_layout(title='Expected-loss decision boundary',xaxis_title='Probability of default (%)',yaxis_title='Expected loss ($m)',height=390,template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)');st.plotly_chart(fig,use_container_width=True)
    st.write(f"**Scenario signal:** {scenario['decision_signal']}")
    revised=st.radio('Your action after this reveal',case['decision_choices'],horizontal=True,key=f"choice_{idx}")
    note=st.text_area('What changed in your reasoning?',key=f'note_{idx}')
    st.session_state.final_decision=revised
    c1,c2=st.columns([4,1])
    if idx>0 and c1.button('← Prior scenario'): st.session_state.scenario_index-=1; st.rerun()
    if idx<len(visible)-1:
        if c2.button('Reveal next scenario →',type='primary',use_container_width=True,disabled=not bool(note.strip())): st.session_state.scenario_index+=1; st.rerun()
    else:
        if c2.button('Request sponsor response →',type='primary',use_container_width=True,disabled=not bool(note.strip())): goto('intervention')

elif p=='intervention':
    s=[x for x in scenarios if x.get('facilitator_only')][0]; r=calculate(case,s)
    st.subheader('The sponsor returns with a proposal')
    st.success(s['description'])
    c1,c2,c3,c4=st.columns(4);c1.metric('New equity','$30m');c2.metric('Principal paydown','$20m');c3.metric('Recovery',f"{r['recovery']:.0f}%");c4.metric('Expected loss',f"${r['expected_loss']:.2f}m")
    st.markdown('### Negotiate the lender protections')
    protections=st.multiselect('Select the protections required for consent',['Mandatory $20m paydown','Monthly liquidity reporting','Board observer right','Milestone-based covenant reset','PIK cap','Cash sweep','Independent valuation','Sponsor equity funded before consent'])
    final=st.radio('Final action',case['decision_choices'],horizontal=True,key='sponsor_final')
    reversal=st.number_input('State the maximum acceptable probability of default (%)',min_value=0.0,max_value=100.0,value=float(round(reversal_pd(case,r['recovery']),1)),step=.5)
    st.session_state.final_decision=final;st.session_state.protections=protections;st.session_state.user_reversal=reversal
    nav('defense',len(protections)<2)

elif p=='defense':
    st.subheader('Board defense')
    a,b,c=st.columns(3);a.metric('Initial action',st.session_state.initial_decision or '—');b.metric('Final action',st.session_state.final_decision or '—');c.metric('Your reversal PD',f"{st.session_state.get('user_reversal',0):.1f}%")
    if st.session_state.initial_decision!=st.session_state.final_decision: st.success('The recommendation changed. Defend why the change reflects disciplined updating rather than reaction.')
    else: st.info('The recommendation survived the scenarios. Explain why the evidence did not cross the reversal condition.')
    statement=st.text_area('Final investment-committee statement',height=180,placeholder='Recommendation; controlling evidence; required protections; model limitation; numerical reversal condition.')
    with st.expander('Reveal the case architecture'):
        st.markdown('**Mandate → evidence → commitment → scenario sequence → sponsor negotiation → numerical reversal → defense**')
    st.download_button('Download committee record',data=f"Initial: {st.session_state.initial_decision}\nFinal: {st.session_state.final_decision}\nProtections: {', '.join(st.session_state.get('protections',[]))}\nReversal PD: {st.session_state.get('user_reversal',0):.1f}%\nStatement: {statement}",file_name='northstar_committee_record.txt',disabled=not bool(statement.strip()),type='primary')
