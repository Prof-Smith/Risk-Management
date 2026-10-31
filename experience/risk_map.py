import streamlit as st
from services.session_manager import move_to

RISKS = {
    "Market": ("What moves?", "Volatility, rates, prices, and correlations"),
    "Credit": ("Who fails?", "Default, migration, recovery, and concentration"),
    "Liquidity": ("What cannot be exited?", "Depth, spreads, liquidation time, and funding"),
    "Operational": ("What breaks?", "People, processes, systems, and controls"),
    "Model": ("What is wrong?", "Assumptions, estimation, validation, and governance"),
    "Systemic": ("What propagates?", "Networks, common exposures, and feedback loops"),
}


def render() -> None:
    st.caption("01 / INTEGRATED RISK MAP")
    st.title("Risk is a connected system")
    st.write("Select a domain to connect the concept, model, and professional decision.")
    cols = st.columns(3)
    for index, (name, (question, scope)) in enumerate(RISKS.items()):
        with cols[index % 3]:
            with st.container(border=True):
                st.subheader(name)
                st.markdown(f"**{question}**")
                st.caption(scope)
                if st.button(f"Explore {name}", key=f"risk_{name}", use_container_width=True):
                    st.session_state.selected_risk = name
    selected = st.session_state.get("selected_risk", "Market")
    st.info(f"Selected domain: **{selected}**. The flagship case combines market, liquidity, and model risk.")
    if st.button("Enter the flagship case", type="primary"):
        move_to("live_case")
        st.rerun()
