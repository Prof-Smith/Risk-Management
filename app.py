from __future__ import annotations
import json
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from services.case_engine import load_case, calculate, reversal_pd
from services.fund_engine import simulate_fund, liquidity_waterfall, mitigation_effects, SECTORS

st.set_page_config(page_title='Northstar Private Debt Lab',page_icon='◈',layout='wide',initial_sidebar_state='collapsed')
case,scenarios,evidence=load_case()
PHASES=['briefing','evidence','decision','shock','run','response','defense']
LABELS=['Mandate','Evidence','Commit','Credit Shock','Run Lab','Response','Defense']
DEFAULT={'phase':'briefing','journal':[],'initial_decision':None,'final_decision':None,'shock':45,'stale_days':30,'run_pct':8.0,'gate_pct':5.0}
for k,v in DEFAULT.items(): st.session_state.setdefault(k,v.copy() if isinstance(v,list) else v)

st.markdown('''<style>
.block-container{max-width:1480px;padding-top:1.25rem}.kicker{color:#55D6CF;font-weight:800;font-size:.78rem;letter-spacing:.14em}.panel{border:1px solid #2B4358;border-radius:14px;padding:1rem;background:linear-gradient(145deg,#102235,#091724)}.callout{border-left:4px solid #E4B45B;background:#13283A;padding:.8rem 1rem;border-radius:5px}.stButton>button{border-radius:9px;font-weight:750}.metric-label{color:#9FB0BE}</style>''',unsafe_allow_html=True)

def goto(p): st.session_state.phase=p; st.rerun()
def progress():
    i=PHASES.index(st.session_state.phase);st.progress((i+1)/len(PHASES));cols=st.columns(len(PHASES))
    for j,(c,l) in enumerate(zip(cols,LABELS)): c.markdown(f"**{'● ' if i==j else ''}{l}**" if j<=i else f"<span style='color:#61768A'>{l}</span>",unsafe_allow_html=True)
def add_note(stage,text,kind='analysis'):
    if text.strip(): st.session_state.journal.append({'time':datetime.now().strftime('%H:%M:%S'),'stage':stage,'type':kind,'text':text.strip()})
def note_box(stage,prompt,key):
    with st.form(f'form_{key}',clear_on_submit=True):
        text=st.text_area(prompt,key=f'text_{key}')
        submitted=st.form_submit_button('Add to committee record')
        if submitted: add_note(stage,text); st.success('Added to the committee record.')
def journal_panel():
    with st.expander(f"Committee record ({len(st.session_state.journal)} entries)"):
        if not st.session_state.journal: st.caption('No entries yet.')
        for n in st.session_state.journal: st.markdown(f"**{n['stage']} · {n['time']}**  \n{n['text']}")
def nav(nextp=None,disabled=False):
    a,b=st.columns([4,1])
    i=PHASES.index(st.session_state.phase)
    if i and a.button('← Previous room'): goto(PHASES[i-1])
    if nextp and b.button('Continue →',type='primary',use_container_width=True,disabled=disabled): goto(nextp)
def layout(fig,title,height=390):
    fig.update_layout(title=title,height=height,template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',margin=dict(l=35,r=25,t=58,b=35),font=dict(color='#F4F7FA'),legend=dict(orientation='h',y=1.08));return fig

def tail_chart(base,stress):
    fig=go.Figure()
    for r,name,color in [(base,'Baseline','#55D6CF'),(stress,'Stressed','#D45B5B')]:
        h,e=np.histogram(r['losses'],bins=90,density=True);x=(e[:-1]+e[1:])/2
        fig.add_trace(go.Scatter(x=x,y=h,mode='lines',name=name,line=dict(color=color,width=3),fill='tozeroy',opacity=.55))
    fig.add_vline(x=stress['var95'],line_color='#E4B45B',line_width=3,annotation_text='95% VaR')
    fig.add_vline(x=stress['cvar95'],line_color='#D45B5B',line_width=3,annotation_text='95% CVaR')
    fig.update_xaxes(title='One-year simulated fund loss ($m)');fig.update_yaxes(title='Density')
    return layout(fig,'Loss distribution: reported calm versus economic stress',430)

def metric_row(r):
    cols=st.columns(6);items=[('95% VaR',f"${r['var95']:.0f}m"),('95% CVaR',f"${r['cvar95']:.0f}m"),('99% CVaR',f"${r['cvar99']:.0f}m"),('Economic NAV',f"${r['economic_nav']:.0f}m"),('Stale-NAV gap',f"${r['stale_gap']:.0f}m"),('Ending cash',f"${r['ending_cash']:.0f}m")]
    for c,(k,v) in zip(cols,items):c.metric(k,v)

st.markdown("<div class='kicker'>NORTHSTAR DIRECT LENDING FUND III / PRIVATE CREDIT LIQUIDITY LAB</div>",unsafe_allow_html=True)
st.title('Meridian: When the Mark Meets the Run')
st.caption('Fictional firms and synthetic data. VaR/CVaR, valuation, run, and liquidity calculations are teaching models, not forecasts.')
progress();journal_panel();st.divider();p=st.session_state.phase

if p=='briefing':
    l,r=st.columns([1.5,1])
    with l:
        st.subheader('8:10 a.m. Investment Committee')
        st.write(case['narrative']);st.markdown("<div class='callout'><b>Mandate</b><br>Decide whether to amend the Meridian loan while protecting fund liquidity, reported NAV credibility, and investor equity.</div>",unsafe_allow_html=True)
        st.warning('The borrower is current, but private marks update slowly and redemption requests settle against reported NAV.')
    with r:
        st.markdown("<div class='panel'><b>FUND SNAPSHOT</b><hr>NAV: <b>$1.25bn</b><br>Cash: <b>6% of NAV</b><br>Committed line: <b>5% of NAV</b><br>Quarterly redemption gate: <b>5%</b><br>Meridian position: <b>6.4% of NAV</b><br>Expected-loss limit: <b>$4.5m</b></div>",unsafe_allow_html=True)
    ack=st.checkbox('I accept the mandate.');nav('evidence',not ack)

elif p=='evidence':
    st.subheader('Evidence room: borrower and fund')
    t1,t2,t3=st.tabs(['Borrower trajectory','Fund concentration','Valuation clock'])
    with t1:
        fig=go.Figure();fig.add_trace(go.Scatter(x=evidence.period,y=evidence.arr_retention_pct,name='ARR retention',line=dict(color='#55D6CF',width=3)));fig.add_trace(go.Scatter(x=evidence.period,y=evidence.ebitda_margin_pct,name='EBITDA margin',yaxis='y2',line=dict(color='#E4B45B',width=3)));fig.update_layout(yaxis2=dict(overlaying='y',side='right'));st.plotly_chart(layout(fig,'Operating deterioration'),use_container_width=True)
    with t2:
        weights=np.array([24,20,17,13,14,12]);fig=go.Figure(go.Bar(x=SECTORS,y=weights,marker_color=['#D45B5B','#18A7A0','#18A7A0','#E4B45B','#55D6CF','#9FB0BE']));fig.update_yaxes(title='% of fund NAV');st.plotly_chart(layout(fig,'Synthetic portfolio concentration'),use_container_width=True)
    with t3:
        days=np.array([0,15,30,45,60,75,90]);reported=np.repeat(100.,len(days));economic=100-(days/90)*9
        fig=go.Figure();fig.add_trace(go.Scatter(x=days,y=reported,name='Reported mark',line=dict(color='#55D6CF',width=3)));fig.add_trace(go.Scatter(x=days,y=economic,name='Illustrative economic value',line=dict(color='#D45B5B',width=3)));fig.update_xaxes(title='Days since independent valuation');fig.update_yaxes(title='Value / par');st.plotly_chart(layout(fig,'Valuation lag can conceal the stress path'),use_container_width=True)
    note_box('Evidence','What evidence matters most, and what is missing?','evidence');nav('decision',len(st.session_state.journal)==0)

elif p=='decision':
    st.subheader('Commit before the market reprices')
    d=st.radio(case['decision_prompt'],case['decision_choices'],horizontal=True);conf=st.slider('Confidence',0,100,60);why=st.text_area('Initial committee rationale')
    if st.button('Lock initial decision',type='primary',disabled=not why.strip()):
        st.session_state.initial_decision=d;st.session_state.initial_confidence=conf;add_note('Initial decision',f"{d} ({conf}% confidence). {why}",'decision');st.success('Decision locked and added to the record.')
    nav('shock',st.session_state.initial_decision is None)

elif p=='shock':
    st.subheader('Credit shock lab: what happens to VaR and CVaR?')
    c1,c2,c3=st.columns(3)
    shock=c1.slider('Credit shock intensity',0,100,st.session_state.shock,5);st.session_state.shock=shock
    stale=c2.slider('Days since independent marks',0,90,st.session_state.stale_days,5);st.session_state.stale_days=stale
    run=c3.slider('Redemption requests (% NAV)',0.,25.,st.session_state.run_pct,.5);st.session_state.run_pct=run
    base=simulate_fund(1250,0,5,0,5);stress=simulate_fund(1250,shock,stale,run,st.session_state.gate_pct)
    metric_row(stress);st.plotly_chart(tail_chart(base,stress),use_container_width=True)
    a,b=st.columns(2)
    with a:
        fig=go.Figure(go.Bar(x=['VaR 95','CVaR 95','CVaR 99'],y=[stress['var95'],stress['cvar95'],stress['cvar99']],marker_color=['#E4B45B','#D45B5B','#8D3C4B']));st.plotly_chart(layout(fig,'Tail-loss ladder',330),use_container_width=True)
    with b:
        fig=go.Figure(go.Waterfall(x=SECTORS,y=stress['sector_losses'],measure=['relative']*6,connector={'line':{'color':'#50657A'}}));st.plotly_chart(layout(fig,'Median sector contribution to economic change',330),use_container_width=True)
    note_box('Credit shock',f"At {shock}% shock intensity, what drives the change in VaR/CVaR?",'shock');nav('run')

elif p=='run':
    st.subheader('Run lab: cash, stale marks, and forced sales')
    c1,c2,c3=st.columns(3)
    run=c1.slider('Redemption requests (% NAV)',0.,25.,st.session_state.run_pct,.5,key='run2');st.session_state.run_pct=run
    gate=c2.slider('Quarterly gate (% NAV)',1.,10.,st.session_state.gate_pct,.5);st.session_state.gate_pct=gate
    stale=c3.slider('Valuation staleness (days)',0,90,st.session_state.stale_days,5,key='stale2');st.session_state.stale_days=stale
    r=simulate_fund(1250,st.session_state.shock,stale,run,gate);metric_row(r)
    lft,rgt=st.columns([1.5,1])
    with lft:
        wf=liquidity_waterfall(r);fig=go.Figure(go.Waterfall(x=wf.Step,y=wf.Amount,measure=wf.Measure,connector={'line':{'color':'#60768A'}},increasing={'marker':{'color':'#18A7A0'}},decreasing={'marker':{'color':'#D45B5B'}},totals={'marker':{'color':'#E4B45B'}}));st.plotly_chart(layout(fig,'Liquidity waterfall ($m)',430),use_container_width=True)
    with rgt:
        fig=go.Figure(go.Indicator(mode='gauge+number',value=r['coverage'],number={'suffix':'×'},title={'text':'Economic asset / liability coverage'},gauge={'axis':{'range':[0,8]},'bar':{'color':'#D45B5B' if r['coverage']<2 else '#18A7A0'},'threshold':{'line':{'color':'#E4B45B','width':4},'value':2}}));st.plotly_chart(layout(fig,'Solvency buffer after run',430),use_container_width=True)
    st.markdown(f"<div class='callout'><b>Run mechanics</b><br>Requested: ${r['redemption_request']:.1f}m · Payable under gate: ${r['payable']:.1f}m · Forced-sale need: ${r['sale_need']:.1f}m · Forced-sale loss: ${r['forced_sale_loss']:.1f}m</div>",unsafe_allow_html=True)
    note_box('Run lab','Does the fund have a credit problem, a liquidity problem, or a valuation-governance problem?','run');nav('response')

elif p=='response':
    st.subheader('Response room: cope with stale valuations and a run')
    actions=st.multiselect('Select the response package',['Independent revaluation','Tighten redemption gate','Draw liquidity line early','Sell public liquid sleeve','Suspend new originations'])
    before=simulate_fund(1250,st.session_state.shock,st.session_state.stale_days,st.session_state.run_pct,st.session_state.gate_pct)
    after=mitigation_effects(1250,st.session_state.shock,st.session_state.stale_days,st.session_state.run_pct,st.session_state.gate_pct,actions)
    df=pd.DataFrame({'Metric':['95% CVaR','Economic NAV','Stale-NAV gap','Ending cash','Coverage ratio'],'Before':[before['cvar95'],before['economic_nav'],before['stale_gap'],before['ending_cash'],before['coverage']],'After':[after['cvar95'],after['economic_nav'],after['stale_gap'],after['ending_cash'],after['coverage']]})
    fig=go.Figure();fig.add_trace(go.Bar(x=df.Metric,y=df.Before,name='Before',marker_color='#D45B5B'));fig.add_trace(go.Bar(x=df.Metric,y=df.After,name='After',marker_color='#18A7A0'));fig.update_layout(barmode='group');st.plotly_chart(layout(fig,'Response package: before versus after'),use_container_width=True)
    st.caption('Metrics have different units; use hover values and the detailed cards below rather than comparing bar heights across metrics.')
    cols=st.columns(4);cols[0].metric('CVaR improvement',f"${before['cvar95']-after['cvar95']:.1f}m");cols[1].metric('NAV gap reduction',f"${before['stale_gap']-after['stale_gap']:.1f}m");cols[2].metric('Ending cash',f"${after['ending_cash']:.1f}m");cols[3].metric('Coverage',f"{after['coverage']:.2f}×")
    response_note=st.text_area('Why is this response package preferable to the alternatives?')
    final=st.radio('Final amendment decision',case['decision_choices'],horizontal=True)
    if st.button('Lock response and final decision',type='primary',disabled=not(actions and response_note.strip())):
        st.session_state.final_decision=final;st.session_state.actions=actions;add_note('Fund response',f"Actions: {', '.join(actions)}. Final decision: {final}. {response_note}",'decision');st.success('Response added to the committee record.')
    nav('defense',st.session_state.final_decision is None)

elif p=='defense':
    st.subheader('Board defense and committee record')
    stress=simulate_fund(1250,st.session_state.shock,st.session_state.stale_days,st.session_state.run_pct,st.session_state.gate_pct)
    c=st.columns(5);c[0].metric('Initial',st.session_state.initial_decision or '—');c[1].metric('Final',st.session_state.final_decision or '—');c[2].metric('95% CVaR',f"${stress['cvar95']:.0f}m");c[3].metric('Stale-NAV gap',f"${stress['stale_gap']:.0f}m");c[4].metric('Ending cash',f"${stress['ending_cash']:.0f}m")
    statement=st.text_area('Final investment-committee statement',height=180,placeholder='Decision; data; VaR/CVaR; liquidity; valuation governance; response actions; reversal condition.')
    record={'case':case['title'],'initial_decision':st.session_state.initial_decision,'final_decision':st.session_state.final_decision,'shock_intensity':st.session_state.shock,'valuation_staleness_days':st.session_state.stale_days,'redemption_requests_pct_nav':st.session_state.run_pct,'gate_pct_nav':st.session_state.gate_pct,'metrics':{k:round(float(stress[k]),3) for k in ['var95','cvar95','var99','cvar99','economic_nav','stale_gap','ending_cash','coverage']},'actions':st.session_state.get('actions',[]),'journal':st.session_state.journal,'final_statement':statement}
    st.download_button('Download complete committee record',json.dumps(record,indent=2),file_name='northstar_committee_record.json',mime='application/json',type='primary',disabled=not statement.strip())
    st.markdown('### Decision journal')
    for n in st.session_state.journal: st.markdown(f"<div class='panel'><b>{n['stage']} · {n['time']}</b><br>{n['text']}</div><br>",unsafe_allow_html=True)
