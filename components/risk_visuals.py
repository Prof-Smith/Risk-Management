from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

NAVY = "#071A2B"
TEAL = "#18A7A0"
CYAN = "#55D6CF"
GOLD = "#E4B45B"
RED = "#D45B5B"
MUTED = "#9FB0BE"


def _layout(fig: go.Figure, title: str, height: int = 390) -> go.Figure:
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=30, r=25, t=60, b=35),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F7F8FA"),
        hoverlabel=dict(bgcolor=NAVY),
        legend=dict(orientation="h", y=1.08, x=1, xanchor="right"),
    )
    fig.update_xaxes(gridcolor="rgba(159,176,190,.12)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(159,176,190,.12)", zeroline=False)
    return fig


def _metric_strip(risk: str, shock: float, status: str) -> None:
    a, b, c, d = st.columns(4)
    a.metric("Risk channel", risk)
    b.metric("Shock intensity", f"{shock:.0f}%")
    c.metric("Control status", status)
    d.metric("Decision state", "REVIEW" if shock >= 55 else "MONITOR")


def _market(shock: float) -> None:
    rng = np.random.default_rng(21)
    n = 120
    base = rng.normal(0.0004, 0.008, n)
    stressed = base.copy()
    stressed[72:] *= 1 + 2.5 * shock / 100
    prices = 100 * np.exp(np.cumsum(stressed))
    rolling = pd.Series(stressed).rolling(20).std() * np.sqrt(252) * 100
    left, right = st.columns([1.7, 1])
    with left:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=np.arange(n), y=prices, mode="lines", name="Portfolio", line=dict(color=CYAN, width=3)))
        fig.add_vrect(x0=72, x1=119, fillcolor=RED, opacity=.08, line_width=0, annotation_text="Stress window")
        st.plotly_chart(_layout(fig, "Market path under the selected shock"), use_container_width=True)
    with right:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=float(rolling.iloc[-1]), number={"suffix": "%"},
            gauge={"axis": {"range": [0, 80]}, "bar": {"color": RED if shock >= 55 else TEAL},
                   "steps": [{"range": [0, 25], "color": "rgba(24,167,160,.15)"}, {"range": [25, 50], "color": "rgba(228,180,91,.15)"}, {"range": [50, 80], "color": "rgba(212,91,91,.15)"}],
                   "threshold": {"line": {"color": GOLD, "width": 4}, "value": 40}}))
        st.plotly_chart(_layout(fig, "Annualized volatility", 390), use_container_width=True)


def _credit(shock: float) -> None:
    ratings = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "Default"]
    base = np.array([5, 11, 22, 28, 18, 9, 5, 2], dtype=float)
    migration = shock / 100 * np.array([-4, -7, -9, -7, 7, 8, 7, 5])
    stressed = np.clip(base + migration, 0, None)
    stressed = stressed / stressed.sum() * 100
    fig = go.Figure()
    fig.add_trace(go.Bar(x=ratings, y=base, name="Baseline", marker_color=MUTED))
    fig.add_trace(go.Bar(x=ratings, y=stressed, name="Stressed", marker_color=RED))
    fig.update_layout(barmode="group")
    st.plotly_chart(_layout(fig, "Illustrative rating distribution after migration shock"), use_container_width=True)


def _liquidity(shock: float) -> None:
    quantity = np.linspace(0, 100, 30)
    depth = 100 - quantity * (0.42 + 0.75 * shock / 100)
    cost = 4 + quantity * (0.08 + 0.20 * shock / 100)
    left, right = st.columns(2)
    with left:
        fig = go.Figure(go.Scatter(x=quantity, y=depth, fill="tozeroy", line=dict(color=CYAN, width=3)))
        st.plotly_chart(_layout(fig, "Available market depth", 360), use_container_width=True)
    with right:
        fig = go.Figure(go.Scatter(x=quantity, y=cost, line=dict(color=GOLD, width=3)))
        st.plotly_chart(_layout(fig, "Estimated liquidation cost", 360), use_container_width=True)


def _operational(shock: float) -> None:
    categories = ["Process", "Systems", "People", "External", "Controls"]
    frequency = np.array([18, 12, 15, 8, 10]) * (1 + shock / 150)
    severity = np.array([25, 45, 30, 65, 40]) * (1 + shock / 100)
    size = frequency * severity / 20
    fig = go.Figure(go.Scatter(x=frequency, y=severity, mode="markers+text", text=categories, textposition="top center",
        marker=dict(size=size, color=[TEAL, CYAN, GOLD, RED, MUTED], opacity=.82, line=dict(color="white", width=1))))
    fig.update_xaxes(title="Expected event frequency")
    fig.update_yaxes(title="Relative loss severity")
    st.plotly_chart(_layout(fig, "Operational risk map: frequency × severity"), use_container_width=True)


def _model(shock: float) -> None:
    x = np.linspace(0.05, 0.60, 40)
    normal = 1.65 * x * 100
    tail = normal * (1.05 + 0.65 * shock / 100) + 4 * x**2 * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=normal, name="Normal assumption", line=dict(color=TEAL, width=3)))
    fig.add_trace(go.Scatter(x=x, y=tail, name="Heavy-tail assumption", line=dict(color=RED, width=3)))
    fig.add_trace(go.Scatter(x=x, y=tail-normal, name="Model uncertainty gap", fill="tozeroy", line=dict(color=GOLD)))
    fig.update_xaxes(title="Volatility assumption")
    fig.update_yaxes(title="Estimated loss metric")
    st.plotly_chart(_layout(fig, "Model risk: two defensible assumptions, different decisions"), use_container_width=True)


def _systemic(shock: float) -> None:
    theta = np.linspace(0, 2*np.pi, 9)[:-1]
    x, y = np.cos(theta), np.sin(theta)
    edges_x, edges_y = [], []
    for i in range(8):
        for j in range(i+1, 8):
            if (i+j) % 3 == 0 or abs(i-j) == 1:
                edges_x += [x[i], x[j], None]
                edges_y += [y[i], y[j], None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=edges_x, y=edges_y, mode="lines", line=dict(color="rgba(85,214,207,.28)", width=1+shock/40), hoverinfo="skip"))
    node_color = [RED if i < max(1, int(shock/20)) else TEAL for i in range(8)]
    fig.add_trace(go.Scatter(x=x, y=y, mode="markers+text", text=[f"I{i+1}" for i in range(8)], textposition="middle center",
        marker=dict(size=42, color=node_color, line=dict(color="white", width=1)), hovertemplate="Institution %{text}<extra></extra>"))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False, scaleanchor="x")
    st.plotly_chart(_layout(fig, "Systemic network: stressed nodes and transmission links"), use_container_width=True)


def render_risk_lab(risk: str) -> None:
    control, display = st.columns([1, 4])
    with control:
        st.subheader("Shock console")
        shock = st.slider("Intensity", 0, 100, 35, 5, key=f"shock_{risk}")
        horizon = st.select_slider("Horizon", options=["1 day", "10 days", "1 month", "1 quarter"], value="10 days", key=f"horizon_{risk}")
        st.toggle("Show stressed state", value=True, key=f"stress_{risk}")
        st.caption(f"Selected horizon: {horizon}")
        st.markdown("**Lab question**")
        questions = {
            "Market": "At what volatility does the position breach the limit?",
            "Credit": "Which migration changes the transaction decision?",
            "Liquidity": "How quickly does exit cost erase the expected return?",
            "Operational": "Which control failure dominates loss exposure?",
            "Model": "When does the choice of model reverse the recommendation?",
            "Systemic": "Which node turns a local failure into a network event?",
        }
        st.write(questions[risk])
    effective_shock = shock if st.session_state.get(f"stress_{risk}", True) else 0
    with display:
        _metric_strip(risk, effective_shock, "BREACH" if effective_shock >= 70 else "ACTIVE")
        {
            "Market": _market,
            "Credit": _credit,
            "Liquidity": _liquidity,
            "Operational": _operational,
            "Model": _model,
            "Systemic": _systemic,
        }[risk](effective_shock)
