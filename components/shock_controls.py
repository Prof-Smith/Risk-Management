import streamlit as st


def shock_controls(case: dict) -> tuple[float, float]:
    st.subheader("Model and shock controls")
    left, right = st.columns(2)
    with left:
        volatility = st.slider(
            "Annualized volatility",
            5.0,
            60.0,
            float(case["baseline"]["volatility"]),
            1.0,
        )
    with right:
        correlation = st.slider(
            "Average correlation",
            0.0,
            0.95,
            float(case["baseline"]["correlation"]),
            0.05,
        )
    st.toggle("Activate stress scenario", key="shock_active")
    if st.session_state.shock_active:
        volatility *= case["shock"]["volatility_multiplier"]
        correlation = max(correlation, case["shock"]["correlation_floor"])
    return min(volatility, 100.0), min(correlation, 0.99)
