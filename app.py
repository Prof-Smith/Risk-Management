from __future__ import annotations

import json
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.case_engine import load_case
from services.fund_engine import simulate_fund, liquidity_waterfall, mitigation_effects, SECTORS

st.set_page_config(page_title="Northstar Private Debt Lab", page_icon="◈", layout="wide", initial_sidebar_state="collapsed")
case, scenarios, evidence = load_case()

ACTS = ["calm", "crack", "run", "decision"]
ACT_LABELS = ["1. Apparent calm", "2. Hidden crack", "3. The run", "4. Committee decision"]
DEFAULTS = {
    "act": "calm",
    "notes": {},
    "initial_decision": None,
    "final_decision": None,
    "shock": 55,
    "stale_days": 45,
    "run_pct": 10.0,
    "gate_pct": 5.0,
    "actions": [],
}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value.copy() if isinstance(value, (dict, list)) else value)

st.markdown("""
<style>
.block-container {max-width: 1380px; padding-top: 1.2rem; padding-bottom: 3rem;}
[data-testid="stMetricValue"] {font-size: 1.7rem;}
[data-testid="stMetricLabel"] {font-size: .82rem;}
.story-line {font-size: 1.25rem; line-height: 1.55; max-width: 950px;}
.eyebrow {color: #168C86; font-size: .78rem; font-weight: 800; letter-spacing: .12em;}
.small-note {font-size: .85rem; opacity: .72;}
</style>
""", unsafe_allow_html=True)


def chart_style(fig, title, height=420):
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=35, r=25, t=65, b=45),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial"),
        legend=dict(orientation="h", y=1.08),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,.16)", zeroline=False)
    return fig


def go_to(act):
    st.session_state.act = act
    st.rerun()


def save_note(act, prompt):
    with st.form(f"note_{act}"):
        response = st.text_area(prompt, value=st.session_state.notes.get(act, ""), height=95)
        saved = st.form_submit_button("Save reasoning")
        if saved:
            st.session_state.notes[act] = response.strip()
            st.success("Reasoning saved for the final committee record.")


def progress():
    index = ACTS.index(st.session_state.act)
    st.progress((index + 1) / len(ACTS))
    columns = st.columns(4)
    for i, (column, label) in enumerate(zip(columns, ACT_LABELS)):
        column.markdown(f"**{label}**" if i == index else label)


def navigation(next_act=None, require_note=False):
    left, right = st.columns([4, 1])
    index = ACTS.index(st.session_state.act)
    if index > 0 and left.button("← Back"):
        go_to(ACTS[index - 1])
    disabled = require_note and not st.session_state.notes.get(st.session_state.act, "").strip()
    if next_act and right.button("Continue →", type="primary", use_container_width=True, disabled=disabled):
        go_to(next_act)


def loss_distribution(base, stress):
    fig = go.Figure()
    for result, name, color in [(base, "Reported calm", "#18A7A0"), (stress, "Economic stress", "#D45B5B")]:
        hist, edges = np.histogram(result["losses"], bins=80, density=True)
        centers = (edges[:-1] + edges[1:]) / 2
        fig.add_trace(go.Scatter(x=centers, y=hist, mode="lines", name=name, line=dict(color=color, width=3), fill="tozeroy", opacity=.42))
    fig.add_vline(x=stress["var95"], line_color="#E4B45B", line_width=3, annotation_text="VaR")
    fig.add_vline(x=stress["cvar95"], line_color="#D45B5B", line_width=3, annotation_text="CVaR")
    fig.update_xaxes(title="Simulated one-year fund loss ($m)")
    fig.update_yaxes(title="Relative frequency")
    return chart_style(fig, "The shock moves the entire loss distribution, not just one estimate", 455)


def compact_record():
    rows = []
    names = {"calm": "Initial view", "crack": "After the shock", "run": "After the run", "decision": "Final rationale"}
    for act in ACTS:
        text = st.session_state.notes.get(act, "").strip()
        if text:
            rows.append({"Stage": names[act], "Reasoning": text})
    return pd.DataFrame(rows)


st.markdown('<div class="eyebrow">NORTHSTAR DIRECT LENDING FUND III · PRIVATE CREDIT LAB</div>', unsafe_allow_html=True)
st.title("The Mark, the Shock, and the Run")
st.caption("A fictional decision story using synthetic data. The model is instructional, not a forecast or investment recommendation.")
progress()
st.divider()

act = st.session_state.act

if act == "calm":
    st.subheader("Act 1: Everything looks manageable")
    st.markdown(
        '<div class="story-line">Meridian is current on its loan. Northstar reports a $1.25 billion NAV, holds cash, and has a committed line. The amendment request appears to be a borrower problem. The first question is whether the fund is seeing the whole risk.</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    metrics = st.columns(5)
    for column, label, value in zip(
        metrics,
        ["Fund NAV", "Cash", "Credit line", "Meridian exposure", "Redemption gate"],
        ["$1.25bn", "$75m", "$62.5m", "$80m", "5% NAV"],
    ):
        column.metric(label, value)

    left, right = st.columns([1.7, 1])
    with left:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=evidence.period, y=evidence.arr_retention_pct, name="ARR retention", line=dict(color="#18A7A0", width=4)))
        fig.add_trace(go.Scatter(x=evidence.period, y=evidence.ebitda_margin_pct, name="EBITDA margin", yaxis="y2", line=dict(color="#E4B45B", width=4)))
        fig.update_layout(yaxis=dict(title="Retention (%)"), yaxis2=dict(title="Margin (%)", overlaying="y", side="right"))
        st.plotly_chart(chart_style(fig, "The borrower is weakening before the payment default"), use_container_width=True)
    with right:
        st.markdown("### What the data says")
        st.write("ARR retention declines from **94% to 86%**.")
        st.write("EBITDA margin declines from **20.6% to 15.7%**.")
        st.write("Liquidity declines from **$31m to $17m**.")
        st.write("Net leverage rises from **4.8× to 5.9×**, above the original 5.75× covenant.")
        st.info("The company is still paying. The trend says the cushion is disappearing.")

    initial = st.radio("Your initial action", case["decision_choices"], horizontal=True)
    st.session_state.initial_decision = initial
    save_note("calm", "What is the simplest explanation of the risk at this point?")
    navigation("crack", require_note=True)

elif act == "crack":
    st.subheader("Act 2: A shock reveals what stale marks hide")
    st.markdown(
        '<div class="story-line">Software credit weakens, correlations rise, and independent marks are delayed. Reported NAV changes slowly, while the economic loss distribution changes immediately.</div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    shock = c1.slider("Credit shock", 0, 100, st.session_state.shock, 5, help="Raises sector volatility, correlation, and expected loss.")
    stale = c2.slider("Days since independent valuation", 0, 90, st.session_state.stale_days, 5)
    st.session_state.shock, st.session_state.stale_days = shock, stale

    base = simulate_fund(1250, 0, 5, 0, 5)
    stress = simulate_fund(1250, shock, stale, 0, 5)
    cards = st.columns(4)
    cards[0].metric("95% VaR", f"${stress['var95']:.0f}m", delta=f"+${stress['var95']-base['var95']:.0f}m")
    cards[1].metric("95% CVaR", f"${stress['cvar95']:.0f}m", delta=f"+${stress['cvar95']-base['cvar95']:.0f}m")
    cards[2].metric("Economic NAV", f"${stress['economic_nav']:.0f}m", delta=f"-${stress['stale_gap']:.0f}m vs reported", delta_color="inverse")
    cards[3].metric("Avg. correlation", f"{stress['rho']:.2f}")
    st.plotly_chart(loss_distribution(base, stress), use_container_width=True)

    with st.expander("What do VaR and CVaR mean here?"):
        st.write("**VaR** marks a selected loss threshold. **CVaR** is the average loss beyond that threshold. In this teaching model, the shock raises volatility and correlation, so both measures rise and CVaR moves farther into the tail.")
    save_note("crack", "What changed in the risk story after seeing the distribution and valuation gap?")
    navigation("run", require_note=True)

elif act == "run":
    st.subheader("Act 3: The valuation problem becomes a cash problem")
    st.markdown(
        '<div class="story-line">Investors redeem against reported NAV. The fund can use cash, draw its line, apply the gate, or sell assets. If private marks are stale, redeeming investors may leave at a value that continuing investors later discover was too high.</div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    run = c1.slider("Redemption requests (% of NAV)", 0.0, 25.0, st.session_state.run_pct, 0.5)
    gate = c2.slider("Amount payable now (% of NAV)", 1.0, 10.0, st.session_state.gate_pct, 0.5)
    st.session_state.run_pct, st.session_state.gate_pct = run, gate
    result = simulate_fund(1250, st.session_state.shock, st.session_state.stale_days, run, gate)

    cards = st.columns(5)
    cards[0].metric("Requested", f"${result['redemption_request']:.0f}m")
    cards[1].metric("Payable now", f"${result['payable']:.0f}m")
    cards[2].metric("Cash + line + income", f"${result['cash']+result['lines']+result['income']:.0f}m")
    cards[3].metric("Forced-sale need", f"${result['sale_need']:.0f}m")
    cards[4].metric("Ending cash", f"${result['ending_cash']:.0f}m")

    waterfall = liquidity_waterfall(result)
    fig = go.Figure(go.Waterfall(
        x=waterfall.Step,
        y=waterfall.Amount,
        measure=waterfall.Measure,
        connector={"line": {"color": "#8293A1"}},
        increasing={"marker": {"color": "#18A7A0"}},
        decreasing={"marker": {"color": "#D45B5B"}},
        totals={"marker": {"color": "#E4B45B"}},
    ))
    fig.update_yaxes(title="$ millions")
    st.plotly_chart(chart_style(fig, "How the fund meets the run", 455), use_container_width=True)

    st.warning(
        f"Reported NAV remains $1,250m, while the model estimates economic NAV near ${result['economic_nav']:.0f}m. "
        f"The implied stale-mark gap is ${result['stale_gap']:.0f}m."
    )
    save_note("run", "In one paragraph, explain how stale marks can transfer value between redeeming and remaining investors.")
    navigation("decision", require_note=True)

elif act == "decision":
    st.subheader("Act 4: Choose the response, then defend it")
    st.markdown(
        '<div class="story-line">The committee cannot eliminate the loss already embedded in the portfolio. The committee can decide how quickly to recognize it, how to fund withdrawals, and how to protect remaining investors.</div>',
        unsafe_allow_html=True,
    )
    actions = st.multiselect(
        "Select up to three actions",
        ["Independent revaluation", "Tighten redemption gate", "Draw liquidity line early", "Sell public liquid sleeve", "Suspend new originations"],
        default=st.session_state.actions,
        max_selections=3,
    )
    st.session_state.actions = actions
    before = simulate_fund(1250, st.session_state.shock, st.session_state.stale_days, st.session_state.run_pct, st.session_state.gate_pct)
    after = mitigation_effects(1250, st.session_state.shock, st.session_state.stale_days, st.session_state.run_pct, st.session_state.gate_pct, actions)

    comparison = pd.DataFrame({
        "Measure": ["95% CVaR", "Economic NAV", "Stale-mark gap", "Ending cash"],
        "Before": [before["cvar95"], before["economic_nav"], before["stale_gap"], before["ending_cash"]],
        "After": [after["cvar95"], after["economic_nav"], after["stale_gap"], after["ending_cash"]],
    })
    fig = go.Figure()
    fig.add_trace(go.Bar(y=comparison.Measure, x=comparison.Before, name="Before", orientation="h", marker_color="#D45B5B"))
    fig.add_trace(go.Bar(y=comparison.Measure, x=comparison.After, name="After", orientation="h", marker_color="#18A7A0"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(title="$ millions")
    st.plotly_chart(chart_style(fig, "What the response package changes", 420), use_container_width=True)
    st.caption("All four measures are shown in $ millions. The response may improve liquidity or valuation transparency without eliminating underlying credit loss.")

    final = st.radio("Final amendment decision", case["decision_choices"], horizontal=True)
    st.session_state.final_decision = final
    save_note("decision", "Give the final decision in plain English. Cite the two numbers that matter most and state what would reverse the decision.")

    st.divider()
    st.subheader("Committee record")
    record = compact_record()
    if record.empty:
        st.info("Saved reasoning will appear here.")
    else:
        st.dataframe(record, use_container_width=True, hide_index=True, column_config={"Stage": st.column_config.TextColumn(width="small"), "Reasoning": st.column_config.TextColumn(width="large")})

    summary = {
        "initial_decision": st.session_state.initial_decision,
        "final_decision": st.session_state.final_decision,
        "shock": st.session_state.shock,
        "stale_days": st.session_state.stale_days,
        "redemptions_pct_nav": st.session_state.run_pct,
        "payable_pct_nav": st.session_state.gate_pct,
        "actions": actions,
        "before": {k: round(float(before[k]), 2) for k in ["var95", "cvar95", "economic_nav", "stale_gap", "ending_cash"]},
        "after": {k: round(float(after[k]), 2) for k in ["var95", "cvar95", "economic_nav", "stale_gap", "ending_cash"]},
        "reasoning": st.session_state.notes,
        "generated": datetime.now().isoformat(timespec="seconds"),
    }
    st.download_button(
        "Download committee record",
        data=json.dumps(summary, indent=2),
        file_name="northstar_committee_record.json",
        mime="application/json",
        type="primary",
        disabled=not st.session_state.notes.get("decision", "").strip(),
    )
