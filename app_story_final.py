"""Final presenter-only entrypoint for Blackridge.

Requires app_story_presenter.py in the same repository directory. This entrypoint
removes audience input, centers portraits, removes reverse navigation, and applies
a fully dark presentation theme to alerts and download controls.
"""
from pathlib import Path
import re

SOURCE = Path(__file__).with_name("app_story_presenter.py")
if not SOURCE.exists():
    raise FileNotFoundError("Keep app_story_presenter.py beside app_story_final.py")

code = SOURCE.read_text(encoding="utf-8")

# 1) One-way navigation: scene count plus Next only.
code = re.sub(
    r"def presenter_nav\(\):.*?(?=def nav\(next_scene=None\):)",
    '''def presenter_nav():
    i = SCENES.index(st.session_state.scene)
    counter_col, next_col = st.columns([7.5, 1.0])
    with counter_col:
        st.markdown(
            f"<div class='presenter-counter'>Scene {i + 1} of {len(SCENES)}</div>",
            unsafe_allow_html=True,
        )
    with next_col:
        if st.button(
            "Next →",
            key=f"final_next_{st.session_state.scene}",
            disabled=i == len(SCENES) - 1,
            type="primary",
            width="stretch",
        ):
            st.session_state.scene = SCENES[i + 1]
            st.rerun()


''',
    code,
    count=1,
    flags=re.S,
)

# 2) Replace the entire decision scene with a fixed presenter-led decision.
decision_scene = '''elif scene == "decision":
    scene_header("12:16 AM | Executive Committee", "The Decision", "The warning has survived challenge. Management must decide whether waiting is more dangerous than acting.")
    official = historical_stats(portfolio_losses(INTERNAL), 0.99)
    cases = challenge_cases(0.99)
    left, right = st.columns([1, 2.7])
    with left:
        st.markdown(character_html(
            "John Tuld", "Chief Executive", "john",
            "I do not need the model to be perfect. I need to know whether waiting is more dangerous than acting.",
            "A calm official estimate, a warning that survives challenge, and the cost of selling early.",
            "The institutional choice.",
            "The price of being early versus the cost of being late.",
            "decisive",
        ), unsafe_allow_html=True)
    with right:
        metrics = st.columns(4)
        metrics[0].metric("Official VaR", f"${official['var']:.1f}m")
        metrics[1].metric("Moderate warning", f"${cases['Moderate']['var']:.1f}m")
        metrics[2].metric("Central warning", f"${cases['Central']['var']:.1f}m")
        metrics[3].metric("Severe warning", f"${cases['Severe']['var']:.1f}m")
        option_cols = st.columns(3)
        options = [
            ("Hold", "High", "$0", "Wait for confirmation", "risk-high"),
            ("Reduce selectively", "Moderate", "Known but limited", "Sell CDO, BBB-, and BBB", "risk-mid"),
            ("Liquidate", "Low after sale", "Very high", "Exit every position", "risk-low"),
        ]
        for col, (name, tail, cost, focus, css) in zip(option_cols, options):
            with col:
                st.markdown(
                    f"<div class='option'><h3>{name}</h3><b>Tail exposure:</b> <span class='{css}'>{tail}</span><br><b>Immediate cost:</b> {cost}<br><br>{focus}</div>",
                    unsafe_allow_html=True,
                )
        st.markdown(
            "<div class='decision-panel'><div class='case-label'>Committee decision</div><h2>Reduce selectively before the market opens</h2><p>Cut the three most proxy-sensitive positions first. Reverse if proxy drawdown improves above -5% and volatility falls below 1.5× baseline.</p><p><b>Primary uncertainty:</b> temporary illiquidity versus lasting credit deterioration.</p></div>",
            unsafe_allow_html=True,
        )
    st.session_state.decision = "Selective reduction"
    st.session_state.rationale = "Reduce the three most proxy-sensitive positions before internal marks fully reprice."
    st.session_state.reversal = "Reverse if drawdown improves above -5% and volatility falls below 1.5× baseline."
    st.session_state.uncertainty = "Temporary illiquidity versus lasting credit deterioration."
    st.session_state.decision_locked = True
    nav("execution")

'''
code = re.sub(
    r'elif scene == "decision":.*?(?=# ---------- Scene 8 ----------)',
    decision_scene,
    code,
    count=1,
    flags=re.S,
)

# 3) Ensure later scenes never demand prior audience interaction.
for scene_name in ("execution", "validation"):
    code = re.sub(
        rf'(elif scene == "{scene_name}":)\n\s+if not st\.session_state\.decision_locked:.*?(?=\n\s+scene_header\()',
        rf'''\1
    if not st.session_state.decision_locked:
        st.session_state.decision = "Selective reduction"
        st.session_state.rationale = "Reduce the three most proxy-sensitive positions before internal marks fully reprice."
        st.session_state.reversal = "Reverse if drawdown improves above -5% and volatility falls below 1.5× baseline."
        st.session_state.uncertainty = "Temporary illiquidity versus lasting credit deterioration."
        st.session_state.decision_locked = True''',
        code,
        count=1,
        flags=re.S,
    )

# 4) Remove other audience controls and replace with narrated content.
code = re.sub(
    r'\s*st\.radio\("Eric\'s recommendation".*?\)\n',
    '\n        st.markdown("<div class=\'narrative-panel\'><b>Risk response:</b> Initiate a model review before internal marks confirm the shift.</div>", unsafe_allow_html=True)\n',
    code,
    count=1,
)
code = re.sub(
    r'\s*selected = st\.selectbox\("Inspect a mortgage pool".*?\)\n',
    '\n        selected = "CDO Mezzanine Residual"\n',
    code,
    count=1,
)
code = re.sub(
    r'\s*st\.session_state\.confidence = st\.select_slider\("Confidence level".*?\)\n',
    '\n        st.session_state.confidence = 0.99\n',
    code,
    count=1,
)
code = re.sub(
    r'\s*answers = st\.columns\(3\).*?(?=\n\s*nav\("assignment"\))',
    '\n    st.markdown("<div class=\'closing-panel\'><h3>Closing insight</h3><p>The warning was directionally correct and early enough to affect the decision. Usefulness did not require perfect prediction.</p></div>", unsafe_allow_html=True)\n',
    code,
    count=1,
    flags=re.S,
)

# 5) Remove checkbox gate and reset control.
code = re.sub(
    r'\s*ok = st\.checkbox\(.*?\)\n\s*if st\.button\("Enter Blackridge", type="primary", disabled=not ok\):',
    '\n    if st.button("Enter Blackridge", type="primary"):',
    code,
    count=1,
    flags=re.S,
)
code = re.sub(
    r'\s*if st\.button\("Reset the simulation"\):.*?st\.rerun\(\)\n',
    '\n',
    code,
    count=1,
    flags=re.S,
)

# 6) Replace pale alerts with dark narrative panels.
code = code.replace(
    'st.success("The early-warning conclusion survives the moderate case. Shadow VaR remains materially above the official estimate.")',
    'st.markdown("<div class=\'story-callout positive\'><b>Challenge result:</b> The warning survives the moderate case. Even the least severe assumptions leave risk materially above the official estimate.</div>", unsafe_allow_html=True)',
)
code = code.replace(
    'st.warning("The escalation depends on stronger correlation or sensitivity assumptions.")',
    'st.markdown("<div class=\'story-callout caution\'><b>Challenge result:</b> The warning depends on stronger assumptions.</div>", unsafe_allow_html=True)',
)
code = code.replace(
    'st.info("The shadow model did not need to predict every realized loss exactly. The relevant question is whether the warning was credible early enough to improve the institutional decision.")',
    'st.markdown("<div class=\'story-callout insight\'><b>Closing insight:</b> The warning mattered because it arrived early enough to improve the institutional decision.</div>", unsafe_allow_html=True)',
)

# 7) Final visual overrides: centered profiles and no white controls.
final_css = r'''
/* FINAL PRESENTER OVERRIDES */
.presenter-counter{color:#8fa6b8;font-size:.82rem;padding:.65rem 0;text-transform:uppercase;letter-spacing:.08em}
.portrait-card{text-align:center!important;display:flex!important;flex-direction:column!important;align-items:center!important}
.portrait-card img{display:block!important;width:220px!important;height:220px!important;max-width:90%!important;object-fit:contain!important;object-position:center!important;margin:0 auto 12px!important;background:#071521!important;border-radius:14px!important}
.person-name,.person-role{text-align:center!important;width:100%!important}
.quote{text-align:left!important;width:100%!important;box-sizing:border-box!important}
.decision-panel,.narrative-panel,.closing-panel,.story-callout{border-radius:12px;padding:15px 18px;margin:10px 0;color:#f7f3e8;border:1px solid #29465c;background:#102a43;line-height:1.45}
.decision-panel{border-left:6px solid #f3a712;background:linear-gradient(90deg,rgba(243,167,18,.12),rgba(16,42,67,.97))}
.narrative-panel,.closing-panel,.story-callout.insight{border-left:6px solid #19a7a0;background:linear-gradient(90deg,rgba(25,167,160,.12),rgba(16,42,67,.97))}
.story-callout.positive{border-left:6px solid #2ead7b;background:linear-gradient(90deg,rgba(46,173,123,.12),rgba(16,42,67,.97))}
.story-callout.caution{border-left:6px solid #f3a712;background:linear-gradient(90deg,rgba(243,167,18,.12),rgba(16,42,67,.97))}
[data-testid="stDownloadButton"] button{background:#102a43!important;color:#f7f3e8!important;border:1px solid #3b607a!important;border-radius:10px!important;min-height:44px!important}
[data-testid="stDownloadButton"] button:hover{background:#173a55!important;border-color:#19a7a0!important;color:#fff!important}
[data-testid="stDownloadButton"] button p,[data-testid="stDownloadButton"] button span{color:#f7f3e8!important}
[data-testid="stAlert"]{background:#102a43!important;color:#f7f3e8!important;border:1px solid #29465c!important}
[data-testid="stAlert"] p,[data-testid="stAlert"] div{color:#f7f3e8!important}
[data-testid="stButton"] button[kind="primary"]{background:#c7474b!important;color:#fff!important;border-color:#c7474b!important;min-height:42px!important}
'''
code = code.replace("</style>", final_css + "\n</style>", 1)

exec(compile(code, str(SOURCE), "exec"), globals(), globals())
