"""
🧠 UI FORMS — st.form() to prevent screen jump while typing
==========================================================
Forms batch inputs: no rerun until Submit. Layout stays fixed.
Uses edit_buffer (form_teacher/form_class) for prefilled data — never mutates widget keys.
"""

import streamlit as st
from typing import Optional, Callable

from models import Teacher, Class, ClassSubject


def _teacher_form_key(editing_index: Optional[int], field: str, prefix: str = "main") -> str:
    """Unique key per mode + tab. Never shared with widget-backed keys."""
    if editing_index is None:
        return f"t_{prefix}_{field}_add"
    return f"t_{prefix}_{field}_edit_{editing_index}"


def _class_form_key(editing_index: Optional[int], field: str, prefix: str = "main") -> str:
    if editing_index is None:
        return f"c_{prefix}_{field}_add"
    return f"c_{prefix}_{field}_edit_{editing_index}"


"""
ui_forms.py — Streamlit forms and UI helpers for Timable
"""
import streamlit as st
from models import Teacher, Class, ClassSubject
from typing import List

def teacher_form(teacher: Teacher = None) -> Teacher:
    with st.form(key=f"teacher_form_{teacher.id if teacher else 'new'}"):
        name = st.text_input("Teacher Name", value=teacher.name if teacher else "")
        subjects = st.text_input("Subjects (comma-separated)", value=", ".join(teacher.subjects) if teacher else "")
        max_per_day = st.number_input("Max Periods/Day", min_value=1, max_value=10, value=teacher.max_periods_per_day if teacher else 6)
        max_per_week = st.number_input("Max Periods/Week", min_value=1, max_value=60, value=teacher.max_periods_per_week if teacher else 30)
        submitted = st.form_submit_button("Save Teacher")
        if submitted:
            return Teacher(
                id=teacher.id if teacher else name.replace(" ", "_"),
                name=name,
                subjects=[s.strip() for s in subjects.split(",") if s.strip()],
                max_periods_per_day=max_per_day,
                max_periods_per_week=max_per_week
            )
    return None

def class_form(cls: Class = None) -> Class:
    with st.form(key=f"class_form_{cls.id if cls else 'new'}"):
        name = st.text_input("Class Name", value=cls.name if cls else "")
        subjects = st.text_area("Subjects (one per line, format: subject,weekly_periods,teacher_id)",
            value="\n".join(f"{s.subject},{s.weekly_periods},{s.teacher_id}" for s in cls.subjects) if cls else "")
        submitted = st.form_submit_button("Save Class")
        if submitted:
            subject_objs = []
            for line in subjects.splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) == 3:
                    subject_objs.append(ClassSubject(subject=parts[0], weekly_periods=int(parts[1]), teacher_id=parts[2]))
            return Class(
                id=cls.id if cls else name.replace(" ", "_"),
                name=name,
                subjects=subject_objs
            )
    return None
