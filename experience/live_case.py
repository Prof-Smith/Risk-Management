from __future__ import annotations

import streamlit as st

from components.case_experience import (
    render_briefing,
    render_commitment,
    render_debrief,
    render_evidence_room,
    render_shock_room,
)
from services.session_manager import move_to

PHASES = ["briefing", "evidence", "commit", "shock", "debrief"]
PHASE_LABELS = {
    "briefing": "Briefing",
    "evidence": "Evidence Room",
    "commit": "Decision Desk",
    "shock": "Shock Room",
    "debrief": "Board Defense",
}


def _initialize_case(case: dict) -> None:
    if st.session_state.get("active_experience_case") != case["id"]:
        st.session_state.active_experience_case = case["id"]
        st.session_state.case_phase = "briefing"
        for key in (
            "initial_decision", "initial_confidence", "final_decision",
            "final_confidence", "shock_active", "defense_text"
        ):
            st.session_state.pop(key, None)


def _progress() -> None:
    current = st.session_state.case_phase
    st.progress((PHASES.index(current) + 1) / len(PHASES))
    cols = st.columns(len(PHASES))
    for col, phase in zip(cols, PHASES):
        with col:
            label = PHASE_LABELS[phase]
            st.caption(f"● {label}" if phase == current else label)


def _next_phase() -> None:
    index = PHASES.index(st.session_state.case_phase)
    if index < len(PHASES) - 1:
        st.session_state.case_phase = PHASES[index + 1]


def _previous_phase() -> None:
    index = PHASES.index(st.session_state.case_phase)
    if index > 0:
        st.session_state.case_phase = PHASES[index - 1]


def render(case: dict) -> None:
    _initialize_case(case)
    st.caption("02 / LIVE CASE EXPERIENCE")
    st.title(case["title"])
    _progress()
    st.divider()

    phase = st.session_state.case_phase
    ready = True
    if phase == "briefing":
        ready = render_briefing(case)
    elif phase == "evidence":
        ready = render_evidence_room(case)
    elif phase == "commit":
        ready = render_commitment(case)
    elif phase == "shock":
        ready = render_shock_room(case)
    elif phase == "debrief":
        render_debrief(case)

    st.divider()
    left, center, right = st.columns([1, 2, 1])
    with left:
        if phase != "briefing" and st.button("← Previous room", use_container_width=True):
            _previous_phase()
            st.rerun()
    with center:
        if phase == "debrief":
            if st.button("Enter the case gallery", type="primary", use_container_width=True):
                move_to("case_gallery")
                st.rerun()
    with right:
        if phase != "debrief":
            if st.button("Continue →", type="primary", use_container_width=True, disabled=not ready):
                _next_phase()
                st.rerun()
