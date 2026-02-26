"""
Smart Timetable Builder – Streamlit front-end.

Clean rebuild of the main app:
- Stable Streamlit layout (no backend code leaked into UI)
- Dark, colorful, beginner‑friendly design
- Uses the existing solver / storage / PDF modules
"""

from __future__ import annotations

import copy
from datetime import timedelta
from typing import Dict, List, Tuple

import activity_logger as logger
from activity_logger import Activities

import numpy as np
import pandas as pd
import streamlit as st

from models import Class, ClassPriorityConfig, ClassSubject, SchoolConfig, Teacher
import plotly.express as px

from pdf_export import (
    export_class_timetables_pdf,
    export_teacher_timetables_pdf,
    flat_to_class_timetables,
)
from solver.engine import invert_to_teacher_timetable, solve_timetable
from solver.rotation import generate_rotations
from storage import (
    append_history,
    clear_base_timetable,
    clear_demo_loaded,
    clear_scenario_state,
    is_demo_loaded,
    load_base_timetable,
    load_classes,
    load_config,
    load_history,
    load_scenario_state,
    load_teachers,
    save_base_timetable,
    save_classes,
    save_config,
    save_scenario_state,
    save_teachers,
    set_demo_loaded,
)


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

ANIMATION_CSS = """
<style>
    /* GitHub / Medium‑style dark UI */
    .main {
        background-color: #0d1117;
        color: #f0f6fc;
    }
    .main .block-container {
        padding-top: 32px;
        padding-bottom: 32px;
    }
    h1, h2, h3 {
        color: #f0f6fc !important;
    }
    p, span, label, .stMarkdown {
        color: #c9d1d9 !important;
    }

    [data-testid="stSidebar"] {
        background-color: #010409;
        border-right: 1px solid #30363d;
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] label {
        color: #e6edf3 !important;
    }

    /* Tabs */
    .stTabs {
        background-color: transparent;
        padding: 6px 8px;
        border-radius: 10px;
    }
    .stTabs > div > div { background-color: transparent; }
    .stTabs [data-baseweb="tab-list"]{
        background-color: #0d1117;
        border-radius: 10px;
        padding: 4px;
        border: 1px solid #30363d;
        box-shadow: 0 0 0 1px rgba(240,246,252,0.02);
        transition: all 0.15s ease;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #8b949e;
        border-radius: 6px;
        transition: all 0.15s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff;
        background-color: #161b22;
    }
    .stTabs [aria-selected="true"] {
        background-color: #161b22;
        color: #ffffff !important;
        box-shadow: 0 0 0 1px #f0f6fc;
    }

    /* Toasts */
    .toast-item {
        font-size: 13px;
        color: #e6edf3;
        max-width: 320px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        border-radius: 999px;
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 4px 10px;
        animation: toastFadeIn 0.2s ease-out;
    }
    @keyframes toastFadeIn {
        from { opacity: 0; transform: translateY(-3px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .toast-msg { flex: 1; }
    .toast-countdown { font-size: 11px; color: #8b949e; min-width: 24px; }

    /* Buttons */
    button {
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        border-radius: 6px !important;
        border: 1px solid #30363d !important;
    }
    button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.4);
    }
    button:active { transform: translateY(0); box-shadow: none; }
    .stButton button[kind="primary"] {
        background-color: #238636;
        color: #ffffff;
        border-color: #2ea043 !important;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #2ea043;
        border-color: #3fb950 !important;
    }
    .stButton button[kind="primary"]:active {
        background-color: #196c2e;
        border-color: #238636 !important;
    }

    /* Cards / expanders */
    .stExpander {
        animation: cardFadeIn 0.2s ease-out;
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
    }
    @keyframes cardFadeIn {
        from { opacity: 0; transform: translateY(2px); }
        to   { opacity: 1; transform: translateY(0); }
    }
</style>
"""


st.set_page_config(
    page_title="Smart Timetable Builder",
    page_icon="📅",
    layout="wide",
)
st.markdown(ANIMATION_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers / session state
# ---------------------------------------------------------------------------

Timetable = Dict[Tuple[str, int, int], Tuple[str, str]]


def deep_copy_tt(tt: Timetable | None) -> Timetable | None:
    return copy.deepcopy(tt) if tt is not None else None


def _shorten(text: str, max_len: int = 20) -> str:
    """Shorten long cell text so it fits inside timetable tables."""
    if not isinstance(text, str):
        text = str(text)
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def _init_session() -> None:
    if "initialized" in st.session_state:
        return

    # Load from storage first
    st.session_state.teachers: List[Teacher] = load_teachers()
    st.session_state.classes: List[Class] = load_classes()
    st.session_state.priority_configs: List[ClassPriorityConfig] = []
    st.session_state.config: SchoolConfig = load_config()

    base = load_base_timetable()
    st.session_state.class_timetable: Timetable | None = base or None
    st.session_state.teacher_timetable: Dict[str, Dict[Tuple[int, int], Tuple[str, str]]] | None = None

    st.session_state.notifications: List[dict] = []
    st.session_state.scenario_state = load_scenario_state()

    st.session_state.initialized = True


def show_toast(msg: str, duration_sec: int = 3) -> None:
    uid = f"n_{len(st.session_state.notifications)}_{hash(msg)}"
    st.session_state.notifications.append(
        {"msg": msg, "until": timedelta(seconds=duration_sec), "id": uid}
    )


@st.fragment(run_every=timedelta(seconds=1))
def _notification_ticker() -> None:
    now = timedelta(seconds=0)
    notifications = st.session_state.get("notifications", [])
    active: List[dict] = []

    for n in notifications:
        remaining = n["until"] - timedelta(seconds=1)
        if remaining > now:
            n["until"] = remaining
            active.append(n)

    st.session_state.notifications = active

    for n in active:
        secs = int(n["until"].total_seconds())
        st.markdown(
            f"<div class='toast-item'><span class='toast-msg'>{n['msg']}</span>"
            f"<span class='toast-countdown'>{secs}s</span></div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------


def load_demo_into_session() -> None:
    """Populate in‑memory teachers/classes with the README demo."""
    st.session_state.teachers = [
        Teacher(
            teacher_id="Eric Simon",
            name="Eric Simon",
            subjects=["Physics"],
            max_periods_per_day=5,
            max_periods_per_week=30,
            target_free_periods_per_day=3,
        ),
        Teacher(
            teacher_id="Aisha Khan",
            name="Aisha Khan",
            subjects=["Chemistry"],
            max_periods_per_day=5,
            max_periods_per_week=30,
            target_free_periods_per_day=3,
        ),
        Teacher(
            teacher_id="Rahul Mehta",
            name="Rahul Mehta",
            subjects=["Mathematics"],
            max_periods_per_day=5,
            max_periods_per_week=30,
            target_free_periods_per_day=3,
        ),
        Teacher(
            teacher_id="Neha Verma",
            name="Neha Verma",
            subjects=["Biology"],
            max_periods_per_day=5,
            max_periods_per_week=30,
            target_free_periods_per_day=3,
        ),
        Teacher(
            teacher_id="Daniel Brooks",
            name="Daniel Brooks",
            subjects=["English"],
            max_periods_per_day=4,
            max_periods_per_week=20,
            target_free_periods_per_day=4,
        ),
        Teacher(
            teacher_id="Priya Nair",
            name="Priya Nair",
            subjects=["Economics"],
            max_periods_per_day=5,
            max_periods_per_week=30,
            target_free_periods_per_day=3,
        ),
        Teacher(
            teacher_id="Arjun Patel",
            name="Arjun Patel",
            subjects=["Accountancy"],
            max_periods_per_day=5,
            max_periods_per_week=30,
            target_free_periods_per_day=3,
        ),
        Teacher(
            teacher_id="Kavita Rao",
            name="Kavita Rao",
            subjects=["Business Studies"],
            max_periods_per_day=4,
            max_periods_per_week=24,
            target_free_periods_per_day=4,
        ),
        Teacher(
            teacher_id="Sofia Mendes",
            name="Sofia Mendes",
            subjects=["History"],
            max_periods_per_day=5,
            max_periods_per_week=30,
            target_free_periods_per_day=3,
        ),
        Teacher(
            teacher_id="Aman Gupta",
            name="Aman Gupta",
            subjects=["Political Science"],
            max_periods_per_day=5,
            max_periods_per_week=30,
            target_free_periods_per_day=3,
        ),
        Teacher(
            teacher_id="Ritu Chawla",
            name="Ritu Chawla",
            subjects=["Geography"],
            max_periods_per_day=4,
            max_periods_per_week=24,
            target_free_periods_per_day=4,
        ),
        Teacher(
            teacher_id="Marcus Lee",
            name="Marcus Lee",
            subjects=["Physical Education"],
            max_periods_per_day=3,
            max_periods_per_week=15,
            target_free_periods_per_day=5,
        ),
    ]

    def cls(cid: str, subjects: List[Tuple[str, int, str]]) -> Class:
        return Class(
            id=cid,
            name=cid,
            subjects=[ClassSubject(s, w, t) for (s, w, t) in subjects],
        )

    st.session_state.classes = [
        cls(
            "11SCI",
            [
                ("Physics", 6, "Eric Simon"),
                ("Chemistry", 6, "Aisha Khan"),
                ("Mathematics", 6, "Rahul Mehta"),
                ("Biology", 6, "Neha Verma"),
                ("English", 4, "Daniel Brooks"),
                ("Physical Education", 2, "Marcus Lee"),
            ],
        ),
        cls(
            "12SCI",
            [
                ("Physics", 6, "Eric Simon"),
                ("Chemistry", 6, "Aisha Khan"),
                ("Mathematics", 6, "Rahul Mehta"),
                ("Biology", 6, "Neha Verma"),
                ("English", 4, "Daniel Brooks"),
                ("Physical Education", 2, "Marcus Lee"),
            ],
        ),
    ]

    save_teachers(st.session_state.teachers)
    save_classes(st.session_state.classes)
    show_toast("Demo data loaded (teachers + classes)")
    logger.log_activity(Activities.DEMO_LOADED, "Demo data loaded with sample teachers and classes", "system")
    set_demo_loaded()


# ---------------------------------------------------------------------------
# Sidebar – configuration & demo controls
# ---------------------------------------------------------------------------


def render_sidebar() -> None:
    cfg = st.session_state.config
    st.sidebar.title("⚙️ School Setup")

    with st.sidebar.form("sidebar_config", clear_on_submit=False):
        st.markdown("**📆 Days & Periods**")
        days_str = st.text_input(
            "Days (comma-separated)",
            value=",".join(cfg.days),
        )
        periods = st.number_input(
            "Periods per day",
            min_value=4,
            max_value=12,
            value=cfg.periods_per_day,
        )
        st.markdown("**🥤 Break Periods**")
        st.caption("One per line: period_number,name (e.g. 4,Lunch)")
        break_str = st.text_area(
            "Break periods",
            value="\n".join(f"{i+1},{name}" for i, name in cfg.break_periods.items()),
            height=80,
        )

        if st.form_submit_button("Apply Config"):
            days = [d.strip() for d in days_str.split(",") if d.strip()]
            breaks: Dict[int, str] = {}
            for line in break_str.splitlines():
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2:
                    try:
                        idx = int(parts[0]) - 1
                        breaks[idx] = parts[1]
                    except ValueError:
                        continue
            st.session_state.config = SchoolConfig(
                days=days or cfg.days,
                periods_per_day=int(periods),
                break_periods=breaks or cfg.break_periods,
            )
            save_config(st.session_state.config)
            logger.log_activity(Activities.CONFIG_UPDATED, f"Updated: {days} days, {periods} periods/day, {len(breaks)} breaks", "system")
            show_toast("Config saved")

    st.sidebar.markdown("---")
    with st.sidebar.expander("🧪 Demo / Testing"):
        if st.button("Load Demo Data"):
            load_demo_into_session()

    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Clear all generated timetables"):
        st.session_state.class_timetable = None
        st.session_state.teacher_timetable = None
        clear_base_timetable()
        clear_scenario_state()
        clear_demo_loaded()
        logger.log_activity(Activities.DATA_CLEARED, "Cleared all timetables and demo data", "system")
        show_toast("Cleared generated timetables")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------


def tab_teachers_classes() -> None:
    st.header("Teachers & Classes")

    cfg: SchoolConfig = st.session_state.config

    # --- Teachers ---
    st.subheader("1. Teachers")
    with st.expander("➕ Add teacher", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            t_id = st.text_input("Teacher name / ID", key="new_teacher_id")
        with col2:
            subs = st.text_input(
                "Subjects (comma-separated)", key="new_teacher_subjects"
            )
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            max_per_day = st.number_input(
                "Max periods/day",
                min_value=0,
                max_value=12,
                value=6,
                key="new_teacher_max_day",
            )
        with col_m2:
            max_per_week = st.number_input(
                "Max periods/week",
                min_value=0,
                max_value=40,
                value=30,
                key="new_teacher_max_week",
            )
        with col_m3:
            free_per_day = st.number_input(
                "Free periods/day",
                min_value=0,
                max_value=12,
                value=max(0, cfg.periods_per_day - max_per_day),
                key="new_teacher_free_per_day",
            )
        
        st.caption(f"Teacher will teach at most {max_per_day} periods/day ({max_per_week}/week).")
        if st.button("Save Teacher", key="save_teacher_btn"):
            if t_id.strip():
                teacher = Teacher(
                    teacher_id=t_id.strip(),
                    name=t_id.strip(),
                    subjects=[s.strip() for s in subs.split(",") if s.strip()],
                    max_periods_per_day=int(max_per_day),
                    max_periods_per_week=int(max_per_week),
                    target_free_periods_per_day=int(free_per_day),
                )
                st.session_state.teachers.append(teacher)
                save_teachers(st.session_state.teachers)
                show_toast(f"Teacher {t_id} added")
                logger.log_activity(Activities.TEACHER_ADDED, f"Teacher '{t_id}' with subjects: {subs}", "teacher")
                append_history("add", f"Teacher {t_id}", f"Added teacher {t_id}")

    if st.session_state.teachers:
        for i, t in enumerate(st.session_state.teachers):
            cols = st.columns([4, 1, 1])
            with cols[0]:
                subjects = ", ".join(t.subjects) if isinstance(t.subjects, list) else str(
                    t.subjects
                )
                st.markdown(
                    f"**{t.teacher_id}** — {subjects or 'No subjects yet'} "
                    f"(max {t.max_periods_per_day}/day)"
                )
            with cols[1]:
                if st.button("✏️ Edit", key=f"edit_teacher_{i}"):
                    st.session_state[f"editing_teacher_{i}"] = True
                    
                # Handle edit mode
                if st.session_state.get(f"editing_teacher_{i}", False):
                    with st.expander(f"Editing: {t.teacher_id}", expanded=True):
                        new_name = st.text_input("Name / ID", value=t.teacher_id, key=f"edit_name_{i}")
                        new_subjects = st.text_input("Subjects (comma-separated)", value=", ".join(t.subjects), key=f"edit_subj_{i}")
                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            new_max_day = st.number_input("Max periods/day", min_value=0, max_value=12, value=t.max_periods_per_day, key=f"edit_max_{i}")
                        with col_m2:
                            new_target_free = st.number_input("Free periods/day", min_value=0, max_value=12, value=getattr(t, 'target_free_periods_per_day', 0), key=f"edit_free_{i}")
                        
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            if st.button("💾 Save", key=f"save_teacher_{i}"):
                                old_name = t.teacher_id
                                t.teacher_id = new_name.strip()
                                t.name = new_name.strip()
                                t.subjects = [s.strip() for s in new_subjects.split(",") if s.strip()]
                                t.max_periods_per_day = int(new_max_day)
                                t.target_free_periods_per_day = int(new_target_free)
                                save_teachers(st.session_state.teachers)
                                show_toast(f"Teacher '{new_name}' updated!")
                                logger.log_activity(Activities.TEACHER_UPDATED, f"Teacher '{old_name}' updated to '{new_name}'", "teacher")
                                st.session_state[f"editing_teacher_{i}"] = False
                                st.rerun()
                        with col_e2:
                            if st.button("Cancel", key=f"cancel_teacher_{i}"):
                                st.session_state[f"editing_teacher_{i}"] = False
                                st.rerun()
            with cols[2]:
                if st.button("🗑️", key=f"rm_teacher_{i}"):
                    removed = st.session_state.teachers.pop(i)
                    save_teachers(st.session_state.teachers)
                    show_toast(f"Teacher {removed.teacher_id} removed")
                    logger.log_activity(Activities.TEACHER_REMOVED, f"Teacher '{removed.teacher_id}' removed", "teacher")
                    append_history(
                        "delete",
                        f"Teacher {removed.teacher_id}",
                        f"Removed teacher {removed.teacher_id}",
                    )
                    st.rerun()
    else:
        st.info("No teachers yet. Add a few above.")

    st.markdown("---")

    # --- Classes ---
    st.subheader("2. Classes")
    with st.expander("➕ Add class", expanded=True):
        cid = st.text_input("Class ID (e.g. 11SCI)", key="new_class_id")
        subj_lines = st.text_area(
            "Subjects (one per line: subject,weekly_periods,teacher_id)",
            key="new_class_subjects",
        )
        if st.button("Save Class", key="save_class_btn"):
            if cid.strip():
                subjects: List[ClassSubject] = []
                for line in subj_lines.splitlines():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) == 3:
                        try:
                            subjects.append(
                                ClassSubject(
                                    subject=parts[0],
                                    weekly_periods=int(parts[1]),
                                    teacher_id=parts[2],
                                )
                            )
                        except ValueError:
                            continue
                st.session_state.classes.append(
                    Class(id=cid.strip(), name=cid.strip(), subjects=subjects)
                )
                save_classes(st.session_state.classes)
                show_toast(f"Class {cid} added")
                logger.log_activity(Activities.CLASS_ADDED, f"Class '{cid}' with {len(subjects)} subjects", "class")
                append_history("add", f"Class {cid}", f"Added class {cid}")

    if st.session_state.classes:
        for i, c in enumerate(st.session_state.classes):
            subj_str = ", ".join(
                f"{cs.subject}({cs.weekly_periods}w → {cs.teacher_id})"
                for cs in c.subjects
            ) or "No subjects yet"
            cols = st.columns([4, 1, 1])
            with cols[0]:
                st.markdown(f"**{c.id}** — {subj_str}")
            with cols[1]:
                if st.button("✏️ Edit", key=f"edit_class_btn_{i}"):
                    st.session_state[f"editing_class_{i}"] = True
                    
                # Handle edit mode
                if st.session_state.get(f"editing_class_{i}", False):
                    with st.expander(f"Editing: {c.id}", expanded=True):
                        new_id = st.text_input("Class ID", value=c.id, key=f"edit_class_id_{i}")
                        st.markdown("**Subjects (one per line: subject,periods,teacher)**")
                        subj_lines_edit = "\n".join(
                            f"{cs.subject},{cs.weekly_periods},{cs.teacher_id}"
                            for cs in c.subjects
                        )
                        new_subj_lines = st.text_area("Subjects", value=subj_lines_edit, key=f"edit_class_subj_{i}", height=150)
                        
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            if st.button("💾 Save", key=f"save_class_{i}"):
                                old_id = c.id
                                c.id = new_id.strip()
                                c.name = new_id.strip()
                                # Parse subjects
                                new_subjects = []
                                for line in new_subj_lines.splitlines():
                                    parts = [p.strip() for p in line.split(",")]
                                    if len(parts) >= 3:
                                        try:
                                            new_subjects.append(ClassSubject(
                                                subject=parts[0],
                                                weekly_periods=int(parts[1]),
                                                teacher_id=parts[2]
                                            ))
                                        except ValueError:
                                            continue
                                c.subjects = new_subjects
                                save_classes(st.session_state.classes)
                                show_toast(f"Class '{new_id}' updated!")
                                logger.log_activity(Activities.CLASS_UPDATED, f"Class '{old_id}' updated to '{new_id}'", "class")
                                st.session_state[f"editing_class_{i}"] = False
                                st.rerun()
                        with col_e2:
                            if st.button("Cancel", key=f"cancel_class_{i}"):
                                st.session_state[f"editing_class_{i}"] = False
                                st.rerun()
            with cols[2]:
                if st.button("🗑️", key=f"rm_class_{i}"):
                    removed = st.session_state.classes.pop(i)
                    save_classes(st.session_state.classes)
                    show_toast(f"Class {removed.id} removed")
                    logger.log_activity(Activities.CLASS_REMOVED, f"Class '{removed.id}' removed", "class")
                    append_history(
                        "delete",
                        f"Class {removed.id}",
                        f"Removed class {removed.id}",
                    )
                    st.rerun()
    else:
        st.info("No classes yet. Add a few above.")


def tab_history() -> None:
    st.header("🕓 History")
    history = load_history()
    if not history:
        st.info("No history yet.")
        return
    for entry in history:
        ts = entry.get("ts", "")
        summary = entry.get("summary", "")
        action = entry.get("action", "")
        target = entry.get("target", "")
        with st.expander(f"{ts} — {summary}"):
            st.markdown(f"**Action:** {action}  •  **Target:** {target}")
            details = entry.get("details", "")
            if details:
                st.caption(details)


def tab_class_timetables() -> None:
    st.header("Class Timetables")
    cfg: SchoolConfig = st.session_state.config

    if st.button("🚀 Generate Timetable", type="primary"):
        if not st.session_state.teachers:
            st.error("Add at least one teacher first.")
            return
        if not st.session_state.classes:
            st.error("Add at least one class first.")
            return
        with st.spinner("Solving with OR‑Tools..."):
            tt = solve_timetable(
                cfg, st.session_state.teachers, st.session_state.classes
            )
        if tt is None:
            st.error("No solution found. Try changing config or weekly periods.")
            append_history("generate", "Timetable", "No solution found")
            logger.log_activity(Activities.TIMETABLE_GENERATED, "Failed: No solution found", "timetable")
            return

        st.session_state.class_timetable = tt
        st.session_state.teacher_timetable = invert_to_teacher_timetable(tt, cfg)
        save_base_timetable(tt)
        append_history("generate", "Timetable", "Generated clash‑free timetable")
        logger.log_activity(Activities.TIMETABLE_GENERATED, f"Generated timetable for {len(st.session_state.classes)} classes and {len(st.session_state.teachers)} teachers", "timetable")
        show_toast("Timetable generated!")

    if not st.session_state.class_timetable:
        st.info("Generate a timetable to see class views.")
        return

    # Keys should be (class_id, day, period) tuples, but be defensive.
    keys = list(st.session_state.class_timetable.keys())
    class_ids = sorted(
        {k[0] for k in keys if isinstance(k, (tuple, list)) and len(k) >= 1}
    )
    breaks = cfg.break_periods
    period_cols = [
        f"P{p+1}" + (f" ({breaks[p]})" if p in breaks else "")
        for p in range(cfg.periods_per_day)
    ]

    col_config = {"Day": st.column_config.TextColumn("Day", width="medium")}
    for pc in period_cols:
        col_config[pc] = st.column_config.TextColumn(pc, width="large")

    for cid in class_ids:
        st.subheader(f"Class {cid}")
        rows = []
        for d, day_name in enumerate(cfg.days):
            row = [day_name]
            for p in range(cfg.periods_per_day):
                if p in breaks:
                    row.append(breaks[p])
                else:
                    val = st.session_state.class_timetable.get((cid, d, p), ("", ""))[0]
                    cell = val or "Free period"
                    row.append(_shorten(cell, 18))
            rows.append(row)
        st.dataframe(
            pd.DataFrame(rows, columns=["Day"] + period_cols),
            column_config=col_config,
            width="stretch",
            hide_index=True,
        )


def tab_teacher_timetables() -> None:
    st.header("Teacher Timetables")
    if not st.session_state.teacher_timetable:
        st.info("Generate a timetable first.")
        return

    cfg: SchoolConfig = st.session_state.config
    breaks = cfg.break_periods
    period_cols = [
        f"P{p+1}" + (f" ({breaks[p]})" if p in breaks else "")
        for p in range(cfg.periods_per_day)
    ]
    col_config = {"Day": st.column_config.TextColumn("Day", width="medium")}
    for pc in period_cols:
        col_config[pc] = st.column_config.TextColumn(pc, width="large")

    for tid, tt in sorted(st.session_state.teacher_timetable.items()):
        st.subheader(f"Teacher {tid}")
        rows = []
        for d, day_name in enumerate(cfg.days):
            row = [day_name]
            for p in range(cfg.periods_per_day):
                if p in breaks:
                    row.append(breaks[p])
                else:
                    cid, subj = tt.get((d, p), ("", ""))
                    cell = f"{cid}: {subj}" if subj else "Free period"
                    row.append(_shorten(cell, 22))
            rows.append(row)
        st.dataframe(
            pd.DataFrame(rows, columns=["Day"] + period_cols),
            column_config=col_config,
            width="stretch",
            hide_index=True,
        )


def tab_substitution() -> None:
    """Smart Substitution - Find best substitute for absent teacher."""
    st.header("🔄 Smart Substitution")
    st.markdown("*Find the best substitute teacher instantly*")
    
    cfg = st.session_state.config
    
    if not st.session_state.class_timetable:
        st.info("Please generate a timetable first!")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        absent_day = st.selectbox("Select Day", cfg.days, key="absent_day")
    with col2:
        absent_period = st.selectbox("Select Period", [f"P{i+1}" for i in range(cfg.periods_per_day)], key="absent_period")
    
    if st.button("🔍 Find Substitute", type="primary"):
        day_idx = cfg.days.index(absent_day)
        period_idx = int(absent_period.replace("P", "")) - 1
        
        # Get the class and subject at this slot
        classes_at_slot = []
        for (cid, d, p), (subj, tid) in st.session_state.class_timetable.items():
            if d == day_idx and p == period_idx:
                classes_at_slot.append((cid, subj, tid))
        
        if not classes_at_slot:
            st.success("All classes have free period!")
            return
        
        # Find substitutes
        st.subheader("📋 Substitution Plan")
        for cid, subj, original_teacher in classes_at_slot:
            # Find teachers who can teach this subject and are free
            potential_subs = []
            for t in st.session_state.teachers:
                if subj in t.subjects and t.teacher_id != original_teacher:
                    # Check if teacher is free at this time
                    is_free = True
                    for (c2, d2, p2), (s2, t2) in st.session_state.class_timetable.items():
                        if d2 == day_idx and p2 == period_idx and t2 == t.teacher_id:
                            is_free = False
                            break
                    if is_free:
                        potential_subs.append(t.teacher_id)
            
            with st.expander(f"**{cid}**: {subj} ({original_teacher})", expanded=True):
                if potential_subs:
                    st.success(f"✅ Available substitutes: {', '.join(potential_subs)}")
                else:
                    st.warning("⚠️ No substitute available for this subject!")

def tab_free_teacher() -> None:
    """Free Teacher Finder - Instantly find free teachers."""
    st.header("👨‍🏫 Free Teacher Finder")
    st.markdown("*Find available teachers for any period*")
    
    cfg = st.session_state.config
    
    if not st.session_state.class_timetable:
        st.info("Please generate a timetable first!")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        free_day = st.selectbox("Select Day", cfg.days, key="free_day")
    with col2:
        free_period = st.selectbox("Select Period", [f"P{i+1}" for i in range(cfg.periods_per_day)], key="free_period")
    
    day_idx = cfg.days.index(free_day)
    period_idx = int(free_period.replace("P", "")) - 1
    
    # Skip if break
    if period_idx in cfg.break_periods:
        st.warning(f"Period {period_idx + 1} is a break: {cfg.break_periods[period_idx]}")
        return
    
    # Find all teachers teaching at this time
    busy_teachers = set()
    for (cid, d, p), (subj, tid) in st.session_state.class_timetable.items():
        if d == day_idx and p == period_idx:
            busy_teachers.add(tid)
    
    # Find free teachers
    all_teachers = set(t.teacher_id for t in st.session_state.teachers)
    free_teachers = all_teachers - busy_teachers
    
    st.subheader(f"📅 {free_day} - {free_period}")
    
    if free_teachers:
        st.success(f"**{len(free_teachers)} teachers available:**")
        for t in sorted(free_teachers):
            teacher = next((x for x in st.session_state.teachers if x.teacher_id == t), None)
            if teacher:
                st.markdown(f"• **{t}** - Subjects: {', '.join(teacher.subjects)}")
    else:
        st.warning("⚠️ All teachers are busy during this period!")

def tab_load_analyzer() -> None:
    """Teacher Load Analyzer - Show workload analysis."""
    st.header("📊 Teacher Load Analyzer")
    st.markdown("*Automatic load balancing analysis for teachers*")
    
    if not st.session_state.class_timetable:
        st.info("Please generate a timetable first!")
        return
    
    cfg = st.session_state.config
    
    # Calculate load per teacher
    teacher_load = {}
    for t in st.session_state.teachers:
        teacher_load[t.teacher_id] = {
            'total': 0,
            'daily': {d: 0 for d in cfg.days},
            'subjects': {}
        }
    
    for (cid, d, p), (subj, tid) in st.session_state.class_timetable.items():
        if p not in cfg.break_periods and tid in teacher_load:
            teacher_load[tid]['total'] += 1
            teacher_load[tid]['daily'][cfg.days[d]] += 1
            teacher_load[tid]['subjects'][subj] = teacher_load[tid]['subjects'].get(subj, 0) + 1
    
    # Display load
    st.subheader("📈 Weekly Workload")
    
    # Create load data
    load_data = []
    for tid, data in teacher_load.items():
        teacher = next((t for t in st.session_state.teachers if t.teacher_id == tid), None)
        max_allowed = teacher.max_periods_per_week if teacher else 30
        load_pct = (data['total'] / max_allowed * 100) if max_allowed > 0 else 0
        
        status = "✅" if data['total'] <= max_allowed else "⚠️"
        
        load_data.append({
            "Teacher": tid,
            "Total Periods": data['total'],
            "Max Allowed": max_allowed,
            "Utilization %": f"{load_pct:.0f}%",
            "Status": status
        })
    
    if load_data:
        st.dataframe(load_data, use_container_width=True)
    
    # Daily distribution
    st.subheader("📅 Daily Distribution")
    daily_data = []
    for tid, data in teacher_load.items():
        row = {"Teacher": tid}
        for d in cfg.days:
            row[d] = data['daily'].get(d, 0)
        row["Total"] = data['total']
        daily_data.append(row)
    
    if daily_data:
        st.dataframe(daily_data, use_container_width=True)
    
    # Overload warnings
    st.subheader("⚠️ Overload Alerts")
    overloads = []
    for tid, data in teacher_load.items():
        teacher = next((t for t in st.session_state.teachers if t.teacher_id == tid), None)
        if teacher and data['total'] > teacher.max_periods_per_week:
            overloads.append(f"**{tid}**: {data['total']}/{teacher.max_periods_per_week} periods (exceeded by {data['total'] - teacher.max_periods_per_week})")
    
    if overloads:
        for alert in overloads:
            st.warning(alert)
    else:
        st.success("✅ All teachers are within their workload limits!")


def tab_heatmaps() -> None:
    st.header("🔥 Heatmaps")
    if not st.session_state.class_timetable:
        st.info("Generate a timetable first.")
        return

    cfg: SchoolConfig = st.session_state.config
    tt: Timetable = st.session_state.class_timetable
    teachers = [t.teacher_id for t in st.session_state.teachers]
    days = cfg.days

    # Build teacher × day load matrix
    load = np.zeros((len(teachers), len(days)), dtype=int)
    for key, (_, tid) in tt.items():
        if not isinstance(key, (tuple, list)) or len(key) != 3:
            continue
        _, d, p = key
        if p in cfg.break_periods:
            continue
        if tid in teachers:
            i = teachers.index(tid)
            load[i, d] += 1

    if not teachers:
        st.info("Add some teachers first.")
        return

    # Build a "wave-dot" style heatmap: grid of circles whose size and brightness
    # represent load. This feels more cinematic than plain blocks.
    xs: List[str] = []
    ys: List[str] = []
    sizes: List[float] = []
    colors: List[int] = []
    for i, tid in enumerate(teachers):
        for j, day in enumerate(days):
            xs.append(day)
            ys.append(tid)
            val = int(load[i, j])
            colors.append(val)
            # Base dot size + extra per period
            sizes.append(10 + 10 * val)

    fig = px.scatter(
        x=xs,
        y=ys,
        color=colors,
        size=sizes,
        color_continuous_scale="Viridis",
        labels=dict(x="Day", y="Teacher", color="Load"),
    )
    fig.update_traces(
        mode="markers",
        marker=dict(
            opacity=0.85,
            line=dict(width=0),
        ),
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="#f0f6fc"),
        margin=dict(l=40, r=20, t=40, b=40),
        yaxis=dict(categoryorder="array", categoryarray=teachers),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Bigger, brighter dots = more periods for that teacher on that day.")


def tab_pdf_export() -> None:
    st.header("📄 Export PDFs")
    if not (st.session_state.class_timetable and st.session_state.teacher_timetable):
        st.info("Generate a timetable first.")
        return

    cfg: SchoolConfig = st.session_state.config
    class_tt = flat_to_class_timetables(st.session_state.class_timetable)
    class_pdf = export_class_timetables_pdf(class_tt, cfg)
    teacher_pdf = export_teacher_timetables_pdf(
        st.session_state.teacher_timetable, cfg
    )
    st.subheader("All timetables")
    col1, col2 = st.columns(2)
    with col1:
        if st.download_button(
            "📥 Download ALL Class Timetables (PDF)",
            data=class_pdf,
            file_name="class_timetables.pdf",
            mime="application/pdf",
            key="dl_all_classes_pdf",
        ):
            append_history("export", "PDF", "Exported all class timetables PDF")
            logger.log_activity(Activities.TIMETABLE_EXPORTED, "Exported PDF for all classes", "timetable")
            show_toast("All class PDFs downloaded")
    with col2:
        if st.download_button(
            "📥 Download ALL Teacher Timetables (PDF)",
            data=teacher_pdf,
            file_name="teacher_timetables.pdf",
            mime="application/pdf",
            key="dl_all_teachers_pdf",
        ):
            append_history("export", "PDF", "Exported all teacher timetables PDF")
            logger.log_activity(Activities.TIMETABLE_EXPORTED, "Exported PDF for all teachers", "timetable")
            show_toast("All teacher PDFs downloaded")

    st.markdown("---")
    st.subheader("Single class / teacher")

    class_ids = sorted(class_tt.keys())
    teacher_ids = sorted(st.session_state.teacher_timetable.keys())

    colc, colt = st.columns(2)
    with colc:
        sel_class = st.selectbox(
            "Class", ["— select class —"] + class_ids, key="pdf_single_class"
        )
        if sel_class != "— select class —":
            single_class_pdf = export_class_timetables_pdf(
                {sel_class: class_tt[sel_class]}, cfg
            )
            st.download_button(
                f"📥 Download {sel_class} Timetable (PDF)",
                data=single_class_pdf,
                file_name=f"{sel_class}_timetable.pdf",
                mime="application/pdf",
                key="dl_one_class_pdf",
            )

    with colt:
        sel_teacher = st.selectbox(
            "Teacher", ["— select teacher —"] + teacher_ids, key="pdf_single_teacher"
        )
        if sel_teacher != "— select teacher —":
            single_teacher_pdf = export_teacher_timetables_pdf(
                {sel_teacher: st.session_state.teacher_timetable[sel_teacher]}, cfg
            )
            st.download_button(
                f"📥 Download {sel_teacher} Timetable (PDF)",
                data=single_teacher_pdf,
                file_name=f"{sel_teacher}_timetable.pdf",
                mime="application/pdf",
                key="dl_one_teacher_pdf",
            )


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------


def main() -> None:
    _init_session()

    # Custom header with datetime
    from datetime import datetime
    import pytz
    
    # Set timezone to IST (India Standard Time)
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    date_str = now.strftime("%a, %d %b %Y")
    time_str = now.strftime("%I:%M %p")
    
    # Hide default header
    hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding-top: 1rem !important;}
        </style>
    """
    st.markdown(hide_menu_style, unsafe_allow_html=True)
    
    # Custom top bar
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%); border-radius: 12px; margin-bottom: 20px; border: 1px solid #2d2d44;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 28px;">📅</span>
            <span style="font-size: 20px; font-weight: 600; color: #fff;">Timetable</span>
        </div>
        <div style="display: flex; align-items: center; gap: 20px;">
            <span style="color: #888; font-size: 14px;">{date_str}</span>
            <span style="color: #00d4ff; font-size: 18px; font-weight: 600; font-family: monospace;">{time_str}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    render_sidebar()

    _notification_ticker()

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(
        [
            "👥 Teachers & Classes",
            "🕓 History",
            "📋 Class Timetables",
            "👨‍🏫 Teacher Timetables",
            "🔄 Substitution",
            "👨‍🏫 Free Teachers",
            "📊 Load Analyzer",
            "🔥 Heatmaps",
            "📄 PDF Export",
        ]
    )

    with tab1:
        tab_teachers_classes()
    with tab2:
        tab_history()
    with tab3:
        tab_class_timetables()
    with tab4:
        tab_teacher_timetables()
    with tab5:
        tab_substitution()
    with tab6:
        tab_free_teacher()
    with tab7:
        tab_load_analyzer()
    with tab8:
        tab_heatmaps()
    with tab9:
        tab_pdf_export()


if __name__ == "__main__":
    main()

