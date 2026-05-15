import pytest

from models import SchoolConfig, Teacher, Class, ClassSubject, ClassPriorityConfig
from solver.engine import _greedy_initial_assignment, _perform_feasibility_analysis, solve_timetable
from solver.scoring import compute_timetable_score
from solver.improver import improve_timetable


def make_teacher(tid, max_week=30):
    return Teacher(teacher_id=tid, name=f"T{tid}", max_periods_per_week=max_week)


def make_class(cid, subjects):
    # subjects: list of (subject_name, weekly_periods, teacher_id)
    cs = [ClassSubject(subject=s[0], weekly_periods=s[1], teacher_id=s[2]) for s in subjects]
    return Class(id=cid, name=cid, subjects=cs)


def test_greedy_initial_assignment_respects_minimum():
    cfg = SchoolConfig(days=["Mon","Tue","Wed","Thu","Fri"], periods_per_day=6, break_periods={})
    # non_breaks_per_day = 6 -> min occupied per day = 4 -> min_weekly_needed = 20
    # Create a class with weekly periods exactly 20
    cls = make_class("C1", [("Math", 20, "T1")])
    t = make_teacher("T1", max_week=30)
    greedy = _greedy_initial_assignment(cfg, [t], [cls])
    assert greedy is not None


def test_feasibility_analysis_detects_free_period_violation():
    cfg = SchoolConfig(days=["Mon","Tue","Wed","Thu","Fri"], periods_per_day=6, break_periods={})
    # class with only 12 weekly periods (too few for min_weekly_needed=20)
    cls = make_class("C2", [("Eng", 12, "T2")])
    t = make_teacher("T2", max_week=30)
    notes = _perform_feasibility_analysis(cfg, [t], [cls])
    assert any("will likely violate the preferred" in n for n in notes)


def test_improver_improves_score():
    cfg = SchoolConfig(days=["Mon","Tue","Wed","Thu","Fri"], periods_per_day=6, break_periods={})
    cls = make_class("C3", [("Math", 20, "T3")])
    t = make_teacher("T3")
    greedy = _greedy_initial_assignment(cfg, [t], [cls])
    assert greedy is not None
    priority = [ClassPriorityConfig(class_id="C3", priority_subjects=["Math"], heavy_subjects=[])]
    before = compute_timetable_score(greedy, cfg, priority)
    improved = improve_timetable(greedy, cfg, [cls], priority, max_iters=20)
    after = compute_timetable_score(improved, cfg, priority)
    assert after >= before


def test_relaxation_allows_solution():
    cfg = SchoolConfig(days=["Mon","Tue","Wed","Thu","Fri"], periods_per_day=6, break_periods={})
    # create simple scenario with two classes and two teachers
    classes = [
        make_class("A", [("Math", 20, "T1")]),
        make_class("B", [("Sci", 20, "T2")]),
    ]
    teachers = [make_teacher("T1"), make_teacher("T2")]
    # With strict free-period rule the solver may fail; request relaxation
    tt = solve_timetable(cfg, teachers, classes, allow_relax_class_free_periods=True)
    assert tt is not None
