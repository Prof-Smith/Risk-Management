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
    n = len(holdings)
    calm_corr = np.full((n, n), 0.22)
    np.fill_diagonal(calm_corr, 1.0)
    calm_daily_vol = holdings["base_annual_vol"].to_numpy() / np.sqrt(252)
    calm = rng.multivariate_normal(
        np.full(n, 0.00012),
        np.outer(calm_daily_vol, calm_daily_vol) * calm_corr,
        250,
    )

    crisis_annual_vol = np.array([0.030, 0.055, 0.090, 0.180, 0.280, 0.350])
    crisis_corr = np.full((n, n), 0.62)
    crisis_corr[2:, 2:] = 0.82
    np.fill_diagonal(crisis_corr, 1.0)
    crisis_daily_vol = crisis_annual_vol / np.sqrt(252)
    crisis = rng.multivariate_normal(
        np.full(n, -0.0009),
        np.outer(crisis_daily_vol, crisis_daily_vol) * crisis_corr,
        250,
    )
    for row, magnitude in zip(rng.choice(250, 18, replace=False), rng.uniform(0.010, 0.035, 18)):
        crisis[row] -= magnitude * np.array([0.25, 0.45, 0.70, 0.95, 1.10, 1.25])

    calm_dates = pd.date_range("2006-07-03", periods=250, freq="B")
    crisis_dates = pd.date_range(calm_dates[-1] + pd.offsets.BDay(1), periods=250, freq="B")
    internal = pd.DataFrame(calm, columns=holdings["pool"])
    internal.insert(0, "date", calm_dates)
    future = pd.DataFrame(crisis, columns=holdings["pool"])
    future.insert(0, "date", crisis_dates)

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
POOLS = H["pool"].tolist()
WEIGHTS = H["weight"].to_numpy()
PORTFOLIO_VALUE_MM = float(H["exposure_mm"].sum())

SCENES = ["intro", "official", "warning", "signal", "update", "shadow", "decision", "reveal", "assignment"]
LABELS = ["INTRO", "OFFICIAL", "WARNING", "SIGNAL", "UPDATE", "SHADOW", "DECIDE", "REVEAL", "ASSIGN"]

for key, value in {
    "accepted": False,
    "scene": "intro",
    "confidence": 0.99,
    "decision": None,
    "rationale": "",
    "decision_locked": False,
    "proxy_cap": 4.0,
    "corr_strength": 0.75,
    "beta_multiplier": 1.0,
}.items():
    st.session_state.setdefault(key, value)

st.markdown(
    """
<style>
.block-container{width:calc(100vw - 28px);max-width:none!important;padding:1rem 14px!important}
.eyebrow{color:#0f7890;font-size:.72rem;font-weight:800;letter-spacing:.14em}
.ttl{font:700 1.9rem Georgia;margin:.05rem 0}.copy{font:1rem/1.42 Georgia}
.character{border:1px solid #cbd6dc;border-radius:12px;background:#fff;padding:16px;min-height:190px;box-shadow:0 3px 10px rgba(16,42,67,.06)}
.character img{width:76px;height:76px;object-fit:cover;border-radius:10px;float:left;margin:0 12px 8px 0}
.character-name{font-size:1.12rem;font-weight:800;color:#102a43}.character-role{font-size:.78rem;color:#0f7890;font-weight:800;letter-spacing:.08em}
.character-input{clear:both;padding-top:7px;font-size:.97rem;line-height:1.45}.character-output{border-left:4px solid #f3911b;background:#fff8e9;padding:9px;margin-top:10px;font-size:.93rem}
.tile{border:1px solid #cbd6dc;border-radius:11px;background:linear-gradient(145deg,#fff,#f3f8f9);padding:18px;min-height:150px;font-size:1.03rem;line-height:1.48}
.tile-title{font-size:1.12rem;font-weight:800;color:#102a43;margin-bottom:8px}
.signal-pass{border-left:6px solid #218c74;background:#effaf6;padding:16px;border-radius:8px;min-height:135px}
.signal-fail{border-left:6px solid #9aa5ad;background:#f6f7f8;padding:16px;border-radius:8px;min-height:135px}
.assumption{border-left:6px solid #f3911b;background:#fff8e9;padding:18px 20px;border-radius:8px;font-size:1.04rem;line-height:1.5}
.flow{border:1px solid #cbd6dc;border-radius:12px;padding:18px;background:#fff;min-height:280px;text-align:center;font-size:1.03rem;line-height:1.65}
.flow-title{font-size:1.2rem;font-weight:800;color:#102a43;margin-bottom:10px}.arrow{font-size:1.4rem;color:#0f7890;font-weight:800}
.assignment{border:1px solid #cbd6dc;border-radius:12px;background:#fff;padding:22px;min-height:330px;box-shadow:0 4px 14px rgba(16,42,67,.06)}
.assignment h3{font-size:1.45rem;margin:.1rem 0 .75rem;color:#102a43}.assignment li,.assignment p{font-size:1.08rem;line-height:1.56;margin-bottom:.48rem}
[data-testid="stMetricValue"]{font-size:1.28rem}.stButton>button{font-weight:700}
</style>
""",
    unsafe_allow_html=True,
)


def header(kicker, title, copy):
    st.markdown(f"<div class='eyebrow'>{kicker}</div><div class='ttl'>{title}</div><div class='copy'>{copy}</div>", unsafe_allow_html=True)


def goto_scene(scene):
    st.session_state.scene = scene
    st.rerun()


def navigation(next_scene=None):
    a, b = st.columns([6, 1])
    i = SCENES.index(st.session_state.scene)
    if i and a.button("← Previous"):
        goto_scene(SCENES[i - 1])
    if next_scene and b.button("Continue →", type="primary", width="stretch"):
        goto_scene(next_scene)


def timeline():
    i = SCENES.index(st.session_state.scene)
    st.progress((i + 1) / len(SCENES))
    for j, (column, label) in enumerate(zip(st.columns(len(SCENES)), LABELS)):
        column.caption(("● " if i == j else "") + label)


def portrait(key, state="concerned"):
    return ROOT / "assets" / "expressions" / f"{key}_{state}.jpg"


def image_html(key, state="concerned"):
    path = portrait(key, state)
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode()
    return f"<img src='data:image/jpeg;base64,{encoded}'>"


def character_card(name, key, role, inputs, output, state="concerned"):
    st.markdown(
        f"<div class='character'>{image_html(key,state)}<div class='character-name'>{name}</div>"
        f"<div class='character-role'>{role}</div><div class='character-input'><b>Likely inputs:</b> {inputs}</div>"
        f"<div class='character-output'><b>Model contribution:</b> {output}</div></div>",
        unsafe_allow_html=True,
    )


def style(fig, title, height=390):
    fig.update_layout(title=title, height=height, margin=dict(l=40, r=20, t=55, b=40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#fcfbf8", font=dict(size=10), legend=dict(orientation="h", y=1.08), uirevision="proxy-v3")
    fig.update_yaxes(gridcolor="rgba(120,120,120,.12)")
    return fig


def portfolio_losses(frame):
    return -PORTFOLIO_VALUE_MM * (frame[POOLS].to_numpy() @ WEIGHTS)


def historical_stats(losses, confidence):
    values = np.asarray(losses, dtype=float)
    var = float(np.quantile(values, confidence, method="linear"))
    tail = values[values >= var]
    return {"volatility": float(values.std(ddof=1)), "var": var, "cvar": float(tail.mean()), "tail_count": int(tail.size)}


def signal_metrics():
    baseline_vol = float(PROXY.loc[PROXY.index < 220, "return"].std(ddof=1) * np.sqrt(252))
    drawdown = float(PROXY["drawdown"].iloc[-1])
    current_vol = float(PROXY["rolling_vol_30d"].iloc[-1])
    return_5d = float(PROXY["return_5d"].iloc[-1])
    ratio = current_vol / baseline_vol
    flags = {"Drawdown ≤ -10%": drawdown <= -0.10, "30-day volatility ≥ 2× baseline": ratio >= 2.0, "Five-day return ≤ -5%": return_5d <= -0.05}
    count = int(sum(flags.values()))
    return {"baseline_vol": baseline_vol, "current_drawdown": drawdown, "current_vol": current_vol, "current_5d": return_5d, "vol_ratio": ratio, "flags": flags, "signal_count": count, "stress_trigger": count >= 2, "stress_score": count / 3.0}


def z_for_confidence(c):
    return {0.95: 1.6448536269514722, 0.975: 1.959963984540054, 0.99: 2.3263478740408408}[c]


def shadow_model(confidence, proxy_cap=None, corr_strength=None, beta_multiplier=None):
    signal = signal_metrics()
    proxy_cap = st.session_state.proxy_cap if proxy_cap is None else proxy_cap
    corr_strength = st.session_state.corr_strength if corr_strength is None else corr_strength
    beta_multiplier = st.session_state.beta_multiplier if beta_multiplier is None else beta_multiplier
    base_corr = INTERNAL[POOLS].corr().to_numpy()
    ratio = float(np.clip(signal["vol_ratio"], 1.0, proxy_cap))
    betas = H["stress_beta"].to_numpy() * beta_multiplier
    stressed_annual_vol = H["base_annual_vol"].to_numpy() * np.power(ratio, betas)
    lam = corr_strength * signal["stress_score"]
    stress_corr = base_corr + lam * (1 - base_corr)
    np.fill_diagonal(stress_corr, 1.0)
    daily_vol = stressed_annual_vol / np.sqrt(252)
    cov = np.outer(daily_vol, daily_vol) * stress_corr
    dollar_vol = PORTFOLIO_VALUE_MM * float(np.sqrt(WEIGHTS @ cov @ WEIGHTS))
    z = z_for_confidence(confidence)
    pdf = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
    return {**signal, "base_corr": base_corr, "proxy_vol_ratio_capped": ratio, "betas": betas, "stressed_annual_vol": stressed_annual_vol, "correlation_lambda": lam, "stress_corr": stress_corr, "dollar_vol": dollar_vol, "var": z * dollar_vol, "cvar": dollar_vol * pdf / (1 - confidence)}


def heatmap(matrix, title):
    names = ["Prime AAA", "Alt-A AAA", "Subprime AAA", "Subprime BBB", "2007 BBB-", "CDO Mezz"]
    fig = go.Figure(go.Heatmap(z=matrix, x=names, y=names, zmin=-1, zmax=1, colorscale="RdBu_r", text=np.round(matrix, 2), texttemplate="%{text:.2f}", colorbar=dict(title="ρ")))
    return style(fig, title, 400)


if not st.session_state.accepted:
    st.title("Educational Use and Historical Context")
    st.warning("Original fictional teaching case inspired by Margin Call (2011). Mortgage pools, market proxy, return data, dialogue, and liquidation assumptions are synthetic.")
    left, right = st.columns([2.3, 1])
    with left:
        st.video(VIDEO)
    with right:
        ok = st.checkbox("I understand this is an educational simulation.")
        if st.button("Enter the case", type="primary", disabled=not ok, width="stretch"):
            st.session_state.accepted = True
            st.rerun()
    st.stop()

st.title("One Night Inside the Tail: Early-Warning Edition")
st.caption("Version 2: Acting on an external warning before internal confirmation")
timeline()
st.divider()
scene = st.session_state.scene

if scene == "intro":
    header("INTRO", "From measuring a regime to evolving a model", "Version 1 asks what changed after the crisis. Version 2 asks whether the firm should act before internal confirmation.")
    comparison = pd.DataFrame({
        "Dimension": ["Primary question", "Information timing", "External proxy", "Correlations", "Risk estimate", "Human judgment", "Decision"],
        "Version 1": ["What changed?", "After the regime", "Narrative context", "Realized sample", "Historical", "Mostly implicit", "Retrospective"],
        "Version 2": ["Act before confirmation?", "Before internal repricing", "Quantitative trigger", "Forecast, then validated", "Official plus shadow", "Explicit by character", "Locked before reveal"],
    })
    st.dataframe(comparison, hide_index=True, width="stretch")
    cols = st.columns(4)
    with cols[0]: character_card("Eric Dale", "eric", "MARKET EVIDENCE", "Proxy price, drawdown, rolling volatility, five-day return.", "Creates the observable stress score.")
    with cols[1]: character_card("Sarah Robertson", "sarah", "EVIDENCE MAPPING", "Product comparability, timing, and pool-level proxy relevance.", "Assigns documented pool sensitivities.")
    with cols[2]: character_card("Peter Sullivan", "peter", "QUANTITATIVE UPDATE", "Official volatility, observed correlations, stress score, sensitivities, weights.", "Builds forecast covariance, VaR, and CVaR.", "decisive")
    with cols[3]: character_card("Seth Bregman", "seth", "MODEL CHALLENGE", "Proxy cap, beta multiplier, correlation convergence, confidence level.", "Tests whether the conclusion survives moderate assumptions.")
    cols = st.columns(3)
    with cols[0]: character_card("Jared Cohen", "jared", "GOVERNANCE", "Official versus shadow risk, persistence, limits, challenge results.", "Applies escalation rules.", "decisive")
    with cols[1]: character_card("John Tuld", "john", "INSTITUTIONAL DECISION", "Risk range, model limits, cost of waiting, execution consequences.", "Chooses hold, selective reduction, or liquidation.", "decisive")
    with cols[2]: character_card("Sam Rogers", "sam", "EXECUTION", "Market depth, discounts, speed, sequencing, information leakage.", "Translates model choice into realized transaction cost.")
    navigation("official")

elif scene == "official":
    header("OFFICIAL MODEL", "Version 1: the approved historical calibration", "Only the 250 internal mortgage observations available at the decision date are used. Future crisis returns remain hidden.")
    confidence = st.select_slider("Confidence level", [0.95, 0.975, 0.99], value=st.session_state.confidence, format_func=lambda x: f"{x:.1%}")
    st.session_state.confidence = confidence
    official = historical_stats(portfolio_losses(INTERNAL), confidence)
    m = st.columns(4)
    for col, (label, value) in zip(m, [("Internal observations", "250"), ("One-day loss volatility", f"${official['volatility']:.1f}m"), (f"{confidence:.1%} historical VaR", f"${official['var']:.1f}m"), (f"{confidence:.1%} historical CVaR", f"${official['cvar']:.1f}m")]): col.metric(label, value)
    left, right = st.columns([1.3, 1])
    with left: st.plotly_chart(heatmap(INTERNAL[POOLS].corr().to_numpy(), "Observed internal correlation"), width="stretch", config={"displayModeBar": False})
    with right:
        character_card("Peter Sullivan", "peter", "OFFICIAL MODEL OWNER", "250 internal returns, portfolio weights, and approved historical methodology.", "Produces observed backward-looking risk estimates.", "decisive")
        st.markdown("<div class='assumption'><b>Classification:</b> Observed and backward-looking. This is Version 1's endpoint and Version 2's starting point.</div>", unsafe_allow_html=True)
    navigation("warning")

elif scene == "warning":
    header("EXTERNAL WARNING", "Eric introduces evidence outside the official model", "The proxy deteriorates before the mortgage portfolio has produced crisis observations.")
    signal = signal_metrics()
    fig = go.Figure(go.Scatter(x=PROXY["date"], y=PROXY["proxy_price"], name="External proxy", line=dict(color="#c7474b", width=3)))
    fig.add_vrect(x0=PROXY["date"].iloc[220], x1=PROXY["date"].iloc[-1], fillcolor="#f3911b", opacity=.12, line_width=0, annotation_text="Early-warning window")
    st.plotly_chart(style(fig, "External mortgage-market proxy", 420), width="stretch", config={"displayModeBar": False})
    a, b = st.columns([1, 2])
    with a: character_card("Eric Dale", "eric", "MARKET EVIDENCE", "External price, drawdown, 30-day volatility, baseline volatility, five-day return.", "Converts outside prices into three auditable warning tests.")
    with b:
        m = st.columns(3)
        m[0].metric("Drawdown", f"{signal['current_drawdown']:.1%}", "Trigger: -10%")
        m[1].metric("Volatility ratio", f"{signal['vol_ratio']:.1f}×", "Trigger: 2.0×")
        m[2].metric("Five-day return", f"{signal['current_5d']:.1%}", "Trigger: -5%")
        st.markdown("<div class='assumption'><b>Eric's update:</b> External proxy → drawdown, volatility ratio, momentum → warning tests → stress score.</div>", unsafe_allow_html=True)
    navigation("signal")

elif scene == "signal":
    header("SIGNAL TEST", "Eric's evidence activates the shadow-model process", "At least two of three warning conditions must trigger. Sarah then determines how the signal maps to the mortgage positions.")
    signal = signal_metrics()
    tests = [("Drawdown", f"{signal['current_drawdown']:.1%}", "≤ -10%", signal['flags']["Drawdown ≤ -10%"]), ("Volatility ratio", f"{signal['vol_ratio']:.1f}×", "≥ 2.0×", signal['flags']["30-day volatility ≥ 2× baseline"]), ("Five-day return", f"{signal['current_5d']:.1%}", "≤ -5%", signal['flags']["Five-day return ≤ -5%"])]
    for col, (name, observed, threshold, passed) in zip(st.columns(3), tests):
        with col:
            css = "signal-pass" if passed else "signal-fail"
            st.markdown(f"<div class='{css}'><b>{name}</b><br><br>Observed: <b>{observed}</b><br>Threshold: {threshold}<br>Status: <b>{'TRIGGERED' if passed else 'NOT TRIGGERED'}</b></div>", unsafe_allow_html=True)
    st.success(f"{signal['signal_count']} of 3 signals triggered. Stress score = {signal['stress_score']:.2f}. Shadow-model review activated.")
    left, right = st.columns([1, 2])
    with left: character_card("Sarah Robertson", "sarah", "EVIDENCE MAPPING", "Proxy relevance, product similarity, position seniority, liquidity, and timing.", "Assigns expert stress sensitivities, explicitly identified as assumptions.")
    with right:
        mapping = H[["pool", "base_annual_vol", "stress_beta"]].copy()
        mapping.columns = ["Mortgage pool", "Official annual volatility", "Sarah's proxy sensitivity β"]
        st.dataframe(mapping.style.format({"Official annual volatility":"{:.1%}", "Sarah's proxy sensitivity β":"{:.2f}"}), hide_index=True, width="stretch")
        st.caption("The β values are expert-assigned stress sensitivities, not historically estimated betas.")
    navigation("update")

elif scene == "update":
    header("MODEL UPDATE", "Show the full path from Version 1 to Version 2", "The shadow model combines observed evidence, expert mapping, quantitative transformation, challenge, and governance.")
    left, middle, right = st.columns(3)
    with left:
        st.markdown("<div class='flow'><div class='flow-title'>VERSION 1: OFFICIAL</div>Internal mortgage returns<div class='arrow'>↓</div>Observed volatility<div class='arrow'>↓</div>Observed correlations<div class='arrow'>↓</div>Historical losses<div class='arrow'>↓</div>Historical VaR and CVaR<br><br><b>Observed and backward-looking</b></div>", unsafe_allow_html=True)
    with middle:
        st.markdown("<div class='flow'><div class='flow-title'>HUMAN INPUTS</div>Eric: external warning<div class='arrow'>↓</div>Sarah: sensitivity mapping<div class='arrow'>↓</div>Peter: math update<div class='arrow'>↓</div>Seth: challenge<div class='arrow'>↓</div>Jared: escalation<div class='arrow'>↓</div>Tuld and Sam: decision and execution<br><br><b>Judgment and governance</b></div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='flow'><div class='flow-title'>VERSION 2: SHADOW</div>Proxy stress score<div class='arrow'>↓</div>Pool-specific stressed volatility<div class='arrow'>↓</div>Forecast correlation convergence<div class='arrow'>↓</div>Forward covariance<div class='arrow'>↓</div>Shadow VaR and CVaR<br><br><b>Forecast and forward-looking</b></div>", unsafe_allow_html=True)

    shadow = shadow_model(st.session_state.confidence)
    ledger = pd.DataFrame({
        "Model item": ["Proxy stress score", "Prime sensitivity", "CDO sensitivity", "Proxy volatility cap", "Correlation convergence λ", "Risk method", "Escalation threshold"],
        "Version 1": ["Not used", "Not used", "Not used", "Not used", "Not used", "Historical", "None"],
        "Character": ["Eric", "Sarah", "Sarah", "Seth", "Peter", "Peter", "Jared"],
        "Version 2": [f"{shadow['stress_score']:.2f}", f"{shadow['betas'][0]:.2f}", f"{shadow['betas'][-1]:.2f}", f"{st.session_state.proxy_cap:.1f}×", f"{shadow['correlation_lambda']:.2f}", "Parametric stress", "2× official risk"],
        "Classification": ["Observed signal", "Expert assumption", "Expert assumption", "Challenge parameter", "Stress assumption", "Method choice", "Governance rule"],
    })
    st.markdown("### Model-update ledger")
    st.dataframe(ledger, hide_index=True, width="stretch")
    with st.expander("See the exact update equations", expanded=True):
        st.latex(r"\sigma_{i,shadow}=\sigma_{i,official}\left(\frac{\sigma_{proxy,current}}{\sigma_{proxy,baseline}}\right)^{\beta_i}")
        st.latex(r"\rho_{ij,shadow}=\rho_{ij,official}+\lambda(1-\rho_{ij,official})")
        st.latex(r"\lambda=\text{correlation strength}\times\text{stress score}")
        st.write("Worked examples use the current proxy ratio and Sarah's pool sensitivities. Lower-quality pools receive a larger volatility update from the same external signal.")
    navigation("shadow")

elif scene == "shadow":
    header("SHADOW MODEL", "Peter builds; Seth challenges", "Use the controls to see whether the conclusion survives less severe assumptions.")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.session_state.proxy_cap = st.select_slider("Proxy volatility cap", [2.0, 3.0, 4.0], value=st.session_state.proxy_cap, format_func=lambda x: f"{x:.1f}×")
    with c2: st.session_state.corr_strength = st.select_slider("Correlation convergence", [0.25, 0.50, 0.75], value=st.session_state.corr_strength, format_func=lambda x: f"{x:.0%}")
    with c3: st.session_state.beta_multiplier = st.select_slider("Sensitivity multiplier", [0.75, 1.0, 1.25], value=st.session_state.beta_multiplier, format_func=lambda x: f"{x:.2f}×")
    with c4: st.session_state.confidence = st.select_slider("Confidence", [0.95, 0.975, 0.99], value=st.session_state.confidence, format_func=lambda x: f"{x:.1%}")
    official = historical_stats(portfolio_losses(INTERNAL), st.session_state.confidence)
    shadow = shadow_model(st.session_state.confidence)
    m = st.columns(4)
    m[0].metric("Official VaR", f"${official['var']:.1f}m")
    m[1].metric("Shadow VaR", f"${shadow['var']:.1f}m", f"{shadow['var']/official['var']:.1f}×")
    m[2].metric("Official CVaR", f"${official['cvar']:.1f}m")
    m[3].metric("Shadow CVaR", f"${shadow['cvar']:.1f}m", f"{shadow['cvar']/official['cvar']:.1f}×")
    left, right = st.columns(2)
    with left: character_card("Peter Sullivan", "peter", "QUANTITATIVE UPDATE", "Official volatilities, observed correlations, Eric's score, Sarah's sensitivities, portfolio weights.", "Builds forecast volatility, covariance, VaR, and CVaR.", "decisive")
    with right: character_card("Seth Bregman", "seth", "MODEL CHALLENGE", "Alternative caps, sensitivity multipliers, convergence strengths, and confidence levels.", "Tests whether escalation depends on the harshest assumptions.")
    mapping = H[["pool", "base_annual_vol"]].copy(); mapping["beta"] = shadow["betas"]; mapping["stressed_vol"] = shadow["stressed_annual_vol"]
    mapping.columns = ["Mortgage pool", "Official volatility", "Applied β", "Forecast stressed volatility"]
    st.dataframe(mapping.style.format({"Official volatility":"{:.1%}", "Applied β":"{:.2f}", "Forecast stressed volatility":"{:.1%}"}), hide_index=True, width="stretch")
    left, right = st.columns(2)
    with left: st.plotly_chart(heatmap(shadow["base_corr"], "Observed internal correlation"), width="stretch", config={"displayModeBar": False})
    with right: st.plotly_chart(heatmap(shadow["stress_corr"], "Forecast stress correlation"), width="stretch", config={"displayModeBar": False})
    navigation("decision")

elif scene == "decision":
    header("DECISION", "Govern the model, then act", "Jared applies the escalation rule. Tuld chooses the institutional response. Sam frames the execution cost.")
    official = historical_stats(portfolio_losses(INTERNAL), st.session_state.confidence)
    shadow = shadow_model(st.session_state.confidence)
    signal_persistent = shadow["signal_count"] == 3
    criteria = {
        "Shadow VaR ≥ 2× official VaR": shadow["var"] >= 2 * official["var"],
        "Shadow CVaR ≥ 2× official CVaR": shadow["cvar"] >= 2 * official["cvar"],
        "All three proxy signals triggered": signal_persistent,
        "Shadow VaR exceeds $75m portfolio limit": shadow["var"] >= 75,
    }
    cols = st.columns(3)
    with cols[0]: character_card("Jared Cohen", "jared", "GOVERNANCE", "Official and shadow risk, signal persistence, limits, and challenge results.", f"Escalates because {sum(criteria.values())} of 4 criteria are met.", "decisive")
    with cols[1]: character_card("John Tuld", "john", "INSTITUTIONAL DECISION", "Range of losses, model uncertainty, cost of waiting, and franchise consequences.", "Chooses hold, selective reduction, or accelerated liquidation.", "decisive")
    with cols[2]: character_card("Sam Rogers", "sam", "EXECUTION", "Position size, market depth, discounts, speed, sequence, and information leakage.", "Estimates the certain cost of reducing risk now.")
    st.markdown("### Jared's escalation test")
    for label, passed in criteria.items():
        (st.success if passed else st.info)(f"{'PASS' if passed else 'NOT MET'}: {label}")
    st.markdown("### Committee evidence summary")
    summary = pd.DataFrame({"Contributor":["Eric", "Sarah", "Peter", "Seth", "Jared", "Sam"], "Input":["3 of 3 warning signals", "Pool sensitivities 0.35–1.25", f"Shadow VaR ${shadow['var']:.1f}m", "Moderate-case challenge controls", f"{sum(criteria.values())} of 4 escalation rules", "Execution trade-off required"], "Classification":["Observed", "Assumption", "Forecast", "Challenge", "Governance", "Execution assumption"]})
    st.dataframe(summary, hide_index=True, width="stretch")
    choices = ["Maintain the official model and current exposures", "Reduce the most proxy-sensitive positions selectively", "Initiate an accelerated portfolio liquidation"]
    default = choices.index(st.session_state.decision) if st.session_state.decision in choices else 0
    decision = st.radio("Risk-committee decision", choices, index=default, disabled=st.session_state.decision_locked)
    rationale = st.text_area("Decision rationale and numerical reversal condition", value=st.session_state.rationale, placeholder="Example: Reduce the CDO and lower-rated subprime positions; reverse if proxy drawdown improves above -5% and volatility falls below 1.5× baseline.", disabled=st.session_state.decision_locked)
    st.caption(f"{len(rationale.strip())}/30 minimum characters")
    if not st.session_state.decision_locked:
        if st.button("Lock decision and reveal the realized regime", type="primary", disabled=len(rationale.strip()) < 30):
            st.session_state.decision = decision; st.session_state.rationale = rationale.strip(); st.session_state.decision_locked = True; goto_scene("reveal")
    else:
        navigation("reveal")

elif scene == "reveal":
    if not st.session_state.decision_locked:
        st.warning("Record and lock a decision before viewing realized crisis data.")
        if st.button("Return to decision"): goto_scene("decision")
        st.stop()
    header("EX POST REVEAL", "Validate the model evolution", "Compare Version 1, the Version 2 forecast, and the realized crisis after the decision was locked.")
    c = st.session_state.confidence
    official = historical_stats(portfolio_losses(INTERNAL), c); shadow = shadow_model(c); realized = historical_stats(portfolio_losses(FUTURE), c)
    comparison = pd.DataFrame({"Measure":["One-day loss volatility ($mm)", f"{c:.1%} VaR ($mm)", f"{c:.1%} CVaR ($mm)"], "Version 1 official":[official['volatility'],official['var'],official['cvar']], "Version 2 shadow":[shadow['dollar_vol'],shadow['var'],shadow['cvar']], "Realized crisis":[realized['volatility'],realized['var'],realized['cvar']]})
    st.dataframe(comparison.style.format({"Version 1 official":"${:,.1f}","Version 2 shadow":"${:,.1f}","Realized crisis":"${:,.1f}"}), hide_index=True, width="stretch")
    left, right = st.columns(2)
    with left: st.plotly_chart(heatmap(shadow["stress_corr"], "Forecast stress correlation"), width="stretch", config={"displayModeBar": False})
    with right: st.plotly_chart(heatmap(FUTURE[POOLS].corr().to_numpy(), "Realized crisis correlation"), width="stretch", config={"displayModeBar": False})
    st.markdown("### Locked committee decision")
    st.write(f"**Decision:** {st.session_state.decision}")
    st.write(f"**Rationale and reversal condition:** {st.session_state.rationale}")
    st.markdown("<div class='assumption'><b>Validation question:</b> Did Eric's signal, Sarah's mapping, Peter's forecast, Seth's challenge, and Jared's governance process create a useful early warning, even if the point estimates differed from realized risk?</div>", unsafe_allow_html=True)
    navigation("assignment")

elif scene == "assignment":
    header("ASSIGNMENT", "Model-evolution risk-committee memorandum", "Explain not only what the estimate became, but who contributed each input, how the update was calculated, and how the model was challenged and governed.")
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("<div class='assignment'><h3>Model reconstruction</h3><ol><li>Reproduce Version 1 official risk from 250 internal observations.</li><li>Calculate Eric's proxy warning tests and stress score.</li><li>Document Sarah's pool sensitivities as expert assumptions.</li><li>Reproduce Peter's volatility and correlation equations.</li><li>Run Seth's moderate and severe challenge cases.</li></ol></div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='assignment'><h3>Governance and decision</h3><ol><li>Apply Jared's escalation criteria.</li><li>Defend Tuld's institutional action before the reveal.</li><li>Evaluate Sam's execution trade-off.</li><li>Compare the shadow forecast with realized crisis outcomes.</li><li>State whether Version 2 improved on Version 1 and provide a numerical reversal condition.</li></ol></div>", unsafe_allow_html=True)
    st.info("Deliverable: completed workbook or notebook plus a 750–1,000 word memorandum distinguishing observed evidence, expert assumptions, forecast outputs, governance rules, locked decision, and realized validation.")
    st.markdown("### Downloadable case files")
    a,b,c,d=st.columns(4)
    a.download_button("Holdings.csv", H.to_csv(index=False), "proxy_case_holdings.csv", "text/csv", width="stretch")
    b.download_button("Internal returns.csv", INTERNAL.to_csv(index=False), "internal_mortgage_returns.csv", "text/csv", width="stretch")
    c.download_button("External proxy.csv", PROXY.to_csv(index=False), "external_proxy_early_warning.csv", "text/csv", width="stretch")
    d.download_button("Ex-post returns.csv", FUTURE.to_csv(index=False), "realized_crisis_returns.csv", "text/csv", width="stretch")
    if st.button("Reset decision for another attempt"):
        st.session_state.decision=None; st.session_state.rationale=""; st.session_state.decision_locked=False; goto_scene("intro")

