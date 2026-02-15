#  Smart Timetable Builder

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/streamlit-1.28%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![OR-Tools](https://img.shields.io/badge/OR--Tools-9.5%2B-4285F4?style=for-the-badge&logo=google&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/status-production-success?style=for-the-badge)

### **An intelligent, animated school timetable generator**
**Powered by constraint programming • Built with love for educators**

*Smooth • Stable • Alive*

[ Quick Start](#-quick-start) • [ Features](#-features) • [Documentation](#-documentation) • [ Demo](#-demo-data)

![Separator](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

</div>

---

##  Overview

**Smart Timetable Builder** is a next-generation scheduling solution that transforms the complex task of school timetable creation into an elegant, visual experience. Combining **Google's OR-Tools constraint solver** with a **beautifully animated dark-themed interface**, it generates mathematically guaranteed clash-free schedules while providing real-time analytics, scenario simulation, and stunning visualizations.

### Why Smart Timetable Builder?

<table>
<tr>
<td width="33%" align="center">
<h3> Intelligent</h3>
Constraint programming ensures zero conflicts. No manual checking needed.
</td>
<td width="33%" align="center">
<h3> Beautiful</h3>
Fluid animations, glowing transitions, and a modern dark theme.
</td>
<td width="33%" align="center">
<h3> Analytical</h3>
Visual heatmaps and energy fields reveal insights at a glance.
</td>
</tr>
</table>

###  Key Highlights

- **Zero Conflicts Guaranteed** - Mathematical proof via constraint programming
- **5 What-If Scenarios** - Test disruptions without touching base timetable
- **4 Visual Analytics** - Heatmaps for load, fatigue, congestion, clashes
- **4 Energy Maps** - Animated Plotly fields with glowing orbs and wave motion
- **Auto-Save Everything** - 8 JSON files persist all data across sessions
- **Chrome-Style History** - Full audit trail with timestamps
- **Demo Data Included** - 12 teachers, 6 classes, 164 periods ready to go
- **Professional PDFs** - Print-ready A4 exports for classes and teachers

---

##  Features

###  Core Scheduling Engine

<table>
<tr>

<td><b>Clash-Free Generation</b></td>
<td>No teacher or class double-booking (hard constraint)</td>
</tr>
<tr>

<td><b>Priority Scheduling</b></td>
<td>Important subjects scheduled earlier in the day (optional)</td>
</tr>
<tr>

<td><b>Teacher Constraints</b></td>
<td>Respect max periods per day + max periods per week</td>
</tr>
<tr>

<td><b>Break Periods</b></td>
<td>Configurable breaks (e.g., "4, Lunch Break" or "7, Tea Break")</td>
</tr>
<tr>

<td><b>Weekly Rotation</b></td>
<td>3-week automatic rotation for fairness</td>
</tr>
<tr>

<td><b>OR-Tools Solver</b></td>
<td>Google's constraint programming solver (CP-SAT)</td>
</tr>
</table>

###  What-If Lab (5 Scenarios)

Simulate disruptions **without modifying the base timetable**:

| Scenario | Description | Use Case |
|----------|-------------|----------|
|  **Teacher Absent** | Mark teacher unavailable, auto-substitute or free period | Sick leave, training |
|  **Substitute Teacher** | Assign replacement teacher for specific classes | Planned absence |
|  **Lab Unavailable** | Mark lab subjects (Physics, Chemistry, Biology) as free | Maintenance, exams |
|  **Shortened Day** | Reduce max periods for the day | Half-day schedule |
|  **Emergency Free** | Force specific class/period to be free | Assembly, event |

###  Visual Analytics

#### Heatmaps (4 Types)

```
┌─────────────────────────────────────────────────────────────┐
│   Teacher Load       │  Periods per teacher per day       │
│   Day Congestion     │  Total teaching periods per day    │
│   Class Fatigue      │  Heavy subject clustering          │
│    Clash Risk        │  Overload and conflict detection   │
└─────────────────────────────────────────────────────────────┘
```

#### Energy Maps (4 Types - Animated with Plotly)

```
┌─────────────────────────────────────────────────────────────┐
│   Teacher Load       │  Glowing orbs sized by workload    │
│   Fatigue Flow       │  Ripple effects show heavy clusters│
│   Congestion         │  Pulsing gradients per day         │
│   Impact Diffusion   │  Wave propagation from changes     │
└─────────────────────────────────────────────────────────────┘
```

**Controls:** Animation Speed • Glow Intensity • Motion Toggle

###  Auto-Persistence (8 JSON Files)

All data automatically saves to `data/` directory:

```
data/
├── teachers.json          # Teacher definitions
├── classes.json           # Class and subject assignments  
├── priority_configs.json  # Priority settings per class
├── config.json            # School configuration
├── history.json           # Activity log (last 500 entries)
├── demo_loaded.json       # Demo data flag
├── base_timetable.json    # Generated timetable
└── scenario_state.json    # What-If Lab scenarios
```

###  User Experience

<table>
<tr>
<td width="50%">

**Smooth Animations**
- Fade-in transitions (0.3-0.4s)
- Glow effects on changes
- Pulsing notifications
- Interpolated heatmaps

</td>
<td width="50%">

**Intuitive Interface**
- 10-tab navigation
- Expandable forms
- In-place editing
- Stackable toasts

</td>
</tr>
</table>

###  Dark Theme

Modern, eye-friendly design:
- Background: `#0f0f0f`
- Containers: `#18181b`
- Borders: `#27272a`
- Text: `#fafafa` / `#e4e4e7` / `#a1a1aa`

---

##  Quick Start

###  Prerequisites

```bash
Python 3.8 or higher
pip package manager
4GB RAM recommended
```

###  Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/smart-timetable-builder.git
cd smart-timetable-builder

# Install dependencies
pip install -r requirements.txt
```

### Run Application

```bash
streamlit run app.py
```

Application opens at: **http://localhost:8501**

### First Steps (3 Minutes)

<table>
<tr>
<td width="33%" align="center">

**1. Load Demo**

Click **"Load Demo Data"** in sidebar

<small>12 teachers + 6 classes ready to use</small>

</td>
<td width="33%" align="center">

**2. Generate**

Navigate to **"Class Timetables"** tab

Click **"Generate Timetable"**

<small>Solver runs ~2-5 seconds</small>

</td>
<td width="33%" align="center">

**3. Explore**

View results, try scenarios, check analytics

<small>All features now unlocked!</small>

</td>
</tr>
</table>

---

##  Demo Data

###  Teachers (12 Total)

<table>
<tr>
<th>Stream</th>
<th>Teacher</th>
<th>Subjects</th>
<th>Max/Day</th>
</tr>
<tr>
<td rowspan="4"><b>Science</b></td>
<td>Eric Simon</td>
<td>Physics</td>
<td>5</td>
</tr>
<tr>
<td>Aisha Khan</td>
<td>Chemistry</td>
<td>5</td>
</tr>
<tr>
<td>Rahul Mehta</td>
<td>Mathematics</td>
<td>5</td>
</tr>
<tr>
<td>Neha Verma</td>
<td>Biology</td>
<td>5</td>
</tr>
<tr>
<td rowspan="3"><b>Commerce</b></td>
<td>Priya Nair</td>
<td>Economics</td>
<td>5</td>
</tr>
<tr>
<td>Arjun Patel</td>
<td>Accountancy</td>
<td>5</td>
</tr>
<tr>
<td>Kavita Rao</td>
<td>Business Studies</td>
<td>4</td>
</tr>
<tr>
<td rowspan="3"><b>Humanities</b></td>
<td>Sofia Mendes</td>
<td>History</td>
<td>5</td>
</tr>
<tr>
<td>Aman Gupta</td>
<td>Political Science</td>
<td>5</td>
</tr>
<tr>
<td>Ritu Chawla</td>
<td>Geography</td>
<td>4</td>
</tr>
<tr>
<td rowspan="2"><b>Common</b></td>
<td>Daniel Brooks</td>
<td>English (all streams)</td>
<td>4</td>
</tr>
<tr>
<td>Marcus Lee</td>
<td>Physical Education (all)</td>
<td>3</td>
</tr>
</table>

###  Classes (6 Total)

```
┌─────────┬────────────────────────────────────────────────┬────────┐
│ Class   │ Subjects (periods/week)                        │ Total  │
├─────────┼────────────────────────────────────────────────┼────────┤
│ 11SCI   │ Physics(6) • Chemistry(6) • Math(6)           │   30   │
│         │ Biology(6) • English(4) • PE(2)                │        │
├─────────┼────────────────────────────────────────────────┼────────┤
│ 12SCI   │ Physics(6) • Chemistry(6) • Math(6)           │   30   │
│         │ Biology(6) • English(4) • PE(2)                │        │
├─────────┼────────────────────────────────────────────────┼────────┤
│ 11COM   │ Accountancy(6) • Business(6) • Economics(6)   │   28   │
│         │ Math(4) • English(4) • PE(2)                   │        │
├─────────┼────────────────────────────────────────────────┼────────┤
│ 12COM   │ Accountancy(6) • Business(6) • Economics(6)   │   28   │
│         │ Math(4) • English(4) • PE(2)                   │        │
├─────────┼────────────────────────────────────────────────┼────────┤
│ 11HUM   │ History(6) • PolSci(6) • Geography(6)         │   24   │
│         │ English(4) • PE(2)                             │        │
├─────────┼────────────────────────────────────────────────┼────────┤
│ 12HUM   │ History(6) • PolSci(6) • Geography(6)         │   24   │
│         │ English(4) • PE(2)                             │        │
└─────────┴────────────────────────────────────────────────┴────────┘

Total: 164 periods/week across 6 classes
```

---

## Documentation

### 10-Tab Interface

```
┌────────────────────────────────────────────────────────────────────┐
│  Teachers &   Saved   History   Class     Teacher      │
│    Classes      Data                 Timetables   Timetables       │
│                                                                     │
│  Rotation   What-If   Insights   Energy   PDF           │
│               Lab                     Maps      Export            │
└────────────────────────────────────────────────────────────────────┘
```

###  Complete User Guide

#### 1. Configure School (Sidebar)

```yaml
Days: Mon,Tue,Wed,Thu,Fri
Periods per day: 8

Break Periods:
  4, Lunch Break
  7, Tea Break
```

Click **"Apply Config"** to save.

#### 2. Add Teachers

Navigate to **"Teachers & Classes"** tab:

```
┌─────────────────────────────────────┐
│ Teacher ID: Eric Simon              │
│ Subjects: Physics                   │
│ Sections: 11SCI, 12SCI              │
│ Max Periods/Day: 5                  │
│                                     │
│        [Save]   [Cancel]            │
└─────────────────────────────────────┘
```

**Result:** Toast notification " Teacher Eric Simon added"

#### 3. Add Classes

Scroll to **"2. Add Classes"** section:

```
┌─────────────────────────────────────┐
│ Class ID: 11SCI                     │
│                                     │
│ Add Subjects:                       │
│ • Physics: 6 periods → Eric Simon   │
│ • Chemistry: 6 periods → Aisha Khan │
│ • Math: 6 periods → Rahul Mehta     │
│ ...                                 │
│                                     │
│        [Save]   [Cancel]            │
└─────────────────────────────────────┘
```

#### 4. Priority Settings (Optional)

Expand each class to configure:

```
Priorities for 11SCI:
┌─────────────────────────────────────┐
│ Priority (early) subjects:          │
│ Physics, Chemistry, Mathematics     │
│                                     │
│ Weak subjects:                      │
│ Physics, Chemistry                  │
│                                     │
│ Heavy subjects:                     │
│ Physics, Chemistry, Math, Biology   │
│                                     │
│        [Save]                       │
└─────────────────────────────────────┘
```

#### 5. Generate Timetable

Navigate to **" Class Timetables"** tab:

1. Click **" Generate Timetable"**
2. Spinner appears: "Solving..."
3. Toast: " Timetable generated!"
4. View results in tables below

#### 6. What-If Scenarios

Navigate to **" What-If Lab"** tab:

```
Day: [Monday ▼]

Scenarios:
☑ Teacher absent today
  └─ Absent teacher: [Eric Simon ▼]

☑ Shortened school day  
  └─ Max periods today: [6]

Live timetable updates below ↓
```

#### 7. Visual Analytics

**Heatmaps** ( Insights tab):

```
Heatmap: [Teacher load ▼]

Displays: Styled dataframe with color gradients
- Green → Yellow → Orange → Red
- Darker = Higher load
```

**Energy Maps** ( Energy Maps tab):

```
Energy Map Type: [Teacher Load Energy Field ▼]
Animation Speed: ————●———— 0.5
Glow Intensity:  ————●———— 1.0
Motion: ☑

Displays: Animated Plotly chart with:
- Glowing orbs (teacher workload)
- Smooth gradients
- Wave motion effects
```

#### 8. Export PDFs

Navigate to **" PDF Export"** tab:

```
┌──────────────────────────────────┐
│   Download Class PDFs          │
│   Download Teacher PDFs        │
└──────────────────────────────────┘

Format: A4, print-ready
```

---

## Technical Architecture

### Data Models (`models.py`)

```python
@dataclass
class Teacher:
    teacher_id: str                    # Unique ID (e.g., "Eric Simon")
    subjects: List[str]                # ["Physics"]
    sections: List[str]                # ["11SCI", "12SCI"]
    max_periods_per_day: int = 6       # Daily limit

@dataclass
class ClassSubject:
    subject: str                       # "Physics"
    weekly_periods: int                # 6
    teacher_id: str                    # "Eric Simon"

@dataclass
class Class:
    class_id: str                      # "11SCI"
    subjects: List[ClassSubject]       # List of subjects

@dataclass
class SchoolConfig:
    days: List[str] = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    periods_per_day: int = 8
    break_periods: Dict[int, str] = {}  # {3: "Lunch", 6: "Tea"}

@dataclass
class ClassPriorityConfig:
    class_id: str
    priority_subjects: List[str] = []  # Early scheduling
    weak_subjects: List[str] = []      # Morning only
    heavy_subjects: List[str] = []     # Avoid consecutive
```

### Application Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. Session State Init (_init_session)                      │
│     └─ Load from JSON (all 8 files)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  2. Render UI (10 tabs)                                     │
│     └─ Streamlit components + custom CSS                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  3. User Actions (add/edit/delete/generate)                 │
│     └─ Form submissions, button clicks                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  4. Business Logic                                          │
│     ├─ Solver (OR-Tools CP-SAT)                            │
│     ├─ Scenarios (overlay, no mutation)                    │
│     └─ Analytics (heatmaps, energy maps)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  5. Auto-Save (storage.py → JSON)                          │
│     └─ Persist to data/ directory                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  6. Update UI + Show Toast Notification                     │
│     └─ Fragment reruns, smooth animations                   │
└─────────────────────────────────────────────────────────────┘
```

### Constraint Solver (`solver.py`)

```python
# Hard Constraints (MUST be satisfied)
✓ No teacher conflicts     # Teacher can't be in 2 places
✓ No class conflicts       # Class can't have 2 subjects
✓ All periods satisfied    # Sum matches weekly_periods
✓ Teacher max per day      # Respect daily limit
✓ Teacher max per week     # Respect weekly limit

# Soft Constraints (Optimization - if priority configs exist)
⚡ Priority subjects early  # Morning scheduling
⚡ Weak subjects morning    # When students fresh
⚡ Heavy not consecutive    # Avoid back-to-back
```

**Solver Performance:**
- Small (6 classes): ~2 seconds
- Medium (20 classes): ~5-10 seconds  
- Large (50+ classes): ~20-60 seconds

### Storage Layer (`storage.py`)

```python
# Core Functions
load_teachers() → List[Teacher]
save_teachers(teachers: List[Teacher])

load_classes() → List[Class]
save_classes(classes: List[Class])

load_config() → SchoolConfig
save_config(config: SchoolConfig)

load_priority_configs() → List[ClassPriorityConfig]
save_priority_configs(configs)

# History & State
append_history(action, target, summary, details)
load_history() → List[dict]  # Last 500 entries

load_scenario_state() → dict
save_scenario_state(state: dict)

load_base_timetable() → Optional[dict]
save_base_timetable(serialized: dict)

# Utility
is_demo_loaded() → bool
set_demo_loaded()
clear_demo_loaded()
clear_base_timetable()
clear_scenario_state()
```

---

##  UI Design

###  Dark Theme

```css
/* Color Palette */
--bg-primary: #0f0f0f
--bg-secondary: #18181b
--border: #27272a
--text-primary: #fafafa
--text-secondary: #e4e4e7
--text-muted: #a1a1aa

/* Gradients */
--sidebar: linear-gradient(180deg, #18181b 0%, #0f0f0f 100%)
```

### ✨ Animations

```css
/* Fade In */
@keyframes cardFadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Glow (Changed Cells) */
@keyframes glow {
  0% { box-shadow: 0 0 8px 2px #ffd700; }
  100% { box-shadow: 0 0 16px 6px #ffec99; }
}

/* Toast Slide */
@keyframes toastFadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
```

### 📲 Notifications

Stackable toast notifications with live countdown:

```python
show_toast("Timetable generated!", duration_sec=3)
```

**Display:**
```
┌─────────────────────────────────┐
│  Timetable generated!     3s │
│  Teacher added            2s │
│  PDF exported             1s │
└─────────────────────────────────┘
```

Fragment reruns every 1 second via `@st.fragment(run_every=timedelta(seconds=1))`

---

## Example Output

### Class Timetable

```
Class 11SCI
┌───────────┬──────────┬──────────┬──────────┬────────────┬──────────┬──────────┬──────────┬──────────┐
│ Day       │ P1       │ P2       │ P3       │ P4 (Lunch) │ P5       │ P6       │ P7 (Tea) │ P8       │
│           │ 08:00    │ 08:45    │ 09:30    │ 10:15      │ 11:00    │ 11:45    │ 12:30    │ 13:15    │
├───────────┼──────────┼──────────┼──────────┼────────────┼──────────┼──────────┼──────────┼──────────┤
│ Monday    │ Physics  │ Chemistry│ Math     │ BREAK      │ Biology  │ English  │ BREAK    │ Free     │
├───────────┼──────────┼──────────┼──────────┼────────────┼──────────┼──────────┼──────────┼──────────┤
│ Tuesday   │ Chemistry│ Math     │ Biology  │ BREAK      │ Physics  │ English  │ BREAK    │ PE       │
├───────────┼──────────┼──────────┼──────────┼────────────┼──────────┼──────────┼──────────┼──────────┤
│ Wednesday │ Math     │ Physics  │ Chemistry│ BREAK      │ English  │ Biology  │ BREAK    │ Free     │
├───────────┼──────────┼──────────┼──────────┼────────────┼──────────┼──────────┼──────────┼──────────┤
│ Thursday  │ Biology  │ Chemistry│ Physics  │ BREAK      │ Math     │ PE       │ BREAK    │ Free     │
├───────────┼──────────┼──────────┼──────────┼────────────┼──────────┼──────────┼──────────┼──────────┤
│ Friday    │ English  │ Math     │ Chemistry│ BREAK      │ Physics  │ Biology  │ BREAK    │ Free     │
└───────────┴──────────┴──────────┴──────────┴────────────┴──────────┴──────────┴──────────┴──────────┘
```

###  Teacher Timetable

```
Teacher: Eric Simon (Physics) - Max 5 periods/day
┌───────────┬─────────┬─────────┬─────────┬────────────┬─────────┬─────────┬──────────┬─────────┐
│ Day       │ P1      │ P2      │ P3      │ P4 (Lunch) │ P5      │ P6      │ P7 (Tea) │ P8      │
├───────────┼─────────┼─────────┼─────────┼────────────┼─────────┼─────────┼──────────┼─────────┤
│ Monday    │ 11SCI   │ Free    │ 12SCI   │ BREAK      │ Free    │ Free    │ BREAK    │ Free    │
├───────────┼─────────┼─────────┼─────────┼────────────┼─────────┼─────────┼──────────┼─────────┤
│ Tuesday   │ Free    │ 12SCI   │ Free    │ BREAK      │ 11SCI   │ Free    │ BREAK    │ Free    │
├───────────┼─────────┼─────────┼─────────┼────────────┼─────────┼─────────┼──────────┼─────────┤
│ Wednesday │ Free    │ 11SCI   │ Free    │ BREAK      │ Free    │ 12SCI   │ BREAK    │ Free    │
├───────────┼─────────┼─────────┼─────────┼────────────┼─────────┼─────────┼──────────┼─────────┤
│ Thursday  │ Free    │ Free    │ 11SCI   │ BREAK      │ Free    │ Free    │ BREAK    │ Free    │
├───────────┼─────────┼─────────┼─────────┼────────────┼─────────┼─────────┼──────────┼─────────┤
│ Friday    │ Free    │ Free    │ Free    │ BREAK      │ 12SCI   │ Free    │ BREAK    │ Free    │
└───────────┴─────────┴─────────┴─────────┴────────────┴─────────┴─────────┴──────────┴─────────┘

Summary:
• Total periods: 10/40 (25%)
• Periods per day: 2.0 average
• Max daily: 2 periods
• Free periods: 30
```

---

## Advanced Features

### History Log

Chrome-style activity tracking (last 500 entries):

```
┌────────────────────────────────────────────────────────────┐
│  2024-02-15 14:30 — Generated clash-free timetable      │
│    Action: generate | Target: Timetable                   │
├────────────────────────────────────────────────────────────┤
│  2024-02-15 14:25 — Exported class timetables PDF       │
│    Action: export | Target: PDF                           │
├────────────────────────────────────────────────────────────┤
│  2024-02-15 14:20 — Updated teacher Eric Simon          │
│    Action: edit | Target: Teacher Eric Simon              │
├────────────────────────────────────────────────────────────┤
│  2024-02-15 14:15 — Added class 11SCI                   │
│    Action: add | Target: Class 11SCI                      │
└────────────────────────────────────────────────────────────┘
```

### 🔄 Weekly Rotation

Automatic 3-week rotation system:

```
Week 1: Original schedule
Week 2: All subjects shifted +1 period (with wraparound)
Week 3: All subjects shifted +2 periods (with wraparound)

Result: Same subject doesn't always fall at same time of day
Benefits: Fairer for students, accounts for energy variations
```

###  Scenario Persistence

What-If scenarios auto-save:

```json
{
  "selected_day": 0,
  "scenarios": {
    "teacher_absent": {
      "active": true,
      "teacher_id": "Eric Simon"
    },
    "shortened_day": {
      "active": true,
      "max_periods": 6
    },
    "substitute": {
      "active": false
    }
  }
}
```

**Base timetable never modified** - scenarios create live overlay view.

---

##  Troubleshooting

###  Common Issues

<details>
<summary><b>Q: "No solution found" error when generating</b></summary>

**Possible Causes:**
1. Too many periods required vs. available slots
2. Teacher max_periods_per_day too restrictive
3. Conflicting teacher-subject assignments

**Solutions:**
```python
# Check math:
total_required = sum(subject.weekly_periods for class in classes 
                     for subject in class.subjects)
available_slots = periods_per_day × days_per_week
# Must satisfy: total_required ≤ available_slots × num_classes

# Check teacher capacity:
teacher_capacity = sum(teacher.max_periods_per_day × days_per_week 
                      for teacher in teachers)
# Must satisfy: total_required ≤ teacher_capacity
```

**Quick Fix:**
- Reduce subject weekly_periods
- Increase teacher max_periods_per_day
- Add more teachers

</details>

<details>
<summary><b>Q: Data disappeared after browser refresh</b></summary>

**Answer:** Check `data/` folder exists and has write permissions.

**Verify:**
```bash
ls -la data/
# Should show 8 JSON files
```

**If missing:** Click "Load Demo Data" to restore sample data.

</details>

<details>
<summary><b>Q: Timetable won't generate (button does nothing)</b></summary>

**Verify Prerequisites:**
- ✓ At least 1 teacher exists
- ✓ At least 1 class exists  
- ✓ Days and periods configured (sidebar)
- ✓ Teachers can teach assigned subjects

**Check Console:**
Press F12 → Console tab → Look for errors

</details>

<details>
<summary><b>Q: Energy maps not animating</b></summary>

**Solutions:**
1. Toggle "Motion" switch ON in Energy Maps tab
2. Use modern browser (Chrome 90+, Firefox 88+, Safari 14+)
3. Disable browser extensions that block JavaScript
4. Check browser console for errors

</details>

<details>
<summary><b>Q: PDF download shows blank pages</b></summary>

**Solutions:**
1. Regenerate timetable first
2. Try different PDF viewer (Adobe Reader, Chrome, Firefox)
3. Check if timetable has data:
   ```python
   # In Class Timetables tab, verify table shows data
   ```
4. Update ReportLab: `pip install --upgrade reportlab`

</details>

---

## 📚 Dependencies

```txt
# Core Framework
streamlit>=1.28.0          # Web UI framework
ortools>=9.5.0             # Constraint programming solver

# Data Processing
pandas>=1.5.0              # DataFrames and tables
numpy>=1.23.0              # Numerical operations

# Visualization
plotly>=5.14.0             # Interactive charts (energy maps)
matplotlib>=3.7.0          # Static charts (heatmaps)

# PDF Generation
reportlab>=4.0.0           # Professional PDF documents

# Scientific Computing
scipy>=1.10.0              # Gaussian filters, image processing

# Utilities
python-dateutil>=2.8.2     # Date/time handling
```

**Installation:**
```bash
pip install -r requirements.txt
```

---

## 🛠️ Tech Stack

<table>
<tr>
<th>Layer</th>
<th>Technology</th>
<th>Version</th>
<th>Purpose</th>
</tr>
<tr>
<td rowspan="2"><b>Frontend</b></td>
<td>Streamlit</td>
<td>1.28+</td>
<td>Reactive web interface</td>
</tr>
<tr>
<td>Custom CSS</td>
<td>-</td>
<td>Dark theme, animations</td>
</tr>
<tr>
<td><b>Solver</b></td>
<td>OR-Tools CP-SAT</td>
<td>9.5+</td>
<td>Constraint programming</td>
</tr>
<tr>
<td rowspan="2"><b>Visualization</b></td>
<td>Plotly</td>
<td>5.14+</td>
<td>Interactive energy maps</td>
</tr>
<tr>
<td>Matplotlib</td>
<td>3.7+</td>
<td>Static heatmaps</td>
</tr>
<tr>
<td rowspan="2"><b>Data</b></td>
<td>Pandas</td>
<td>1.5+</td>
<td>DataFrames, tables</td>
</tr>
<tr>
<td>NumPy</td>
<td>1.23+</td>
<td>Array operations</td>
</tr>
<tr>
<td><b>PDF</b></td>
<td>ReportLab</td>
<td>4.0+</td>
<td>Document generation</td>
</tr>
<tr>
<td><b>Scientific</b></td>
<td>SciPy</td>
<td>1.10+</td>
<td>Filters, effects</td>
</tr>
<tr>
<td><b>Storage</b></td>
<td>JSON</td>
<td>stdlib</td>
<td>Lightweight persistence</td>
</tr>
</table>

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### 🔧 Development Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/smart-timetable-builder.git
cd smart-timetable-builder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run in development mode
streamlit run app.py
```


## 🙏 Acknowledgments

<table>
<tr>
<td width="25%" align="center">
<img src="https://www.gstatic.com/images/branding/product/2x/google_cloud_48dp.png" width="48"><br>
<b>Google OR-Tools</b><br>
<small>Constraint programming solver</small>
</td>
<td width="25%" align="center">
<img src="https://streamlit.io/images/brand/streamlit-mark-color.png" width="48"><br>
<b>Streamlit</b><br>
<small>Web app framework</small>
</td>
<td width="25%" align="center">
<img src="https://plotly.com/all_static/images/favicon.ico" width="48"><br>
<b>Plotly</b><br>
<small>Interactive visualizations</small>
</td>
<td width="25%" align="center">
<img src="https://www.reportlab.com/media/logo.gif" width="48"><br>
<b>ReportLab</b><br>
<small>PDF generation</small>
</td>
</tr>
</table>

**Special Thanks:**
- All [contributors](https://github.com/yourusername/smart-timetable-builder/graphs/contributors)
- Educators who provided feedback
- Open source community

---

## 📧 Contact & Support

<table>
<tr>
<td width="33%" align="center">

### 🐛 Issues
[Report Bugs](https://github.com/yourusername/smart-timetable-builder/issues)

Found a bug? Let us know!

</td>
<td width="33%" align="center">

### 💬 Discussions
[Join Discussions](https://github.com/yourusername/smart-timetable-builder/discussions)

Questions? Ideas? Let's talk!

</td>
<td width="33%" align="center">

### 📧 Email
[your.email@example.com](mailto:your.email@example.com)

Direct contact for sensitive issues

</td>
</tr>
</table>


##  Show Your Support

<div align="center">

**If this project helps your school, please consider:**

**Starring** the repository on GitHub  
**Sharing** on social media  
**Contributing** improvements  
**Writing** about your experience  

[![GitHub stars](https://img.shields.io/github/stars/yourusername/smart-timetable-builder?style=social)](https://github.com/yourusername/smart-timetable-builder)
[![GitHub forks](https://img.shields.io/github/forks/yourusername/smart-timetable-builder?style=social)](https://github.com/yourusername/smart-timetable-builder)
[![GitHub watchers](https://img.shields.io/github/watchers/yourusername/smart-timetable-builder?style=social)](https://github.com/yourusername/smart-timetable-builder)

<br>

[⬆ Back to Top](#-smart-timetable-builder)

</div>

---

<div align="center">

**© 2024 Smart Timetable Builder**

Made using Python, Streamlit, and OR-Tools

</div>