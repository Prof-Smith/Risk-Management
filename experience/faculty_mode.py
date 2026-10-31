import streamlit as st
from services.session_manager import move_to


def render() -> None:
    st.caption("04 / FACULTY DESIGN MODE")
    st.title("Turn a finance topic into a decision experience")
    with st.form("blueprint"):
        topic = st.text_input("Finance topic", "Portfolio risk")
        decision = st.text_input("Professional decision", "Retain, hedge, reduce, or reject?")
        assumption = st.text_input("Adjustable assumption", "Annualized volatility")
        shock = st.text_input("Disruptive shock", "Volatility doubles and correlations rise")
        consequence = st.text_input("Visible consequence", "Expected shortfall breaches the risk limit")
        reversal = st.text_input("Reversal condition", "The first volatility level that breaches the limit")
        deliverable = st.text_input("Student deliverable", "Two-page risk recommendation memo")
        submitted = st.form_submit_button("Build the blueprint", type="primary")
    if submitted:
        st.success("Case blueprint created")
        st.markdown(f"""
### {topic}: decision experience
**Decision:** {decision}  
**Assumption:** {assumption}  
**Shock:** {shock}  
**Consequence:** {consequence}  
**Reversal condition:** {reversal}  
**Student deliverable:** {deliverable}
""")
    if st.button("Close the experience"):
        move_to("closing")
        st.rerun()
