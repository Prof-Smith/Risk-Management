"""Drop-in Streamlit component for calculation transparency and reconciliation."""
import pandas as pd
import streamlit as st
from risk_engine import regime_statistics, run_audits

def render_rebuild_model(holdings, loss_data, confidence, workbook_bytes=None):
    st.subheader('Rebuild the model')
    st.write('Reproduce the calculation in Excel or Python, then reconcile your results with the app.')
    with st.expander('How these estimates are calculated', expanded=False):
        st.markdown('''
1. **Weight each pool:** exposure divided by total portfolio exposure of $5.2 billion.
2. **Calculate portfolio return:** sum the six pool returns multiplied by their weights.
3. **Convert return to loss:** `-$5,200 million × portfolio return`.
4. **Calculate VaR:** selected percentile of the daily dollar-loss series.
5. **Calculate CVaR:** average losses equal to or greater than VaR.
''')
    initial = regime_statistics(loss_data, 'Initial', confidence)
    updated = regime_statistics(loss_data, 'Updated', confidence)
    summary = pd.DataFrame([
        ['Initial', initial['observations'], initial['volatility_mm'], initial['var_mm'], initial['cvar_mm'], initial['tail_count']],
        ['Updated', updated['observations'], updated['volatility_mm'], updated['var_mm'], updated['cvar_mm'], updated['tail_count']],
    ], columns=['Regime','Observations','One-day loss volatility ($mm)','VaR ($mm)','CVaR ($mm)','Tail observations'])
    st.dataframe(summary.style.format({'One-day loss volatility ($mm)':'${:,.1f}', 'VaR ($mm)':'${:,.1f}', 'CVaR ($mm)':'${:,.1f}'}), hide_index=True, use_container_width=True)
    if confidence == 0.99:
        st.warning('With 250 observations, 99% CVaR is driven by only a few extreme losses. Treat it as informative but statistically fragile.')
    with st.expander('Model audit checks'):
        for label, passed in run_audits(holdings, loss_data).items():
            st.success(label) if passed else st.error(label)
    if workbook_bytes is not None:
        st.download_button('Download student calculation workbook', workbook_bytes,
                           file_name='student_risk_model.xlsx',
                           mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
