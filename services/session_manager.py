import streamlit as st

DEFAULTS = {
    "stage": "opening",
    "case_id": "portfolio_tail_risk",
    "facilitator_mode": False,
    "shock_active": False,
}


def initialize_session() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)


def move_to(stage: str) -> None:
    st.session_state.stage = stage


def reset_experience() -> None:
    for key in list(st.session_state):
        del st.session_state[key]
    initialize_session()
