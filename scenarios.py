"""
scenarios.py — Minimal placeholder for scenario/config logic in Timable
"""
# (Extend with scenario features as needed)


def apply_scenario_overlay(base_tt, scenario_state, config, teachers):
    """
    Apply scenario overlays to base timetable. Never mutates base.
    Returns resolved view.
    """
    resolved = copy.deepcopy(base_tt)
    day_idx = scenario_state.get("selected_day", 0)
    scenarios = scenario_state.get("scenarios", {})

    # Build teacher->subjects map
    teacher_subjects = {t.teacher_id: set(t.subjects) for t in teachers}
    # Build subject->teachers who can teach it
    subject_teachers: Dict[str, List[str]] = {}
    for t in teachers:
        for s in t.subjects:
            if s not in subject_teachers:
                subject_teachers[s] = []
            subject_teachers[s].append(t.teacher_id)

    # 1. Teacher absent today
    if scenarios.get("teacher_absent", {}).get("active"):
        tid = scenarios["teacher_absent"].get("teacher_id", "")
        if tid:
            _apply_teacher_absent(resolved, config, day_idx, tid, teacher_subjects, subject_teachers)

    # 2. Lab unavailable — replace lab periods with free (simplified)
    if scenarios.get("lab_unavailable", {}).get("active"):
        lab_subs = scenarios["lab_unavailable"].get("lab_subjects", "Physics,Chemistry,Biology").split(",")
        lab_set = {s.strip() for s in lab_subs if s.strip()}
        for (cid, d, p), (subj, _) in list(resolved.items()):
            if d == day_idx and subj in lab_set:
                resolved[(cid, d, p)] = ("Free period", "")

    # 3. Shortened day
    if scenarios.get("shortened_day", {}).get("active"):
        new_max = scenarios["shortened_day"].get("max_periods", 4)
        _apply_shortened_day(resolved, config, day_idx, new_max)

    # 4. Emergency free period — insert free for a class in a slot
    if scenarios.get("emergency_free", {}).get("active"):
        cid = scenarios["emergency_free"].get("class_id", "")
        period = scenarios["emergency_free"].get("period", 0)
        if cid and (cid, day_idx, period) in resolved:
            resolved[(cid, day_idx, period)] = ("Free period", "")

    # 5. Substitute teacher assigned
    if scenarios.get("substitute", {}).get("active"):
        orig_tid = scenarios["substitute"].get("original_teacher", "")
        sub_tid = scenarios["substitute"].get("substitute_teacher", "")
        if orig_tid and sub_tid:
            for (cid, d, p), (subj, t) in list(resolved.items()):
                if d == day_idx and t == orig_tid:
                    resolved[(cid, d, p)] = (subj, sub_tid)

    return resolved


def _apply_teacher_absent(
    resolved: Dict,
    config: SchoolConfig,
    day_idx: int,
    absent_tid: str,
    teacher_subjects: dict,
    subject_teachers: dict,
) -> None:
    """Replace absent teacher's slots: try substitute, else free period."""
    for (cid, d, p), (subj, tid) in list(resolved.items()):
        if d != day_idx or tid != absent_tid:
            continue
        # Try find free substitute who teaches this subject
        candidates = subject_teachers.get(subj, [])
        candidates = [c for c in candidates if c != absent_tid]
        substitute = None
        for cand in candidates:
            # Check if cand is free this slot (no other assignment)
            busy = any(
                t == cand for (_, dd, pp), (_, t) in resolved.items()
                if dd == day_idx and pp == p
            )
            if not busy:
                substitute = cand
                break
        if substitute:
            resolved[(cid, d, p)] = (subj, substitute)
        else:
            resolved[(cid, d, p)] = ("Free period", "")


def _apply_shortened_day(
    resolved: Dict,
    config: SchoolConfig,
    day_idx: int,
    new_max: int,
) -> None:
    """Drop periods beyond new_max for that day. Replace with free."""
    for (cid, d, p), _ in list(resolved.items()):
        if d == day_idx and p >= new_max:
            resolved[(cid, d, p)] = ("Free period", "")


# ---------------------------------------------------------------------------
# HEATMAP DATA
# ---------------------------------------------------------------------------

def teacher_load_heatmap(
    tt: Dict[Tuple[str, int, int], Tuple[str, str]],
    config: SchoolConfig,
) -> Dict[str, Dict[int, int]]:
    """Teacher -> day_idx -> periods count."""
    teacher_days: Dict[str, Dict[int, int]] = {}
    for (cid, d, p), (subj, tid) in tt.items():
        if p in config.break_period_indices:
            continue
        if tid and tid != "":
            if tid not in teacher_days:
                teacher_days[tid] = {}
            teacher_days[tid][d] = teacher_days[tid].get(d, 0) + 1
    return teacher_days


def class_fatigue_heatmap(
    tt: Dict[Tuple[str, int, int], Tuple[str, str]],
    config: SchoolConfig,
    heavy_subjects: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, Dict[int, float]]:
    """Class -> period -> difficulty density (0-1)."""
    heavy = heavy_subjects or {}
    class_periods: Dict[str, Dict[int, List[str]]] = {}
    for (cid, d, p), (subj, _) in tt.items():
        if p in config.break_period_indices or not subj:
            continue
        if cid not in class_periods:
            class_periods[cid] = {}
        if p not in class_periods[cid]:
            class_periods[cid][p] = []
        class_periods[cid][p].append(subj)
    # Compute density: count heavy subjects per period, normalize
    result: Dict[str, Dict[int, float]] = {}
    for cid, periods in class_periods.items():
        result[cid] = {}
        hsubs = set(heavy.get(cid, ["Mathematics", "Physics", "Chemistry", "Biology"]))
        for p, subs in periods.items():
            count = sum(1 for s in subs if s in hsubs)
            result[cid][p] = min(1.0, count / 3.0)  # 3+ heavy = max
    return result


def day_congestion_heatmap(
    tt: Dict[Tuple[str, int, int], Tuple[str, str]],
    config: SchoolConfig,
) -> Dict[int, int]:
    """Day_idx -> total teaching periods (excluding breaks)."""
    day_totals: Dict[int, int] = {}
    for d in range(len(config.days)):
        day_totals[d] = 0
    for (cid, d, p), (subj, _) in tt.items():
        if p not in config.break_period_indices and subj:
            day_totals[d] = day_totals.get(d, 0) + 1
    return day_totals


def clash_risk_heatmap(
    tt: Dict[Tuple[str, int, int], Tuple[str, str]],
    config: SchoolConfig,
    teachers: List[Teacher],
) -> Dict[str, Any]:
    """Identify cells with clash risk: teacher overload, back-to-back labs."""
    risks = {"teacher_overload": [], "back_to_back_heavy": []}
    teacher_max = {t.teacher_id: t.max_periods_per_day for t in teachers}
    load = teacher_load_heatmap(tt, config)
    for tid, days in load.items():
        for d, count in days.items():
            if count > teacher_max.get(tid, 6):
                risks["teacher_overload"].append({"teacher": tid, "day": d, "count": count})
    return risks
