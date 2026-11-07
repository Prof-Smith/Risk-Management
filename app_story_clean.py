"""Clean presenter entrypoint.

This file reads the existing app_story_presenter.py, applies presentation-only fixes,
and executes the result. It preserves all calculations and scenes while removing the
back button, light alert bands, white download buttons, and reset control.
"""
from pathlib import Path

SOURCE = Path(__file__).with_name("app_story_presenter.py")
if not SOURCE.exists():
    raise FileNotFoundError("app_story_presenter.py must remain beside app_story_clean.py")

code = SOURCE.read_text(encoding="utf-8")

# One-way presenter navigation: scene number plus Next only.
nav_start = code.index("def presenter_nav():")
nav_end = code.index("def nav(next_scene=None):", nav_start)
clean_nav = '''def presenter_nav():
    i = SCENES.index(st.session_state.scene)
    counter_col, next_col = st.columns([7.4, 1.0])
    with counter_col:
        st.markdown(
            f"<div class='presenter-counter'>Scene {i + 1} of {len(SCENES)}</div>",
            unsafe_allow_html=True,
        )
    with next_col:
        if st.button(
            "Next →",
            key=f"clean_next_{st.session_state.scene}",
            disabled=i == len(SCENES) - 1,
            type="primary",
            width="stretch",
        ):
            st.session_state.scene = SCENES[i + 1]
            st.rerun()


'''
code = code[:nav_start] + clean_nav + code[nav_end:]

# Replace the pale challenge alert with a dark story panel.
code = code.replace(
'''        if cases["Moderate"]["var"] >= 2 * official["var"]:
            st.success("The early-warning conclusion survives the moderate case. Shadow VaR remains materially above the official estimate.")
        else:
            st.warning("The escalation depends on stronger correlation or sensitivity assumptions.")''',
'''        if cases["Moderate"]["var"] >= 2 * official["var"]:
            st.markdown(
                "<div class='story-callout positive'><b>Challenge result:</b> The warning survives the moderate case. Even the least severe assumptions leave risk materially above the official estimate.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='story-callout caution'><b>Challenge result:</b> The warning depends on stronger correlation or sensitivity assumptions.</div>",
                unsafe_allow_html=True,
            )'''
)

# Replace the pale validation alert.
code = code.replace(
'''    st.info("The shadow model did not need to predict every realized loss exactly. The relevant question is whether the warning was credible early enough to improve the institutional decision.")''',
'''    st.markdown(
        "<div class='story-callout insight'><b>Closing insight:</b> The shadow model did not need to predict every realized loss exactly. The warning mattered because it arrived early enough to improve the institutional decision.</div>",
        unsafe_allow_html=True,
    )'''
)

# Remove the bottom reset control from the presenter ending.
reset_block = '''    if st.button("Reset the simulation"):
        for key in ["decision", "rationale", "reversal", "uncertainty"]:
            st.session_state[key] = None if key == "decision" else ""
        st.session_state.decision_locked = False
        st.session_state.scene = "warning"
        st.rerun()
'''
code = code.replace(reset_block, "")

# Inject dark styling for download controls and any remaining Streamlit alerts.
clean_css = r'''
/* Clean presenter controls */
.presenter-counter{color:#8fa6b8;font-size:.82rem;padding:.6rem 0;text-transform:uppercase;letter-spacing:.08em}
.story-callout{border-radius:12px;padding:15px 18px;margin:10px 0 2px;color:#f7f3e8;border:1px solid #29465c;background:#102a43;line-height:1.45}
.story-callout.positive{border-left:6px solid #2ead7b;background:linear-gradient(90deg,rgba(46,173,123,.14),rgba(16,42,67,.96))}
.story-callout.caution{border-left:6px solid #f3a712;background:linear-gradient(90deg,rgba(243,167,18,.14),rgba(16,42,67,.96))}
.story-callout.insight{border-left:6px solid #19a7a0;background:linear-gradient(90deg,rgba(25,167,160,.14),rgba(16,42,67,.96))}
/* Dark file-download controls */
[data-testid="stDownloadButton"] button{background:#102a43!important;color:#f7f3e8!important;border:1px solid #3b607a!important;border-radius:10px!important;min-height:44px!important}
[data-testid="stDownloadButton"] button:hover{background:#173a55!important;border-color:#19a7a0!important;color:#fff!important}
[data-testid="stDownloadButton"] button p,[data-testid="stDownloadButton"] button span{color:#f7f3e8!important}
/* No pale alert bands */
[data-testid="stAlert"]{background:#102a43!important;color:#f7f3e8!important;border:1px solid #29465c!important}
[data-testid="stAlert"] p,[data-testid="stAlert"] div{color:#f7f3e8!important}
/* Compact, dark forward navigation */
[data-testid="stButton"] button[kind="primary"]{background:#c7474b!important;color:#fff!important;border-color:#c7474b!important;min-height:42px!important}
'''
code = code.replace("</style>", clean_css + "\n</style>", 1)

exec(compile(code, str(SOURCE), "exec"), globals(), globals())
