import plotly.graph_objects as go
import streamlit as st


def risk_metrics(results: dict) -> None:
    first, second, third = st.columns(3)
    first.metric("Volatility", f"{results['volatility']:.1f}%")
    second.metric("Illustrative VaR", f"{results['var']:.2f}%")
    third.metric("Illustrative ES", f"{results['expected_shortfall']:.2f}%")

    color = "#D45B5B" if results["breach"] else "#18A7A0"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=results["limit_usage"],
        number={"suffix": "%"},
        title={"text": "Risk-limit utilization"},
        gauge={
            "axis": {"range": [0, 150]},
            "bar": {"color": color},
            "threshold": {"line": {"color": "#E4B45B", "width": 4}, "value": 100},
        },
    ))
    fig.update_layout(height=290, margin=dict(l=30, r=30, t=60, b=20))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("The starter model is illustrative. Replace it with the validated course model and case assumptions.")
