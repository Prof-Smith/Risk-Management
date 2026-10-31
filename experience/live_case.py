import streamlit as st
from components.decision_panel import decision_panel
from components.risk_metrics import risk_metrics
from components.shock_controls import shock_controls
from services.reversal_engine import find_reversal
from services.simulation_engine import run_case
from services.session_manager import move_to


def render(case: dict) -> None:
    st.caption("02 / FLAGSHIP CASE")
    st.title(case["title"])
    st.write(case["narrative"])

    decision_panel(case)
    volatility, correlation = shock_controls(case)
    results = run_case(case, volatility=volatility, correlation=correlation)
    risk_metrics(results)

    if st.session_state.get("shock_active"):
        reversal = find_reversal(case, correlation=correlation)
        st.warning(
            f"Decision boundary: the risk limit is first breached at approximately "
            f"{reversal:.1f}% annualized volatility under the current assumptions."
        )
        st.text_area(
            "What changed your decision?",
            key="reversal_explanation",
            placeholder="Identify the assumption, consequence, and reversal condition.",
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Open the case gallery", use_container_width=True):
            move_to("case_gallery")
            st.rerun()
    with col2:
        if st.button("Enter faculty design mode", type="primary", use_container_width=True):
            move_to("faculty_mode")
            st.rerun()
