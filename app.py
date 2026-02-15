
import streamlit as st
import streamlit as st
from datetime import timedelta
import time
import numpy as np
from storage import (
    load_teachers, save_teachers, 
    load_classes, save_classes, 
    load_config, save_config,
    load_priority_configs, save_priority_configs,
    load_base_timetable, clear_base_timetable,
    load_scenario_state, clear_scenario_state,
    is_demo_loaded, set_demo_loaded, clear_demo_loaded # <--- THIS FIXES THE NEW ERROR
)
from models import Teacher, Class, ClassSubject, SchoolConfig
from datetime import timedelta
# --- PHASE 10: TESTING CHECKLIST ---
def show_testing_checklist():
    st.markdown("""
    ### Testing Checklist
    - [ ] Export individual class PDF
    - [ ] Export individual teacher PDF
    - [ ] Export multiple selections
    - [ ] Export all
    - [ ] PDFs appear in Printables
    - [ ] Removing printable works
    - [ ] Teacher overload moves visibly
    - [ ] Heatmap animates smoothly
    - [ ] UI does not jump
    - [ ] No state resets
    """)
# --- PHASE 9: FINAL INTEGRATION FLOW ---
def full_timetable_update(generate_or_modify_timetable, recalc_teacher_violations, force_fit_where_possible, compute_heatmaps):
    # save_old_state
    st.session_state.last_timetable = deep_copy_tt(st.session_state.class_timetable)
    # apply_change
    new_tt = generate_or_modify_timetable()
    st.session_state.class_timetable = new_tt
    # recalculate_violations
    violations = recalc_teacher_violations(new_tt)
    # force_fit
    try:
        max_iter = 10
        for _ in range(max_iter):
            new_tt2 = force_fit_where_possible(new_tt, violations)
            if new_tt2 == new_tt:
                break
            new_tt = new_tt2
        st.session_state.class_timetable = new_tt
    except Exception:
        st.session_state.class_timetable = deep_copy_tt(st.session_state.last_timetable)
    # update_heatmaps
    heatmap_data = compute_heatmaps(st.session_state.class_timetable)
    # detect_diff
    diffs = detect_diff(st.session_state.last_timetable, st.session_state.class_timetable)
    st.session_state.heatmap_state = heatmap_data
    st.session_state.diff_log = diffs
    # animate_transitions
    render_heatmap_animated(heatmap_data)
    # render_updated_ui (example: timetable and notification)
    render_timetable_with_diff(st.session_state.class_timetable, diffs)
    if diffs:
        for d in diffs:
            queue_notification(f"{d[0]}: {d[3]} → {d[4]} ({d[1]} {d[2]})")
    render_notification_bar()
# --- PHASE 8: UI STABILITY RULES ---
def stable_panel(panel_func, *args, **kwargs):
    with st.container():
        panel_func(*args, **kwargs)

# Add global CSS for fixed-height containers and lock layout
st.markdown("""

""", unsafe_allow_html=True)
# --- PHASE 7: USER-VISIBLE CHANGE FEEDBACK ---
def queue_notification(msg, duration=3):
    if "notification_queue" not in st.session_state:
        st.session_state.notification_queue = []
    st.session_state.notification_queue.append({"msg": msg, "countdown": duration})

def render_notification_bar():
    if "notification_queue" not in st.session_state:
        st.session_state.notification_queue = []
    if st.session_state.notification_queue:
        notif = st.session_state.notification_queue[0]
        st.markdown(f"<div style='background:#e0f7fa;padding:8px 16px;border-radius:8px;box-shadow:0 2px 8px #b2ebf2;font-weight:600;animation:fadein 0.5s;'>\U0001F501 {notif['msg']}</div>", unsafe_allow_html=True)
        notif["countdown"] -= 1
        if notif["countdown"] <= 0:
            st.session_state.notification_queue.pop(0)
        else:
            time.sleep(1)
            st.experimental_rerun()
import time
import numpy as np
# --- PHASE 6: HEATMAP ANIMATION SYSTEM ---
def interpolate_heatmaps(prev, curr, steps=10):
    if prev is None or curr is None:
        return [curr]
    prev = np.array(prev)
    curr = np.array(curr)
    frames = [prev + (curr - prev) * (i / (steps - 1)) for i in range(steps)]
    return frames

def render_heatmap_animated(curr_heatmap):
    prev_heatmap = st.session_state.get("prev_heatmap")
    st.session_state.prev_heatmap = curr_heatmap
    frames = interpolate_heatmaps(prev_heatmap, curr_heatmap, steps=10)
    heatmap_placeholder = st.empty()
    for frame in frames:
        # Use matplotlib for smooth gradients, no grid lines
        import matplotlib.pyplot as plt
        plt.figure(figsize=(6, 2))
        plt.imshow(frame, cmap="YlOrRd", aspect="auto", interpolation="bilinear")
        plt.axis("off")
        plt.tight_layout(pad=0)
        # Glow halo effect
        plt.gca().set_facecolor("#fffbe6")
        heatmap_placeholder.pyplot(plt)
        plt.close()
        time.sleep(0.03)  # Reduce for UI stability
# --- PHASE 5: VISUAL DIFF SYSTEM ("WHAT CHANGED") ---
def render_timetable_with_diff(timetable, diff_log):
    # Example: timetable is a dict[class][day][period]
    # diff_log: list of (class, day, period, old_val, new_val)
    diff_cells = set((cid, day, period) for cid, day, period, _, _ in diff_log)
    # Add CSS for animation
    st.markdown("""
        <style>
        .changed-cell {
            animation: glow 1s ease-in-out 0s 2 alternate;
            background: #ffe066;
            border-radius: 6px;
            box-shadow: 0 0 8px 2px #ffd700;
            transition: background 0.5s;
            padding: 2px 4px;
            display: inline-block;
        }
        @keyframes glow {
            0% { box-shadow: 0 0 8px 2px #ffd700; }
            100% { box-shadow: 0 0 16px 6px #ffec99; }
        }
        </style>
    """, unsafe_allow_html=True)
    # Render timetable (simplified example)
    for cid in timetable:
        st.markdown(f"### {cid}")
        for day in timetable[cid]:
            row = ""
            for period in timetable[cid][day]:
                cell = timetable[cid][day][period]
                if (cid, day, period) in diff_cells:
                    # Find diff for tooltip
                    for d in diff_log:
                        if d[0] == cid and d[1] == day and d[2] == period:
                            old_val, new_val = d[3], d[4]
                            break
                    tooltip = f"Moved from {old_val} → {new_val}" if old_val != new_val else "Changed"
                    row += f"<span class='changed-cell' title='{tooltip}'>{cell}</span> "
                else:
                    row += f"{cell} "
            st.markdown(f"<div style='min-height:28px'>{row}</div>", unsafe_allow_html=True)
    # Clear diff_log after animation
    st.session_state.diff_log = []
# --- PHASE 4: REACTIVE TIMETABLE UPDATE PIPELINE ---
def reactive_timetable_update(generate_or_modify_timetable, recalc_teacher_violations, force_fit_where_possible, compute_heatmaps):
    # Save old state before change
    st.session_state.last_timetable = deep_copy_tt(st.session_state.class_timetable)

    # Apply timetable change
    new_tt = generate_or_modify_timetable()
    st.session_state.class_timetable = new_tt

    # Run reactive update chain
    violations = recalc_teacher_violations(new_tt)
    try:
        max_iter = 10
        for _ in range(max_iter):
            new_tt2 = force_fit_where_possible(new_tt, violations)
            if new_tt2 == new_tt:
                break
            new_tt = new_tt2
        st.session_state.class_timetable = new_tt
    except Exception:
        st.session_state.class_timetable = deep_copy_tt(st.session_state.last_timetable)

    heatmap_data = compute_heatmaps(st.session_state.class_timetable)
    diffs = detect_diff(st.session_state.last_timetable, st.session_state.class_timetable)
    st.session_state.heatmap_state = heatmap_data
    st.session_state.diff_log = diffs
# --- PHASE 3: PRINTABLES PANEL ---
def printables_panel():
    with st.container():
        for idx, item in enumerate(st.session_state.printables[::-1]):
            with st.container():
                st.markdown(f"\U0001F4C4 **{item['name']}** — {item['time']}")
                st.download_button("Download", open(item["path"], "rb"), file_name=item["name"], key=f"dl_{idx}")
                if st.button("Delete", key=f"del_{idx}"):
                    # Remove from printables (reverse index)
                    real_idx = len(st.session_state.printables) - 1 - idx
                    st.session_state.printables.pop(real_idx)
                    st.experimental_rerun()

# --- PHASE 2: ADVANCED PDF EXPORT UI ---
import streamlit as st

# Example: all_classes and all_teachers should be defined elsewhere in your app
# all_classes = ...
# all_teachers = ...
# generate_selected_pdfs = ...

def export_panel():
    with st.expander("\U0001F4E5 Export Timetables", expanded=False):
        # Use session_state for selections
        if "class_choices" not in st.session_state:
            st.session_state.class_choices = []
        if "teacher_choices" not in st.session_state:
            st.session_state.teacher_choices = []
        if "export_mode" not in st.session_state:
            st.session_state.export_mode = "Individual PDFs"

        st.session_state.class_choices = st.multiselect(
            "Select Classes", all_classes, default=st.session_state.class_choices, key="class_multiselect")
        st.session_state.teacher_choices = st.multiselect(
            "Select Teachers", all_teachers, default=st.session_state.teacher_choices, key="teacher_multiselect")
        st.session_state.export_mode = st.radio(
            "Export Mode", ["Individual PDFs", "Merge into Single PDF"], index=0 if st.session_state.export_mode=="Individual PDFs" else 1, key="export_mode_radio")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Select All", key="select_all_btn"):
                st.session_state.class_choices = all_classes.copy()
                st.session_state.teacher_choices = all_teachers.copy()
        with col2:
            if st.button("Clear All", key="clear_all_btn"):
                st.session_state.class_choices = []
                st.session_state.teacher_choices = []

        if st.button("\U0001F4C4 Generate & Download", key="generate_download_btn"):
            pdf_files = generate_selected_pdfs(
                st.session_state.class_choices,
                st.session_state.teacher_choices,
                st.session_state.export_mode)
            for pdf in pdf_files:
                st.session_state.printables.append({
                    "name": pdf.name,
                    "path": pdf.path,
                    "time": timestamp(),
                })
            st.success("PDFs generated and added to Printables")

# Call export_panel() in the Export/Print tab location
"""
🧠 SMART TIMETABLE BUILDER — Smooth, stable, alive
==================================================
- Notifications count down smoothly (fragment run_every)
- st.form() prevents screen jump while typing
- History log like Chrome
- All data persisted to disk
- Priority section optional (timetable works without it)
# --- Ensure Streamlit is imported first ---
import streamlit as st
import streamlit as st
from models import Teacher, Class, SchoolConfig
from storage import load_teachers, save_teachers, load_classes, save_classes, load_config, save_config
from solver import build_timetable
from ui_forms import teacher_form, class_form

st.set_page_config(page_title="Smart Timetable Builder", page_icon="📅", layout="wide")
st.title("📅 Smart Timetable Builder")

# Load data
teachers = load_teachers()
classes = load_classes()
config = load_config() or SchoolConfig()

tab1, tab2, tab3 = st.tabs(["Teachers", "Classes", "Timetable"])

with tab1:
    st.header("Teachers")
    for t in teachers:
        st.write(f"**{t.name}** — Subjects: {', '.join(t.subjects)}")
    if st.button("Add Teacher"):
        new_teacher = teacher_form()
        if new_teacher:
            teachers.append(new_teacher)
            save_teachers(teachers)
            st.experimental_rerun()

with tab2:
    st.header("Classes")
    for c in classes:
        st.write(f"**{c.name}** — Subjects: {', '.join(s.subject for s in c.subjects)}")
    if st.button("Add Class"):
        new_class = class_form()
        if new_class:
            classes.append(new_class)
            save_classes(classes)
            st.experimental_rerun()

with tab3:
    st.header("Timetable Preview")
    if st.button("Build Timetable"):
        timetable = build_timetable(classes, teachers, config)
        for (class_id, day, period), (subject, teacher_id) in timetable.items():
            st.write(f"Class {class_id} — {config.days[day]} P{period+1}: {subject} ({teacher_id})")
# CSS — Animations (smooth, no layout shift)
# ---------------------------------------------------------------------------
"""
ANIMATION_CSS = """
<style>
    /* Dark theme - gray / neutral */
    .main { background-color: #0f0f0f; }
    .main .block-container { padding-top: 32px; }
    h1 { color: #fafafa !important; }
    h2, h3 { color: #e4e4e7 !important; }
    p, span, label { color: #a1a1aa !important; }
    .stMarkdown { color: #a1a1aa; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #18181b 0%, #0f0f0f 100%);
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label { color: #e4e4e7 !important; }

    /* Tab bar */
    .stTabs {
        background-color: #0f0f0f;
        padding: 6px 8px;
        border-radius: 10px;
    }
    .stTabs > div > div {
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #111113;
        border-radius: 10px;
        padding: 4px;
        border: 1px solid #27272a;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.02), 0 12px 28px rgba(0,0,0,0.45);
        transition: all 0.25s ease;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #a1a1aa;
        border-radius: 6px;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #e4e4e7;
        background-color: rgba(63,63,70,0.35);
    }

    .stTabs [aria-selected="true"] {
        background-color: #27272a !important;
        color: #fafafa !important;
    }
    .toast-item {
        font-size: 13px;
        color: #e4e4e7;
        max-width: 300px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        animation: toastFadeIn 0.3s ease;
    }
    @keyframes toastFadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .toast-msg { flex: 1; }
    .toast-countdown { font-size: 11px; color: #71717a; min-width: 24px; }

    /* Buttons */
    button {
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    }
    button:active { transform: translateY(0); }
    .stButton button[kind="primary"] {
        background: #e4e4e7;
        color: #111827;
        border: 1px solid #52525b;
        box-shadow: 0 6px 14px rgba(0,0,0,0.35);
    }
    .stButton button[kind="primary"]:hover {
        background: #f4f4f5;
        color: #020617;
        box-shadow: 0 10px 20px rgba(0,0,0,0.45);
    }
    .stButton button[kind="primary"]:active {
        background: #d4d4d8;
        color: #111827;
    }

    /* Expanders / cards */
    .stExpander {
        animation: cardFadeIn 0.35s ease;
        background-color: #18181b;
        border: 1px solid #27272a;
        border-radius: 8px;
    }
    @keyframes cardFadeIn {
        from { opacity: 0; transform: translateY(4px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Tables — full text visible, no truncation */
    [data-testid="stDataFrame"] {
        animation: tableFadeIn 0.4s ease;
    }
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        min-width: 90px !important;
        max-width: 180px !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        padding: 10px 12px !important;
        line-height: 1.4 !important;
    }
    [data-testid="stDataFrame"] .stDataFrame {
        width: 100% !important;
    }


    @keyframes tableFadeIn {
        from { opacity: 0; }
        to { opacity: 1; }


    }
</style>
"""

st.markdown(ANIMATION_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# SESSION STATE — Load from disk
# ---------------------------------------------------------------------------





# ---------------------------------------------------------------------------
# DEMO DATA — Predefined for quick testing
# ---------------------------------------------------------------------------

def _get_demo_teachers():
    """Demo teachers: Science, Commerce, Humanities streams. Realistic names."""
    return [
        Teacher("Eric Simon", ["Physics"], ["11SCI", "12SCI"], 5),
        Teacher("Aisha Khan", ["Chemistry"], ["11SCI", "12SCI"], 5),
        Teacher("Rahul Mehta", ["Mathematics"], ["11SCI", "12SCI", "11COM", "12COM"], 5),
        Teacher("Neha Verma", ["Biology"], ["11SCI", "12SCI"], 5),
        Teacher("Daniel Brooks", ["English"], ["11SCI", "12SCI", "11COM", "12COM", "11HUM", "12HUM"], 4),
        Teacher("Priya Nair", ["Economics"], ["11COM", "12COM"], 5),
        Teacher("Arjun Patel", ["Accountancy"], ["11COM", "12COM"], 5),
        Teacher("Kavita Rao", ["Business Studies"], ["11COM", "12COM"], 4),
        Teacher("Sofia Mendes", ["History"], ["11HUM", "12HUM"], 5),
        Teacher("Aman Gupta", ["Political Science"], ["11HUM", "12HUM"], 5),
        Teacher("Ritu Chawla", ["Geography"], ["11HUM", "12HUM"], 4),
        Teacher("Marcus Lee", ["Physical Education"], ["11SCI", "12SCI", "11COM", "12COM", "11HUM", "12HUM"], 3),
    ]


def _get_demo_classes():
    """Demo classes: 11SCI, 12SCI, 11COM, 12COM, 11HUM, 12HUM."""
    return [
        Class("11SCI", [
            ClassSubject("Physics", 6, "Eric Simon"),
            ClassSubject("Chemistry", 6, "Aisha Khan"),
            ClassSubject("Mathematics", 6, "Rahul Mehta"),
            ClassSubject("Biology", 6, "Neha Verma"),
            ClassSubject("English", 4, "Daniel Brooks"),
            ClassSubject("Physical Education", 2, "Marcus Lee"),
        ]),
        Class("12SCI", [
            ClassSubject("Physics", 6, "Eric Simon"),
            ClassSubject("Chemistry", 6, "Aisha Khan"),
            ClassSubject("Mathematics", 6, "Rahul Mehta"),
            ClassSubject("Biology", 6, "Neha Verma"),
            ClassSubject("English", 4, "Daniel Brooks"),
            ClassSubject("Physical Education", 2, "Marcus Lee"),
        ]),
        Class("11COM", [
            ClassSubject("Accountancy", 6, "Arjun Patel"),
            ClassSubject("Business Studies", 6, "Kavita Rao"),
            ClassSubject("Economics", 6, "Priya Nair"),
            ClassSubject("Mathematics", 4, "Rahul Mehta"),
            ClassSubject("English", 4, "Daniel Brooks"),
            ClassSubject("Physical Education", 2, "Marcus Lee"),
        ]),
        Class("12COM", [
            ClassSubject("Accountancy", 6, "Arjun Patel"),
            ClassSubject("Business Studies", 6, "Kavita Rao"),
            ClassSubject("Economics", 6, "Priya Nair"),
            ClassSubject("Mathematics", 4, "Rahul Mehta"),
            ClassSubject("English", 4, "Daniel Brooks"),
            ClassSubject("Physical Education", 2, "Marcus Lee"),
        ]),
        Class("11HUM", [
            ClassSubject("History", 6, "Sofia Mendes"),
            ClassSubject("Political Science", 6, "Aman Gupta"),
            ClassSubject("Geography", 6, "Ritu Chawla"),
            ClassSubject("English", 4, "Daniel Brooks"),
            ClassSubject("Physical Education", 2, "Marcus Lee"),
        ]),
        Class("12HUM", [
            ClassSubject("History", 6, "Sofia Mendes"),
            ClassSubject("Political Science", 6, "Aman Gupta"),
            ClassSubject("Geography", 6, "Ritu Chawla"),
            ClassSubject("English", 4, "Daniel Brooks"),
            ClassSubject("Physical Education", 2, "Marcus Lee"),
        ]),
    ]


def _load_demo_data() -> bool:
    """
    Inject demo teachers and classes. Skip duplicates by ID.
    Saves to disk. Sets demo_loaded flag so button disables.
    Returns True if any data was added.
    """
    existing_t_ids = {t.teacher_id for t in st.session_state.teachers}
    existing_c_ids = {c.class_id for c in st.session_state.classes}
    added = False
    for t in _get_demo_teachers():
        if t.teacher_id not in existing_t_ids:
            st.session_state.teachers.append(t)
            existing_t_ids.add(t.teacher_id)
            added = True
    for c in _get_demo_classes():
        if c.class_id not in existing_c_ids:
            st.session_state.classes.append(c)
            existing_c_ids.add(c.class_id)
            added = True
    if added:
        save_teachers(st.session_state.teachers)
        save_classes(st.session_state.classes)
    set_demo_loaded()  # Always disable button after first use
    append_history("demo", "Demo Data", "Loaded demo teachers and classes", "")
    st.session_state.class_timetable = None
    st.session_state.teacher_timetable = None
    return added


# ---------------------------------------------------------------------------
# NOTIFICATIONS — Stackable, smooth countdown via fragment
# ---------------------------------------------------------------------------

def show_toast(msg: str, duration_sec: int = 3) -> None:
    """Add a notification. Stackable — new ones don't replace old."""
    uid = f"n_{time.time()}_{id(msg)}"
    st.session_state.notifications.append({
        "msg": msg,
        "until": time.time() + duration_sec,
        "id": uid,
    })

@st.fragment(run_every=timedelta(seconds=1))
def _notification_ticker():
    """
    Runs every second. Removes expired toasts, countdown ticks smoothly.
    Fragment reruns only this block — no full-page refresh.
    """
    now = time.time()
    notifications = st.session_state.get("notifications", [])
    active = [n for n in notifications if n["until"] > now]
    if len(active) != len(notifications):
        st.session_state.notifications = active

    if not active:
        return

    for n in active:
        remaining = max(0, int(n["until"] - now))
        st.markdown(
            f'<div class="toast-item">'
            f'<span class="toast-msg">{n["msg"]}</span>'
            f'<span class="toast-countdown">{remaining}s</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# SIDEBAR — Config (persisted)
# ---------------------------------------------------------------------------

st.sidebar.title("⚙️ School Setup")

if "config" not in st.session_state:
    from storage import load_config
    from models import SchoolConfig
    st.session_state.config = load_config() or SchoolConfig()

cfg = st.session_state.config

with st.sidebar.form("sidebar_config", clear_on_submit=False):
    st.markdown("**📆 Days & Periods**")
    days_input = st.text_input(
        "Days (comma-separated)",
        value=",".join(cfg.days) if cfg.days else "Mon,Tue,Wed,Thu,Fri",
        key="sb_days",
    )
    periods = st.number_input(
        "Periods per day",
        min_value=4,
        max_value=12,
        value=cfg.periods_per_day or 8,
        key="sb_periods",
    )
    st.markdown("**🥤 Break Periods**")
    st.caption("Add in the fields below (period number, name)")
    break_p_str = st.text_area(
        "Break periods (one per line: period,name)",
        value="\n".join(f"{p+1},{n}" for p, n in sorted(cfg.break_periods.items())),
        height=80,
        key="sb_breaks",
    )
    if st.form_submit_button("Apply Config"):
        days = [d.strip() for d in days_input.split(",") if d.strip()]
        break_periods = {}
        for line in break_p_str.strip().split("\n"):
            parts = line.strip().split(",")
            if len(parts) >= 2:
                try:
                    p = int(parts[0].strip()) - 1
                    name = parts[1].strip()
                    if name:
                        break_periods[p] = name
                except ValueError:
                    pass
        if days:
            st.session_state.config = SchoolConfig(
                days=days,
                periods_per_day=int(periods),
                break_periods=break_periods or cfg.break_periods,
            )
            save_config(st.session_state.config)
            show_toast("Config saved")
            st.rerun()

st.sidebar.markdown("---")
with st.sidebar.expander("🧪 Demo / Testing"):
    demo_loaded = is_demo_loaded()
    if demo_loaded:
        st.caption("Demo data already loaded.")
        st.button("Load Demo Data", key="demo_btn", disabled=True)
    else:
        if st.button("Load Demo Data", key="demo_btn"):
            if _load_demo_data():
                show_toast("Demo data loaded successfully")
            else:
                show_toast("Demo data already present (no duplicates added)")
            st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear all data"):
    st.session_state.teachers = []
    st.session_state.classes = []
    st.session_state.priority_configs = []
    st.session_state.class_timetable = None
    st.session_state.teacher_timetable = None
    st.session_state.scenario_state = {"selected_day": 0, "scenarios": {}}
    st.session_state.editing_teacher = None
    st.session_state.editing_class = None
    save_teachers([])
    save_classes([])
    save_priority_configs([])
    clear_base_timetable()
    clear_scenario_state()
    clear_demo_loaded()
    append_history("clear", "All", "All teachers and classes cleared", "")
    show_toast("All data cleared")
    st.rerun()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

st.title("📅 Smart Timetable Builder")

def _init_session():
    import storage
    
    # 1. Load Data from storage
    if "initialized" not in st.session_state:
        st.session_state.teachers = storage.load_teachers()
        st.session_state.classes = storage.load_classes()
        st.session_state.config = storage.load_config() or SchoolConfig()
        # Fix for the scenario error you saw earlier
        st.session_state.scenario_state = storage.load_scenario_state() or {"selected_day": 0, "scenarios": {}}
        st.session_state.initialized = True

    # 2. UI State Defaults (Fixes your current "editing_teacher" error)
    if "editing_teacher" not in st.session_state:
        st.session_state.editing_teacher = None
    if "editing_class" not in st.session_state:
        st.session_state.editing_class = None
    if "class_timetable" not in st.session_state:
        st.session_state.class_timetable = None

# Call the function right after defining it
_init_session()
st.markdown("*Smooth, stable, alive. Data persists across refresh.*")

# Notification slot — fixed height to prevent layout shift
st.markdown('<div id="notification-slot"></div>', unsafe_allow_html=True)
_notification_ticker()

tabs = st.tabs([
    "👥 Teachers & Classes",
    "📚 Saved Data",
    "🕓 History",
    "📋 Class Timetables",
    "👨‍🏫 Teacher Timetables",
    "🔄 Rotation",
    "🧪 What-If Lab",
    "🔥 Insights",
    "🌌 Energy Maps",
    "📄 PDF Export",
])
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = tabs
# ----- TAB 10: Energy Maps (Animated, Fluid) -----
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

with tab10:
    st.header("🌌 Energy Maps")
    st.markdown("""
    <span style='font-size:1.2em'>
    <b>Heatmaps, reimagined:</b> <br>
    <span style='color:#fbbf24'>🔥 Alive</span>, <span style='color:#38bdf8'>🌊 Fluid</span>, <span style='color:#a3e635'>🧠 Intuitive</span>.<br>
    <ul>
    <li>Glowing, animated energy fields</li>
    <li>Smooth gradients, halos, wave motion</li>
    <li>Soft pulsing, no harsh grid lines</li>
    </ul>
    </span>
    """, unsafe_allow_html=True)

    base_tt = st.session_state.class_timetable
    if not base_tt:
        st.info("Generate a timetable first.")
    else:
        cfg = st.session_state.config
        ss = st.session_state.scenario_state
        resolved = apply_scenarios(base_tt, cfg, st.session_state.teachers, st.session_state.classes, ss)

        # UI Controls
        col1, col2, col3, col4 = st.columns([2,1,1,1])
        with col1:
            emap_type = st.selectbox(
                "Energy Map Type",
                [
                    "Teacher Load Energy Field",
                    "Class Fatigue Flow Map",
                    "Congestion Pressure Field",
                    "What-If Impact Diffusion Map"
                ],
                key="emap_type",
            )
        with col2:
            anim_speed = st.slider("Animation Speed", 0.1, 2.0, 0.5, 0.05, key="emap_speed")
        with col3:
            glow_intensity = st.slider("Glow Intensity", 0.0, 2.0, 1.0, 0.05, key="emap_glow")
        with col4:
            motion_on = st.toggle("Motion", value=True, key="emap_motion")

        # Helper: animated energy field
        def plot_energy_field(Z, row_labels, col_labels, color_map, orb_mode=False, pulse=1.0, flow=None, glow=1.0, animate=False, frame_count=20):
            # Z: 2D np.array, color_map: px.colors.sequential
            # orb_mode: draw glowing orbs per cell (for teacher load)
            # flow: 2D vector field (for flow maps)
            # pulse: controls pulsing
            # animate: if True, returns Plotly animation
            nrows, ncols = Z.shape
            fig = go.Figure()
            if orb_mode:
                # Each cell: glowing orb, radius = workload
                for i in range(nrows):
                    for j in range(ncols):
                        val = Z[i, j]
                        color = px.colors.sample_colorscale(color_map, (val-np.min(Z))/(np.ptp(Z)+1e-6))[0]
                        fig.add_trace(go.Scatter(
                            x=[j], y=[i],
                            mode="markers",
                            marker=dict(
                                size=30 + 40*val/np.max(Z),
                                color=color,
                                opacity=0.7 + 0.3*glow,
                                line=dict(width=0),
                                sizemode="diameter",
                                symbol="circle",
                                blur=10*glow,
                                ),
                            showlegend=False,
                            hoverinfo="skip",
                        ))
                # Glow halo: overlay blurred heatmap
                fig.add_trace(go.Heatmap(
                    z=Z,
                    colorscale=color_map,
                    opacity=0.25*glow,
                    showscale=False,
                ))
            else:
                # Smooth field
                fig.add_trace(go.Heatmap(
                    z=Z,
                    colorscale=color_map,
                    zsmooth="best",
                    showscale=False,
                    opacity=0.85,
                ))
            # Optionally overlay flow vectors
            if flow is not None:
                U, V = flow
                fig.add_trace(go.Cone(
                    x=np.tile(np.arange(ncols), nrows),
                    y=np.repeat(np.arange(nrows), ncols),
                    u=U.flatten(), v=V.flatten(),
                    sizemode="scaled",
                    sizeref=2,
                    anchor="tail",
                    colorscale="Blues",
                    showscale=False,
                    opacity=0.5,
                ))
            fig.update_layout(
                xaxis=dict(
                    tickvals=list(range(ncols)),
                    ticktext=col_labels,
                    showgrid=False,
                    zeroline=False,
                    showticklabels=True,
                ),
                yaxis=dict(
                    tickvals=list(range(nrows)),
                    ticktext=row_labels,
                    showgrid=False,
                    zeroline=False,
                    showticklabels=True,
                    autorange="reversed",
                ),
                margin=dict(l=40, r=20, t=20, b=40),
                plot_bgcolor="#18181b",
                paper_bgcolor="#18181b",
                height=60*nrows+60,
                width=80*ncols+80,
            )
            return fig

        # Animate: Perlin-like noise for fluid motion
        def perlin_noise(shape, seed=0):
            np.random.seed(seed)
            base = np.random.rand(*shape)
            from scipy.ndimage import gaussian_filter
            return gaussian_filter(base, sigma=shape[0]/3)

        # Main logic per map type
        if emap_type == "Teacher Load Energy Field":
            load = teacher_load_heatmap(resolved, cfg)
            teachers = [t.teacher_id for t in st.session_state.teachers]
            days = cfg.days
            Z = np.array([[load.get((tid, d), 0) for d in range(len(days))] for tid in teachers])
            color_map = px.colors.sequential.YlOrRd
            orb_mode = True
            # Animate: pulse and flow
            if motion_on:
                t = time.time() * anim_speed
                pulse = 1.0 + 0.15*np.sin(t)
                # Simulate flow: gradient of Z
                U, V = np.gradient(Z.astype(float))
                U = U * 0.5 * np.sin(t)
                V = V * 0.5 * np.cos(t)
            else:
                pulse = 1.0
                U = V = None
            fig = plot_energy_field(Z*pulse, teachers, days, color_map, orb_mode=True, pulse=pulse, flow=(U,V) if motion_on else None, glow=glow_intensity, animate=motion_on)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.caption("Rows = teachers, Cols = days. Each orb: workload. Color: green→yellow→red. Glow, pulse, and flow animate.")

        elif emap_type == "Class Fatigue Flow Map":
            pcs = getattr(st.session_state, "priority_configs", None) or []
            heavy_map = {pc.class_id: pc.heavy_subjects for pc in pcs}
            fatigue = class_fatigue_heatmap(resolved, cfg, heavy_map)
            classes = sorted(fatigue.keys())
            periods = list(range(cfg.periods_per_day))
            Z = np.array([fatigue[c] for c in classes])
            color_map = px.colors.sequential.Plasma
            # Animate: ripple effect
            if motion_on:
                t = time.time() * anim_speed
                ripple = 1.0 + 0.2*np.sin(np.linspace(0, np.pi*2, Z.shape[1]) + t)
                Z_anim = Z * ripple
            else:
                Z_anim = Z
            fig = plot_energy_field(Z_anim, classes, [f"P{p+1}" for p in periods], color_map, orb_mode=False, glow=glow_intensity, animate=motion_on)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.caption("Rows = classes, Cols = periods. Ripple = heavy clusters. Colors pulse with load.")

        elif emap_type == "Congestion Pressure Field":
            cong = day_congestion_heatmap(resolved, cfg)
            days = cfg.days
            Z = np.array([cong[d] for d in range(len(days))]).reshape(1, -1)
            color_map = px.colors.sequential.YlGnBu
            # Animate: pulse per day
            if motion_on:
                t = time.time() * anim_speed
                pulse = 1.0 + 0.2*np.sin(np.linspace(0, np.pi*2, Z.shape[1]) + t)
                Z_anim = Z * pulse
            else:
                Z_anim = Z
            fig = plot_energy_field(Z_anim, ["All classes"], days, color_map, orb_mode=False, glow=glow_intensity, animate=motion_on)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.caption("Entire week as pressure map. Heavier days pulse stronger.")

        elif emap_type == "What-If Impact Diffusion Map":
            # Simulate: after scenario, show wave spread from affected slots
            # For demo: pick a random slot as 'impacted', diffuse out
            days = cfg.days
            periods = list(range(cfg.periods_per_day))
            shape = (len(days), len(periods))
            impact = np.zeros(shape)
            # Pick a slot (center or random)
            center = (len(days)//2, len(periods)//2)
            impact[center] = 1.0
            # Diffuse: Gaussian blur
            from scipy.ndimage import gaussian_filter
            t = time.time() * anim_speed if motion_on else 0
            sigma = 1.5 + 0.5*np.sin(t)
            Z = gaussian_filter(impact, sigma=sigma)
            color_map = px.colors.sequential.PuRd
            fig = plot_energy_field(Z, days, [f"P{p+1}" for p in periods], color_map, orb_mode=False, glow=glow_intensity, animate=motion_on)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.caption("After scenario: wave spreads from affected slot. Ripple effects visualized.")

        # Fallback: static if motion off
        if not motion_on:
            st.info("Animation is off. Showing static energy field.")


# ----- TAB 1: Teachers & Classes -----
with tab1:
    st.header("1. Add Teachers")
    editing_t = st.session_state.editing_teacher
    ft = st.session_state.form_teacher

    with st.expander("➕ Add a teacher" if editing_t is None else "✏️ Edit teacher", expanded=True):
        def on_teacher_save(t_id: str, subj_list: list, sec_list: list, t_max: int):
            t = Teacher(teacher_id=t_id, subjects=subj_list, sections=sec_list, max_periods_per_day=t_max)
            if editing_t is not None:
                st.session_state.teachers[editing_t] = t
                show_toast(f"Teacher {t_id} updated")
                append_history("edit", f"Teacher {t_id}", f"Updated teacher {t_id}", "")
            else:
                st.session_state.teachers.append(t)
                show_toast(f"Teacher {t_id} added")
                append_history("add", f"Teacher {t_id}", f"Added teacher {t_id}", "")
            save_teachers(st.session_state.teachers)
            st.session_state.form_teacher = {"id": "", "subjects": "", "sections": "", "max": 6}
            st.session_state.editing_teacher = None
            st.session_state.class_timetable = None
            st.session_state.teacher_timetable = None
            st.rerun()

        def on_teacher_cancel():
            st.session_state.editing_teacher = None
            st.session_state.form_teacher = {"id": "", "subjects": "", "sections": "", "max": 6}
            st.rerun()

        render_teacher_form(editing_t, ft, on_teacher_save, on_teacher_cancel)

    if st.session_state.teachers:
        st.subheader("Teachers")
        for i, t in enumerate(st.session_state.teachers):
            with st.container():
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    st.markdown(f"**{t.teacher_id}** — {', '.join(t.subjects)} · Max {t.max_periods_per_day}/day")
                with c2:
                    if st.button("Edit", key=f"t_edit_{i}"):
                        st.session_state.editing_teacher = i
                        st.session_state.form_teacher = get_edit_buffer_teacher(t)
                        st.rerun()
                with c3:
                    if st.button("Remove", key=f"t_rm_{i}"):
                        name = t.teacher_id
                        st.session_state.teachers.pop(i)
                        save_teachers(st.session_state.teachers)
                        st.session_state.class_timetable = None
                        st.session_state.teacher_timetable = None
                        append_history("delete", f"Teacher {name}", f"Removed teacher {name}", "")
                        show_toast(f"Teacher {name} removed")
                        st.rerun()

    st.markdown("---")
    st.header("2. Add Classes")
    editing_c = st.session_state.editing_class
    fc = st.session_state.form_class

    with st.expander("➕ Add a class" if editing_c is None else "✏️ Edit class", expanded=True):
        def on_class_save(c_id: str, subs: list):
            cls = Class(class_id=c_id, subjects=subs)
            if editing_c is not None:
                st.session_state.classes[editing_c] = cls
                show_toast(f"Class {c_id} updated")
                append_history("edit", f"Class {c_id}", f"Updated class {c_id}", "")
            else:
                st.session_state.classes.append(cls)
                show_toast(f"Class {c_id} added")
                append_history("add", f"Class {c_id}", f"Added class {c_id}", "")
            save_classes(st.session_state.classes)
            st.session_state.form_class = {"id": "", "subjects": ""}
            st.session_state.editing_class = None
            st.session_state.class_timetable = None
            st.session_state.teacher_timetable = None
            st.rerun()

        def on_class_cancel():
            st.session_state.editing_class = None
            st.session_state.form_class = {"id": "", "subjects": ""}
            st.rerun()

        render_class_form(editing_c, fc, on_class_save, on_class_cancel)

    if st.session_state.classes:
        st.subheader("Classes")
        for i, c in enumerate(st.session_state.classes):
            subj_str = ", ".join(f"{cs.subject}({cs.weekly_periods}w)" for cs in c.subjects)
            with st.container():
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    st.markdown(f"**{c.class_id}** — {subj_str}")
                with c2:
                    if st.button("Edit", key=f"c_edit_{i}"):
                        st.session_state.editing_class = i
                        st.session_state.form_class = get_edit_buffer_class(c)
                        st.rerun()
                with c3:
                    if st.button("Remove", key=f"c_rm_{i}"):
                        name = c.class_id
                        st.session_state.classes.pop(i)
                        st.session_state.priority_configs = [
                            p for p in st.session_state.priority_configs if p.class_id != name
                        ]
                        save_classes(st.session_state.classes)
                        save_priority_configs(st.session_state.priority_configs)
                        st.session_state.class_timetable = None
                        st.session_state.teacher_timetable = None
                        append_history("delete", f"Class {name}", f"Removed class {name}", "")
                        show_toast(f"Class {name} removed")
                        st.rerun()

    st.markdown("---")
    st.header("3. Priority Settings (Optional)")
    st.caption("Leave empty if you don't need priority scheduling. Timetable still generates.")
    for i, c in enumerate(st.session_state.classes):
        with st.expander(f"Priorities for {c.class_id}"):
            pc = next((p for p in st.session_state.priority_configs if p.class_id == c.class_id), None)
            if pc is None:
                pc = ClassPriorityConfig(class_id=c.class_id)
                st.session_state.priority_configs.append(pc)
            with st.form(f"prio_form_{c.class_id}"):
                prio = st.text_input("Priority (early) subjects", value=",".join(pc.priority_subjects), key=f"prio_{c.class_id}")
                weak = st.text_input("Weak subjects", value=",".join(pc.weak_subjects), key=f"weak_{c.class_id}")
                heavy = st.text_input("Heavy subjects", value=",".join(pc.heavy_subjects), key=f"heavy_{c.class_id}")
                if st.form_submit_button("Save"):
                    pc.priority_subjects = [s.strip() for s in prio.split(",") if s.strip()]
                    pc.weak_subjects = [s.strip() for s in weak.split(",") if s.strip()]
                    pc.heavy_subjects = [s.strip() for s in heavy.split(",") if s.strip()]
                    save_priority_configs(st.session_state.priority_configs)
                    show_toast(f"Priorities for {c.class_id} saved")
                    st.rerun()


# ----- TAB 2: Saved Data -----
with tab2:
    st.header("📚 Saved Data")
    editing_t = st.session_state.editing_teacher
    editing_c = st.session_state.editing_class

    if editing_t is not None:
        with st.expander("✏️ Edit teacher", expanded=True):
            t = st.session_state.teachers[editing_t]
            def _on_hist_t_save(t_id, subj_list, sec_list, t_max):
                st.session_state.teachers[editing_t] = Teacher(
                    teacher_id=t_id, subjects=subj_list, sections=sec_list, max_periods_per_day=t_max
                )
                save_teachers(st.session_state.teachers)
                append_history("edit", f"Teacher {t_id}", f"Updated {t_id}", "")
                show_toast(f"Teacher {t_id} updated")
                st.session_state.editing_teacher = None
                st.session_state.form_teacher = {"id": "", "subjects": "", "sections": "", "max": 6}
                st.session_state.class_timetable = None
                st.session_state.teacher_timetable = None
                st.rerun()
            def _on_hist_t_cancel():
                st.session_state.editing_teacher = None
                st.session_state.form_teacher = {"id": "", "subjects": "", "sections": "", "max": 6}
                st.rerun()
            render_teacher_form(editing_t, get_edit_buffer_teacher(t), _on_hist_t_save, _on_hist_t_cancel, prefix="hist")

    if editing_c is not None:
        with st.expander("✏️ Edit class", expanded=True):
            c = st.session_state.classes[editing_c]
            def _on_hist_c_save(c_id, subs):
                st.session_state.classes[editing_c] = Class(class_id=c_id, subjects=subs)
                save_classes(st.session_state.classes)
                append_history("edit", f"Class {c_id}", f"Updated {c_id}", "")
                show_toast(f"Class {c_id} updated")
                st.session_state.editing_class = None
                st.session_state.form_class = {"id": "", "subjects": ""}
                st.session_state.class_timetable = None
                st.session_state.teacher_timetable = None
                st.rerun()
            def _on_hist_c_cancel():
                st.session_state.editing_class = None
                st.session_state.form_class = {"id": "", "subjects": ""}
                st.rerun()
            render_class_form(editing_c, get_edit_buffer_class(c), _on_hist_c_save, _on_hist_c_cancel, prefix="hist")

    st.subheader("Teachers")
    if st.session_state.teachers:
        for i, t in enumerate(st.session_state.teachers):
            with st.container():
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.markdown(f"**{t.teacher_id}** — {', '.join(t.subjects)}")
                with col2:
                    if st.button("✏️ Edit", key=f"hist_t_edit_{i}"):
                        st.session_state.editing_teacher = i
                        st.session_state.form_teacher = get_edit_buffer_teacher(t)
                        st.rerun()
                with col3:
                    if st.button("🗑️ Delete", key=f"hist_t_del_{i}"):
                        name = t.teacher_id
                        st.session_state.teachers.pop(i)
                        save_teachers(st.session_state.teachers)
                        append_history("delete", f"Teacher {name}", f"Deleted {name}", "")
                        show_toast(f"Teacher {name} deleted")
                        st.rerun()
    else:
        st.info("No teachers yet.")

    st.markdown("---")
    st.subheader("Classes")
    if st.session_state.classes:
        for i, c in enumerate(st.session_state.classes):
            subj_str = ", ".join(f"{cs.subject}({cs.weekly_periods}w)" for cs in c.subjects)
            with st.container():
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.markdown(f"**{c.class_id}** — {subj_str}")
                with col2:
                    if st.button("✏️ Edit", key=f"hist_c_edit_{i}"):
                        st.session_state.editing_class = i
                        st.session_state.form_class = get_edit_buffer_class(c)
                        st.rerun()
                with col3:
                    if st.button("🗑️ Delete", key=f"hist_c_del_{i}"):
                        name = c.class_id
                        st.session_state.classes.pop(i)
                        st.session_state.priority_configs = [
                            p for p in st.session_state.priority_configs if p.class_id != name
                        ]
                        save_classes(st.session_state.classes)
                        save_priority_configs(st.session_state.priority_configs)
                        append_history("delete", f"Class {name}", f"Deleted {name}", "")
                        show_toast(f"Class {name} deleted")
                        st.rerun()
    else:
        st.info("No classes yet.")


# ----- TAB 3: History (Chrome-style log) -----
with tab3:
    st.header("🕓 History")
    st.markdown("Activity log — add, edit, delete, generate, export.")
    history = load_history()
    if history:
        for entry in history:
            ts = entry.get("ts", "")
            action = entry.get("action", "")
            target = entry.get("target", "")
            summary = entry.get("summary", "")
            details = entry.get("details", "")
            try:
                dt = datetime.fromisoformat(ts)
                ts_fmt = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                ts_fmt = ts
            icon = {"add": "➕", "edit": "✏️", "delete": "🗑️", "generate": "🚀", "export": "📥", "clear": "🗑️"}.get(action, "•")
            with st.expander(f"{icon} {ts_fmt} — {summary}"):
                st.markdown(f"**Action:** {action} | **Target:** {target}")
                if details:
                    st.caption(details)
    else:
        st.info("No history yet. Actions will appear here.")


# ----- TAB 4: Class Timetables -----
with tab4:
    st.header("Class Timetables")
    if st.button("🚀 Generate Timetable", type="primary", key="gen_tt"):
        teachers = st.session_state.teachers
        classes = st.session_state.classes
        cfg = st.session_state.config
        if not cfg.days or cfg.periods_per_day < 1:
            st.error("Configure days and periods in the sidebar first!")
        elif not teachers:
            st.error("Add at least one teacher first!")
        elif not classes:
            st.error("Add at least one class first!")
        else:
            with st.spinner("Solving..."):
                tt = solve_timetable(cfg, teachers, classes)
            if tt is None:
                st.error("No solution found!")
            else:
                st.session_state.class_timetable = tt
                # Priority optional — improve only if configs exist
                prio = st.session_state.priority_configs
                if prio:
                    st.session_state.class_timetable = improve_timetable(
                        tt, cfg, classes, prio,
                    )
                st.session_state.teacher_timetable = invert_to_teacher_timetable(
                    st.session_state.class_timetable, cfg
                )
                save_base_timetable(serialize_timetable(st.session_state.class_timetable))
                append_history("generate", "Timetable", "Generated clash-free timetable", "")
                show_toast("Timetable generated!")

    if st.session_state.class_timetable:
        cfg = st.session_state.config
        class_ids = sorted({k[0] for k in st.session_state.class_timetable})
        period_cols = [f"P{p+1}" + (f" ({get_break_name(cfg, p)})" if p in cfg.break_period_indices else "") for p in range(cfg.periods_per_day)]
        col_config = {"Day": st.column_config.TextColumn("Day", width="medium")}
        for pc in period_cols:
            col_config[pc] = st.column_config.TextColumn(pc, width="medium")
        for cid in class_ids:
            st.subheader(f"Class {cid}")
            rows = []
            for d in range(len(cfg.days)):
                row = [cfg.days[d]]
                for p in range(cfg.periods_per_day):
                    if p in cfg.break_period_indices:
                        row.append(get_break_name(cfg, p))
                    else:
                        val = st.session_state.class_timetable.get((cid, d, p), ("", ""))[0]
                        row.append(val if val else "Free period")
                rows.append(row)
            st.dataframe(pd.DataFrame(rows, columns=["Day"] + period_cols), column_config=col_config, use_container_width=True, hide_index=True)


# ----- TAB 5: Teacher Timetables -----
with tab5:
    st.header("Teacher Timetables")
    if st.session_state.teacher_timetable:
        cfg = st.session_state.config
        period_cols = [f"P{p+1}" + (f" ({get_break_name(cfg, p)})" if p in cfg.break_period_indices else "") for p in range(cfg.periods_per_day)]
        col_config = {"Day": st.column_config.TextColumn("Day", width="medium")}
        for pc in period_cols:
            col_config[pc] = st.column_config.TextColumn(pc, width="medium")
        for tid in sorted(st.session_state.teacher_timetable.keys()):
            st.subheader(f"Teacher {tid}")
            tt = st.session_state.teacher_timetable[tid]
            rows = []
            for d in range(len(cfg.days)):
                row = [cfg.days[d]]
                for p in range(cfg.periods_per_day):
                    if p in cfg.break_period_indices:
                        row.append(get_break_name(cfg, p))
                    else:
                        val = tt.get((d, p), ("", ""))
                        row.append(f"{val[0]}: {val[1]}" if val[0] else "Free period")
                rows.append(row)
            st.dataframe(pd.DataFrame(rows, columns=["Day"] + period_cols), column_config=col_config, use_container_width=True, hide_index=True)
    else:
        st.info("Generate a timetable first.")


# ----- TAB 6: Rotation -----
with tab6:
    st.header("Weekly Rotation")
    if st.session_state.class_timetable:
        rotations = generate_rotations(st.session_state.class_timetable, st.session_state.config, 3)
        cfg = st.session_state.config
        period_cols = [f"P{p+1}" + (f" ({get_break_name(cfg, p)})" if p in cfg.break_period_indices else "") for p in range(cfg.periods_per_day)]
        col_config = {"Day": st.column_config.TextColumn("Day", width="medium")}
        for pc in period_cols:
            col_config[pc] = st.column_config.TextColumn(pc, width="medium")
        for week_idx, rot in enumerate(rotations):
            st.subheader(f"Week {week_idx + 1}")
            class_ids = sorted({k[0] for k in rot})
            for cid in class_ids[:2]:
                rows = []
                for d in range(len(cfg.days)):
                    row = [cfg.days[d]]
                    for p in range(cfg.periods_per_day):
                        if p in cfg.break_period_indices:
                            row.append(get_break_name(cfg, p))
                        else:
                            val = rot.get((cid, d, p), ("", ""))[0]
                            row.append(val if val else "Free period")
                    rows.append(row)
                st.caption(f"Class {cid}")
                st.dataframe(pd.DataFrame(rows, columns=["Day"] + period_cols), column_config=col_config, use_container_width=True, hide_index=True)
            if len(class_ids) > 2:
                st.caption(f"... and {len(class_ids)-2} more")
    else:
        st.info("Generate a timetable first.")


# ----- TAB 7: What-If Lab -----
with tab7:
    st.header("🧪 What-If Lab")
    st.markdown("Simulate disruptions. Base timetable is never modified — you see a live overlay.")
    base_tt = st.session_state.class_timetable
    if not base_tt:
        st.info("Generate a timetable first in the Class Timetables tab.")
    else:
        ss = st.session_state.scenario_state
        cfg = st.session_state.config

        # Day selector
        day_idx = st.selectbox(
            "Day",
            range(len(cfg.days)),
            format_func=lambda i: cfg.days[i],
            key="whatif_day",
            index=ss.get("selected_day", 0),
        )
        ss["selected_day"] = day_idx

        # Scenario checkboxes
        st.subheader("Scenarios")
        scenarios = ss.get("scenarios", {})

        def _get(name, default):
            return scenarios.get(name, default)

        c1, c2 = st.columns(2)
        with c1:
            sc_ta = st.checkbox("Teacher absent today", _get("teacher_absent", {}).get("active", False), key="sc_ta")
            sc_sub = st.checkbox("Substitute teacher assigned", _get("substitute", {}).get("active", False), key="sc_sub")
            sc_lab = st.checkbox("Lab unavailable today", _get("lab_unavailable", {}).get("active", False), key="sc_lab")
        with c2:
            sc_short = st.checkbox("Shortened school day", _get("shortened_day", {}).get("active", False), key="sc_short")
            sc_free = st.checkbox("Emergency free period", _get("emergency_free", {}).get("active", False), key="sc_free")

        # Expanded fields per scenario
        teacher_ids = [t.teacher_id for t in st.session_state.teachers]
        class_ids = sorted({k[0] for k in base_tt})

        if sc_ta and teacher_ids:
            with st.expander("Teacher absent — select teacher"):
                saved = scenarios.get("teacher_absent", {}).get("teacher_id")
                idx = teacher_ids.index(saved) if saved in teacher_ids else 0
                absent_tid = st.selectbox("Absent teacher", teacher_ids, index=idx, key="absent_tid")
                scenarios["teacher_absent"] = {"active": True, "teacher_id": absent_tid}
        else:
            scenarios["teacher_absent"] = {"active": False}

        if sc_sub and teacher_ids:
            with st.expander("Substitute — who replaces whom"):
                saved_orig = scenarios.get("substitute", {}).get("original_teacher")
                saved_sub = scenarios.get("substitute", {}).get("substitute_teacher")
                idx_orig = teacher_ids.index(saved_orig) if saved_orig in teacher_ids else 0
                idx_sub = teacher_ids.index(saved_sub) if saved_sub in teacher_ids else min(1, len(teacher_ids) - 1)
                orig = st.selectbox("Original teacher", teacher_ids, index=idx_orig, key="sub_orig")
                sub = st.selectbox("Substitute teacher", teacher_ids, index=idx_sub, key="sub_sub")
                scenarios["substitute"] = {"active": True, "original_teacher": orig, "substitute_teacher": sub}
        else:
            scenarios["substitute"] = {"active": False}

        if sc_lab:
            with st.expander("Lab unavailable — which subjects"):
                default_lab = scenarios.get("lab_unavailable", {}).get("lab_subjects", "Physics, Chemistry, Biology")
                lab_subs = st.text_input("Lab subjects (comma-separated)", default_lab, key="lab_subs")
                scenarios["lab_unavailable"] = {"active": True, "lab_subjects": lab_subs}
        else:
            scenarios["lab_unavailable"] = {"active": False}

        if sc_short:
            with st.expander("Shortened day"):
                new_max = st.number_input(
                    "Max periods today",
                    min_value=1,
                    max_value=cfg.periods_per_day,
                    value=scenarios.get("shortened_day", {}).get("max_periods", 4),
                    key="short_max",
                )
                scenarios["shortened_day"] = {"active": True, "max_periods": new_max}
        else:
            scenarios["shortened_day"] = {"active": False}

        if sc_free and class_ids:
            with st.expander("Emergency free period"):
                saved_cid = scenarios.get("emergency_free", {}).get("class_id")
                saved_p = scenarios.get("emergency_free", {}).get("period", 2)
                idx_c = class_ids.index(saved_cid) if saved_cid in class_ids else 0
                free_cid = st.selectbox("Class", class_ids, index=idx_c, key="free_cid")
                free_p = st.number_input("Period (0-based)", min_value=0, max_value=cfg.periods_per_day - 1, value=saved_p, key="free_p")
                scenarios["emergency_free"] = {"active": True, "class_id": free_cid, "period": free_p}
        else:
            scenarios["emergency_free"] = {"active": False}

        ss["scenarios"] = scenarios
        save_scenario_state(ss)

        # Resolved view
        resolved = apply_scenarios(base_tt, cfg, st.session_state.teachers, st.session_state.classes, ss)
        st.subheader("Live timetable (with scenarios)")
        period_cols = [f"P{p+1}" + (f" ({get_break_name(cfg, p)})" if p in cfg.break_period_indices else "") for p in range(cfg.periods_per_day)]
        col_config = {"Day": st.column_config.TextColumn("Day", width="medium")}
        for pc in period_cols:
            col_config[pc] = st.column_config.TextColumn(pc, width="medium")
        for cid in sorted({k[0] for k in resolved}):
            st.caption(f"Class {cid}")
            rows = []
            for d in range(len(cfg.days)):
                row = [cfg.days[d]]
                for p in range(cfg.periods_per_day):
                    if p in cfg.break_period_indices:
                        row.append(get_break_name(cfg, p))
                    else:
                        val = resolved.get((cid, d, p), ("", ""))[0]
                        row.append(val if val else "Free period")
                rows.append(row)
            df = pd.DataFrame(rows, columns=["Day"] + period_cols)
            st.dataframe(df, column_config=col_config, use_container_width=True, hide_index=True)


# ----- TAB 8: Insights (Heatmaps) -----
with tab8:
    st.header("🔥 Insights")
    st.markdown("Visual heatmaps: overload, fatigue, congestion. Darker = higher load.")
    base_tt = st.session_state.class_timetable
    if not base_tt:
        st.info("Generate a timetable first.")
    else:
        cfg = st.session_state.config
        ss = st.session_state.scenario_state
        resolved = apply_scenarios(base_tt, cfg, st.session_state.teachers, st.session_state.classes, ss)

        heatmap_type = st.selectbox(
            "Heatmap",
            ["Teacher load", "Day congestion", "Class fatigue", "Clash risk"],
            key="heatmap_sel",
        )

        if heatmap_type == "Teacher load":
            load = teacher_load_heatmap(resolved, cfg)
            teacher_max = {t.teacher_id: t.max_periods_per_day for t in st.session_state.teachers}
            styled = render_teacher_load_heatmap(load, cfg.days, teacher_max)
            st.dataframe(styled, use_container_width=True)
            st.caption("Rows = teachers, Cols = days. Darker = more periods.")
        elif heatmap_type == "Day congestion":
            cong = day_congestion_heatmap(resolved, cfg)
            styled = render_day_congestion_heatmap(cong, cfg.days)
            st.dataframe(styled, use_container_width=True)
            st.caption("Total teaching periods per day.")
        elif heatmap_type == "Class fatigue":
            pcs = getattr(st.session_state, "priority_configs", None) or []
            heavy_map = {pc.class_id: pc.heavy_subjects for pc in pcs}
            fatigue = class_fatigue_heatmap(resolved, cfg, heavy_map)
            styled = render_class_fatigue_heatmap(fatigue, cfg.periods_per_day)
            st.dataframe(styled, use_container_width=True)
            st.caption("Rows = classes, Cols = periods. Heavier subjects = hotter.")
        else:
            risks = clash_risk_heatmap(resolved, cfg, st.session_state.teachers)
            st.subheader("Clash risks")
            if risks["teacher_overload"]:
                st.warning("Teacher overload detected:")
                for r in risks["teacher_overload"]:
                    st.write(f"• {r['teacher']}: {r['count']} periods on {cfg.days[r['day']]} (over max)")
            else:
                st.success("No teacher overload detected.")
            if risks["back_to_back_heavy"]:
                st.warning("Back-to-back heavy subjects — review manually.")


# ----- TAB 9: PDF Export -----
with tab9:
    st.header("Export PDFs")
    if st.session_state.class_timetable and st.session_state.teacher_timetable:
        class_tt = flat_to_class_timetables(st.session_state.class_timetable)
        class_pdf = export_class_timetables_pdf(class_tt, st.session_state.config)
        teacher_pdf = export_teacher_timetables_pdf(st.session_state.teacher_timetable, st.session_state.config)
        col1, col2 = st.columns(2)
        with col1:
            if st.download_button(
                "📥 Download Class Timetables PDF",
                data=class_pdf,
                file_name="class_timetables.pdf",
                mime="application/pdf",
                key="dl_class",
            ):
                append_history("export", "PDF", "Exported class timetables PDF", "")
                show_toast("Class PDF downloaded")
        with col2:
            if st.download_button(
                "📥 Download Teacher Timetables PDF",
                data=teacher_pdf,
                file_name="teacher_timetables.pdf",
                mime="application/pdf",
                key="dl_teacher",
            ):
                append_history("export", "PDF", "Exported teacher timetables PDF", "")
                show_toast("Teacher PDF downloaded")
    else:
        st.info("Generate a timetable first.")

# Ensure the app initializes even if functions were defined late
