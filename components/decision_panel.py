import streamlit as st


def decision_panel(case: dict) -> None:
    with st.container(border=True):
        st.subheader("Commit before the reveal")
        st.radio(
            case["decision_prompt"],
            case["decision_choices"],
            horizontal=True,
            key="initial_decision",
        )
        st.slider("Decision confidence", 0, 100, 60, key="decision_confidence")
