from __future__ import annotations
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from data_portfolio import portfolio_data
from risk_engine import apply_scenario, metrics, cash_run

st.set_page_config(page_title='Northstar Portfolio Risk Lab',page_icon='◈',layout='wide',initial_sidebar_state='collapsed')
BASE=portfolio_data(); STEPS=['book','signals','shock','liquidity','committee']; LABELS=['The Book','Risk Signals','Stress Test','Liquidity','Committee']
for k,v in {'step':'book','scenario':'Software disruption','redemptions':10.0,'gate':5.0,'notes':{},'decision':'Protect liquidity and re-underwrite'}.items(): st.session_state.setdefault(k,v)
st.markdown('''<style>.block-container{max-width:1440px;padding-top:1rem}.eyebrow{color:#168c86;font-size:.78rem;font-weight:800;letter-spacing:.13em}.story{font-size:1.18rem;line-height:1.55;max-width:1050px}[data-testid="stMetricValue"]{font-size:1.65rem}</style>''',unsafe_allow_html=True)

def style(fig,title,h=400):
    fig.update_layout(title=title,height=h,margin=dict(l=35,r=20,t=60,b=40),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',legend=dict(orientation='h',y=1.08),hovermode='closest');fig.update_yaxes(gridcolor='rgba(128,128,128,.15)');return fig
def goto(x):st.session_state.step=x;st.rerun()
def prog():
    i=STEPS.index(st.session_state.step);st.progress((i+1)/5);cs=st.columns(5)
    for j,(c,l) in enumerate(zip(cs,LABELS)):c.markdown(f'**{l}**' if i==j else l)
def nav(n=None):
    a,b=st.columns([4,1]);i=STEPS.index(st.session_state.step)
    if i and a.button('← Back'):goto(STEPS[i-1])
    if n and b.button('Continue →',type='primary',use_container_width=True):goto(n)
def note(key,prompt):
    with st.form('f_'+key):
        t=st.text_area(prompt,value=st.session_state.notes.get(key,''),height=85)
        if st.form_submit_button('Save learning note'):st.session_state.notes[key]=t.strip();st.success('Saved.')
def loss_plot(a,b):
    fig=go.Figure()
    for m,n,c in [(a,'Base','#18A7A0'),(b,'Stress','#D45B5B')]:
        h,e=np.histogram(m['losses'],bins=75,density=True);x=(e[:-1]+e[1:])/2;fig.add_trace(go.Scatter(x=x,y=h,name=n,line=dict(color=c,width=3),fill='tozeroy',opacity=.4))
    fig.add_vline(x=b['var'],line_color='#E4B45B',line_width=3,annotation_text='VaR');fig.add_vline(x=b['cvar'],line_color='#D45B5B',line_width=3,annotation_text='CVaR');fig.update_xaxes(title='Portfolio loss ($m)');return style(fig,'Portfolio loss distribution: base versus stress',440)

st.markdown('<div class="eyebrow">NORTHSTAR PRIVATE DEBT OPPORTUNITIES FUND · RISK MANAGER EXPERIENCE</div>',unsafe_allow_html=True)
st.title('Eight Loans. Five Risks. One Investment Committee.')
st.caption('Fictional manager, borrowers, and data. Calculations are transparent teaching models for a risk-management course.')
prog();st.divider();step=st.session_state.step

if step=='book':
    st.subheader('Morning: inherit the book')
    st.markdown('<div class="story">You manage an $800 million pool of private loans inside a $1.25 billion fund. Every borrower is current. The book looks diversified, but the loans carry different combinations of default, recovery, duration, concentration, valuation, and liquidity risk.</div>',unsafe_allow_html=True)
    m=metrics(BASE);c=st.columns(6);vals=[('Exposure','$800m'),('Expected loss',f"${m['expected_loss']:.1f}m"),('Weighted PD',f"{m['weighted_pd']:.1%}"),('Weighted LGD',f"{m['weighted_lgd']:.1%}"),('Duration',f"{m['duration']:.1f}"),('HHI',f"{m['hhi']:.3f}")]
    for x,(a,b) in zip(c,vals):x.metric(a,b)
    fig=go.Figure(go.Scatter(x=BASE.pd*100,y=BASE.lgd*100,mode='markers+text',text=BASE.asset,textposition='top center',marker=dict(size=BASE.exposure/3,color=BASE.days_to_liquidate,colorscale='Tealgrn',showscale=True,colorbar=dict(title='Days to liquidate'))));fig.update_xaxes(title='Probability of default (%)');fig.update_yaxes(title='Loss given default (%)');st.plotly_chart(style(fig,'The book: credit risk, recovery risk, position size, and liquidity'),use_container_width=True)
    with st.expander('Learning calculations'):
        st.markdown('**Expected loss:** $EL_i=EAD_i\\times PD_i\\times LGD_i$  \\n**Portfolio expected loss:** $EL_P=\\sum_i EL_i$  \\n**Concentration:** $HHI=\\sum_i w_i^2$  \\n**Weighted duration:** $D_P=\\sum_i w_iD_i$')
    note('book','Which two loans deserve immediate attention, and which risk measure supports that conclusion?');nav('signals')

elif step=='signals':
    st.subheader('Late morning: risk does not arrive in one form')
    m=metrics(BASE);d=m['detail'].copy();d['EL % exposure']=100*d.expected_loss/d.exposure
    choice=st.selectbox('Choose the risk lens',['Expected loss','Concentration','Interest coverage','Valuation gap','Liquidity haircut'])
    if choice=='Expected loss':y=d.expected_loss;title='Expected loss by borrower ($m)'
    elif choice=='Concentration':y=100*d.exposure/d.exposure.sum();title='Portfolio weight by borrower (%)'
    elif choice=='Interest coverage':y=d.coverage;title='Interest coverage by borrower (×)'
    elif choice=='Valuation gap':y=d.valuation_gap;title='Par less economic value ($m)'
    else:y=100*d.liq_haircut;title='Estimated liquidation haircut (%)'
    colors=['#D45B5B' if (choice=='Interest coverage' and v<1.5) else '#18A7A0' for v in y]
    fig=go.Figure(go.Bar(x=d.asset,y=y,marker_color=colors,text=np.round(y,2),textposition='outside'));st.plotly_chart(style(fig,title),use_container_width=True)
    a,b=st.columns(2)
    with a:st.info('**Learning opportunity:** expected loss is not the same as unexpected tail loss. A loan can have modest EL and still dominate CVaR because of size, correlation, or recovery uncertainty.')
    with b:st.warning('**Learning opportunity:** liquidity and valuation are separate from borrower default. A current loan can still create a cash problem if investors redeem and the loan cannot be sold near its mark.')
    note('signals','How does the ranking change when you switch risk lenses?');nav('shock')

elif step=='shock':
    st.subheader('Afternoon: the book is hit by a scenario')
    scenario=st.selectbox('Choose the event',['Software disruption','Higher for longer','Consumer slowdown','Liquidity run','Combined stress'],index=['Software disruption','Higher for longer','Consumer slowdown','Liquidity run','Combined stress'].index(st.session_state.scenario));st.session_state.scenario=scenario
    stressed=apply_scenario(BASE,scenario);base_m=metrics(BASE);stress_m=metrics(stressed)
    c=st.columns(6);pairs=[('Expected loss',base_m['expected_loss'],stress_m['expected_loss'],'$'),('95% VaR',base_m['var'],stress_m['var'],'$'),('95% CVaR',base_m['cvar'],stress_m['cvar'],'$'),('Economic value',base_m['economic_value'],stress_m['economic_value'],'$'),('Valuation gap',base_m['valuation_gap'],stress_m['valuation_gap'],'$'),('Weighted PD',base_m['weighted_pd']*100,stress_m['weighted_pd']*100,'%')]
    for col,(name,b,s,u) in zip(c,pairs):col.metric(name,f"{u}{s:.1f}" if u=='$' else f"{s:.1f}{u}",delta=f"{s-b:+.1f}",delta_color='inverse' if name not in ['Economic value'] else 'normal')
    st.plotly_chart(loss_plot(base_m,stress_m),use_container_width=True)
    left,right=st.columns(2)
    with left:
        q=stress_m['detail'].sort_values('expected_loss',ascending=True);fig=go.Figure(go.Bar(y=q.asset,x=q.expected_loss,orientation='h',marker_color='#D45B5B'));st.plotly_chart(style(fig,'Stressed expected loss contribution',330),use_container_width=True)
    with right:
        q=stress_m['detail'];fig=go.Figure(go.Scatter(x=q.days_to_liquidate,y=q.valuation_gap,mode='markers+text',text=q.asset,textposition='top center',marker=dict(size=q.exposure/4,color=q.pd,colorscale='Reds')));fig.update_xaxes(title='Days to liquidate');fig.update_yaxes(title='Valuation gap ($m)');st.plotly_chart(style(fig,'Where valuation and liquidity risk meet',330),use_container_width=True)
    with st.expander('Learning calculations'):
        st.markdown('**VaR:** percentile loss threshold at the chosen confidence level.  \\n**CVaR:** average loss conditional on losses exceeding VaR.  \\n**Stress loss:** revalue PD, LGD, marks, correlation, and liquidity under a coherent event rather than shocking one input in isolation.')
    note('shock','Which risk moved most under this scenario, and why?');nav('liquidity')

elif step=='liquidity':
    st.subheader('Close: investors ask for cash before marks fully adjust')
    stressed=apply_scenario(BASE,st.session_state.scenario);m=metrics(stressed)
    a,b=st.columns(2);run=a.slider('Redemption requests (% NAV)',0.,25.,10.,.5);gate=b.slider('Payable this period (% NAV)',1.,10.,5.,.5);r=cash_run(m,run,gate_pct=gate)
    c=st.columns(6);items=[('Requested',r['requested']),('Payable now',r['payable']),('Liquidity sources',r['sources']),('Asset sales needed',r['sale_need']),('Forced-sale loss',r['forced_loss']),('Ending cash',r['ending_cash'])]
    for col,(n,v) in zip(c,items):col.metric(n,f"${v:.1f}m")
    fig=go.Figure(go.Waterfall(x=['Cash','Credit line','Income','Redemptions','Forced-sale loss','Ending cash'],y=[75,62.5,11.25,-r['payable'],-r['forced_loss'],r['ending_cash']],measure=['relative','relative','relative','relative','relative','total'],increasing={'marker':{'color':'#18A7A0'}},decreasing={'marker':{'color':'#D45B5B'}},totals={'marker':{'color':'#E4B45B'}}));fig.update_yaxes(title='$ millions');st.plotly_chart(style(fig,'Liquidity waterfall: meeting the run',440),use_container_width=True)
    st.warning(f"The stressed book is marked at ${m['economic_value']:.1f}m but may realize only ${m['liquidity_value']:.1f}m under the modeled liquidation haircuts. The difference is ${m['economic_value']-m['liquidity_value']:.1f}m.")
    with st.expander('Learning calculations'):
        st.markdown('**Liquidity-adjusted value:** $V_i^{liq}=V_i(1-h_i)$  \\n**Cash shortfall:** $\\max(0,Redemptions-Cash-Line-Income)$  \\n**Forced-sale loss:** $SaleNeed\\times PortfolioHaircut$')
    note('liquidity','Is this primarily a credit, valuation, liquidity, or governance problem? Defend the classification.');nav('committee')

elif step=='committee':
    st.subheader('Investment committee: manage the portfolio, not one loan')
    scenario=st.session_state.scenario;stressed=apply_scenario(BASE,scenario);m=metrics(stressed)
    action=st.multiselect('Select up to four actions',['Reduce Meridian Cloud','Add cash buffer','Draw credit line early','Independent valuation','Tighten redemption gate','Hedge duration','Suspend new originations','Transfer weak credits to special situations'],max_selections=4)
    decision=st.radio('Portfolio stance',['Maintain risk','Selective de-risking','Broad de-risking','Defensive liquidity posture'],horizontal=True);st.session_state.decision=decision
    st.markdown('### Required committee memo')
    st.write('State the portfolio stance, name the two largest risks, cite three calculations, specify actions, and give a numerical reversal condition.')
    note('committee','Write the recommendation in complete paragraphs using the course calculations as evidence.')
    record=pd.DataFrame([{'Learning stage':k.replace('_',' ').title(),'Reasoning':v} for k,v in st.session_state.notes.items() if v])
    if not record.empty:st.dataframe(record,use_container_width=True,hide_index=True)
    output={'scenario':scenario,'portfolio_stance':decision,'actions':action,'metrics':{'expected_loss':round(m['expected_loss'],2),'var95':round(m['var'],2),'cvar95':round(m['cvar'],2),'weighted_pd':round(m['weighted_pd'],4),'weighted_lgd':round(m['weighted_lgd'],4),'hhi':round(m['hhi'],4),'economic_value':round(m['economic_value'],2),'liquidity_value':round(m['liquidity_value'],2)},'learning_notes':st.session_state.notes}
    st.download_button('Download investment committee record',json.dumps(output,indent=2),file_name='northstar_portfolio_committee_record.json',mime='application/json',type='primary')
