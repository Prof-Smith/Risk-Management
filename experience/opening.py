import streamlit as st
from services.session_manager import move_to

VIDEO_URL = "https://youtu.be/BLYCx_AOgUs"


def render() -> None:
    st.markdown("## RISK MANAGEMENT DECISION LAB")
    st.title("When does risk become a decision?")
    st.write(
        "Enter the course as a decision-maker. Commit to a judgment, expose the "
        "assumptions, apply a shock, and identify what would reverse the decision."
    )
    st.video(VIDEO_URL)
    left, right = st.columns([2, 1])
    with left:
        st.text_input(
            "In one sentence, what makes a risk measure decision-useful?",
            key="opening_response",
        )
    with right:
        st.metric("Experience", "50 minutes")
        st.metric("Core sequence", "Decide → Shock → Reverse")
    if st.button("Enter the lab", type="primary", use_container_width=True):
        move_to("risk_map")
        st.rerun()
