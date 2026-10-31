import streamlit as st

from components.risk_visuals import render_risk_lab
from services.session_manager import move_to

RISKS = {
    "Market": {"question": "What moves?", "scope": "Prices, rates, volatility, and correlation", "icon": "↗"},
    "Credit": {"question": "Who fails?", "scope": "Default, migration, recovery, and concentration", "icon": "◎"},
    "Liquidity": {"question": "What cannot be exited?", "scope": "Depth, spreads, liquidation time, and funding", "icon": "≋"},
    "Operational": {"question": "What breaks?", "scope": "People, processes, systems, and controls", "icon": "⚙"},
    "Model": {"question": "What is wrong?", "scope": "Assumptions, estimation, validation, and governance", "icon": "△"},
    "Systemic": {"question": "What propagates?", "scope": "Networks, common exposures, and feedback loops", "icon": "⌘"},
}


def _select_risk(name: str) -> None:
    st.session_state.selected_risk = name


def render() -> None:
    st.caption("01 / INTEGRATED RISK LAB")
    st.title("Risk is a connected system")
    st.write(
        "Choose a risk channel. The workbench below updates to show a standard visual, "
        "a decision metric, and a controllable stress test."
    )

    selected = st.session_state.get("selected_risk", "Market")
    columns = st.columns(6)
    for column, (name, details) in zip(columns, RISKS.items()):
        with column:
            active = name == selected
            st.markdown(
                f"<div style='font-size:1.7rem;text-align:center;color:{'#18A7A0' if active else '#9FB0BE'}'>"
                f"{details['icon']}</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                name,
                key=f"risk_{name}",
                type="primary" if active else "secondary",
                use_container_width=True,
                on_click=_select_risk,
                args=(name,),
            ):
                pass
            st.caption(details["question"])

    selected = st.session_state.get("selected_risk", "Market")
    st.divider()
    render_risk_lab(selected)

    left, right = st.columns([3, 1])
    with left:
        st.info(
            f"Active channel: **{selected} risk**. Use the controls above the visual to alter the scenario. "
            "All starter data are synthetic and intended to demonstrate the interaction pattern."
        )
    with right:
        if st.button("Send this shock to the flagship case", type="primary", use_container_width=True):
            st.session_state.case_origin_risk = selected
            move_to("live_case")
            st.rerun()
