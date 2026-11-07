from __future__ import annotations

from pathlib import Path
import base64
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="One Night Inside the Tail",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ROOT = Path(__file__).resolve().parent
VIDEO = "https://youtu.be/BLYCx_AOgUs"
BUILD_ID = "PRESENTER-2026-11-07-1015"

# ---------- Reproducible fictional case data ----------
@st.cache_data(show_spinner=False)
def build_case_data():
    holdings = pd.DataFrame(
        [
            ["Prime RMBS AAA", 1400, 0.012, 0.35, 0.06],
            ["Alt-A RMBS AAA", 1000, 0.020, 0.55, 0.12],
            ["Subprime 2006-2 AAA", 900, 0.030, 0.75, 0.20],
            ["Subprime 2006-2 BBB", 600, 0.055, 0.95, 0.32],
            ["Subprime 2007-1 BBB-", 500, 0.075, 1.10, 0.45],
            ["CDO Mezzanine Residual", 800, 0.085, 1.25, 0.55],
        ],
        columns=["pool", "exposure_mm", "base_annual_vol", "stress_beta", "liquidation_discount"],
    )
    holdings["weight"] = holdings["exposure_mm"] / holdings["exposure_mm"].sum()

    rng = np.random.default_rng(2007)
    n = len(holdings)
    base_corr = np.full((n, n), 0.22)
    np.fill_diagonal(base_corr, 1.0)
    base_daily_vol = holdings["base_annual_vol"].to_numpy() / np.sqrt(252)
    calm = rng.multivariate_normal(
        np.full(n, 0.00012), np.outer(base_daily_vol, base_daily_vol) * base_corr, 250
    )

    crisis_vol = np.array([0.030, 0.055, 0.090, 0.180, 0.280, 0.350])
    crisis_corr = np.full((n, n), 0.62)
    crisis_corr[2:, 2:] = 0.82
    np.fill_diagonal(crisis_corr, 1.0)
    crisis_daily_vol = crisis_vol / np.sqrt(252)
    crisis = rng.multivariate_normal(
        np.full(n, -0.0009), np.outer(crisis_daily_vol, crisis_daily_vol) * crisis_corr, 250
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

SCENES = ["warning", "relevance", "rebuild", "challenge", "tail", "escalation", "decision", "execution", "validation", "assignment"]
TIMES = ["4:17 PM", "5:02 PM", "6:08 PM", "7:34 PM", "9:10 PM", "11:26 PM", "12:16 AM", "6:30 AM", "AFTER OPEN", "ASSIGN"]

for key, value in {
    "accepted": False,
    "scene": "warning",
    "confidence": 0.99,
    "proxy_cap": 4.0,
    "corr_strength": 0.50,
    "beta_multiplier": 1.0,
    "decision": None,
    "rationale": "",
    "reversal": "",
    "uncertainty": "",
    "decision_locked": False,
}.items():
    st.session_state.setdefault(key, value)

# ---------- Visual system ----------
st.markdown(
    """
<style>
:root{--ink:#f7f3e8;--muted:#aebbc5;--navy:#071521;--surface:#102a43;--teal:#19a7a0;--blue:#3e8bc9;--amber:#f3a712;--red:#c7474b;--green:#2ead7b}
.stApp{background:linear-gradient(180deg,#071521 0%,#0b1e2d 100%);color:var(--ink)}
.block-container{max-width:none!important;padding:1.25rem 2rem 2rem!important}
h1,h2,h3{font-family:Georgia,serif;color:var(--ink)!important}.stMarkdown,p,label{color:var(--ink)}
.case-label{color:var(--teal);font-size:.72rem;font-weight:800;letter-spacing:.18em;text-transform:uppercase}
.hero-title{font:700 2.35rem/1.1 Georgia;color:var(--ink);margin:.15rem 0}.hero-sub{color:var(--muted);font-size:1.05rem}
.timebar{display:flex;justify-content:space-between;gap:8px;margin:.7rem 0 1.2rem}.timechip{flex:1;padding:8px 5px;border-top:3px solid #29465c;text-align:center;color:#718392;font-size:.72rem}.timechip.on{border-color:var(--amber);color:var(--ink);font-weight:800}
.scene-grid{display:grid;grid-template-columns:minmax(190px,22%) 1fr minmax(235px,24%);gap:18px;align-items:start}
.portrait-card,.insight-card,.glass{background:rgba(16,42,67,.86);border:1px solid #29465c;border-radius:16px;padding:18px;box-shadow:0 12px 30px rgba(0,0,0,.18)}
.portrait-card img{width:100%;height:210px;object-fit:contain;object-position:center;background:#071521;border-radius:12px}
.person-name{font:700 1.4rem Georgia;color:var(--ink);margin-top:12px}.person-role{color:var(--teal);font-size:.78rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
.quote{border-left:5px solid var(--amber);padding:12px 14px;margin-top:14px;background:rgba(243,167,18,.08);font:italic 1.04rem/1.45 Georgia;color:var(--ink)}
.insight-title{color:var(--amber);font-size:.75rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;margin:8px 0 4px}.insight-body{color:var(--ink);line-height:1.45}
.badge{display:inline-block;padding:3px 8px;border-radius:99px;font-size:.65rem;font-weight:800;letter-spacing:.08em;margin-right:5px}.obs{background:#0f6f6a;color:#dff}.calc{background:#245b87;color:#eaf5ff}.assume{background:#805d0b;color:#fff4ce}.later{background:#7e2a2d;color:#ffe8e8}
.kpi{background:rgba(16,42,67,.82);border:1px solid #29465c;border-radius:12px;padding:14px}.kpi-label{color:var(--muted);font-size:.74rem}.kpi-value{color:var(--ink);font:700 1.55rem Georgia}.kpi-note{color:var(--teal);font-size:.72rem}
.option{background:rgba(16,42,67,.86);border:1px solid #29465c;border-radius:14px;padding:16px;min-height:205px}.option h3{margin-top:0}.risk-high{color:#ff8589}.risk-mid{color:#f3c15d}.risk-low{color:#66d3a5}
[data-testid="stMetric"]{background:rgba(16,42,67,.82);border:1px solid #29465c;border-radius:12px;padding:12px}[data-testid="stMetricLabel"],[data-testid="stMetricValue"]{color:var(--ink)!important}
[data-testid="stDataFrame"]{border:1px solid #29465c;border-radius:12px;overflow:hidden}.stButton>button{font-weight:800;border-radius:10px}.stExpander{border-color:#29465c!important;background:rgba(16,42,67,.55)}
@media(max-width:900px){.scene-grid{grid-template-columns:1fr}.timebar{overflow-x:auto}.timechip{min-width:90px}}

/* Presenter mode: compact, readable, and navigable at 1920x1080 */
.hero-title{font-size:2rem}.hero-sub{font-size:.95rem}.timebar{margin:.35rem 0 .5rem}.timechip{padding:5px 3px}.portrait-card,.insight-card,.glass{padding:14px}.quote{font-size:.96rem}.option{min-height:170px;padding:14px}
</style>
""",
    unsafe_allow_html=True,
)

# ---------- Calculation helpers ----------
def portfolio_losses(frame):
    return -PORTFOLIO_VALUE_MM * (frame[POOLS].to_numpy() @ WEIGHTS)


def historical_stats(losses, confidence):
    x = np.asarray(losses, dtype=float)
    var = float(np.quantile(x, confidence, method="linear"))
    tail = x[x >= var]
    return {"vol": float(x.std(ddof=1)), "var": var, "cvar": float(tail.mean()), "tail_count": int(tail.size)}


def signal_metrics():
    baseline_vol = float(PROXY.loc[PROXY.index < 220, "return"].std(ddof=1) * np.sqrt(252))
    drawdown = float(PROXY["drawdown"].iloc[-1])
    current_vol = float(PROXY["rolling_vol_30d"].iloc[-1])
    return_5d = float(PROXY["return_5d"].iloc[-1])
    ratio = current_vol / baseline_vol
    flags = {"drawdown": drawdown <= -0.10, "volatility": ratio >= 2.0, "momentum": return_5d <= -0.05}
    count = int(sum(flags.values()))
    return {"baseline_vol": baseline_vol, "drawdown": drawdown, "current_vol": current_vol, "return_5d": return_5d, "ratio": ratio, "flags": flags, "count": count, "score": count / 3.0}


def z_value(c):
    return {0.95: 1.6448536269514722, 0.975: 1.959963984540054, 0.99: 2.3263478740408408}[c]


def shadow_model(confidence, cap=None, corr=None, beta=None):
    sig = signal_metrics()
    cap = st.session_state.proxy_cap if cap is None else cap
    corr = st.session_state.corr_strength if corr is None else corr
    beta = st.session_state.beta_multiplier if beta is None else beta
    base_corr = INTERNAL[POOLS].corr().to_numpy()
    ratio = float(np.clip(sig["ratio"], 1.0, cap))
    betas = H["stress_beta"].to_numpy() * beta
    stressed_vol = H["base_annual_vol"].to_numpy() * np.power(ratio, betas)
    lam = corr * sig["score"]
    stress_corr = base_corr + lam * (1 - base_corr)
    np.fill_diagonal(stress_corr, 1.0)
    daily = stressed_vol / np.sqrt(252)
    cov = np.outer(daily, daily) * stress_corr
    dollar_vol = PORTFOLIO_VALUE_MM * float(np.sqrt(WEIGHTS @ cov @ WEIGHTS))
    z = z_value(confidence)
    pdf = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
    return {**sig, "ratio_capped": ratio, "betas": betas, "stressed_vol": stressed_vol, "lambda": lam, "base_corr": base_corr, "stress_corr": stress_corr, "dollar_vol": dollar_vol, "var": z * dollar_vol, "cvar": dollar_vol * pdf / (1 - confidence)}


def challenge_cases(confidence):
    cases = {
        "Moderate": (2.0, 0.25, 0.75),
        "Central": (3.0, 0.50, 1.00),
        "Severe": (4.0, 0.75, 1.25),
    }
    return {name: shadow_model(confidence, *params) for name, params in cases.items()}


def execution_table(strategy):
    sale = H.copy()
    if strategy == "Maintain exposures":
        sale["selected"] = False
    elif strategy == "Selective reduction":
        sale["selected"] = sale["pool"].isin(POOLS[-3:])
    else:
        sale["selected"] = True
    sale["realized_loss_mm"] = np.where(sale["selected"], sale["exposure_mm"] * sale["liquidation_discount"], 0.0)
    return sale

# ---------- Visual helpers ----------
def portrait_path(key, state="concerned"):
    return ROOT / "assets" / "expressions" / f"{key}_{state}.jpg"


def encoded_portrait(key, state="concerned"):
    path = portrait_path(key, state)
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode()


def character_html(name, role, key, quote, sees, contributes, uncertain, state="concerned"):
    encoded = encoded_portrait(key, state)
    img = f"<img src='data:image/jpeg;base64,{encoded}'>" if encoded else ""
    return f"""
    <div class='portrait-card'>{img}<div class='person-name'>{name}</div><div class='person-role'>{role}</div><div class='quote'>{quote}</div></div>
    <div class='insight-card'>
      <div class='insight-title'>What this character sees</div><div class='insight-body'>{sees}</div>
      <div class='insight-title'>What this character contributes</div><div class='insight-body'>{contributes}</div>
      <div class='insight-title'>What remains uncertain</div><div class='insight-body'>{uncertain}</div>
    </div>"""


def scene_header(kicker, title, subtitle):
    st.markdown(f"<div class='case-label'>{kicker}</div><div class='hero-title'>{title}</div><div class='hero-sub'>{subtitle}</div>", unsafe_allow_html=True)


def style_fig(fig, title, height=410):
    fig.update_layout(title=title, height=height, margin=dict(l=40, r=20, t=55, b=40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0d2233", font=dict(color="#f7f3e8", size=11), legend=dict(orientation="h", y=1.08), uirevision="story-v1")
    fig.update_xaxes(gridcolor="rgba(255,255,255,.08)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,.08)")
    return fig


def heatmap(matrix, title):
    names = ["Prime AAA", "Alt-A AAA", "Subprime AAA", "Subprime BBB", "2007 BBB-", "CDO Mezz"]
    fig = go.Figure(go.Heatmap(z=matrix, x=names, y=names, zmin=-1, zmax=1, colorscale=[[0,"#153c52"],[.5,"#f4e6c8"],[1,"#b32832"]], text=np.round(matrix, 2), texttemplate="%{text:.2f}", colorbar=dict(title="ρ")))
    return style_fig(fig, title, 390)


def presenter_nav():
    i = SCENES.index(st.session_state.scene)
    previous_col, center_col, next_col = st.columns([1.15, 5.7, 1.15])
    with previous_col:
        if st.button("← Previous", key=f"top_prev_{st.session_state.scene}", disabled=i == 0, width="stretch"):
            st.session_state.scene = SCENES[i - 1]
            st.rerun()
    with center_col:
        st.caption(f"Scene {i + 1} of {len(SCENES)} · Presenter controls remain visible in full-screen view")
    with next_col:
        if st.button("Next →", key=f"top_next_{st.session_state.scene}", disabled=i == len(SCENES) - 1, type="primary", width="stretch"):
            st.session_state.scene = SCENES[i + 1]
            st.rerun()

def nav(next_scene=None):
    # Navigation is intentionally rendered at the top so it remains accessible in full-screen presentation mode.
    return None


def timeline():
    i = SCENES.index(st.session_state.scene)
    chips = "".join(f"<div class='timechip {'on' if j == i else ''}'>{time}</div>" for j, time in enumerate(TIMES))
    st.markdown(f"<div class='timebar'>{chips}</div>", unsafe_allow_html=True)
    st.progress((i + 1) / len(SCENES))

# ---------- Entry gate ----------
if not st.session_state.accepted:
    st.markdown("<div class='case-label'>Blackridge Capital | Risk Simulation</div><div class='hero-title'>One Night Inside the Tail</div><div class='hero-sub'>An external warning. A model under pressure. One decision before the market opens.</div>", unsafe_allow_html=True)
    hero = ROOT / "assets" / "blackridge_employee_profiles.png"
    if hero.exists():
        st.image(str(hero), width="stretch")
    st.warning("This fictional learning simulation is inspired by institutional risk-management questions explored in Margin Call. The firm, portfolio, proxy, model, dialogue, and transaction estimates are synthetic.")
    with st.expander("Watch the case introduction"):
        st.video(VIDEO)
    if st.button("Enter Blackridge", type="primary"):
        st.session_state.accepted = True
        st.rerun()
    st.stop()

st.markdown("<div class='case-label'>Blackridge Capital | One Night Inside the Tail</div><div class='hero-title'>An external warning. A model under pressure.</div><div class='hero-sub'>One decision before the market opens.</div>", unsafe_allow_html=True)
timeline()
presenter_nav()
st.divider()
scene = st.session_state.scene

# ---------- Scene 1 ----------
if scene == "warning":
    scene_header("4:17 PM | Risk Floor", "The First Warning", "The approved model remains calm. The external market does not.")
    sig = signal_metrics()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=PROXY["date"], y=PROXY["proxy_price"], name="External mortgage proxy", line=dict(color="#f3a712", width=4)))
    fig.add_trace(go.Scatter(x=PROXY["date"], y=PROXY["running_peak"], name="Running peak", line=dict(color="#19a7a0", width=2, dash="dot")))
    fig.add_vrect(x0=PROXY["date"].iloc[220], x1=PROXY["date"].iloc[-1], fillcolor="#c7474b", opacity=.14, line_width=0, annotation_text="Warning window")
    fig.add_annotation(x=PROXY["date"].iloc[-1], y=PROXY["proxy_price"].iloc[-1], text="Decision point", showarrow=True, arrowcolor="#f3a712")
    center = style_fig(fig, "The market moves before the marks", 455)
    st.markdown("<div class='scene-grid'>", unsafe_allow_html=True)
    left, mid, right = st.columns([1.05, 2.25, 1.2])
    with left:
        st.markdown(character_html("Eric Dale", "Former Head of Risk", "eric", "The internal marks are stable because they are late. The external market is already moving.", "A proxy drawdown, a volatility surge, and a sharp five-day decline.", "Evidence that the approved historical window may be stale.", "Whether the proxy truly maps to Blackridge's six positions."), unsafe_allow_html=True)
    with mid:
        st.plotly_chart(center, width="stretch", config={"displayModeBar": False})
        k = st.columns(3)
        k[0].metric("Proxy drawdown", f"{sig['drawdown']:.1%}", "Trigger: -10%")
        k[1].metric("30-day vol ratio", f"{sig['ratio']:.1f}×", "Trigger: 2.0×")
        k[2].metric("Five-day return", f"{sig['return_5d']:.1%}", "Trigger: -5%")
    with right:
        st.markdown("<div class='insight-card'><span class='badge obs'>OBSERVED</span><div class='insight-title'>Evidence available now</div><div class='insight-body'>External proxy price, drawdown, rolling volatility, and five-day momentum.</div><div class='insight-title'>The question</div><div class='insight-body'>Temporary disturbance or the first evidence of a new regime?</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='glass'><b>Risk response:</b><br>Initiate a model review before internal marks confirm the shift.</div>", unsafe_allow_html=True)
    with st.expander("Model mechanics: Eric's signal measures"):
        st.latex(r"r_t^{proxy}=P_t/P_{t-1}-1")
        st.latex(r"DD_t=P_t/\max(P_1,\ldots,P_t)-1")
        st.latex(r"\sigma_{30,t}=STDEV.S(r_{t-29},\ldots,r_t)\sqrt{252}")
    nav("relevance")

# ---------- Scene 2 ----------
elif scene == "relevance":
    scene_header("5:02 PM | Chief Risk Office", "Is the Proxy Relevant?", "A market signal is not yet a portfolio model.")
    left, right = st.columns([1, 2.7])
    with left:
        st.markdown(character_html("Sarah Robertson", "Chief Risk Officer", "sarah", "A market signal is not a portfolio model. Show me how it reaches the positions we actually own.", "One proxy and six positions with different seniority, credit quality, leverage, and liquidity.", "A documented pool-level sensitivity mapping.", "The sensitivities are expert judgments, not estimated historical betas."), unsafe_allow_html=True)
    with right:
        st.markdown("### From senior exposure to leveraged residual")
        selected = "CDO Mezzanine Residual"
        table = H[["pool", "exposure_mm", "weight", "base_annual_vol", "stress_beta"]].copy()
        table.columns = ["Mortgage pool", "Exposure ($mm)", "Weight", "Official vol", "Proxy sensitivity β"]
        st.dataframe(table.style.format({"Exposure ($mm)":"${:,.0f}","Weight":"{:.2%}","Official vol":"{:.1%}","Proxy sensitivity β":"{:.2f}"}), hide_index=True, width="stretch")
        row = H.loc[H["pool"].eq(selected)].iloc[0]
        rationale = {
            "Prime RMBS AAA":"Highest seniority and lowest assumed sensitivity to the proxy.",
            "Alt-A RMBS AAA":"More vulnerable collateral than Prime, but senior in structure.",
            "Subprime 2006-2 AAA":"Senior tranche with direct subprime collateral exposure.",
            "Subprime 2006-2 BBB":"Lower structural protection and stronger spread sensitivity.",
            "Subprime 2007-1 BBB-":"Weaker vintage, lower rating, and limited liquidity.",
            "CDO Mezzanine Residual":"Highly leveraged residual exposure with the strongest assumed response.",
        }[selected]
        st.markdown(f"<div class='glass'><span class='badge assume'>ASSUMED</span><h3>{selected}</h3><p>{rationale}</p><b>β = {row['stress_beta']:.2f}</b></div>", unsafe_allow_html=True)
    with st.expander("Evidence audit"):
        st.write("Exposure and portfolio weight are observed case inputs. Official volatility is calculated from the approved historical model. Proxy sensitivity is an expert-assigned stress assumption.")
    nav("rebuild")

# ---------- Scene 3 ----------
elif scene == "rebuild":
    scene_header("6:08 PM | Quant Desk", "Rebuilding the Model", "Peter turns evidence and judgment into a forward risk estimate.")
    shadow = shadow_model(st.session_state.confidence)
    left, right = st.columns([1, 2.7])
    with left:
        st.markdown(character_html("Peter Sullivan", "Quantitative Risk Analyst", "peter", "The proxy does not tell us the answer. It tells us the historical calibration may be the wrong starting point.", "Eric's stress score, Sarah's sensitivities, official volatilities, observed correlations, and portfolio weights.", "Stressed volatility, forecast correlation, covariance, VaR, and CVaR.", "Forecast correlation is an assumption, not a newly observed fact.", "decisive"), unsafe_allow_html=True)
    with right:
        stages = st.columns(5)
        labels = [("External warning", "3 signals"), ("Pool sensitivity", "βᵢ"), ("Stressed volatility", "σᵢ"), ("Correlation convergence", "ρᵢⱼ"), ("Forward covariance", "Σ")]
        for col, (title, symbol) in zip(stages, labels):
            with col:
                st.markdown(f"<div class='glass' style='text-align:center;min-height:125px'><div class='insight-title'>{title}</div><div class='kpi-value'>{symbol}</div></div>", unsafe_allow_html=True)
        mapping = H[["pool", "base_annual_vol", "stress_beta"]].copy()
        mapping["stressed_vol"] = shadow["stressed_vol"]
        mapping.columns = ["Mortgage pool", "Official vol", "β", "Forecast stressed vol"]
        st.dataframe(mapping.style.format({"Official vol":"{:.1%}","β":"{:.2f}","Forecast stressed vol":"{:.1%}"}), hide_index=True, width="stretch")
        e1, e2 = st.columns(2)
        with e1:
            st.markdown("<div class='glass'><span class='badge calc'>CALCULATED</span><h3>Prime AAA</h3><p>Same warning, low sensitivity.</p><div class='kpi-value'>1.2% → 1.9%</div></div>", unsafe_allow_html=True)
        with e2:
            st.markdown("<div class='glass'><span class='badge calc'>CALCULATED</span><h3>CDO residual</h3><p>Same warning, high sensitivity.</p><div class='kpi-value'>8.5% → 48.1%</div></div>", unsafe_allow_html=True)
    with st.expander("Show the model mechanics"):
        st.latex(r"\sigma_{i,stress}=\sigma_{i,base}\left(\frac{\sigma_{proxy,current}}{\sigma_{proxy,baseline}}\right)^{\beta_i}")
        st.latex(r"\rho_{ij,stress}=\rho_{ij,base}+\lambda(1-\rho_{ij,base})")
        st.code("stressed_vol = base_vol * proxy_ratio ** sensitivity\nstress_corr = base_corr + lambda_value * (1 - base_corr)\nstress_cov = np.outer(stressed_daily_vol, stressed_daily_vol) * stress_corr", language="python")
    nav("challenge")

# ---------- Scene 4 ----------
elif scene == "challenge":
    scene_header("7:34 PM | Quant Desk", "Challenge the Assumptions", "If the warning vanishes under moderate assumptions, the story is fragile.")
    left, right = st.columns([1, 2.7])
    with left:
        st.markdown(character_html("Seth Bregman", "Associate Risk Analyst", "seth", "If the conclusion disappears when we weaken one assumption, we do not have a warning. We have a fragile story.", "Alternative proxy caps, sensitivity multipliers, correlation strengths, and confidence levels.", "An independent robustness test.", "Whether the central estimate survives a moderate challenge."), unsafe_allow_html=True)
    with right:
        st.session_state.confidence = 0.99
        cases = challenge_cases(0.99)
        official = historical_stats(portfolio_losses(INTERNAL), st.session_state.confidence)
        cols = st.columns(3)
        for col, name in zip(cols, ["Moderate", "Central", "Severe"]):
            case = cases[name]
            with col:
                st.markdown(f"<div class='glass'><div class='case-label'>{name}</div><div class='insight-title'>VaR</div><div class='kpi-value'>${case['var']:.1f}m</div><div class='kpi-note'>{case['var']/official['var']:.1f}× official</div><div class='insight-title'>CVaR</div><div class='kpi-value'>${case['cvar']:.1f}m</div><div class='insight-title'>Avg. forecast correlation</div><div class='kpi-value'>{(case['stress_corr'].sum()-len(POOLS))/(len(POOLS)*(len(POOLS)-1)):.2f}</div></div>", unsafe_allow_html=True)
        if cases["Moderate"]["var"] >= 2 * official["var"]:
            st.success("The early-warning conclusion survives the moderate case. Shadow VaR remains materially above the official estimate.")
        else:
            st.warning("The escalation depends on stronger correlation or sensitivity assumptions.")
    nav("tail")

# ---------- Scene 5 ----------
elif scene == "tail":
    scene_header("9:10 PM | Risk Room", "The Tail Takes Shape", "The same portfolio now has two defensible descriptions.")
    official_losses = portfolio_losses(INTERNAL)
    official = historical_stats(official_losses, st.session_state.confidence)
    shadow = shadow_model(st.session_state.confidence)
    rng = np.random.default_rng(91)
    simulated_shadow = rng.normal(0, shadow["dollar_vol"], 25000)
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=official_losses, histnorm="probability density", opacity=.58, name="Official historical", marker_color="#19a7a0", nbinsx=55))
    fig.add_trace(go.Histogram(x=simulated_shadow, histnorm="probability density", opacity=.48, name="Shadow forecast", marker_color="#f3a712", nbinsx=75))
    fig.add_vline(x=official["var"], line_color="#19a7a0", line_dash="dash", annotation_text="Official VaR")
    fig.add_vline(x=shadow["var"], line_color="#f3a712", line_dash="dash", annotation_text="Shadow VaR")
    fig.update_layout(barmode="overlay")
    left, mid, right = st.columns([1, 2.2, 1])
    with left:
        st.markdown(character_html("Peter Sullivan", "Quantitative Risk Analyst", "peter", "The approved model describes the history we have.", "The official loss distribution.", "A forward stress estimate.", "How closely the forecast will match realized outcomes.", "decisive"), unsafe_allow_html=True)
    with mid:
        st.plotly_chart(style_fig(fig, "Official and shadow loss distributions", 470), width="stretch", config={"displayModeBar": False})
        m = st.columns(4)
        m[0].metric("Official VaR", f"${official['var']:.1f}m")
        m[1].metric("Shadow VaR", f"${shadow['var']:.1f}m")
        m[2].metric("Official CVaR", f"${official['cvar']:.1f}m")
        m[3].metric("Shadow CVaR", f"${shadow['cvar']:.1f}m")
    with right:
        st.markdown(character_html("Seth Bregman", "Associate Risk Analyst", "seth", "The shadow model describes the environment the proxy suggests we are entering.", "A challenged range, not one dramatic point estimate.", "A robustness conclusion.", "Whether management should act before confirmation."), unsafe_allow_html=True)
    with st.expander("Technical audit"):
        st.latex(r"\Sigma_{shadow}=D_{stress}R_{stress}D_{stress}")
        st.latex(r"VaR_c=z_cV_0\sqrt{w^\top\Sigma_{shadow}w}")
    nav("escalation")

# ---------- Scene 6 ----------
elif scene == "escalation":
    scene_header("11:26 PM | Division Office", "Escalation", "An unofficial estimate can still become an institutional obligation.")
    official = historical_stats(portfolio_losses(INTERNAL), st.session_state.confidence)
    shadow = shadow_model(st.session_state.confidence)
    criteria = [
        ("Shadow VaR ≥ 2× official VaR", shadow["var"] >= 2 * official["var"], f"{shadow['var']/official['var']:.1f}×"),
        ("Shadow CVaR ≥ 2× official CVaR", shadow["cvar"] >= 2 * official["cvar"], f"{shadow['cvar']/official['cvar']:.1f}×"),
        ("Three external warnings triggered", shadow["count"] == 3, f"{shadow['count']} of 3"),
        ("Shadow VaR exceeds $75m limit", shadow["var"] >= 75, f"${shadow['var']:.1f}m"),
    ]
    left, right = st.columns([1, 2.7])
    with left:
        st.markdown(character_html("Jared Cohen", "Division Head", "jared", "A shadow model is not an official model. But if the evidence is strong enough, ignoring it becomes a governance decision.", "The challenged shadow range, signal persistence, limits, and official risk.", "A rule for institutional escalation.", "The executive action management will choose.", "decisive"), unsafe_allow_html=True)
    with right:
        for label, passed, value in criteria:
            color = "#2ead7b" if passed else "#718392"
            status = "MET" if passed else "NOT MET"
            st.markdown(f"<div class='glass' style='margin-bottom:10px;border-left:6px solid {color}'><b>{status}</b> · {label}<span style='float:right;font-family:monospace'>{value}</span></div>", unsafe_allow_html=True)
        met = sum(p for _, p, _ in criteria)
        st.markdown(f"<div class='glass' style='text-align:center'><div class='case-label'>Escalation result</div><div class='hero-title'>{met} of 4 criteria met</div><div class='hero-sub'>ESCALATE TO EXECUTIVE COMMITTEE</div></div>", unsafe_allow_html=True)
    nav("decision")

# ---------- Scene 7 ----------
elif scene == "decision":
    scene_header("12:16 AM | Executive Committee", "The Decision", "The room has one question: is waiting more dangerous than acting?")
    official = historical_stats(portfolio_losses(INTERNAL), 0.99)
    cases = challenge_cases(0.99)
    left, right = st.columns([1, 2.7])
    with left:
        st.markdown(character_html("John Tuld", "Chief Executive", "john", "I do not need the model to be perfect. I need to know whether waiting is more dangerous than acting.", "A calm official model, a warning that survives challenge, and the cost of selling early.", "The institutional choice.", "The price of being early versus the cost of being late.", "decisive"), unsafe_allow_html=True)
    with right:
        k = st.columns(4)
        k[0].metric("Official VaR", f"${official['var']:.1f}m")
        k[1].metric("Moderate warning", f"${cases['Moderate']['var']:.1f}m")
        k[2].metric("Central warning", f"${cases['Central']['var']:.1f}m")
        k[3].metric("Severe warning", f"${cases['Severe']['var']:.1f}m")
        options = st.columns(3)
        cards = [
            ("Hold", "High", "$0", "Wait for confirmation", "risk-high"),
            ("Reduce selectively", "Moderate", "Known but limited", "Sell CDO, BBB-, and BBB", "risk-mid"),
            ("Liquidate", "Low after sale", "Very high", "Exit every position", "risk-low"),
        ]
        for col, (name, tail, cost, focus, css) in zip(options, cards):
            with col:
                st.markdown(f"<div class='option'><h3>{name}</h3><b>Tail exposure:</b> <span class='{css}'>{tail}</span><br><b>Immediate cost:</b> {cost}<br><br>{focus}</div>", unsafe_allow_html=True)
        st.markdown("<div class='glass' style='border-left:6px solid #f3a712'><div class='case-label'>Committee decision</div><h2>Reduce selectively before the market opens</h2><p>Cut the three most proxy-sensitive positions first. Reverse if the proxy drawdown improves above -5% and its volatility falls below 1.5× baseline.</p><p><b>Primary uncertainty:</b> whether external prices represent temporary illiquidity or a lasting credit regime.</p></div>", unsafe_allow_html=True)
    # Presenter-led: no audience input is required.
    st.session_state.decision = "Selective reduction"
    st.session_state.rationale = "Reduce the three most proxy-sensitive positions before internal marks fully reprice."
    st.session_state.reversal = "Reverse if drawdown improves above -5% and volatility falls below 1.5× baseline."
    st.session_state.uncertainty = "Temporary illiquidity versus lasting credit deterioration."
    st.session_state.decision_locked = True
    nav("execution")

# ---------- Scene 8 ----------
elif scene == "execution":
    if not st.session_state.decision_locked:
        st.session_state.decision = "Selective reduction"
        st.session_state.rationale = "Reduce the three most proxy-sensitive positions before internal marks fully reprice."
        st.session_state.reversal = "Reverse if drawdown improves above -5% and volatility falls below 1.5× baseline."
        st.session_state.uncertainty = "Temporary illiquidity versus lasting credit deterioration."
        st.session_state.decision_locked = True
    scene_header("6:30 AM | Trading Floor", "The Cost of Acting", "Execution turns uncertainty into a certain transaction loss.")
    sale = execution_table(st.session_state.decision)
    fig = go.Figure(go.Bar(x=sale["realized_loss_mm"], y=sale["pool"], orientation="h", marker_color=np.where(sale["selected"], "#c7474b", "#29465c"), text=[f"${v:.0f}m" if v else "Not sold" for v in sale["realized_loss_mm"]], textposition="outside"))
    fig.update_xaxes(title="Modeled execution loss ($mm)")
    left, mid, right = st.columns([1, 2.2, 1])
    with left:
        st.markdown(character_html("Sam Rogers", "Head of Trading", "sam", "The model describes what might happen. Execution determines what we make certain.", "Market depth, discounts, speed, sequence, and information leakage.", "A feasible trade plan and estimated execution loss.", "How the market responds once Blackridge starts selling."), unsafe_allow_html=True)
    with mid:
        st.plotly_chart(style_fig(fig, f"Execution plan: {st.session_state.decision}", 470), width="stretch", config={"displayModeBar": False})
    with right:
        total = sale["realized_loss_mm"].sum()
        st.markdown(f"<div class='insight-card'><span class='badge assume'>ASSUMED</span><div class='insight-title'>Positions sold</div><div class='kpi-value'>{int(sale['selected'].sum())} of 6</div><div class='insight-title'>Modeled execution loss</div><div class='kpi-value'>${total:,.0f}m</div><div class='insight-title'>Central trade-off</div><div class='insight-body'>Selling reduces uncertain future exposure but produces a certain present loss.</div></div>", unsafe_allow_html=True)
    nav("validation")

# ---------- Scene 9 ----------
elif scene == "validation":
    if not st.session_state.decision_locked:
        st.session_state.decision = "Selective reduction"
        st.session_state.rationale = "Reduce the three most proxy-sensitive positions before internal marks fully reprice."
        st.session_state.reversal = "Reverse if drawdown improves above -5% and volatility falls below 1.5× baseline."
        st.session_state.uncertainty = "Temporary illiquidity versus lasting credit deterioration."
        st.session_state.decision_locked = True
    scene_header("After the Open | Validation", "What Actually Happened?", "The subsequent mortgage observations are revealed only after the decision.")
    official = historical_stats(portfolio_losses(INTERNAL), st.session_state.confidence)
    shadow = shadow_model(st.session_state.confidence)
    realized = historical_stats(portfolio_losses(FUTURE), st.session_state.confidence)
    comparison = pd.DataFrame({
        "Measure":["One-day loss volatility ($mm)", f"{st.session_state.confidence:.1%} VaR ($mm)", f"{st.session_state.confidence:.1%} CVaR ($mm)"],
        "Official model":[official["vol"], official["var"], official["cvar"]],
        "Shadow forecast":[shadow["dollar_vol"], shadow["var"], shadow["cvar"]],
        "Realized crisis":[realized["vol"], realized["var"], realized["cvar"]],
    })
    st.dataframe(comparison.style.format({"Official model":"${:,.1f}","Shadow forecast":"${:,.1f}","Realized crisis":"${:,.1f}"}), hide_index=True, width="stretch")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(heatmap(shadow["stress_corr"], "Forecast stress correlation"), width="stretch", config={"displayModeBar":False})
    with right:
        st.plotly_chart(heatmap(FUTURE[POOLS].corr().to_numpy(), "Realized crisis correlation"), width="stretch", config={"displayModeBar":False})
    st.markdown(f"<div class='glass'><span class='badge later'>REALIZED LATER</span><h3>Locked committee decision</h3><b>{st.session_state.decision}</b><p>{st.session_state.rationale}</p><b>Reversal:</b> {st.session_state.reversal}<br><b>Primary uncertainty:</b> {st.session_state.uncertainty}</div>", unsafe_allow_html=True)
    st.info("The shadow model did not need to predict every realized loss exactly. The relevant question is whether the warning was credible early enough to improve the institutional decision.")
    st.markdown("<div class='glass'><h3>Closing insight</h3><p>The warning was directionally correct and early enough to affect the decision. The shadow estimate did not need to predict every realized loss exactly to be useful.</p></div>", unsafe_allow_html=True)
    nav("assignment")

# ---------- Assignment ----------
elif scene == "assignment":
    scene_header("Assignment | Risk Committee", "Complete the Record", "Reconstruct the model, defend the locked choice, and audit the forecast against realized outcomes.")
    left, right = st.columns(2)
    with left:
        st.markdown("<div class='glass'><h3>Technical model</h3><ol><li>Official historical volatility, correlation, VaR, and CVaR</li><li>Proxy drawdown, volatility ratio, and five-day return</li><li>Pool sensitivity mapping</li><li>Shadow volatility, correlation, covariance, VaR, and CVaR</li><li>Moderate, central, and severe challenge cases</li><li>Execution loss under the locked strategy</li></ol></div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='glass'><h3>750–1,000 word memorandum</h3><ol><li>Official-model conclusion</li><li>External-warning evidence</li><li>Proxy relevance and mapping</li><li>Shadow-model construction</li><li>Challenge and governance</li><li>Locked decision and execution consequences</li><li>Ex post validation</li><li>Numerical reversal condition</li></ol></div>", unsafe_allow_html=True)
    st.markdown("### Evidence classification")
    evidence = pd.DataFrame({"Input or output":["Internal returns", "Proxy price and signals", "Pool sensitivities", "Stressed correlation", "Shadow VaR/CVaR", "Future mortgage returns"], "Classification":["Observed", "Observed / calculated", "Assumed", "Assumed / calculated", "Forecast", "Realized later"]})
    st.dataframe(evidence, hide_index=True, width="stretch")
    st.markdown("### Case files")
    a,b,c,d=st.columns(4)
    a.download_button("Holdings.csv", H.to_csv(index=False), "proxy_case_holdings.csv", "text/csv", width="stretch")
    b.download_button("Internal returns.csv", INTERNAL.to_csv(index=False), "internal_mortgage_returns.csv", "text/csv", width="stretch")
    c.download_button("External proxy.csv", PROXY.to_csv(index=False), "external_proxy_early_warning.csv", "text/csv", width="stretch")
    d.download_button("Ex-post returns.csv", FUTURE.to_csv(index=False), "realized_crisis_returns.csv", "text/csv", width="stretch")
    if st.button("Reset the simulation"):
        for key in ["decision", "rationale", "reversal", "uncertainty"]:
            st.session_state[key] = None if key == "decision" else ""
        st.session_state.decision_locked = False
        st.session_state.scene = "warning"
        st.rerun()
