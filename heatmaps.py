"""
heatmaps.py — Minimal visualizations for Timable
"""
import pandas as pd
import streamlit as st

def teacher_load_heatmap(timetable, teachers, config):
    """Show a heatmap of teacher load per day."""
    data = {t.id: [0]*len(config.days) for t in teachers}
    for (class_id, day, period), (subject, teacher_id) in timetable.items():
        data[teacher_id][day] += 1
    df = pd.DataFrame(data, index=config.days)
    st.write("### Teacher Load Heatmap")
    st.dataframe(df.T)
    st.write("(Rows: Teachers, Columns: Days)")
    
    max_vals = df.T.max().max() if not df.empty else 0
    
    def _style(val):
        if pd.isna(val):
            return ""
        intensity = val / max_vals if max_vals else 0
        return _color_scale(intensity)

    return df.style.applymap(_style).set_caption("Teacher Load (darker = more periods)")


def render_day_congestion_heatmap(
    day_totals: Dict[int, int],
    days: List[str],
) -> pd.DataFrame:
    """Rows=days, Col=total periods."""
    row = [day_totals.get(d, 0) for d in range(len(days))]
    df = pd.DataFrame([row], index=["Periods"], columns=days)
    max_val = max(row) if row else 1

    def _style(val):
        intensity = val / max_val if max_val else 0
        return _color_scale(intensity)

    return df.style.applymap(_style).set_caption("Day Congestion")


def render_class_fatigue_heatmap(
    class_periods: Dict[str, Dict[int, float]],
    num_periods: int,
) -> pd.DataFrame:
    """Rows=classes, Cols=periods. Color by difficulty density."""
    classes = sorted(class_periods.keys())
    data = []
    for cid in classes:
        row = [class_periods.get(cid, {}).get(p, 0) for p in range(num_periods)]
        data.append(row)
    df = pd.DataFrame(data, index=classes, columns=[f"P{p+1}" for p in range(num_periods)])
    return df.style.applymap(lambda v: _color_scale(v) if pd.notna(v) else "").set_caption("Class Fatigue (heavier subjects = hotter)")
