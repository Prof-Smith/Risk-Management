import streamlit as st
from services.session_manager import reset_experience


def render() -> None:
    st.caption("05 / CLOSING")
    st.title("What would change your mind?")
    st.write(
        "A strong risk course teaches students to make a decision, expose its assumptions, "
        "survive a shock, and state the condition that reverses the recommendation."
    )
    st.text_area("Which element is most transferable to your finance course?", key="closing_response")
    st.link_button(
        "Explore the Risk Management repository",
        "https://github.com/Prof-Smith/Risk-Management",
        use_container_width=True,
    )
    if st.button("Restart"):
        reset_experience()
        st.rerun()
