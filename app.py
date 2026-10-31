from __future__ import annotations

import streamlit as st

from experience import case_gallery, closing, faculty_mode, live_case, opening, risk_map
from services.case_loader import available_cases, load_case
from services.session_manager import initialize_session, move_to, reset_experience

st.set_page_config(
    page_title="Risk Management Decision Lab",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

initialize_session()

STAGES = {
    "opening": opening.render,
    "risk_map": risk_map.render,
    "live_case": lambda: live_case.render(load_case(st.session_state.case_id)),
    "case_gallery": lambda: case_gallery.render(available_cases()),
    "faculty_mode": faculty_mode.render,
    "closing": closing.render,
}

with st.sidebar:
    st.caption("FACILITATOR CONTROLS")
    st.toggle("Facilitator mode", key="facilitator_mode")
    if st.session_state.facilitator_mode:
        selected = st.selectbox(
            "Experience stage",
            list(STAGES),
            index=list(STAGES).index(st.session_state.stage),
            format_func=lambda value: value.replace("_", " ").title(),
        )
        if selected != st.session_state.stage:
            move_to(selected)
            st.rerun()
        st.selectbox("Active case", available_cases(), key="case_id")
        if st.button("Reset experience", use_container_width=True):
            reset_experience()
            st.rerun()

renderer = STAGES.get(st.session_state.stage)
if renderer is None:
    st.error("Unknown experience stage. The session has been reset.")
    reset_experience()
    st.rerun()
renderer()
