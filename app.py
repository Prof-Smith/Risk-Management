from __future__ import annotations

from pathlib import Path
import base64

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Blackridge Mortgage Regime Lab",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ROOT = Path(__file__).resolve().parent
VIDEO = "https://youtu.be/BLYCx_AOgUs"


@st.cache_data(show_spinner=False)
def data():
    holdings = pd.DataFrame(
        [
            ["Prime RMBS AAA", 1400, 0.012, 0.030],
            ["Alt-A RMBS AAA", 1000, 0.020, 0.055],
            ["Subprime 2006-2 AAA", 900, 0.030, 0.090],
            ["Subprime 2006-2 BBB", 600, 0.055, 0.180],
            ["Subprime 2007-1 BBB-", 500, 0.075, 0.280],
            ["CDO Mezzanine Residual", 800, 0.085, 0.350],
        ],
        columns=["pool", "exposure_mm", "calm_vol", "crisis_vol"],
    )
    holdings["weight"] = holdings["exposure_mm"] / holdings["exposure_mm"].sum()

    rng = np.random.default_rng(2007)
    n_assets = len(holdings)

    calm_corr = np.full((n_assets, n_assets), 0.22)
    np.fill_diagonal(calm_corr, 1.0)

    crisis_corr = np.full((n_assets, n_assets), 0.62)
    crisis_corr[2:, 2:] = 0.82
    np.fill_diagonal(crisis_corr, 1.0)

    calm_daily_vol = holdings["calm_vol"].to_numpy() / np.sqrt(252)
    crisis_daily_vol = holdings["crisis_vol"].to_numpy() / np.sqrt(252)

    calm_returns = rng.multivariate_normal(
        np.full(n_assets, 0.00012),
        np.outer(calm_daily_vol, calm_daily_vol) * calm_corr,
        250,
    )
    crisis_returns = rng.multivariate_normal(
        np.full(n_assets, -0.0009),
        np.outer(crisis_daily_vol, crisis_daily_vol) * crisis_corr,
        250,
    )

    for row, magnitude in zip(
        rng.choice(250, 18, replace=False),
        rng.uniform(0.010, 0.035, 18),
    ):
        crisis_returns[row] -= magnitude * np.array([0.25, 0.45, 0.70, 0.95, 1.10, 1.25])

    dates = pd.date_range("2006-07-03", periods=500, freq="B")
    returns = pd.DataFrame(
        np.vstack([calm_returns, crisis_returns]),
        columns=holdings["pool"],
    )
    returns.insert(0, "date", dates)
    returns.insert(1, "regime", ["Initial"] * 250 + ["Updated"] * 250)

    proxy_price = np.r_[
        100 * np.exp(np.cumsum(rng.normal(0, 0.0015, 250))),
        100 * np.exp(np.cumsum(rng.normal(-0.004, 0.012, 250))),
    ]
    proxy_price = proxy_price / proxy_price[0] * 100
    proxy = pd.DataFrame({"date": dates, "proxy_price": proxy_price})

    return holdings, returns, proxy


H, R, P = data()
SCENES = ["intro", "eric", "peter", "regime", "tuld", "sale", "assignment"]
LABELS = ["INTRO", "4:17", "6:08", "9:10", "12:16", "8:00", "ASSIGN"]

for key, value in {
    "accepted": False,
    "scene": "intro",
    "confidence": 0.99,
}.items():
    st.session_state.setdefault(key, value)

st.markdown(
    """
<style>
.block-container{width:calc(100vw - 28px);max-width:none!important;padding:1rem 14px!important}
.eyebrow{color:#0f7890;font-size:.72rem;font-weight:800;letter-spacing:.14em}
.ttl{font:700 1.9rem Georgia;margin:.05rem 0}.copy{font:1rem/1.42 Georgia}
.dialogue{display:flex;gap:1rem;align-items:center;border:1px solid #cbd6dc;border-radius:11px;background:#fff;padding:.85rem;min-height:164px}
.dialogue img{width:142px;height:142px;object-fit:cover;object-position:center 35%;border-radius:11px;flex:none}
.dialogue b{font-size:1.08rem;color:#102a43}.bubble{border-left:5px solid #0f7890;background:#edf5f6;padding:.8rem .9rem;font:italic 1.02rem/1.42 Georgia}
.insight{border:1px solid #cbd6dc;border-radius:11px;background:#fff;padding:18px;min-height:142px;font-size:1.05rem;line-height:1.48;box-shadow:0 3px 10px rgba(16,42,67,.05)}
.insight strong,.insight b{font-size:1.12rem;color:#102a43}
.takeaway-tile{border:1px solid #cbd6dc;border-radius:11px;background:linear-gradient(145deg,#fff,#f3f8f9);padding:18px;min-height:150px;font-size:1.03rem;line-height:1.48}
.takeaway-title{font-size:1.12rem;font-weight:800;color:#102a43;margin-bottom:8px}
.interpretation{border:1px solid #cbd6dc;border-radius:11px;background:#fff;padding:20px;min-height:155px;font-size:1.08rem;line-height:1.5}
.interpretation b{font-size:1.18rem;color:#102a43}
.assignment{border:1px solid #cbd6dc;border-radius:12px;background:#fff;padding:24px;min-height:330px;box-shadow:0 4px 14px rgba(16,42,67,.06)}
.assignment h3{font-size:1.5rem;margin:.1rem 0 .75rem;color:#102a43}.assignment li,.assignment p{font-size:1.12rem;line-height:1.62;margin-bottom:.48rem}
.assignment-note{border-left:6px solid #f3911b;background:#fff8e9;padding:18px 20px;border-radius:8px;font-size:1.08rem;line-height:1.5}
[data-testid="stMetricValue"]{font-size:1.28rem}.stButton>button{font-weight:700}
</style>
""",
    unsafe_allow_html=True,
)


def header(kicker, title, copy):
    st.markdown(
        f"<div class='eyebrow'>{kicker}</div>"
        f"<div class='ttl'>{title}</div>"
        f"<div class='copy'>{copy}</div>",
        unsafe_allow_html=True,
    )


def goto_scene(scene):
    st.session_state.scene = scene
    st.rerun()


def nav(next_scene=None):
    previous_column, next_column = st.columns([6, 1])
    index = SCENES.index(st.session_state.scene)
    if index and previous_column.button("← Previous"):
        goto_scene(SCENES[index - 1])
    if next_scene and next_column.button("Continue →", type="primary", width="stretch"):
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
    if image_path.exists():
        image = base64.b64encode(image_path.read_bytes()).decode()
        image_html = f"<img src='data:image/jpeg;base64,{image}'>"
    else:
        image_html = ""
    st.markdown(
        f"<div class='dialogue'>{image_html}<div><b>{name}</b>"
        f"<div class='bubble'>{text}</div></div></div>",
        unsafe_allow_html=True,
    )


def style(figure, title, height=390):
    figure.update_layout(
        title=title,
        height=height,
        margin=dict(l=40, r=20, t=50, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#fcfbf8",
        font=dict(size=10),
        legend=dict(orientation="h", y=1.08),
        uirevision="v6",
    )
    figure.update_yaxes(gridcolor="rgba(120,120,120,.12)")
    return figure


def losses(regime):
    regime_returns = R.loc[R["regime"].eq(regime), H["pool"]]
    portfolio_return = regime_returns.to_numpy() @ H["weight"].to_numpy()
    portfolio_value_mm = H["exposure_mm"].sum()
    return -portfolio_return * portfolio_value_mm


def stats(loss_series, confidence):
    """Excel PERCENTILE.INC-compatible historical VaR and CVaR."""
    values = np.asarray(loss_series, dtype=float)
    var = float(np.quantile(values, confidence, method="linear"))
    tail = values[values >= var]
    return var, float(tail.mean()), float(values.std(ddof=1))


def density(values, color, name):
    histogram, edges = np.histogram(values, bins=65, density=True)
    kernel = np.array([1, 2, 4, 6, 4, 2, 1], dtype=float)
    histogram = np.convolve(histogram, kernel / kernel.sum(), "same")
    centers = (edges[:-1] + edges[1:]) / 2
    fill = "rgba(15,120,144,.1)" if color == "#0f7890" else "rgba(199,71,75,.1)"
    return go.Scatter(
        x=centers,
        y=histogram,
        name=name,
        line=dict(color=color, width=3, shape="spline"),
        fill="tozeroy",
        fillcolor=fill,
    )


def calculation_audits(initial_losses, updated_losses, initial_var, updated_var, initial_cvar, updated_cvar):
    return {
        "Portfolio weights sum to 100%": bool(np.isclose(H["weight"].sum(), 1.0)),
        "Initial regime contains 250 observations": len(initial_losses) == 250,
        "Updated regime contains 250 observations": len(updated_losses) == 250,
        "Initial CVaR is at least Initial VaR": initial_cvar >= initial_var,
        "Updated CVaR is at least Updated VaR": updated_cvar >= updated_var,
    }


if not st.session_state.accepted:
    st.title("Educational Use and Historical Context")
    st.warning(
        "Original fictional teaching case inspired by Margin Call (2011). "
        "Mortgage pools, data, model, dialogue, and liquidation discounts are synthetic."
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

st.title("One Night Inside the Tail")
timeline()
st.divider()
scene = st.session_state.scene

if scene == "intro":
    header(
        "INTRO",
        "Meet the room",
        "One consolidated storyboard introduces the eight employees, their positions, and the analytical perspective each person brings to the overnight crisis.",
    )
    profile_image = ROOT / "assets" / "blackridge_employee_profiles.png"
    if profile_image.exists():
        st.image(str(profile_image), width="stretch")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='insight'><b>1. Evidence enters</b><br><br>Eric connects external mortgage pricing to a possible failure in the historical calibration. The question is whether outside prices now describe the portfolio better than the firm’s internal marks.</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='insight'><b>2. The model changes</b><br><br>Peter integrates updated volatility and dependence into the same mortgage exposures. The holdings stay fixed, but the modeled loss distribution changes.</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='insight'><b>3. The firm acts</b><br><br>Tuld escalates the result and Sam converts modeled uncertainty into realized losses. The model becomes an institutional decision.</div>", unsafe_allow_html=True)
    with st.expander("Replay the risk-management introduction"):
        st.video(VIDEO)
    nav("eric")

elif scene == "eric":
    header("4:17 PM · RISK FLOOR", "Eric questions the calibration", "External prices fall while modeled volatility rises.")
    left, right = st.columns([1.72, 1])
    portfolio_returns = R[H["pool"]].to_numpy() @ H["weight"].to_numpy()
    rolling_vol = pd.Series(portfolio_returns, index=R["date"]).rolling(30).std() * np.sqrt(252) * 100
    with left:
        figure = go.Figure()
        figure.add_trace(go.Scatter(x=P["date"], y=P["proxy_price"], name="External proxy", line=dict(color="#c7474b", width=3)))
        figure.add_trace(go.Scatter(x=rolling_vol.index, y=rolling_vol, name="Annualized vol (%)", yaxis="y2", line=dict(color="#0f7890", width=3)))
        figure.update_layout(yaxis2=dict(overlaying="y", side="right"))
        st.plotly_chart(style(figure, "External pricing and volatility", 455), width="stretch", config={"displayModeBar": False})
    with right:
        talk("Eric Dale", "eric", "concerned", "The historical window describes yesterday’s market. The external prices suggest a new regime.")
        talk("Sarah Robertson", "sarah", "concerned", "Then the external evidence must map defensibly to the mortgage pools on our books.")
    nav("peter")

elif scene == "peter":
    header("6:08 PM · QUANT DESK", "Peter updates covariance", "The same exposures produce a different distribution when volatility and dependence rise.")
    left, right = st.columns(2)
    for column, regime, title in [(left, "Initial", "Initial correlation"), (right, "Updated", "Updated correlation")]:
        with column:
            corr = R.loc[R["regime"].eq(regime), H["pool"]].corr()
            figure = go.Figure(go.Heatmap(z=corr.values, x=[x[:10] for x in corr.columns], y=[x[:10] for x in corr.index], zmin=-1, zmax=1, colorscale="RdBu_r", showscale=True))
            st.plotly_chart(style(figure, title, 360), width="stretch", config={"displayModeBar": False})
    left, right = st.columns(2)
    with left:
        talk("Seth Bregman", "seth", "concerned", "The assets did not change overnight. Why did portfolio risk change?")
    with right:
        talk("Peter Sullivan", "peter", "decisive", "Volatility and dependence changed. The same holdings now create a different loss distribution.")
    nav("regime")

elif scene == "regime":
    header("9:10 PM · RISK ROOM", "The regime multiplies tail risk", "Hover directly over any vertical line to read the measure, dollar estimate, and selected confidence level.")
    st.session_state.confidence = st.select_slider(
        "Confidence level",
        options=[0.95, 0.975, 0.99],
        value=st.session_state.confidence,
        format_func=lambda value: f"{value:.1%}",
    )
    initial = losses("Initial")
    updated = losses("Updated")
    initial_var, initial_cvar, initial_vol = stats(initial, st.session_state.confidence)
    updated_var, updated_cvar, updated_vol = stats(updated, st.session_state.confidence)

    metrics = st.columns(6)
    metric_items = [
        ("Initial VaR", initial_var),
        ("Updated VaR", updated_var),
        ("Initial CVaR", initial_cvar),
        ("Updated CVaR", updated_cvar),
        ("Initial one-day loss volatility", initial_vol),
        ("Updated one-day loss volatility", updated_vol),
    ]
    for column, (label, value) in zip(metrics, metric_items):
        column.metric(label, f"${value:.1f}m")

    figure = go.Figure([
        density(initial, "#0f7890", "Initial density"),
        density(updated, "#c7474b", "Updated density"),
    ])
    ymax = max(max(figure.data[0].y), max(figure.data[1].y))
    confidence_label = f"{st.session_state.confidence:.1%}"
    for label, value, color, dash in [
        ("Initial VaR", initial_var, "#0f7890", "dash"),
        ("Updated VaR", updated_var, "#c7474b", "dash"),
        ("Initial CVaR", initial_cvar, "#4f94a1", "dot"),
        ("Updated CVaR", updated_cvar, "#8f2230", "dot"),
    ]:
        figure.add_trace(go.Scatter(
            x=[value, value], y=[0, ymax], mode="lines", name=label,
            line=dict(color=color, width=4, dash=dash),
            customdata=[[label, value, confidence_label], [label, value, confidence_label]],
            hovertemplate="<b>%{customdata[0]}</b><br>$%{customdata[1]:.1f} million<br>Confidence: %{customdata[2]}<extra></extra>",
        ))
    figure.update_layout(hovermode="closest")
    figure.update_xaxes(title="One-day portfolio loss ($m)")
    st.plotly_chart(style(figure, "Mortgage portfolio loss distribution with hoverable VaR and CVaR", 455), width="stretch", config={"displayModeBar": False})
    st.caption("Dashed = VaR. Dotted = CVaR. Hover over a line for the estimate.")
    nav("tuld")

elif scene == "tuld":
    header("12:16 AM · EXECUTIVE COMMITTEE", "The model reaches Tuld", "Peter compares the original base-case model with the current post-regime-shift model.")
    base_losses = losses("Initial")
    current_losses = losses("Updated")
    base_var, base_cvar, base_vol = stats(base_losses, st.session_state.confidence)
    current_var, current_cvar, current_vol = stats(current_losses, st.session_state.confidence)

    st.markdown("### Base case versus current regime")
    summary = st.columns(6)
    items = [
        ("Base-case VaR", base_var, None),
        ("Current VaR", current_var, current_var / base_var),
        ("Base-case CVaR", base_cvar, None),
        ("Current CVaR", current_cvar, current_cvar / base_cvar),
        ("Base-case one-day loss volatility", base_vol, None),
        ("Current one-day loss volatility", current_vol, current_vol / base_vol),
    ]
    for column, (label, value, multiple) in zip(summary, items):
        column.metric(label, f"${value:.1f}m", None if multiple is None else f"×{multiple:.1f}", delta_color="inverse")

    left, right = st.columns(2, gap="large")
    with left:
        figure = go.Figure(go.Bar(x=["Base case", "Current regime"], y=[base_var, current_var], marker_color=["#0f7890", "#c7474b"], text=[f"${base_var:.1f}m", f"${current_var:.1f}m"], textposition="outside"))
        figure.update_yaxes(title="One-day loss threshold ($m)", range=[0, current_var * 1.28])
        st.plotly_chart(style(figure, "VaR comparison: base case vs current regime", 355), width="stretch", config={"displayModeBar": False})
    with right:
        figure = go.Figure(go.Bar(x=["Base case", "Current regime"], y=[base_cvar, current_cvar], marker_color=["#5c99a5", "#8f2230"], text=[f"${base_cvar:.1f}m", f"${current_cvar:.1f}m"], textposition="outside"))
        figure.update_yaxes(title="Average loss beyond VaR ($m)", range=[0, current_cvar * 1.28])
        st.plotly_chart(style(figure, "CVaR comparison: base case vs current regime", 355), width="stretch", config={"displayModeBar": False})
    nav("sale")

elif scene == "sale":
    header("8:00 AM · TRADING FLOOR", "Sam executes the fire sale", "Synthetic discounts convert modeled risk into realized execution loss.")
    discounts = np.array([0.06, 0.12, 0.20, 0.32, 0.45, 0.55])
    sale = H.copy()
    sale["loss"] = sale["exposure_mm"] * discounts
    figure = go.Figure(go.Bar(y=sale["pool"], x=sale["loss"], orientation="h", marker_color=["#0f7890", "#318a98", "#7f9692", "#d69c35", "#ca6a45", "#c7474b"], text=[f"${x:.0f}m" for x in sale["loss"]], textposition="outside"))
    figure.update_xaxes(title="Synthetic liquidation loss ($m)")
    left, right = st.columns([1.72, 1])
    with left:
        st.plotly_chart(style(figure, "Fire-sale loss by mortgage pool", 475), width="stretch", config={"displayModeBar": False})
    with right:
        talk("Sam Rogers", "sam", "concerned", "The model describes the tail. The fire sale turns uncertainty into a certain loss at today’s distressed prices.")
        st.markdown(f"<div class='takeaway-tile'><div class='takeaway-title'>Sam’s execution problem</div>The synthetic sale realizes <b>${sale['loss'].sum():,.0f} million</b> in losses.</div>", unsafe_allow_html=True)
    nav("assignment")

elif scene == "assignment":
    header(
        "ASSIGNMENT",
        "Risk-committee memorandum",
        "Rebuild the portfolio-loss calculation in Excel or Python, reconcile the results with the app, and evaluate the liquidation decision.",
    )

    confidence = st.select_slider(
        "Confidence level for reconciliation",
        options=[0.95, 0.975, 0.99],
        value=st.session_state.confidence,
        format_func=lambda value: f"{value:.1%}",
        key="assignment_confidence",
    )
    st.session_state.confidence = confidence

    initial_losses = losses("Initial")
    updated_losses = losses("Updated")
    initial_var, initial_cvar, initial_vol = stats(initial_losses, confidence)
    updated_var, updated_cvar, updated_vol = stats(updated_losses, confidence)

    st.markdown("### Rebuild and reconcile the model")
    reconciliation = pd.DataFrame(
        {
            "Measure": [
                "Observations",
                "One-day loss volatility ($mm)",
                f"{confidence:.1%} historical VaR ($mm)",
                f"{confidence:.1%} historical CVaR ($mm)",
                "CVaR tail observations",
            ],
            "Initial": [
                len(initial_losses),
                initial_vol,
                initial_var,
                initial_cvar,
                int((initial_losses >= initial_var).sum()),
            ],
            "Updated": [
                len(updated_losses),
                updated_vol,
                updated_var,
                updated_cvar,
                int((updated_losses >= updated_var).sum()),
            ],
        }
    )
    st.dataframe(reconciliation, hide_index=True, width="stretch")

    with st.expander("How to reproduce the calculations in Excel", expanded=True):
        st.markdown(
            """
**1. Calculate portfolio weights**

`Exposure ÷ Total exposure`

Excel: `=B2/SUM($B$2:$B$7)`

**2. Calculate each daily portfolio return**

Excel: `=SUMPRODUCT(asset_returns,portfolio_weights)`

**3. Convert portfolio return into dollar loss**

Excel: `=-5200*portfolio_return`

The portfolio value is $5,200 million, so the result is expressed in millions of dollars.

**4. Calculate historical VaR**

Excel: `=PERCENTILE.INC(loss_range,confidence_level)`

Use the first 250 observations for the Initial regime and the final 250 observations for the Updated regime.

**5. Calculate historical CVaR**

Excel: `=AVERAGEIF(loss_range,">="&VaR_cell,loss_range)`

**6. Reconcile the results**

The Excel workbook or Python notebook and the Streamlit app should produce the same VaR, CVaR, and one-day loss-volatility values.
"""
        )

    if confidence == 0.99:
        st.warning(
            "With 250 observations, 99% CVaR is based on only three extreme losses in each regime. "
            "Treat the estimate as informative but statistically fragile."
        )

    with st.expander("Model audit checks"):
        audits = calculation_audits(
            initial_losses,
            updated_losses,
            initial_var,
            updated_var,
            initial_cvar,
            updated_cvar,
        )
        for label, passed in audits.items():
            st.success(label) if passed else st.error(label)

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown(
            """
<div class='assignment'><h3>Quantitative analysis</h3><ol>
<li><b>Portfolio construction:</b> Calculate each mortgage pool’s exposure weight and confirm that the weights sum to 100%.</li>
<li><b>Daily loss construction:</b> Use SUMPRODUCT to calculate portfolio return and multiply by negative $5,200 million.</li>
<li><b>Base-case risk:</b> Calculate 95%, 97.5%, and 99% historical VaR and CVaR using the first 250 observations.</li>
<li><b>Current-regime risk:</b> Repeat the calculations using the final 250 observations.</li>
<li><b>Dependence and magnitude:</b> Compare one-day loss volatility, correlation matrices, and the change multiples.</li>
</ol></div>
""",
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            """
<div class='assignment'><h3>Risk judgment</h3><ol>
<li><b>External evidence:</b> Explain why the market proxy challenges the original calibration.</li>
<li><b>Interpretation:</b> Distinguish what VaR reveals from what CVaR reveals.</li>
<li><b>Execution:</b> Evaluate the liquidation order and the trade-off among speed, price, and market impact.</li>
<li><b>Model limitation:</b> Explain the thin-tail problem created by only 250 observations.</li>
<li><b>Recommendation:</b> State what the risk committee should do and what evidence would reverse the recommendation.</li>
</ol></div>
""",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<div class='assignment-note'><b>Deliverable:</b> Submit the completed workbook or notebook plus a <b>750–1,000 word risk-committee memorandum</b>. The memorandum must cite the calculated base-case and current-regime VaR and CVaR estimates, explain the regime shift in plain language, distinguish modeled from realized loss, and defend a course of action.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("### Case data files")
    c1, c2, c3 = st.columns(3)
    c1.download_button("Download mortgage_pool_holdings.csv", H.to_csv(index=False), "mortgage_pool_holdings.csv", "text/csv", width="stretch")
    c2.download_button("Download mortgage_pool_returns.csv", R.to_csv(index=False), "mortgage_pool_returns.csv", "text/csv", width="stretch")
    c3.download_button("Download external_market_proxy.csv", P.to_csv(index=False), "external_market_proxy.csv", "text/csv", width="stretch")

