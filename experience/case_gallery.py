import streamlit as st
from services.case_loader import load_case
from services.session_manager import move_to


def render(case_ids: list[str]) -> None:
    st.caption("03 / CASE GALLERY")
    st.title("One architecture, multiple risk decisions")
    columns = st.columns(2)
    for index, case_id in enumerate(case_ids):
        case = load_case(case_id)
        with columns[index % 2]:
            with st.container(border=True):
                st.subheader(case["title"])
                st.caption(" + ".join(case["risk_domains"]))
                st.write(case["decision_prompt"])
                st.markdown(f"**Reversal target:** {case['reversal_target']}")
                if st.button("Run this case", key=case_id, use_container_width=True):
                    st.session_state.case_id = case_id
                    move_to("live_case")
                    st.rerun()
    if st.button("Continue to faculty design mode", type="primary"):
        move_to("faculty_mode")
        st.rerun()
