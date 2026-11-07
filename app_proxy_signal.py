from __future__ import annotations

from pathlib import Path
import base64
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Blackridge Proxy Early-Warning Lab",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ROOT = Path(__file__).resolve().parent
VIDEO = "https://youtu.be/BLYCx_AOgUs"

# -----------------------------------------------------------------------------
# DATA: synthetic, reproducible, and deliberately separated by information set
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def build_case_data():
    holdings = pd.DataFrame(
        [
            ["Prime RMBS AAA", 1400, 0.012, 0.35],
            ["Alt-A RMBS AAA", 1000, 0.020, 0.55],
            ["Subprime 2006-2 AAA", 900, 0.030, 0.75],
            ["Subprime 2006-2 BBB", 600, 0.055, 0.95],
            ["Subprime 2007-1 BBB-", 500, 0.075, 1.10],
            ["CDO Mezzanine Residual", 800, 0.085, 1.25],
        ],
        columns=["pool", "exposure_mm", "base_annual_vol", "stress_beta"],
    )
    holdings["weight"] = holdings["exposure_mm"] / holdings["exposure_mm"].sum()

    rng = np.random.default_rng(2007)
    n_assets = len(holdings)

    # Information available at the decision point: 250 calm internal observations.
    base_corr_assumption = np.full((n_assets, n_assets), 0.22)
    np.fill_diagonal(base_corr_assumption, 1.0)
    base_daily_vol = holdings["base_annual_vol"].to_numpy() / np.sqrt(252)
    internal_returns = rng.multivariate_normal(
        np.full(n_assets, 0.00012),
        np.outer(base_daily_vol, base_daily_vol) * base_corr_assumption,
        250,
    )

    # Hidden until the ex-post scene: 250 realized crisis observations.
    realized_annual_vol = np.array([0.030, 0.055, 0.090, 0.180, 0.280, 0.350])
    realized_corr_assumption = np.full((n_assets, n_assets), 0.62)
    realized_corr_assumption[2:, 2:] = 0.82
    np.fill_diagonal(realized_corr_assumption, 1.0)
    realized_daily_vol = realized_annual_vol / np.sqrt(252)
    future_returns = rng.multivariate_normal(
        np.full(n_assets, -0.0009),
        np.outer(realized_daily_vol, realized_daily_vol) * realized_corr_assumption,
        250,
    )
    for row, magnitude in zip(
        rng.choice(250, 18, replace=False),
        rng.uniform(0.010, 0.035, 18),
    ):
        future_returns[row] -= magnitude * np.array([0.25, 0.45, 0.70, 0.95, 1.10, 1.25])

    internal_dates = pd.date_range("2006-07-03", periods=250, freq="B")
    future_dates = pd.date_range(internal_dates[-1] + pd.offsets.BDay(1), periods=250, freq="B")
    internal = pd.DataFrame(internal_returns, columns=holdings["pool"])
    internal.insert(0, "date", internal_dates)
    future = pd.DataFrame(future_returns, columns=holdings["pool"])
    future.insert(0, "date", future_dates)

    # External proxy leads the internal repricing. The last 30 proxy observations
    # deteriorate before any future mortgage-pool return is revealed.
    proxy_dates = pd.date_range("2007-04-02", periods=250, freq="B")
    proxy_returns = np.r_[
        rng.normal(0.00015, 0.0016, 220),
        rng.normal(-0.0045, 0.0105, 25),
        np.array([-0.012, -0.011, -0.013, -0.0125, -0.014]),
    ]
    proxy_price = 100 * np.exp(np.cumsum(proxy_returns))
    proxy_price = proxy_price / proxy_price[0] * 100
    proxy = pd.DataFrame({"date": proxy_dates, "proxy_price": proxy_price})
    proxy["return"] = proxy["proxy_price"].pct_change()
    proxy["running_peak"] = proxy["proxy_price"].cummax()
    proxy["drawdown"] = proxy["proxy_price"] / proxy["running_peak"] - 1
    proxy["rolling_vol_30d"] = proxy["return"].rolling(30).std(ddof=1) * np.sqrt(252)
    proxy["return_5d"] = proxy["proxy_price"].pct_change(5)

    return holdings, internal, future, proxy


H, INTERNAL, FUTURE, PROXY = build_case_data()
PORTFOLIO_VALUE_MM = float(H["exposure_mm"].sum())
WEIGHTS = H["weight"].to_numpy()
POOLS = H["pool"].tolist()

SCENES = [
    "intro",
    "official",
    "warning",
    "signal",
    "shadow",
    "decision",
    "reveal",
    "assignment",
]
LABELS = ["INTRO", "OFFICIAL", "WARNING", "SIGNAL", "SHADOW", "DECIDE", "REVEAL", "ASSIGN"]

for key, value in {
    "accepted": False,
    "scene": "intro",
    "confidence": 0.99,
    "decision": None,
    "rationale": "",
    "decision_locked": False,
}.items():
    st.session_state.setdefault(key, value)

# -----------------------------------------------------------------------------
# STYLE AND HELPERS
# -----------------------------------------------------------------------------
st.markdown(
    """
<style>
.block-container{width:calc(100vw - 28px);max-width:none!important;padding:1rem 14px!important}
.eyebrow{color:#0f7890;font-size:.72rem;font-weight:800;letter-spacing:.14em}
.ttl{font:700 1.9rem Georgia;margin:.05rem 0}.copy{font:1rem/1.42 Georgia}
.dialogue{display:flex;gap:1rem;align-items:center;border:1px solid #cbd6dc;border-radius:11px;background:#fff;padding:.85rem;min-height:150px}
.dialogue img{width:130px;height:130px;object-fit:cover;object-position:center 35%;border-radius:11px;flex:none}
.dialogue b{font-size:1.08rem;color:#102a43}.bubble{border-left:5px solid #0f7890;background:#edf5f6;padding:.8rem .9rem;font:italic 1.02rem/1.42 Georgia}
.tile{border:1px solid #cbd6dc;border-radius:11px;background:linear-gradient(145deg,#fff,#f3f8f9);padding:18px;min-height:150px;font-size:1.03rem;line-height:1.48}
.tile-title{font-size:1.12rem;font-weight:800;color:#102a43;margin-bottom:8px}
.signal-pass{border-left:6px solid #218c74;background:#effaf6;padding:16px;border-radius:8px;min-height:135px}
.signal-fail{border-left:6px solid #9aa5ad;background:#f6f7f8;padding:16px;border-radius:8px;min-height:135px}
.assumption{border-left:6px solid #f3911b;background:#fff8e9;padding:18px 20px;border-radius:8px;font-size:1.04rem;line-height:1.5}
.assignment{border:1px solid #cbd6dc;border-radius:12px;background:#fff;padding:22px;min-height:330px;box-shadow:0 4px 14px rgba(16,42,67,.06)}
.assignment h3{font-size:1.45rem;margin:.1rem 0 .75rem;color:#102a43}.assignment li,.assignment p{font-size:1.08rem;line-height:1.56;margin-bottom:.48rem}
[data-testid="stMetricValue"]{font-size:1.28rem}.stButton>button{font-weight:700}
</style>
""",
    unsafe_allow_html=True,
)


def header(kicker, title, copy):
    st.markdown(
        f"<div class='eyebrow'>{kicker}</div><div class='ttl'>{title}</div><div class='copy'>{copy}</div>",
        unsafe_allow_html=True,
    )


def goto_scene(scene):
    st.session_state.scene = scene
    st.rerun()


def navigation(next_scene=None, block_next=False):
    previous_col, next_col = st.columns([6, 1])
    index = SCENES.index(st.session_state.scene)
    if index and previous_col.button("← Previous"):
        goto_scene(SCENES[index - 1])
    if next_scene and next_col.button("Continue →", type="primary", width="stretch", disabled=block_next):
        goto_scene(next_scene)


def timeline():
    index = SCENES.index(st.session_state.scene)
    st.progress((index + 1) / len(SCENES))
    columns = st.columns(len(SCENES))
    for item, (column, label) in enumerate(zip(columns, LABELS)):
        column.caption(("● " if index == item else "") + label)


def portrait(key, state):
    return ROOT / "assets" / "expressions" / f"{key}_{state}.jpg"


def talk(name, key, state, text):
    image_path = portrait(key, state)
    image_html = ""
    if image_path.exists():
        encoded = base64.b64encode(image_path.read_bytes()).decode()
        image_html = f"<img src='data:image/jpeg;base64,{encoded}'>"
    st.markdown(
        f"<div class='dialogue'>{image_html}<div><b>{name}</b><div class='bubble'>{text}</div></div></div>",
        unsafe_allow_html=True,
    )


def style(figure, title, height=390):
    figure.update_layout(
        title=title,
        height=height,
        margin=dict(l=40, r=20, t=55, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#fcfbf8",
        font=dict(size=10),
        legend=dict(orientation="h", y=1.08),
        uirevision="proxy-v2",
    )
    figure.update_yaxes(gridcolor="rgba(120,120,120,.12)")
    return figure


def portfolio_losses(frame):
    portfolio_return = frame[POOLS].to_numpy() @ WEIGHTS
    return -PORTFOLIO_VALUE_MM * portfolio_return


def historical_stats(losses, confidence):
    values = np.asarray(losses, dtype=float)
    var = float(np.quantile(values, confidence, method="linear"))
    tail = values[values >= var]
    return {
        "volatility": float(values.std(ddof=1)),
        "var": var,
        "cvar": float(tail.mean()),
        "tail_count": int(tail.size),
    }


def signal_metrics():
    baseline_vol = float(PROXY.loc[PROXY.index < 220, "return"].std(ddof=1) * np.sqrt(252))
    current_drawdown = float(PROXY["drawdown"].iloc[-1])
    current_vol = float(PROXY["rolling_vol_30d"].iloc[-1])
    current_5d = float(PROXY["return_5d"].iloc[-1])
    vol_ratio = current_vol / baseline_vol
    flags = {
        "Drawdown ≤ -10%": current_drawdown <= -0.10,
        "30-day volatility ≥ 2× baseline": vol_ratio >= 2.0,
        "Five-day return ≤ -5%": current_5d <= -0.05,
    }
    count = int(sum(flags.values()))
    return {
        "baseline_vol": baseline_vol,
        "current_drawdown": current_drawdown,
        "current_vol": current_vol,
        "current_5d": current_5d,
        "vol_ratio": vol_ratio,
        "flags": flags,
        "signal_count": count,
        "stress_trigger": count >= 2,
        "stress_score": count / 3.0,
    }


def z_for_confidence(confidence):
    return {0.95: 1.6448536269514722, 0.975: 1.959963984540054, 0.99: 2.3263478740408408}[confidence]


def shadow_model(confidence):
    signal = signal_metrics()
    base_corr = INTERNAL[POOLS].corr().to_numpy()
    proxy_vol_ratio = float(np.clip(signal["vol_ratio"], 1.0, 4.0))
    stressed_annual_vol = H["base_annual_vol"].to_numpy() * np.power(
        proxy_vol_ratio,
        H["stress_beta"].to_numpy(),
    )
    correlation_lambda = 0.75 * signal["stress_score"]
    stress_corr = base_corr + correlation_lambda * (1.0 - base_corr)
    np.fill_diagonal(stress_corr, 1.0)
    stressed_daily_vol = stressed_annual_vol / np.sqrt(252)
    stress_cov = np.outer(stressed_daily_vol, stressed_daily_vol) * stress_corr
    portfolio_daily_vol = float(np.sqrt(WEIGHTS @ stress_cov @ WEIGHTS))
    dollar_vol = PORTFOLIO_VALUE_MM * portfolio_daily_vol
    z = z_for_confidence(confidence)
    normal_pdf = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
    var = z * dollar_vol
    cvar = dollar_vol * normal_pdf / (1.0 - confidence)
    return {
        **signal,
        "base_corr": base_corr,
        "proxy_vol_ratio_capped": proxy_vol_ratio,
        "stressed_annual_vol": stressed_annual_vol,
        "correlation_lambda": correlation_lambda,
        "stress_corr": stress_corr,
        "dollar_vol": dollar_vol,
        "var": var,
        "cvar": cvar,
    }


def heatmap(matrix, title):
    short_names = [
        "Prime AAA",
        "Alt-A AAA",
        "Subprime AAA",
        "Subprime BBB",
        "2007 BBB-",
        "CDO Mezz",
    ]
    figure = go.Figure(
        go.Heatmap(
            z=matrix,
            x=short_names,
            y=short_names,
            zmin=-1,
            zmax=1,
            colorscale="RdBu_r",
            text=np.round(matrix, 2),
            texttemplate="%{text:.2f}",
            colorbar=dict(title="ρ"),
        )
    )
    return style(figure, title, 400)


# -----------------------------------------------------------------------------
# ENTRY SCREEN
# -----------------------------------------------------------------------------
if not st.session_state.accepted:
    st.title("Educational Use and Historical Context")
    st.warning(
        "Original fictional teaching case inspired by Margin Call (2011). "
        "Mortgage pools, market proxy, return data, dialogue, and liquidation assumptions are synthetic."
    )
    left, right = st.columns([2.3, 1])
    with left:
        st.video(VIDEO)
    with right:
        accepted = st.checkbox("I understand this is an educational simulation.")
        if st.button("Enter the case", type="primary", disabled=not accepted, width="stretch"):
            st.session_state.accepted = True
            st.rerun()
    st.stop()

st.title("One Night Inside the Tail: Early-Warning Edition")
timeline()
st.divider()
scene = st.session_state.scene

# -----------------------------------------------------------------------------
# SCENES
# -----------------------------------------------------------------------------
if scene == "intro":
    header(
        "INTRO",
        "The official model still says the book is safe",
        "The internal mortgage data remain calm, but an external market proxy is beginning to move. The task is to decide whether the signal warrants action before the portfolio confirms the regime change.",
    )
    profile = ROOT / "assets" / "blackridge_employee_profiles.png"
    if profile.exists():
        st.image(str(profile), width="stretch")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='tile'><div class='tile-title'>1. Official evidence</div>The approved model uses 250 internal mortgage observations. It is backward-looking and institutionally accepted.</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='tile'><div class='tile-title'>2. External warning</div>A separate mortgage-market proxy deteriorates before the internal portfolio has repriced.</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='tile'><div class='tile-title'>3. Decision under uncertainty</div>Students must choose whether to trust the official model, activate a shadow model, or reduce exposure before realized crisis data exist.</div>", unsafe_allow_html=True)
    navigation("official")

elif scene == "official":
    header(
        "OFFICIAL MODEL",
        "The approved historical calibration",
        "Only the 250 internal mortgage observations available at the decision date are used here. No future crisis returns are visible.",
    )
    confidence = st.select_slider(
        "Confidence level",
        options=[0.95, 0.975, 0.99],
        value=st.session_state.confidence,
        format_func=lambda x: f"{x:.1%}",
    )
    st.session_state.confidence = confidence
    official = historical_stats(portfolio_losses(INTERNAL), confidence)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Internal observations", "250")
    m2.metric("One-day loss volatility", f"${official['volatility']:.1f}m")
    m3.metric(f"{confidence:.1%} historical VaR", f"${official['var']:.1f}m")
    m4.metric(f"{confidence:.1%} historical CVaR", f"${official['cvar']:.1f}m")
    left, right = st.columns([1.35, 1])
    with left:
        st.plotly_chart(heatmap(INTERNAL[POOLS].corr().to_numpy(), "Observed internal correlation matrix"), width="stretch", config={"displayModeBar": False})
    with right:
        talk("Peter Sullivan", "peter", "decisive", "The official model is internally consistent. The unresolved question is whether the historical window still describes the market we are entering.")
        st.markdown("<div class='assumption'><b>Observed, not assumed:</b> The official volatility, VaR, CVaR, and correlation matrix are calculated only from the 250 internal mortgage observations available at the decision point.</div>", unsafe_allow_html=True)
    navigation("warning")

elif scene == "warning":
    header(
        "EXTERNAL WARNING",
        "The proxy moves before the portfolio",
        "The external series is not used as a decorative overlay. Its drawdown, volatility, and momentum determine whether the shadow model activates.",
    )
    signal = signal_metrics()
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=PROXY["date"], y=PROXY["proxy_price"], name="External proxy", line=dict(color="#c7474b", width=3)))
    figure.add_vrect(x0=PROXY["date"].iloc[220], x1=PROXY["date"].iloc[-1], fillcolor="#f3911b", opacity=0.12, line_width=0, annotation_text="Early-warning window", annotation_position="top left")
    figure.update_yaxes(title="Proxy price index")
    st.plotly_chart(style(figure, "External mortgage-market proxy", 430), width="stretch", config={"displayModeBar": False})
    c1, c2, c3 = st.columns(3)
    c1.metric("Current drawdown", f"{signal['current_drawdown']:.1%}", "Trigger: -10%")
    c2.metric("30-day volatility ratio", f"{signal['vol_ratio']:.1f}×", "Trigger: 2.0×")
    c3.metric("Five-day return", f"{signal['current_5d']:.1%}", "Trigger: -5%")
    st.markdown("<div class='assumption'><b>Timing:</b> The proxy warning is available before the 250 future mortgage observations are revealed. Students must make a forecast and decision without using the realized crisis period.</div>", unsafe_allow_html=True)
    navigation("signal")

elif scene == "signal":
    header(
        "SIGNAL TEST",
        "A transparent two-of-three warning rule",
        "The shadow model activates when at least two objective proxy conditions are met.",
    )
    signal = signal_metrics()
    values = [
        ("Drawdown", signal["current_drawdown"], "≤ -10%", signal["flags"]["Drawdown ≤ -10%"], f"{signal['current_drawdown']:.1%}"),
        ("Volatility ratio", signal["vol_ratio"], "≥ 2.0×", signal["flags"]["30-day volatility ≥ 2× baseline"], f"{signal['vol_ratio']:.1f}×"),
        ("Five-day return", signal["current_5d"], "≤ -5%", signal["flags"]["Five-day return ≤ -5%"], f"{signal['current_5d']:.1%}"),
    ]
    columns = st.columns(3)
    for column, (name, _, threshold, passed, display) in zip(columns, values):
        css = "signal-pass" if passed else "signal-fail"
        status = "TRIGGERED" if passed else "NOT TRIGGERED"
        with column:
            st.markdown(f"<div class='{css}'><b>{name}</b><br><br>Observed: <b>{display}</b><br>Threshold: {threshold}<br>Status: <b>{status}</b></div>", unsafe_allow_html=True)
    st.metric("Signals triggered", f"{signal['signal_count']} of 3")
    if signal["stress_trigger"]:
        st.success(f"Shadow model activated. Stress score = {signal['stress_score']:.2f}.")
    else:
        st.info("Shadow model remains inactive because fewer than two conditions were met.")
    navigation("shadow")

elif scene == "shadow":
    header(
        "SHADOW MODEL",
        "Translate the external warning into forward risk",
        "The proxy scales pool volatility by sensitivity and moves correlations toward one. These are forecast stress assumptions, not observed crisis outcomes.",
    )
    shadow = shadow_model(st.session_state.confidence)
    official = historical_stats(portfolio_losses(INTERNAL), st.session_state.confidence)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Official historical VaR", f"${official['var']:.1f}m")
    m2.metric("Proxy-triggered shadow VaR", f"${shadow['var']:.1f}m", f"{shadow['var']/official['var']:.1f}× official")
    m3.metric("Official historical CVaR", f"${official['cvar']:.1f}m")
    m4.metric("Proxy-triggered shadow CVaR", f"${shadow['cvar']:.1f}m", f"{shadow['cvar']/official['cvar']:.1f}× official")

    mapping = H[["pool", "base_annual_vol", "stress_beta"]].copy()
    mapping["stressed_annual_vol"] = shadow["stressed_annual_vol"]
    mapping.columns = ["Mortgage pool", "Base annual volatility", "Proxy sensitivity β", "Forecast stressed volatility"]
    st.dataframe(
        mapping.style.format({
            "Base annual volatility": "{:.1%}",
            "Proxy sensitivity β": "{:.2f}",
            "Forecast stressed volatility": "{:.1%}",
        }),
        hide_index=True,
        width="stretch",
    )

    left, right = st.columns(2)
    with left:
        st.plotly_chart(heatmap(shadow["base_corr"], "Observed internal correlation"), width="stretch", config={"displayModeBar": False})
    with right:
        st.plotly_chart(heatmap(shadow["stress_corr"], "Forecast stress correlation"), width="stretch", config={"displayModeBar": False})
    st.markdown(f"<div class='assumption'><b>Assumption audit:</b> Proxy volatility ratio is capped at {shadow['proxy_vol_ratio_capped']:.2f}×. Correlation convergence λ equals {shadow['correlation_lambda']:.2f}. The right-hand matrix is a forecast assumption generated before crisis returns are observed.</div>", unsafe_allow_html=True)
    navigation("decision")

elif scene == "decision":
    header(
        "DECISION",
        "Act before the internal data confirm the regime",
        "Choose a course of action using only the official model, external warning, and shadow forecast. The future mortgage returns remain hidden.",
    )
    shadow = shadow_model(st.session_state.confidence)
    official = historical_stats(portfolio_losses(INTERNAL), st.session_state.confidence)
    summary = pd.DataFrame({
        "Evidence": ["Historical VaR", "Historical CVaR", "Proxy signals", "Shadow VaR", "Shadow CVaR"],
        "Decision-date result": [f"${official['var']:.1f}m", f"${official['cvar']:.1f}m", f"{shadow['signal_count']} of 3", f"${shadow['var']:.1f}m", f"${shadow['cvar']:.1f}m"],
        "Status": ["Observed", "Observed", "Observed", "Forecast", "Forecast"],
    })
    st.dataframe(summary, hide_index=True, width="stretch")

    choices = [
        "Maintain the official model and current exposures",
        "Reduce the most proxy-sensitive positions selectively",
        "Initiate an accelerated portfolio liquidation",
    ]
    default_index = choices.index(st.session_state.decision) if st.session_state.decision in choices else 0
    decision = st.radio("Risk-committee decision", choices, index=default_index, disabled=st.session_state.decision_locked)
    rationale = st.text_area(
        "Decision rationale and numerical reversal condition",
        value=st.session_state.rationale,
        placeholder="Example: Reduce CDO and lower-rated subprime exposure now; reverse if the proxy volatility ratio falls below 1.5× and drawdown recovers above -5%.",
        disabled=st.session_state.decision_locked,
    )
    if not st.session_state.decision_locked:
        if st.button("Lock decision and reveal the realized regime", type="primary", disabled=len(rationale.strip()) < 30):
            st.session_state.decision = decision
            st.session_state.rationale = rationale.strip()
            st.session_state.decision_locked = True
            goto_scene("reveal")
        st.caption("A rationale of at least 30 characters is required. Once locked, the realized crisis period will be revealed.")
    else:
        st.success("Decision locked. Continue to the ex-post reveal.")
        navigation("reveal")

elif scene == "reveal":
    if not st.session_state.decision_locked:
        st.warning("Record and lock a decision before viewing realized crisis data.")
        if st.button("Return to decision"):
            goto_scene("decision")
        st.stop()

    header(
        "EX POST REVEAL",
        "Did the proxy-driven shadow model provide useful warning?",
        "The 250 subsequent mortgage observations are now available. Compare the official model and proxy-triggered forecast with realized crisis outcomes.",
    )
    confidence = st.session_state.confidence
    official = historical_stats(portfolio_losses(INTERNAL), confidence)
    shadow = shadow_model(confidence)
    realized = historical_stats(portfolio_losses(FUTURE), confidence)
    comparison = pd.DataFrame({
        "Measure": ["One-day loss volatility ($mm)", f"{confidence:.1%} VaR ($mm)", f"{confidence:.1%} CVaR ($mm)"],
        "Official historical": [official["volatility"], official["var"], official["cvar"]],
        "Shadow forecast": [shadow["dollar_vol"], shadow["var"], shadow["cvar"]],
        "Realized crisis": [realized["volatility"], realized["var"], realized["cvar"]],
    })
    st.dataframe(comparison.style.format({
        "Official historical": "${:,.1f}",
        "Shadow forecast": "${:,.1f}",
        "Realized crisis": "${:,.1f}",
    }), hide_index=True, width="stretch")

    left, right = st.columns(2)
    with left:
        st.plotly_chart(heatmap(shadow["stress_corr"], "Forecast stress correlation"), width="stretch", config={"displayModeBar": False})
    with right:
        st.plotly_chart(heatmap(FUTURE[POOLS].corr().to_numpy(), "Realized crisis correlation"), width="stretch", config={"displayModeBar": False})

    st.markdown("### Locked committee decision")
    st.write(f"**Decision:** {st.session_state.decision}")
    st.write(f"**Rationale and reversal condition:** {st.session_state.rationale}")
    st.markdown("<div class='assumption'><b>Validation question:</b> Was the shadow model directionally useful and timely, even if its point estimates differed from realized risk? Evaluate the cost of acting early against the cost of waiting for internal confirmation.</div>", unsafe_allow_html=True)
    navigation("assignment")

elif scene == "assignment":
    header(
        "ASSIGNMENT",
        "Early-warning risk-committee memorandum",
        "Document the signal, forecast, decision, and ex-post validation without confusing observed data with stress assumptions.",
    )
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("""
<div class='assignment'><h3>Model reconstruction</h3><ol>
<li>Calculate official historical volatility, correlation, VaR, and CVaR from the 250 internal observations.</li>
<li>Calculate proxy drawdown, 30-day annualized volatility, volatility ratio, and five-day return.</li>
<li>Apply the two-of-three trigger and calculate the stress score.</li>
<li>Map proxy stress to each pool using β sensitivities and calculate forecast stress correlations.</li>
<li>Calculate the shadow model’s forward parametric VaR and CVaR.</li>
</ol></div>
""", unsafe_allow_html=True)
    with right:
        st.markdown("""
<div class='assignment'><h3>Risk judgment</h3><ol>
<li>Defend or reject the relevance of the external proxy.</li>
<li>Separate observed evidence from stress assumptions and realized outcomes.</li>
<li>Explain the chosen action before the crisis data were revealed.</li>
<li>Compare the shadow forecast with realized crisis results.</li>
<li>State whether the early action was justified and provide a numerical reversal condition.</li>
</ol></div>
""", unsafe_allow_html=True)

    st.info("Deliverable: Submit the completed workbook or notebook plus a 750–1,000 word risk-committee memorandum. The memorandum must distinguish the official model, external signal, shadow forecast, locked decision, and ex-post validation.")

    st.markdown("### Downloadable case files")
    c1, c2, c3, c4 = st.columns(4)
    c1.download_button("Holdings.csv", H.to_csv(index=False), "proxy_case_holdings.csv", "text/csv", width="stretch")
    c2.download_button("Internal returns.csv", INTERNAL.to_csv(index=False), "internal_mortgage_returns.csv", "text/csv", width="stretch")
    c3.download_button("External proxy.csv", PROXY.to_csv(index=False), "external_proxy_early_warning.csv", "text/csv", width="stretch")
    c4.download_button("Ex-post returns.csv", FUTURE.to_csv(index=False), "realized_crisis_returns.csv", "text/csv", width="stretch")

    if st.button("Reset decision for another attempt"):
        st.session_state.decision = None
        st.session_state.rationale = ""
        st.session_state.decision_locked = False
        goto_scene("intro")
