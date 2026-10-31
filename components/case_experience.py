from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.reversal_engine import find_reversal
from services.simulation_engine import run_case

TEAL = "#18A7A0"
CYAN = "#55D6CF"
GOLD = "#E4B45B"
RED = "#D45B5B"
MUTED = "#9FB0BE"


def _plot_layout(fig: go.Figure, title: str, height: int = 360) -> go.Figure:
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=25, r=25, t=55, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F7F8FA"),
        legend=dict(orientation="h", y=1.08),
    )
    fig.update_xaxes(gridcolor="rgba(159,176,190,.12)")
    fig.update_yaxes(gridcolor="rgba(159,176,190,.12)")
    return fig


def render_briefing(case: dict) -> bool:
    left, right = st.columns([1.45, 1])
    with left:
        st.subheader("Committee briefing")
        st.markdown(f"### {case['narrative']}")
        st.write(
            "The committee meets in 20 minutes. You must interpret the available information, "
            "commit to an action, and defend the recommendation after conditions change."
        )
        st.warning("You will not receive perfect information. The lab is testing judgment under uncertainty.")
    with right:
        with st.container(border=True):
            st.caption("YOUR MANDATE")
            st.metric("Risk limit", f"{case['baseline']['risk_limit']:.1f}%")
            st.metric("Decision horizon", f"{case['baseline']['horizon_days']} trading days")
            st.metric("Confidence level", f"{case['baseline']['confidence']:.0%}")
            st.markdown("**Required output**")
            st.write("Choose an action, state the decisive evidence, and identify the reversal condition.")
    st.checkbox("I understand the mandate and accept responsibility for the decision.", key="mandate_ack")
    return bool(st.session_state.get("mandate_ack"))


def render_evidence_room(case: dict) -> bool:
    st.subheader("Evidence room")
    st.write("Inspect the evidence before committing. Hover over charts and record the signal you consider most decision-relevant.")
    tabs = st.tabs(["Market tape", "Loss distribution", "Correlation", "Model audit"])
    rng = np.random.default_rng(12)
    shock_hint = float(case["baseline"]["volatility"]) / 100

    with tabs[0]:
        returns = rng.normal(0.0005, shock_hint / np.sqrt(252), 180)
        prices = 100 * np.exp(np.cumsum(returns))
        fig = go.Figure(go.Scatter(y=prices, mode="lines", line=dict(color=CYAN, width=3), name="Portfolio"))
        fig.add_hline(y=prices[-1] * .92, line_dash="dash", line_color=GOLD, annotation_text="Review threshold")
        st.plotly_chart(_plot_layout(fig, "Synthetic portfolio path"), use_container_width=True)
    with tabs[1]:
        losses = -rng.standard_t(df=5, size=3500) * shock_hint * 100 / np.sqrt(10)
        fig = go.Figure(go.Histogram(x=losses, nbinsx=55, marker_color=TEAL, opacity=.8))
        fig.add_vline(x=np.quantile(losses, .95), line_color=RED, line_width=3, annotation_text="Tail threshold")
        st.plotly_chart(_plot_layout(fig, "Illustrative 10-day loss distribution"), use_container_width=True)
    with tabs[2]:
        labels = ["Equity", "Rates", "Credit", "FX", "Commodities"]
        matrix = np.array([[1,.35,.48,.20,.22],[.35,1,.42,.18,.12],[.48,.42,1,.30,.27],[.20,.18,.30,1,.25],[.22,.12,.27,.25,1]])
        fig = go.Figure(go.Heatmap(z=matrix, x=labels, y=labels, colorscale=[[0,"#071A2B"],[.5,TEAL],[1,GOLD]], zmin=0, zmax=1))
        st.plotly_chart(_plot_layout(fig, "Baseline correlation structure"), use_container_width=True)
    with tabs[3]:
        c1, c2, c3 = st.columns(3)
        c1.metric("Observations", "180")
        c2.metric("Tail assumption", "Student-t")
        c3.metric("Known weakness", "Correlation instability")
        st.info("Audit finding: the baseline model may understate joint losses when correlations converge during stress.")

    signal = st.radio(
        "Which signal matters most?",
        ["Volatility", "Tail loss", "Correlation instability", "Model limitation"],
        horizontal=True,
        key="decisive_signal",
    )
    st.text_input("Record one evidence-based observation", key="evidence_note")
    return bool(signal and st.session_state.get("evidence_note", "").strip())


def render_commitment(case: dict) -> bool:
    st.subheader("Decision desk")
    st.write("Commit before seeing the disruption. The application preserves this answer for comparison after the shock.")
    left, right = st.columns([1.3, 1])
    with left:
        decision = st.radio(
            case["decision_prompt"],
            case["decision_choices"],
            horizontal=True,
            key="initial_decision",
        )
        confidence = st.slider("Confidence in the recommendation", 0, 100, 60, key="initial_confidence")
        rationale = st.text_area(
            "Defend the recommendation in two or three sentences",
            key="initial_rationale",
            placeholder="State the action, decisive evidence, and primary limitation.",
        )
    with right:
        with st.container(border=True):
            st.caption("DECISION TICKET")
            st.metric("Action", decision)
            st.metric("Confidence", f"{confidence}%")
            st.write(f"**Decisive signal:** {st.session_state.get('decisive_signal', 'Not recorded')}")
            st.write(f"**Evidence note:** {st.session_state.get('evidence_note', 'Not recorded')}")
    acknowledged = st.checkbox("Lock this recommendation before the shock is revealed.", key="decision_locked")
    return bool(rationale.strip() and acknowledged)


def render_shock_room(case: dict) -> bool:
    st.subheader("Shock room")
    st.error("BREAKING SCENARIO: volatility accelerates, correlations rise, and the exit window narrows.")
    control, visual = st.columns([1, 3])
    with control:
        intensity = st.slider("Shock intensity", 0, 100, 65, 5, key="case_shock_intensity")
        volatility = case["baseline"]["volatility"] * (1 + intensity / 70)
        correlation = max(case["baseline"]["correlation"], .25 + .65 * intensity / 100)
        st.metric("Volatility assumption", f"{volatility:.1f}%")
        st.metric("Correlation assumption", f"{correlation:.2f}")
        st.caption("Move the slider slowly during the presentation and watch for the breach.")

    results = run_case(case, volatility=volatility, correlation=correlation)
    reversal = find_reversal(case, correlation=correlation)
    with visual:
        x = np.linspace(5, 70, 70)
        usage = [run_case(case, float(v), correlation)["limit_usage"] for v in x]
        fig = go.Figure(go.Scatter(x=x, y=usage, mode="lines", line=dict(color=CYAN, width=4), name="Limit use"))
        fig.add_hline(y=100, line_color=RED, line_width=3, annotation_text="Risk limit")
        fig.add_vline(x=reversal, line_color=GOLD, line_dash="dash", annotation_text=f"Reversal {reversal:.1f}%")
        fig.add_trace(go.Scatter(x=[volatility], y=[results["limit_usage"]], mode="markers", marker=dict(size=16, color=RED if results["breach"] else TEAL), name="Current state"))
        st.plotly_chart(_plot_layout(fig, "Decision boundary under stress"), use_container_width=True)
        metrics = st.columns(3)
        metrics[0].metric("Expected shortfall", f"{results['expected_shortfall']:.2f}%")
        metrics[1].metric("Limit utilization", f"{results['limit_usage']:.0f}%")
        metrics[2].metric("Status", "BREACH" if results["breach"] else "WITHIN LIMIT")

    st.session_state.shock_results = results
    st.session_state.reversal_value = reversal
    decision = st.radio("Your revised action", case["decision_choices"], horizontal=True, key="final_decision")
    confidence = st.slider("Revised confidence", 0, 100, 70, key="final_confidence")
    reason = st.text_area("What changed, and why?", key="revision_reason")
    return bool(decision and confidence >= 0 and reason.strip())


def render_debrief(case: dict) -> None:
    st.subheader("Board defense")
    initial = st.session_state.get("initial_decision", "Not recorded")
    final = st.session_state.get("final_decision", "Not recorded")
    initial_conf = st.session_state.get("initial_confidence", 0)
    final_conf = st.session_state.get("final_confidence", 0)
    reversal = st.session_state.get("reversal_value", 0)

    a, b, c = st.columns(3)
    a.metric("Initial action", initial, delta=f"{initial_conf}% confidence")
    b.metric("Revised action", final, delta=f"{final_conf}% confidence")
    c.metric("Reversal threshold", f"{reversal:.1f}% volatility")

    if initial != final:
        st.success("The recommendation changed after the shock. The task now is to defend why the change is disciplined rather than reactive.")
    else:
        st.info("The recommendation remained unchanged. The task now is to show that the position survived a meaningful falsification attempt.")

    prompt = (
        f"Defend the final recommendation to the committee. Explain why **{final}** is justified, "
        f"identify the controlling evidence, acknowledge the model limitation, and state what would reverse the recommendation."
    )
    st.markdown(prompt)
    st.text_area("Committee statement", key="defense_text", height=150)
    with st.expander("Reveal the learning architecture"):
        st.markdown(
            "**Concept → evidence → commitment → shock → reversal → defense**\n\n"
            "The case is experienced because the participant must act before all information is available, "
            "observe the consequences of altered assumptions, and defend a final judgment."
        )
