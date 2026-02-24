"""
================================================================================
Fitbit AI Health Coach - Detailed continuous dashboard
================================================================================
Complete Fitbit data visualisation with detailed continuous charts.
Displays all data points (second by second) on a single graph.
"""

import streamlit as st
import pandas as pd
import json
import os
import glob
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

# -- Gemini AI (optional) -----------------------------------------------------
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Convert plotly figures to PNG bytes for PDF embedding
def fig_to_png_base64(fig, width=700, height=350):
    """Convert a plotly figure to base64 encoded PNG"""
    try:
        img_bytes = pio.to_image(fig, format="png", width=width, height=height, scale=2)
        return base64.b64encode(img_bytes).decode('utf-8')
    except Exception as e:
        st.warning(f"Chart conversion error: {str(e)}")
        return None

# Generate PDF from HTML using weasyprint
def generate_pdf_from_html(html_content):
    """Convert HTML to PDF using weasyprint (requires packages.txt for system deps)"""
    try:
        from weasyprint import HTML
        import tempfile

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            HTML(string=html_content).write_pdf(tmp.name)
            with open(tmp.name, 'rb') as f:
                pdf_bytes = f.read()
            os.unlink(tmp.name)
            return pdf_bytes
    except Exception as e:
        st.error(f"PDF generation error: {str(e)}")
        return None

st.set_page_config(
    page_title="Fitbit AI Health Coach",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

import streamlit.components.v1 as components
import base64
import io

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Outfit:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg:           #0F1117;
  --bg-card:      #1A1D27;
  --bg-subtle:    #22253A;
  --text:         #E8E9F0;
  --text-muted:   #8B8FA8;
  --text-faint:   #555870;
  --green:        #3DD68C;
  --green-dark:   #1A6B45;
  --green-dim:    rgba(61,214,140,0.12);
  --amber:        #F59E0B;
  --amber-dim:    rgba(245,158,11,0.12);
  --red:          #F87171;
  --red-dim:      rgba(248,113,113,0.12);
  --blue:         #60A5FA;
  --blue-dim:     rgba(96,165,250,0.12);
  --border:       #2A2D3E;
  --border-strong:#3A3D54;
  --shadow:       0 4px 24px rgba(0,0,0,0.4);
  --shadow-sm:    0 1px 4px rgba(0,0,0,0.3);
  --radius:       10px;
  --radius-sm:    6px;
}

html, body, .stApp {
  font-family: 'Outfit', sans-serif !important;
  background-color: var(--bg) !important;
  color: var(--text) !important;
}

.block-container {
  padding-top: 1.5rem !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
  max-width: 1200px !important;
  background: var(--bg) !important;
}

[data-testid="stSidebar"] {
  background-color: var(--bg-card) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { font-family: 'Outfit', sans-serif !important; color: var(--text) !important; }
/* Restore Material Symbols icon font so sidebar collapse icon renders correctly */
.material-symbols-rounded,
.material-symbols-outlined,
.material-icons,
[data-testid="stSidebarCollapsedControl"] span,
[data-testid="stSidebar"] button span,
button[data-testid="collapsedControl"] span {
  font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  font-family: 'Syne', sans-serif !important;
  color: var(--text) !important;
}
[data-testid="stSidebar"] .stTextInput input {
  background: var(--bg-subtle) !important;
  color: var(--text) !important;
  border: 1px solid var(--border-strong) !important;
}

h1, h2, h3, h4 {
  font-family: 'Syne', sans-serif !important;
  color: var(--text) !important;
  letter-spacing: -0.02em;
}

p, li, label, span { color: var(--text) !important; }

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0 8px 0;
  border-bottom: 1px solid var(--border-strong);
  margin: 24px 0 14px 0;
  font-family: 'Syne', sans-serif !important;
  font-weight: 700;
  font-size: 0.95em;
  color: var(--text) !important;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.print-header {
  padding-bottom: 14px;
  margin-bottom: 18px;
  border-bottom: 1px solid var(--border);
}

.alert-critical {
  background: var(--red-dim);
  color: var(--red);
  padding: 11px 15px;
  border-radius: var(--radius);
  margin: 8px 0;
  border-left: 3px solid var(--red);
  font-size: 0.88em;
}
.alert-warning {
  background: var(--amber-dim);
  color: var(--amber);
  padding: 11px 15px;
  border-radius: var(--radius);
  margin: 8px 0;
  border-left: 3px solid var(--amber);
  font-size: 0.88em;
}
.alert-caution {
  background: var(--amber-dim);
  color: var(--amber);
  padding: 10px 14px;
  border-radius: var(--radius);
  margin: 6px 0;
  border-left: 3px solid var(--amber);
  font-size: 0.86em;
}
.alert-good {
  background: var(--green-dim);
  color: var(--green);
  padding: 10px 14px;
  border-radius: var(--radius);
  margin: 6px 0;
  border-left: 3px solid var(--green);
  font-size: 0.86em;
}
.alert-info {
  background: var(--blue-dim);
  color: var(--blue);
  padding: 10px 14px;
  border-radius: var(--radius);
  margin: 6px 0;
  border-left: 3px solid var(--blue);
  font-size: 0.86em;
}

.comment-box {
  background: var(--bg-subtle);
  border-left: 2px solid var(--border-strong);
  padding: 10px 14px;
  margin: 8px 0;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-size: 0.84em;
  color: var(--text-muted) !important;
  line-height: 1.6;
}

.stButton > button {
  font-family: 'Outfit', sans-serif !important;
  font-weight: 600 !important;
  border-radius: var(--radius-sm) !important;
  transition: all 0.15s ease !important;
  letter-spacing: 0.02em !important;
  font-size: 0.88em !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
  background-color: var(--green-dark) !important;
  color: #fff !important;
  border: none !important;
}
.stButton > button[kind="primary"]:hover {
  background-color: #145236 !important;
  transform: translateY(-1px) !important;
  box-shadow: var(--shadow) !important;
}
.stButton > button[kind="secondary"] {
  background-color: var(--bg-card) !important;
  color: var(--text) !important;
  border: 1px solid var(--border-strong) !important;
}

[data-testid="stMetric"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 8px 12px !important;
  box-shadow: var(--shadow-sm) !important;
}
[data-testid="stMetricLabel"] > div {
  font-family: 'Outfit', sans-serif !important;
  font-size: 0.62em !important;
  font-weight: 500 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  color: var(--text-muted) !important;
  white-space: normal !important;
  overflow-wrap: break-word !important;
}
[data-testid="stMetricValue"] > div {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.95em !important;
  font-weight: 500 !important;
  color: var(--text) !important;
  white-space: normal !important;
  overflow-wrap: break-word !important;
}

[data-testid="stTabs"] [data-baseweb="tab-list"] {
  gap: 2px !important;
  border-bottom: 1px solid var(--border) !important;
  background: transparent !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
  font-family: 'Syne', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.88em !important;
  padding: 9px 20px !important;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
  color: var(--text-muted) !important;
  background: transparent !important;
  border: none !important;
  letter-spacing: 0.03em !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
  color: var(--green) !important;
  background: var(--green-dim) !important;
  border-bottom: 2px solid var(--green) !important;
}

.stTextInput input, .stTextArea textarea {
  font-family: 'Outfit', sans-serif !important;
  border-radius: var(--radius-sm) !important;
  border: 1px solid var(--border) !important;
  background: var(--bg-card) !important;
  color: var(--text) !important;
  font-size: 0.9em !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--green) !important;
  box-shadow: 0 0 0 2px rgba(61,214,140,0.15) !important;
}

[data-testid="stFileUploaderDropzone"] {
  border: 1px dashed var(--border-strong) !important;
  border-radius: var(--radius) !important;
  background: var(--bg-card) !important;
}

[data-testid="stExpander"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  background: var(--bg-card) !important;
}
[data-testid="stExpander"] summary {
  color: var(--text) !important;
}

.stRadio label {
  font-family: 'Outfit', sans-serif !important;
  color: var(--text) !important;
  font-size: 0.9em !important;
}
.stRadio div[role="radiogroup"] label { color: var(--text) !important; }

.stSpinner > div { border-top-color: var(--green) !important; }

hr { border-color: var(--border) !important; margin: 1.2rem 0 !important; }

.stMarkdown p, .stMarkdown li { color: var(--text) !important; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
  font-family: 'Syne', sans-serif !important;
  color: var(--text) !important;
}

[data-testid="stAlert"] {
  background: var(--bg-card) !important;
  color: var(--text) !important;
  border-radius: var(--radius) !important;
  border: 1px solid var(--border) !important;
}

.stSelectbox > div > div {
  background: var(--bg-card) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}

div[data-testid="stVerticalBlock"] { background: transparent !important; }

.stDataFrame { background: var(--bg-card) !important; }
.stDataFrame table { color: var(--text) !important; }
</style>
""", unsafe_allow_html=True)

# Inject comprehensive print styles using a different method
st.markdown("""
<style id="print-styles">
@media print {
    /* Page setup */
    @page {
        size: A4 portrait;
        margin: 15mm;
    }

    /* Reset everything to visible */
    * {
        print-color-adjust: exact !important;
        -webkit-print-color-adjust: exact !important;
        -webkit-print-fill-color: inherit !important;
    }

    /* Force document to be printable */
    html {
        height: auto !important;
        overflow: visible !important;
    }

    body {
        height: auto !important;
        overflow: visible !important;
        background: white !important;
        position: static !important;
    }

    /* Streamlit app container */
    .stApp {
        height: auto !important;
        overflow: visible !important;
        position: static !important;
    }

    /* Main content area */
    .main {
        height: auto !important;
        overflow: visible !important;
        max-width: 100% !important;
        position: static !important;
    }

    /* Block container */
    .block-container {
        max-width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
        overflow: visible !important;
        height: auto !important;
    }

    /* Hide UI elements */
    header,
    .stApp > header,
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stStatusWidget"],
    [data-testid="stSidebar"],
    .stDeployButton,
    .stActionButton,
    .stSpinner,
    #print-btn-container,
    div[style*="position: fixed"],
    iframe {
        display: none !important;
    }

    /* Ensure vertical blocks are visible */
    [data-testid="stVerticalBlock"] {
        display: block !important;
        overflow: visible !important;
        height: auto !important;
    }

    [data-testid="stVerticalBlock"] > div {
        display: block !important;
        overflow: visible !important;
    }

    /* Element containers */
    .element-container {
        display: block !important;
        overflow: visible !important;
        page-break-inside: avoid !important;
    }

    /* Markdown content */
    .stMarkdown {
        display: block !important;
        overflow: visible !important;
    }

    /* Plotly charts - CRITICAL */
    .stPlotlyChart {
        display: block !important;
        overflow: visible !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
    }

    .js-plotly-plot,
    .plotly-graph-div,
    .user-select-none,
    svg {
        display: block !important;
        overflow: visible !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        display: block !important;
        break-inside: avoid !important;
        page-break-inside: avoid !important;
    }

    /* Columns */
    [data-testid="column"] {
        display: block !important;
        overflow: visible !important;
        page-break-inside: avoid !important;
    }

    /* Page breaks */
    .page-break {
        page-break-after: always !important;
        break-after: page !important;
    }

    /* Remove any transforms that might break printing */
    * {
        transform: none !important;
    }
}
</style>
""", unsafe_allow_html=True)

def find_takeout_folder():
    patterns = [
        "./Takeout*/Fitbit/Global Export Data",
        "./Takeout*/Fitbit",
        "./**/Takeout*/Fitbit/Global Export Data",
        "./**/Takeout*/Fitbit",
        "./Fitbit/Global Export Data",
        "./Fitbit",
    ]
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            return matches[0]
    return None

def load_json_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def load_csv_file(filepath):
    try:
        return pd.read_csv(filepath)
    except:
        return None

def find_files(base_path, pattern):
    if base_path is None:
        return []
    search_path = os.path.join(base_path, "**", pattern)
    return glob.glob(search_path, recursive=True)

# ==============================================================================
# DATA LOADERS -- CONTINUOUS DETAILED DATA
# ==============================================================================

def parse_detailed_heart_rate(base_path):
    """Load ALL continuous heart rate data."""
    files = find_files(base_path, "heart_rate-*.json")
    all_data = []

    for f in files:
        data = load_json_file(f)
        if data and isinstance(data, list):
            for entry in data:
                value_data = entry.get('value', {})
                bpm = value_data.get('bpm', 0)
                if bpm and 30 <= bpm <= 220:
                    all_data.append({
                        'timestamp': entry.get('dateTime'),
                        'bpm': bpm,
                        'confidence': value_data.get('confidence', 0)
                    })

    if all_data:
        df = pd.DataFrame(all_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%m/%d/%y %H:%M:%S')
        df = df.sort_values('timestamp')
        return df
    return pd.DataFrame()

def parse_detailed_steps(base_path):
    """Load ALL continuous step data."""
    files = find_files(base_path, "steps-*.json")
    all_data = []

    for f in files:
        data = load_json_file(f)
        if data and isinstance(data, list):
            for entry in data:
                try:
                    steps = int(entry.get('value', 0))
                    all_data.append({
                        'timestamp': entry.get('dateTime'),
                        'steps': steps
                    })
                except:
                    pass

    if all_data:
        df = pd.DataFrame(all_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%m/%d/%y %H:%M:%S')
        df = df.sort_values('timestamp')
        return df
    return pd.DataFrame()

def parse_detailed_calories(base_path):
    """Load ALL continuous calorie data."""
    files = find_files(base_path, "calories-*.json")
    all_data = []

    for f in files:
        data = load_json_file(f)
        if data and isinstance(data, list):
            for entry in data:
                try:
                    cals = float(entry.get('value', 0))
                    all_data.append({
                        'timestamp': entry.get('dateTime'),
                        'calories': cals
                    })
                except:
                    pass

    if all_data:
        df = pd.DataFrame(all_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%m/%d/%y %H:%M:%S')
        df = df.sort_values('timestamp')
        return df
    return pd.DataFrame()

def parse_sleep_data(base_path):
    """Load sleep data."""
    sleep_files = find_files(base_path, "sleep-*.json")
    all_sleep = []

    for f in sleep_files:
        data = load_json_file(f)
        if data and isinstance(data, list):
            for entry in data:
                sleep_record = {
                    'date': entry.get('dateOfSleep'),
                    'start_time': entry.get('startTime'),
                    'end_time': entry.get('endTime'),
                    'duration_minutes': entry.get('duration', 0) / 60000 if entry.get('duration') else 0,
                    'minutes_asleep': entry.get('minutesAsleep'),
                    'minutes_awake': entry.get('minutesAwake'),
                    'time_in_bed': entry.get('timeInBed'),
                    'efficiency': entry.get('efficiency'),
                    'type': entry.get('type'),
                    'main_sleep': entry.get('mainSleep', False),
                }

                levels = entry.get('levels', {})
                summary = levels.get('summary', {})

                if sleep_record['type'] == 'stages':
                    if 'deep' in summary:
                        sleep_record['deep_minutes'] = summary['deep'].get('minutes', 0)
                    if 'light' in summary:
                        sleep_record['light_minutes'] = summary['light'].get('minutes', 0)
                    if 'rem' in summary:
                        sleep_record['rem_minutes'] = summary['rem'].get('minutes', 0)
                    if 'wake' in summary:
                        sleep_record['wake_minutes'] = summary['wake'].get('minutes', 0)
                else:
                    if 'restless' in summary:
                        sleep_record['restless_minutes'] = summary['restless'].get('minutes', 0)
                    if 'awake' in summary:
                        sleep_record['awake_minutes'] = summary['awake'].get('minutes', 0)
                    if 'asleep' in summary:
                        sleep_record['asleep_minutes'] = summary['asleep'].get('minutes', 0)

                all_sleep.append(sleep_record)

    if all_sleep:
        # Sort before DataFrame creation to avoid pandas nullable-type sort issues
        all_sleep.sort(key=lambda x: str(x.get('date', '')))
        # Normalise all values to plain Python types (no pd.NA, no pd.BooleanDtype)
        clean = []
        for rec in all_sleep:
            clean.append({k: (bool(v) if isinstance(v, bool) else
                              (int(v) if isinstance(v, int) else
                               (float(v) if isinstance(v, float) else v)))
                          for k, v in rec.items()})
        df = pd.DataFrame(clean)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df[df['date'].notna()].reset_index(drop=True)
        return df
    return pd.DataFrame()

def parse_heart_rate_summary(base_path):
    """Load resting heart rate summaries."""
    files = find_files(base_path, "resting_heart_rate-*.json")
    all_data = []

    for f in files:
        data = load_json_file(f)
        if data and isinstance(data, list):
            for entry in data:
                value_data = entry.get('value', {})
                hr_value = value_data.get('value', 0)
                if hr_value and hr_value > 30:
                    all_data.append({
                        'date': entry.get('dateTime'),
                        'resting_hr': hr_value,
                        'error': value_data.get('error', 0)
                    })

    if all_data:
        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'], format='%m/%d/%y %H:%M:%S')
        df = df.sort_values('date')
        return df
    return pd.DataFrame()

def parse_hrv(base_path):
    """Load heart rate variability data."""
    search_dirs = [
        base_path.replace("Global Export Data", "Heart Rate Variability"),
        base_path
    ]

    all_data = []
    for search_dir in search_dirs:
        files = find_files(search_dir, "Daily Heart Rate Variability Summary*.csv")
        for f in files:
            df = load_csv_file(f)
            if df is not None and not df.empty and 'timestamp' in df.columns:
                all_data.append(df)

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        combined['timestamp'] = pd.to_datetime(combined['timestamp'])
        combined = combined.sort_values('timestamp').drop_duplicates(subset=['timestamp'])
        return combined
    return pd.DataFrame()

def parse_spo2(base_path):
    """Load oxygen saturation data."""
    search_dirs = [
        base_path.replace("Global Export Data", "Oxygen Saturation (SpO2)"),
        base_path
    ]

    for search_dir in search_dirs:
        files = find_files(search_dir, "Daily SpO2*.csv")
        if files:
            df = load_csv_file(files[0])
            if df is not None and not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df
    return pd.DataFrame()

def parse_stress_score(base_path):
    """Load stress score data."""
    search_dirs = [
        base_path.replace("Global Export Data", "Stress Score"),
        base_path
    ]

    for search_dir in search_dirs:
        files = find_files(search_dir, "Stress Score.csv")
        if files:
            df = load_csv_file(files[0])
            if df is not None and not df.empty:
                df['DATE'] = pd.to_datetime(df['DATE'])
                return df
    return pd.DataFrame()

def parse_sleep_score(base_path):
    """Load sleep score data."""
    files = find_files(base_path.replace("Global Export Data", "").rstrip("/"), "*/sleep_score.csv")
    if not files:
        files = find_files(base_path, "sleep_score.csv")

    if files:
        df = load_csv_file(files[0])
        if df is not None and not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            return df
    return pd.DataFrame()

def parse_profile(base_path):
    """Load user profile."""
    search_dirs = [
        base_path.replace("Global Export Data", "Your Profile"),
        base_path
    ]

    for search_dir in search_dirs:
        files = find_files(search_dir, "Profile.csv")
        if files:
            df = load_csv_file(files[0])
            if df is not None and not df.empty:
                return df.iloc[0].to_dict()
    return {}

# ==============================================================================
# EXERCISE DATA PARSER
# ==============================================================================

def parse_exercise_data(base_path):
    """
    Parse exercise sessions from Fitbit export:
      - exercise-*.json  (Global Export Data)
      - UserExercises*.csv (Health Fitness Data_GoogleData)
    Returns a DataFrame sorted most-recent first.
    """
    all_exercises = []

    # 1. JSON exercise files
    json_files = find_files(base_path, "exercise-*.json")
    for f in sorted(json_files):
        data = load_json_file(f)
        if not data or not isinstance(data, list):
            continue
        for ex in data:
            start_time = ex.get('startTime', '')
            date_str = start_time[:10] if start_time else ''
            if not date_str:
                continue
            record = {
                'date': date_str,
                'activity_name': ex.get('activityName', 'Unknown'),
                'duration_minutes': round(ex.get('duration', 0) / 60000, 1),
                'calories': float(ex.get('calories', 0) or 0),
                'avg_heart_rate': float(ex.get('averageHeartRate', 0) or 0),
                'steps': float(ex.get('steps', 0) or 0),
                'distance_km': round(float(ex.get('distance', 0) or 0), 2),
            }
            all_exercises.append(record)

    # 2. CSV exercise files (broader search from Fitbit root)
    fitbit_root = base_path
    for _ in range(4):
        fitbit_root = os.path.dirname(fitbit_root)
        if os.path.basename(fitbit_root).lower().startswith('fitbit'):
            break
    csv_files = find_files(fitbit_root, "UserExercises*.csv")
    for csv_f in csv_files:
        df_csv = load_csv_file(csv_f)
        if df_csv is None or df_csv.empty:
            continue
        for _, row in df_csv.iterrows():
            try:
                # Support both old export format (human-readable columns) and
                # new Google Takeout format (snake_case columns)
                start_raw = str(row.get('exercise_start', row.get('Start Time', '')) or '')
                date_str = start_raw[:10] if len(start_raw) >= 10 else ''
                if not date_str:
                    continue

                # Duration: compute from start/end if no Duration column
                dur_min = 0.0
                if 'exercise_end' in row.index:
                    try:
                        t_start = pd.to_datetime(start_raw, utc=True)
                        t_end = pd.to_datetime(str(row.get('exercise_end', '') or ''), utc=True)
                        dur_min = (t_end - t_start).total_seconds() / 60
                    except Exception:
                        dur_min = 0.0
                else:
                    dur_raw = str(row.get('Duration', '0:0') or '0:0')
                    dur_parts = dur_raw.replace('h', ':').replace('m', ':').replace('s', '').split(':')
                    if len(dur_parts) >= 2:
                        try:
                            dur_min = float(dur_parts[0]) * 60 + float(dur_parts[1])
                        except Exception:
                            dur_min = 0.0

                # Distance: new format stores in mm, old format in km
                dist_km = 0.0
                if 'tracker_total_distance_mm' in row.index:
                    try:
                        dist_km = float(str(row.get('tracker_total_distance_mm', '0') or '0') or 0) / 1_000_000
                    except Exception:
                        dist_km = 0.0
                else:
                    try:
                        dist_km = float(str(row.get('Distance (km)', '0') or '0').replace(',', '.') or 0)
                    except Exception:
                        dist_km = 0.0

                def _safe_float(val):
                    try:
                        return float(str(val or '0').replace(',', '.') or 0)
                    except Exception:
                        return 0.0

                record = {
                    'date': date_str,
                    'activity_name': str(
                        row.get('activity_name', row.get('Activity Name', 'Unknown')) or 'Unknown'
                    ),
                    'duration_minutes': round(dur_min, 1),
                    'calories': _safe_float(
                        row.get('tracker_total_calories', row.get('Calories (kcal)', 0))
                    ),
                    'avg_heart_rate': _safe_float(
                        row.get('tracker_avg_heart_rate', row.get('Average Heart Rate', 0))
                    ),
                    'steps': _safe_float(
                        row.get('tracker_total_steps', row.get('Steps', 0))
                    ),
                    'distance_km': round(dist_km, 2),
                }
                all_exercises.append(record)
            except Exception:
                pass

    if not all_exercises:
        return pd.DataFrame()

    df = pd.DataFrame(all_exercises)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    df = df.sort_values('date', ascending=False)
    df = df.drop_duplicates(subset=['date', 'activity_name', 'duration_minutes'])
    return df.reset_index(drop=True)


def parse_azm(base_path):
    """Load Active Zone Minutes data (actual minutes in each HR zone per day)."""
    # Files: Active Zone Minutes - YYYY-MM-DD.csv
    # Columns: date_time, heart_zone_id, total_minutes
    files = find_files(base_path, "Active Zone Minutes*.csv")
    if not files:
        # Try from Fitbit root
        fitbit_root = base_path
        for _ in range(4):
            fitbit_root = os.path.dirname(fitbit_root)
            if os.path.basename(fitbit_root).lower().startswith('fitbit'):
                break
        files = find_files(fitbit_root, "Active Zone Minutes*.csv")
    all_rows = []
    for f in files:
        df_f = load_csv_file(f)
        if df_f is None or df_f.empty:
            continue
        for _, row in df_f.iterrows():
            try:
                dt_raw = str(row.get('date_time', '') or '')
                if not dt_raw:
                    continue
                date_str = dt_raw[:10]
                zone = str(row.get('heart_zone_id', '') or '').strip()
                mins = float(str(row.get('total_minutes', '0') or '0') or 0)
                all_rows.append({'date': date_str, 'zone': zone, 'minutes': mins})
            except Exception:
                pass
    if not all_rows:
        return pd.DataFrame()
    df = pd.DataFrame(all_rows)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    return df


def parse_temperature(base_path):
    """Load nightly computed wrist skin temperature from Fitbit."""
    # Files: Computed Temperature - YYYY-MM-DD.csv
    # Columns: type, sleep_start, sleep_end, temperature_samples, nightly_temperature,
    #          baseline_relative_nightly_standard_deviation, ...
    files = find_files(base_path, "Computed Temperature*.csv")
    if not files:
        fitbit_root = base_path
        for _ in range(4):
            fitbit_root = os.path.dirname(fitbit_root)
            if os.path.basename(fitbit_root).lower().startswith('fitbit'):
                break
        files = find_files(fitbit_root, "Computed Temperature*.csv")
    all_rows = []
    for f in files:
        df_f = load_csv_file(f)
        if df_f is None or df_f.empty:
            continue
        for _, row in df_f.iterrows():
            try:
                sleep_start = str(row.get('sleep_start', '') or '')
                if not sleep_start or len(sleep_start) < 10:
                    continue
                date_str = sleep_start[:10]
                temp = float(str(row.get('nightly_temperature', '') or '') or 0)
                dev = float(str(row.get('baseline_relative_nightly_standard_deviation', '') or '') or 0)
                if temp > 0:
                    all_rows.append({'date': date_str, 'temp_c': temp, 'deviation': dev})
            except Exception:
                pass
    if not all_rows:
        return pd.DataFrame()
    df = pd.DataFrame(all_rows)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    df = df.sort_values('date')
    return df


# ==============================================================================
# HEALTH SUMMARY FOR GEMINI
# ==============================================================================

def create_health_summary(profile, hr_summary_df, sleep_df, sleep_score_df,
                          hrv_df, spo2_df, stress_df,
                          detailed_steps_df, detailed_cals_df,
                          exercise_df, detailed_hr_df=None,
                          azm_df=None, temp_df=None, data_period=30):
    """
    Build a concise, structured text summary of the user's Fitbit health data
    to include in the Gemini prompt. Raw data is never sent -- only aggregates.
    """
    lines = []
    now = datetime.now()
    cutoff = pd.Timestamp(now - timedelta(days=data_period))

    # -- Profile ---------------------------------------------------------------
    lines.append("=== USER PROFILE ===")
    if profile:
        if 'date_of_birth' in profile:
            try:
                dob = datetime.strptime(str(profile['date_of_birth']), '%Y-%m-%d')
                age = int((now - dob).days / 365.25)
                lines.append(f"Age: {age} years")
            except Exception:
                pass
        gender = profile.get('gender', profile.get('sex', ''))
        if gender:
            lines.append(f"Gender: {gender}")
        height = profile.get('height', 0)
        weight = profile.get('weight', 0)
        try:
            h = float(str(height).replace(',', '.'))
            w = float(str(weight).replace(',', '.'))
            if h > 0 and w > 0:
                bmi = round(w / (h / 100) ** 2, 1)
                lines.append(f"Height: {h:.0f} cm | Weight: {w:.0f} kg | BMI: {bmi}")
        except Exception:
            pass
    else:
        lines.append("Profile: not available")

    lines.append(f"\n=== ANALYSIS PERIOD: last {data_period} days ===")
    lines.append(f"From {cutoff.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}")

    # -- Cardiovascular --------------------------------------------------------
    lines.append("\n=== CARDIOVASCULAR HEALTH ===")
    if not hr_summary_df.empty and 'resting_hr' in hr_summary_df.columns:
        try:
            rhr = hr_summary_df.copy()
            if 'date' in rhr.columns:
                rhr['date'] = pd.to_datetime(rhr['date'], errors='coerce')
                rhr = rhr[rhr['date'] >= cutoff].sort_values('date')
            if not rhr.empty:
                avg_rhr = rhr['resting_hr'].mean()
                trend = (rhr['resting_hr'].iloc[-5:].mean() - rhr['resting_hr'].iloc[:5].mean()
                         if len(rhr) >= 10 else 0)
                lines.append(f"Resting Heart Rate: avg {avg_rhr:.0f} bpm "
                              f"(range {rhr['resting_hr'].min():.0f}-{rhr['resting_hr'].max():.0f})")
                if abs(trend) > 2:
                    direction = "decreasing (improving)" if trend < 0 else "increasing (worsening)"
                    lines.append(f"  RHR trend: {direction} by {abs(trend):.1f} bpm over period")
                # Recent 7-day vs overall
                recent_7 = rhr[rhr['date'] >= pd.Timestamp(now - timedelta(days=7))]
                if not recent_7.empty and len(rhr) > 7:
                    lines.append(f"  RHR last 7 days avg: {recent_7['resting_hr'].mean():.0f} bpm "
                                 f"(vs {avg_rhr:.0f} bpm overall)")
                # Per-day compact table
                rhr_rows = rhr[['date', 'resting_hr']].dropna()
                if not rhr_rows.empty:
                    entries = ", ".join(
                        f"{r['date'].strftime('%m-%d')}:{int(r['resting_hr'])}"
                        for _, r in rhr_rows.iterrows()
                    )
                    lines.append(f"  Daily RHR (mm-dd:bpm): {entries}")
        except Exception:
            pass
    else:
        lines.append("Resting Heart Rate: data not available")

    if not hrv_df.empty and 'rmssd' in hrv_df.columns:
        try:
            hrv = hrv_df.copy()
            if 'timestamp' in hrv.columns:
                hrv['timestamp'] = pd.to_datetime(hrv['timestamp'], errors='coerce')
                hrv = hrv[hrv['timestamp'] >= cutoff]
            if not hrv.empty:
                avg_hrv = hrv['rmssd'].mean()
                lines.append(f"HRV (RMSSD): avg {avg_hrv:.1f} ms")
                if avg_hrv < 20:
                    lines.append("  -> Low HRV: high stress or poor recovery")
                elif avg_hrv > 50:
                    lines.append("  -> Good HRV: healthy autonomic function")
                # HRV trend
                hrv_sorted = hrv.sort_values('timestamp')
                if len(hrv_sorted) >= 10:
                    mid = len(hrv_sorted) // 2
                    first_avg = hrv_sorted.head(mid)['rmssd'].mean()
                    second_avg = hrv_sorted.tail(mid)['rmssd'].mean()
                    delta = second_avg - first_avg
                    direction = "improving" if delta > 2 else "declining" if delta < -2 else "stable"
                    lines.append(f"  HRV trend: {direction} ({delta:+.1f} ms over {data_period} days)")
                if len(hrv_sorted) >= 7:
                    recent_7d_hrv = hrv_sorted.tail(7)['rmssd'].mean()
                    lines.append(f"  HRV last 7 days: {recent_7d_hrv:.1f} ms")
                # Per-day compact table
                hrv_rows = hrv_sorted[['timestamp', 'rmssd']].dropna()
                if not hrv_rows.empty:
                    entries = ", ".join(
                        f"{r['timestamp'].strftime('%m-%d')}:{r['rmssd']:.0f}"
                        for _, r in hrv_rows.iterrows()
                    )
                    lines.append(f"  Daily HRV RMSSD (mm-dd:ms): {entries}")
        except Exception:
            pass

    # HR zone distribution — prefer AZM (actual minutes), fall back to continuous HR %
    lines.append(f"\n=== HEART RATE ZONE DISTRIBUTION (last {data_period} days) ===")
    azm_used = False
    if azm_df is not None and not azm_df.empty:
        try:
            az = azm_df.copy()
            az = az[az['date'] >= cutoff]
            if not az.empty:
                # Total minutes per zone over the period
                zone_totals = az.groupby('zone')['minutes'].sum()
                total_active = zone_totals.sum()
                days_in_period = (az['date'].max() - az['date'].min()).days + 1
                lines.append(f"Active Zone Minutes over {days_in_period} days (Fitbit-logged):")
                zone_order = ['FAT_BURN', 'CARDIO', 'PEAK']
                zone_labels = {'FAT_BURN': 'Fat-burn', 'CARDIO': 'Cardio', 'PEAK': 'Peak'}
                for z in zone_order:
                    if z in zone_totals.index:
                        total = int(zone_totals[z])
                        avg_per_day = total / max(days_in_period, 1)
                        lines.append(f"  {zone_labels.get(z, z)}: {total} min total, "
                                     f"{avg_per_day:.0f} min/day avg")
                # Daily AZM totals for recent period
                daily_azm = az[az['zone'].isin(zone_order)].groupby('date')['minutes'].sum().reset_index()
                daily_azm = daily_azm.sort_values('date')
                if not daily_azm.empty:
                    entries = ", ".join(
                        f"{r['date'].strftime('%m-%d')}:{int(r['minutes'])}"
                        for _, r in daily_azm.iterrows()
                    )
                    lines.append(f"  Daily active zone minutes (mm-dd:min): {entries}")
                azm_used = True
        except Exception:
            pass
    if not azm_used and detailed_hr_df is not None and not detailed_hr_df.empty and 'bpm' in detailed_hr_df.columns:
        try:
            age_for_zones = 30
            if profile and 'date_of_birth' in profile:
                try:
                    dob_z = datetime.strptime(str(profile['date_of_birth']), '%Y-%m-%d')
                    age_for_zones = int((now - dob_z).days / 365.25)
                except Exception:
                    pass
            max_hr_est = 220 - age_for_zones
            hz = detailed_hr_df.copy()
            hz['timestamp'] = pd.to_datetime(hz['timestamp'], errors='coerce')
            hz = hz[hz['timestamp'] >= cutoff]
            if not hz.empty:
                total_pts = len(hz)
                fat_burn = ((hz['bpm'] >= max_hr_est * 0.50) & (hz['bpm'] < max_hr_est * 0.70)).sum()
                cardio_z = ((hz['bpm'] >= max_hr_est * 0.70) & (hz['bpm'] < max_hr_est * 0.85)).sum()
                peak_z = (hz['bpm'] >= max_hr_est * 0.85).sum()
                lines.append(f"Estimated max HR: {max_hr_est} bpm (220 minus age {age_for_zones})")
                lines.append(f"Fat-burn zone (50-69% max HR): {fat_burn/total_pts*100:.0f}% of HR readings")
                lines.append(f"Cardio zone (70-84% max HR): {cardio_z/total_pts*100:.0f}% of HR readings")
                lines.append(f"Peak zone (>=85% max HR): {peak_z/total_pts*100:.0f}% of HR readings")
        except Exception:
            pass

    # -- Sleep -----------------------------------------------------------------
    lines.append("\n=== SLEEP QUALITY ===")
    if not sleep_df.empty:
        try:
            sl = sleep_df.copy()
            if 'main_sleep' in sl.columns:
                sl = sl[sl['main_sleep'] == True]
            if 'date' in sl.columns:
                sl['date'] = pd.to_datetime(sl['date'], errors='coerce')
                sl = sl[sl['date'] >= cutoff]
            if not sl.empty:
                if 'duration_minutes' in sl.columns:
                    avg_dur = sl['duration_minutes'].mean()
                    lines.append(f"Average sleep duration: {avg_dur/60:.1f} h ({avg_dur:.0f} min)")
                if 'efficiency' in sl.columns:
                    avg_eff = sl['efficiency'].mean()
                    lines.append(f"Sleep efficiency: {avg_eff:.0f}%")
                if 'deep_minutes' in sl.columns:
                    avg_deep = sl['deep_minutes'].mean()
                    avg_light = sl.get('light_minutes', pd.Series([0])).mean() if 'light_minutes' in sl.columns else 0
                    avg_rem = sl.get('rem_minutes', pd.Series([0])).mean() if 'rem_minutes' in sl.columns else 0
                    avg_wake = sl.get('wake_minutes', pd.Series([0])).mean() if 'wake_minutes' in sl.columns else 0
                    lines.append(f"Sleep stages (avg/night): Deep {avg_deep:.0f} min | "
                                 f"Light {avg_light:.0f} min | REM {avg_rem:.0f} min | Awake {avg_wake:.0f} min")
        except Exception:
            pass
    else:
        lines.append("Sleep: data not available")

    if not sleep_score_df.empty and 'overall_score' in sleep_score_df.columns:
        try:
            avg_score = sleep_score_df['overall_score'].mean()
            min_score = sleep_score_df['overall_score'].min()
            max_score = sleep_score_df['overall_score'].max()
            lines.append(f"Sleep score: avg {avg_score:.0f}/100 (range {min_score:.0f}-{max_score:.0f})")
            # Sub-scores if available
            for col, label in [('composition_score', 'composition'),
                                ('revitalization_score', 'revitalization'),
                                ('duration_score', 'duration'),
                                ('deep_sleep_in_minutes', 'deep sleep min')]:
                if col in sleep_score_df.columns:
                    val = sleep_score_df[col].mean()
                    lines.append(f"  Sleep {label}: avg {val:.0f}")
        except Exception:
            pass
    # Sleep variability + per-night log
    if not sleep_df.empty:
        try:
            sl_var = sleep_df.copy()
            if 'main_sleep' in sl_var.columns:
                sl_var = sl_var[sl_var['main_sleep'] == True]
            if 'date' in sl_var.columns:
                sl_var['date'] = pd.to_datetime(sl_var['date'], errors='coerce')
                sl_var = sl_var[sl_var['date'] >= cutoff].sort_values('date')
            if not sl_var.empty and 'duration_minutes' in sl_var.columns and len(sl_var) > 2:
                sleep_std = sl_var['duration_minutes'].std()
                sleep_min = sl_var['duration_minutes'].min()
                sleep_max = sl_var['duration_minutes'].max()
                lines.append(f"Sleep duration range: {sleep_min/60:.1f}h - {sleep_max/60:.1f}h "
                             f"(variability ±{sleep_std/60:.1f}h std dev)")
                if sleep_std > 60:
                    lines.append("  -> High sleep variability: inconsistent schedule")
            # Per-night compact log
            if not sl_var.empty:
                night_parts = []
                for _, nr in sl_var.iterrows():
                    d = nr['date'].strftime('%m-%d')
                    h = f"{nr['duration_minutes']/60:.1f}h" if 'duration_minutes' in nr and pd.notna(nr.get('duration_minutes')) else ''
                    e = f"{int(nr['efficiency'])}%" if 'efficiency' in nr and pd.notna(nr.get('efficiency')) else ''
                    deep = f"D{int(nr['deep_minutes'])}m" if 'deep_minutes' in nr and pd.notna(nr.get('deep_minutes')) else ''
                    rem = f"R{int(nr['rem_minutes'])}m" if 'rem_minutes' in nr and pd.notna(nr.get('rem_minutes')) else ''
                    night_parts.append(f"{d}:{h}/{e}/{deep}/{rem}".rstrip('/'))
                lines.append("Per-night log (date:hours/efficiency/deep/REM):")
                lines.append("  " + ", ".join(night_parts))
            # Merge sleep scores into per-night log if available
            if not sleep_score_df.empty and 'overall_score' in sleep_score_df.columns:
                try:
                    sc_copy = sleep_score_df.copy()
                    if 'timestamp' in sc_copy.columns:
                        sc_copy['date'] = pd.to_datetime(sc_copy['timestamp'], errors='coerce').dt.date
                    elif 'date' in sc_copy.columns:
                        sc_copy['date'] = pd.to_datetime(sc_copy['date'], errors='coerce').dt.date
                    sc_copy = sc_copy.dropna(subset=['date'])
                    sc_copy['date'] = pd.to_datetime(sc_copy['date'])
                    sc_copy = sc_copy[sc_copy['date'] >= cutoff].sort_values('date')
                    if not sc_copy.empty:
                        score_entries = ", ".join(
                            f"{r['date'].strftime('%m-%d')}:{int(r['overall_score'])}"
                            for _, r in sc_copy.iterrows()
                        )
                        lines.append(f"  Nightly sleep scores (mm-dd:score): {score_entries}")
                except Exception:
                    pass
        except Exception:
            pass

    # -- Daily Activity --------------------------------------------------------
    lines.append("\n=== DAILY ACTIVITY ===")
    if not detailed_steps_df.empty:
        try:
            sc = detailed_steps_df.copy()
            sc['date'] = sc['timestamp'].dt.date
            daily = sc.groupby('date')['steps'].sum().reset_index()
            daily['date'] = pd.to_datetime(daily['date'])
            recent = daily[daily['date'] >= cutoff]
            if not recent.empty:
                avg_steps = recent['steps'].mean()
                max_steps = recent['steps'].max()
                min_steps = recent['steps'].min()
                lines.append(f"Average daily steps: {avg_steps:,.0f} (peak {max_steps:,.0f}, low {min_steps:,.0f})")
                days_over_10k = (recent['steps'] >= 10000).sum()
                days_under_5k = (recent['steps'] < 5000).sum()
                lines.append(f"Days >=10,000 steps: {days_over_10k} | Days <5,000 steps: {days_under_5k}")
                if avg_steps < 5000:
                    lines.append("  -> Below recommended level (<5,000 steps/day)")
                elif avg_steps >= 10000:
                    lines.append("  -> Excellent activity level (>=10,000 steps/day)")
                # Weekly breakdown (last 4 weeks)
                lines.append("Weekly step totals (most recent week last):")
                for w in range(3, -1, -1):
                    wk_start = pd.Timestamp(now - timedelta(days=(w + 1) * 7))
                    wk_end = pd.Timestamp(now - timedelta(days=w * 7))
                    wk_data = daily[(daily['date'] >= wk_start) & (daily['date'] < wk_end)]
                    if not wk_data.empty:
                        label = "most recent" if w == 0 else f"{w}w ago"
                        lines.append(f"  {label}: avg {wk_data['steps'].mean():,.0f}/day, "
                                     f"total {wk_data['steps'].sum():,.0f}")
        except Exception:
            pass
    else:
        lines.append("Steps: data not available")

    if not detailed_cals_df.empty:
        try:
            cc = detailed_cals_df.copy()
            cc['date'] = cc['timestamp'].dt.date
            daily_cal = cc.groupby('date')['calories'].sum().reset_index()
            daily_cal['date'] = pd.to_datetime(daily_cal['date'])
            recent_cal = daily_cal[daily_cal['date'] >= cutoff]
            if not recent_cal.empty:
                avg_cals = recent_cal['calories'].mean()
                peak_cals = recent_cal['calories'].max()
                min_cals = recent_cal['calories'].min()
                lines.append(f"Daily calories burned: avg {avg_cals:,.0f} kcal | peak {peak_cals:,.0f} | low {min_cals:,.0f}")
        except Exception:
            pass

    # -- SpO2 ------------------------------------------------------------------
    if not spo2_df.empty and 'average_value' in spo2_df.columns:
        lines.append("\n=== OXYGEN SATURATION (SpO2) ===")
        try:
            spo2_r = spo2_df.copy()
            if 'timestamp' in spo2_r.columns:
                spo2_r['date'] = pd.to_datetime(spo2_r['timestamp'], errors='coerce')
            elif 'date' in spo2_r.columns:
                spo2_r['date'] = pd.to_datetime(spo2_r['date'], errors='coerce')
            spo2_r = spo2_r[spo2_r['date'] >= cutoff].sort_values('date')
            avg_spo2 = spo2_r['average_value'].mean() if not spo2_r.empty else spo2_df['average_value'].mean()
            min_spo2 = (spo2_r['lower_bound'].min()
                        if 'lower_bound' in spo2_r.columns and not spo2_r.empty
                        else spo2_r['average_value'].min() if not spo2_r.empty
                        else spo2_df['average_value'].min())
            lines.append(f"Average SpO2: {avg_spo2:.1f}% | Period minimum: {min_spo2:.1f}%")
            if min_spo2 < 90:
                lines.append("  -> SpO2 dropped below 90% -- notable dip during sleep")
            # Per-night compact log
            if not spo2_r.empty:
                night_spo2 = []
                for _, nr in spo2_r.iterrows():
                    d = nr['date'].strftime('%m-%d')
                    avg_v = f"{nr['average_value']:.1f}" if pd.notna(nr.get('average_value')) else ''
                    low_v = f"(min {nr['lower_bound']:.1f})" if 'lower_bound' in nr and pd.notna(nr.get('lower_bound')) else ''
                    night_spo2.append(f"{d}:{avg_v}{low_v}")
                lines.append(f"  Nightly SpO2 avg(min) (mm-dd): {', '.join(night_spo2)}")
        except Exception:
            pass

    # -- Stress ----------------------------------------------------------------
    if not stress_df.empty and 'STRESS_SCORE' in stress_df.columns:
        lines.append("\n=== STRESS & RECOVERY ===")
        try:
            st_df = stress_df.copy()
            # Parse date from stress_df
            date_col = None
            for c in ['DATE', 'date', 'Date', 'UPDATED_AT', 'updated_at']:
                if c in st_df.columns:
                    date_col = c
                    break
            if date_col:
                st_df['_date'] = pd.to_datetime(st_df[date_col], errors='coerce')
                st_df = st_df[st_df['_date'] >= cutoff].sort_values('_date')
            valid = st_df[st_df['STRESS_SCORE'] > 0]
            if not valid.empty:
                avg_s = valid['STRESS_SCORE'].mean()
                lines.append(f"Average Stress/Recovery Score: {avg_s:.0f}/100 (higher = better recovery)")
                if avg_s < 40:
                    lines.append("  -> Consistently elevated stress / low recovery")
                elif avg_s > 70:
                    lines.append("  -> Good stress management and recovery")
                # Recent 7-day vs overall
                if date_col and len(valid) > 7:
                    recent_7_stress = valid[valid['_date'] >= pd.Timestamp(now - timedelta(days=7))]
                    if not recent_7_stress.empty:
                        r7 = recent_7_stress['STRESS_SCORE'].mean()
                        lines.append(f"  Stress score last 7 days: {r7:.0f} (vs {avg_s:.0f} overall)")
                # Trend: first half vs second half
                if len(valid) >= 10:
                    mid = len(valid) // 2
                    first_half = valid.head(mid)['STRESS_SCORE'].mean()
                    second_half = valid.tail(mid)['STRESS_SCORE'].mean()
                    delta = second_half - first_half
                    direction = "improving" if delta > 3 else "declining" if delta < -3 else "stable"
                    lines.append(f"  Stress score trend: {direction} ({delta:+.0f} points over period)")
                # Per-day compact table
                if date_col:
                    s_entries = ", ".join(
                        f"{r['_date'].strftime('%m-%d')}:{int(r['STRESS_SCORE'])}"
                        for _, r in valid.iterrows()
                    )
                    lines.append(f"  Daily stress scores (mm-dd:score): {s_entries}")
        except Exception:
            pass

    # -- Wrist Temperature -----------------------------------------------------
    if temp_df is not None and not temp_df.empty and 'temp_c' in temp_df.columns:
        lines.append("\n=== WRIST SKIN TEMPERATURE (nightly) ===")
        try:
            tmp = temp_df.copy()
            tmp = tmp[tmp['date'] >= cutoff].sort_values('date')
            if not tmp.empty:
                avg_temp = tmp['temp_c'].mean()
                lines.append(f"Average nightly wrist temp: {avg_temp:.2f}°C "
                             f"(range {tmp['temp_c'].min():.2f} - {tmp['temp_c'].max():.2f}°C)")
                if 'deviation' in tmp.columns:
                    avg_dev = tmp['deviation'].mean()
                    max_dev = tmp['deviation'].abs().max()
                    lines.append(f"Avg nightly deviation from baseline: {avg_dev:.3f} "
                                 f"(max deviation: {max_dev:.3f})")
                    if max_dev > 1.0:
                        lines.append("  -> Large temp deviation detected: possible illness or high training load")
                # Per-night compact log
                t_entries = ", ".join(
                    f"{r['date'].strftime('%m-%d')}:{r['temp_c']:.2f}"
                    for _, r in tmp.iterrows()
                )
                lines.append(f"  Nightly wrist temp (mm-dd:°C): {t_entries}")
        except Exception:
            pass

    # -- Exercise History ------------------------------------------------------
    lines.append("\n=== EXERCISE HISTORY ===")
    if not exercise_df.empty:
        try:
            lines.append(f"Total logged sessions: {len(exercise_df)}")
            top_activities = exercise_df['activity_name'].value_counts().head(5)
            lines.append("Most frequent activities: " +
                         ", ".join([f"{n} ({c}x)" for n, c in top_activities.items()]))
            # Per-activity-type stats
            lines.append("Stats by activity type:")
            for act_name, grp in exercise_df.groupby('activity_name'):
                avg_d = grp['duration_minutes'].mean()
                avg_c = grp['calories'].mean()
                hr_grp = grp[grp['avg_heart_rate'] > 0]['avg_heart_rate']
                avg_h = hr_grp.mean() if not hr_grp.empty else 0
                dist_grp = grp[grp['distance_km'] > 0]['distance_km']
                avg_dist = dist_grp.mean() if not dist_grp.empty else 0
                stat_parts = [f"{len(grp)}x", f"{avg_d:.0f}min avg", f"{avg_c:.0f}kcal avg"]
                if avg_h > 0:
                    stat_parts.append(f"{avg_h:.0f}bpm avg HR")
                if avg_dist > 0:
                    stat_parts.append(f"{avg_dist:.1f}km avg dist")
                lines.append(f"  {act_name}: {', '.join(stat_parts)}")
            # Weekly frequency
            ex_copy = exercise_df.copy()
            ex_copy['week'] = pd.to_datetime(ex_copy['date']).dt.to_period('W')
            weekly_freq = ex_copy.groupby('week').size().mean()
            lines.append(f"Average sessions per week (all time): {weekly_freq:.1f}")
            # Last 20 sessions
            # Weekly exercise frequency (last 4 weeks)
            lines.append("Exercise frequency (last 4 weeks, most recent last):")
            ex_copy2 = exercise_df.copy()
            ex_copy2['date_dt'] = pd.to_datetime(ex_copy2['date'], errors='coerce')
            for w in range(3, -1, -1):
                wk_start = pd.Timestamp(now - timedelta(days=(w + 1) * 7))
                wk_end = pd.Timestamp(now - timedelta(days=w * 7))
                wk_ex = ex_copy2[(ex_copy2['date_dt'] >= wk_start) & (ex_copy2['date_dt'] < wk_end)]
                label = "most recent" if w == 0 else f"{w}w ago"
                if not wk_ex.empty:
                    total_min = wk_ex['duration_minutes'].sum()
                    lines.append(f"  {label}: {len(wk_ex)} sessions, {total_min:.0f} min total")
                else:
                    lines.append(f"  {label}: 0 sessions")

            # Average session stats
            avg_dur = exercise_df['duration_minutes'].mean()
            avg_cal_ex = exercise_df['calories'].mean()
            avg_hr_ex = exercise_df[exercise_df['avg_heart_rate'] > 0]['avg_heart_rate'].mean() if (exercise_df['avg_heart_rate'] > 0).any() else 0
            lines.append(f"Average session: {avg_dur:.0f} min, {avg_cal_ex:.0f} kcal"
                        + (f", {avg_hr_ex:.0f} bpm avg HR" if avg_hr_ex > 0 else ""))

            lines.append("Recent sessions (most recent first):")
            for _, row in exercise_df.head(20).iterrows():
                date_str = row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else 'N/A'
                hr_s = f", Avg HR {int(row['avg_heart_rate'])} bpm" if row['avg_heart_rate'] > 0 else ""
                dist_s = f", {row['distance_km']:.1f} km" if row['distance_km'] > 0 else ""
                steps_s = f", {int(row['steps']):,} steps" if row['steps'] > 0 else ""
                lines.append(f"  - {date_str}: {row['activity_name']} -- "
                             f"{row['duration_minutes']:.0f} min, {row['calories']:.0f} kcal"
                             f"{hr_s}{dist_s}{steps_s}")
        except Exception:
            pass
    else:
        lines.append("No exercise session data found.")

    return "\n".join(lines)


# ==============================================================================
# GEMINI AI COACH FUNCTIONS
# ==============================================================================

def generate_ai_fitness_plan(health_summary: str, goals: str,
                              api_key: str, language: str = "English"):
    """Call Gemini to generate a personalised fitness plan."""
    lang_line = "Please respond in French." if language == "Fran\u00e7ais" else "Please respond in English."
    prompt = f"""You are a fitness coach reviewing someone's Fitbit data. Write in plain, direct English -- no bullet points with bold headers, no emojis, no promotional language, no rule-of-three lists, no "testament to" or "pivotal" or "landscape" or "delve" or similar AI filler. Write like a person, not a consultant deck.

Here is the user's health data:

{health_summary}

Their goal: {goals}

The entire plan -- the activities chosen, the type of training, the progression -- must be specific to their stated goal. If the goal is a marathon, build running endurance. If the goal is rock climbing, focus on grip strength, pulling strength, and body tension. If the goal is weight loss, focus on caloric burn and sustainable activity. Do not default to a generic running plan regardless of what the user asked for.

Respond using these exact section headers in this order:

## Where they are right now
Write 2-4 paragraphs. Be direct and specific about their current fitness level based on the numbers. What does the data actually show? Explain what their current fitness means in the context of their specific goal.

## 4-week plan

Output ONLY a JSON code block for this section (no prose before or after the block). Use this exact JSON structure:

```json
{{{{
  "weeks": [
    {{{{
      "week": 1,
      "focus": "one-line description of the week's goal",
      "sessions": [
        {{{{
          "day": "Monday",
          "activity": "activity name",
          "duration_min": 30,
          "effort": "easy/moderate/hard",
          "details": "concrete description of what to do"
        }}}}
      ],
      "checkpoint": "what should be measurably different after this week"
    }}}}
  ],
  "after_week_4": "What to do from week 5 onward. Be specific about progression -- how to increase volume or intensity, what metrics to watch, when to move to the next level."
}}}}
```

Include all 4 weeks. Be specific with durations and effort levels.

IMPORTANT -- session count per week: Use the average sessions per week from their exercise history as your reference point, not their peak week. Apply this logic:
- Zero or near-zero logged exercise: start with 2-3 sessions per week. Check their step count -- if they average over 10,000 steps/day they are not sedentary, just unstructured. Treat them accordingly, not as a complete beginner.
- 1-2 sessions per week average: suggest 2-3 sessions per week. A small, sustainable step up.
- 3-4 sessions per week average: keep 3-4 sessions per week. Do not inflate it.
- 5+ sessions per week average: keep a similar volume, but if their HRV is declining or their resting HR is trending up, reduce by one session and add recovery instead.
Do not jump more than 1 session per week above their recent average in Week 1, regardless of their goal. If the goal eventually requires more volume (e.g. marathon training), increase gradually across the 4 weeks, not from day one.

IMPORTANT -- capability calibration: Do not default to a beginner template. Look at the actual session durations in the exercise history and use them as the baseline for Week 1. If they have been training for 40-50 minutes per session, do not prescribe 20-25 minute sessions. A gap of a few weeks does not reset someone to zero -- it means reducing intensity or effort, not duration. If the problem is that they have been training at too high an intensity, say so clearly and prescribe the same durations at a lower effort, not shorter sessions. This applies to any activity type, not just running.

## Heart rate targets
1-2 paragraphs. Use their actual resting heart rate from the data to give real bpm numbers. Adapt this section to their goal: for endurance goals (running, cycling, swimming), explain aerobic zones and the specific range to target. For strength or skill-based goals (climbing, weightlifting, martial arts, yoga), explain how to use heart rate as a recovery and effort gauge rather than a training zone target -- in those cases the HR data is useful for spotting overtraining, not for pacing sessions.

## Sleep and recovery
1-2 paragraphs. What does their sleep data say, and what specific changes would help?

## Worth noting in the data
1 paragraph. Observations that might affect training. Not warnings.

{lang_line}
"""
    try:
        genai.configure(api_key=api_key)
        # Try 2.5-pro first, fall back to 2.0-flash if unavailable
        try:
            model = genai.GenerativeModel("gemini-2.5-pro")
            response = model.generate_content(prompt)
        except Exception:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Gemini error: {e}")
        return None


def clean_ai_response(text: str) -> str:
    """Remove HTML tags and clean AI response for clean markdown rendering."""
    import re
    # Remove HTML br tags
    text = re.sub(r'<br\s*/?>', '\n', text)
    # Remove other HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove excessive blank lines (more than 2 in a row)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove curly quotes
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    return text.strip()


def parse_plan_json(text):
    """Extract and parse the JSON 4-week plan block from the AI response."""
    import re, json
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except (json.JSONDecodeError, ValueError):
        return None


def render_plan_as_df(plan_data):
    """Flatten the weekly plan JSON into a display DataFrame."""
    rows = []
    for week in plan_data.get('weeks', []):
        wk_num = week.get('week', '')
        focus = week.get('focus', '')
        checkpoint = week.get('checkpoint', '')
        for session in week.get('sessions', []):
            rows.append({
                'Week': wk_num,
                'Focus': focus,
                'Day': session.get('day', ''),
                'Activity': session.get('activity', ''),
                'Duration': f"{session.get('duration_min', '')} min",
                'Effort': session.get('effort', ''),
                'Details': session.get('details', ''),
                'Checkpoint': checkpoint,
            })
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def show_ai_coach_tab(health_summary: str, gemini_api_key: str):
    """Render the AI Coach tab UI."""

    st.markdown('<div class="section-header">AI Fitness Coach</div>', unsafe_allow_html=True)

    st.markdown(
        "Describe your fitness goals below. "
        "The AI coach will analyse your Fitbit health data and create a personalised "
        "plan tailored to your current capabilities."
    )

    if not GEMINI_AVAILABLE:
        st.error("The `google-generativeai` package is not installed. "
                 "Run: `pip install google-generativeai`")
        return

    if not gemini_api_key:
        st.warning("Enter your Gemini API key in the sidebar to use the AI Coach.")
        return

    if not health_summary:
        st.info("Upload your Fitbit data (sidebar) to get personalised recommendations.")
        return

    # Health summary preview
    with st.expander("View data summary sent to Gemini", expanded=False):
        if health_summary and len(health_summary.strip()) > 10:
            st.code(health_summary, language=None)
        else:
            st.warning("No health summary available. Upload Fitbit data first.")

    st.divider()

    # -- Goals input -----------------------------------------------------------
    st.subheader("Your Fitness Goals")
    goals_text = st.text_area(
        "Describe your goals",
        placeholder=(
            "e.g. I want to run a 5 km race in 3 months, lose 5 kg, "
            "sleep better, and build more endurance..."
        ),
        height=130,
        key="goals_text_area",
    )

    goals_final = goals_text

    # -- Generate button -------------------------------------------------------
    if st.button("Generate My Personalised Fitness Plan",
                 type="primary", use_container_width=True):
        if not goals_final.strip():
            st.error("Please describe your fitness goals first.")
        else:
            with st.spinner("Analysing your health data and crafting your plan..."):
                plan = generate_ai_fitness_plan(
                    health_summary=health_summary,
                    goals=goals_final,
                    api_key=gemini_api_key,
                )
            if plan:
                plan = clean_ai_response(plan)
                st.session_state['ai_fitness_plan'] = plan

    # -- Display plan ----------------------------------------------------------
    if st.session_state.get('ai_fitness_plan'):
        st.divider()
        st.markdown("### Your Personalised Fitness Plan")

        raw_plan = st.session_state['ai_fitness_plan']
        plan_data = parse_plan_json(raw_plan)

        if plan_data:
            # Split out the JSON block and render the rest as markdown
            import re
            prose = re.sub(r'## 4-week plan.*?```json.*?```', '', raw_plan, flags=re.DOTALL | re.IGNORECASE).strip()
            # Remove any stray section header that preceded the JSON block
            prose = re.sub(r'\n{3,}', '\n\n', prose)
            st.markdown(prose)

            # Display the weekly plan as a table
            st.markdown("### 4-Week Training Plan")
            plan_df = render_plan_as_df(plan_data)
            if not plan_df.empty:
                # Show per-week tables for readability
                for wk_num in sorted(plan_df['Week'].unique()):
                    wk_df = plan_df[plan_df['Week'] == wk_num].copy()
                    focus = wk_df['Focus'].iloc[0]
                    checkpoint = wk_df['Checkpoint'].iloc[0]
                    st.markdown(f"**Week {wk_num}** — {focus}")
                    display_cols = ['Day', 'Activity', 'Duration', 'Effort', 'Details']
                    st.dataframe(
                        wk_df[display_cols].reset_index(drop=True),
                        use_container_width=True,
                        hide_index=True,
                    )
                    if checkpoint:
                        st.markdown(f"*Week {wk_num} checkpoint: {checkpoint}*")

            # After week 4
            after_4 = plan_data.get('after_week_4', '')
            if after_4:
                st.markdown("### After Week 4")
                st.markdown(after_4)
        else:
            # Fallback: render as plain markdown if JSON parsing fails
            st.markdown(raw_plan)

        st.divider()
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                "Download plan (.md)",
                data=st.session_state['ai_fitness_plan'],
                file_name=f"fitness_plan_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col_dl2:
            if st.button("Regenerate plan", use_container_width=True):
                del st.session_state['ai_fitness_plan']
                st.rerun()


# ==============================================================================
# CHART BUILDERS
# ==============================================================================

def create_continuous_hr_chart(hr_df):
    """Create a continuous heart rate chart with ALL data."""
    if hr_df.empty:
        return None

    # Downsample if too many points for performance
    n_points = len(hr_df)
    if n_points > 50000:
        step = n_points // 25000
        plot_df = hr_df.iloc[::step].copy()
    else:
        plot_df = hr_df.copy()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=plot_df['timestamp'],
        y=plot_df['bpm'],
        mode='lines',
        name='Heart Rate',
        line=dict(color='#e74c3c', width=1),
        hovertemplate='<b>%{x|%Y-%m-%d %H:%M}</b><br>HR: %{y:.0f} bpm<extra></extra>'
    ))

    # Hourly moving average
    if n_points > 1000:
        hr_df_sorted = hr_df.sort_values('timestamp')
        hr_df_sorted['hour'] = hr_df_sorted['timestamp'].dt.floor('H')
        hourly_avg = hr_df_sorted.groupby('hour')['bpm'].mean().reset_index()

        fig.add_trace(go.Scatter(
            x=hourly_avg['hour'],
            y=hourly_avg['bpm'],
            mode='lines',
            name='Hourly Average',
            line=dict(color='#c0392b', width=3),
            hovertemplate='<b>%{x|%Y-%m-%d %H:%M}</b><br>Avg: %{y:.1f} bpm<extra></extra>'
        ))

    # Heart rate zones
    fig.add_hrect(y0=40, y1=60, line_width=0, fillcolor="green", opacity=0.05)
    fig.add_hrect(y0=60, y1=100, line_width=0, fillcolor="green", opacity=0.05)
    fig.add_hrect(y0=100, y1=140, line_width=0, fillcolor="yellow", opacity=0.05)
    fig.add_hrect(y0=140, y1=200, line_width=0, fillcolor="red", opacity=0.05)

    fig.add_hline(y=60, line_dash="dot", line_color="green", opacity=0.5)
    fig.add_hline(y=100, line_dash="dot", line_color="orange", opacity=0.5)
    fig.add_hline(y=140, line_dash="dot", line_color="red", opacity=0.5)

    min_bpm = hr_df['bpm'].min()
    max_bpm = hr_df['bpm'].max()
    avg_bpm = hr_df['bpm'].mean()

    fig.update_layout(
        title=dict(
            text=f"Continuous Heart Rate - {n_points:,} readings<br>" +
                 f"<sub>Min: {min_bpm:.0f} bpm | Max: {max_bpm:.0f} bpm | Avg: {avg_bpm:.1f} bpm</sub>",
            font=dict(size=16)
        ),
        xaxis_title="Date & Time",
        yaxis_title="Heart Rate (bpm)",
        yaxis=dict(range=[30, max(180, max_bpm + 10)]),
        hovermode='x unified',
        template='plotly_dark',
        height=500,
        margin=dict(l=60, r=40, t=80, b=60),
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,29,39,1)',
    )

    return fig

def create_continuous_activity_chart(steps_df, calories_df):
    """Create a continuous activity chart with ALL data."""
    if steps_df.empty:
        return None

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=('Steps / Minute', 'Calories / Minute'),
        vertical_spacing=0.1
    )

    # Downsample if needed
    n_steps = len(steps_df)
    if n_steps > 50000:
        step = n_steps // 25000
        steps_plot = steps_df.iloc[::step].copy()
    else:
        steps_plot = steps_df.copy()

    fig.add_trace(
        go.Bar(
            x=steps_plot['timestamp'],
            y=steps_plot['steps'],
            name='Steps',
            marker_color='#1e8449',
            marker_line_color='#145a32',
            marker_line_width=0.5,
            hovertemplate='<b>%{x|%Y-%m-%d %H:%M}</b><br>Steps: %{y}<extra></extra>'
        ),
        row=1, col=1
    )

    if not calories_df.empty:
        n_cals = len(calories_df)
        if n_cals > 50000:
            step = n_cals // 25000
            cals_plot = calories_df.iloc[::step].copy()
        else:
            cals_plot = calories_df.copy()

        fig.add_trace(
            go.Bar(
                x=cals_plot['timestamp'],
                y=cals_plot['calories'],
                name='Calories',
                marker_color='#1e8449',
                marker_line_color='#145a32',
                marker_line_width=0.5,
                hovertemplate='<b>%{x|%Y-%m-%d %H:%M}</b><br>Cal: %{y:.1f}<extra></extra>'
            ),
            row=2, col=1
        )

    total_steps = steps_df['steps'].sum()
    total_cals = calories_df['calories'].sum() if not calories_df.empty else 0

    fig.update_layout(
        title=dict(
            text=f"Daily Activity<br><sub>Total steps: {int(total_steps):,} | Total calories: {int(total_cals):,}</sub>",
            font=dict(size=16)
        ),
        hovermode='x unified',
        template='plotly_dark',
        height=600,
        margin=dict(l=60, r=40, t=100, b=60),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,29,39,1)',
    )

    return fig

def create_sleep_chart(sleep_df):
    """Create a sleep duration chart."""
    if sleep_df.empty:
        return None

    main_sleep = sleep_df[sleep_df['main_sleep'] == True].copy()
    if main_sleep.empty:
        return None

    fig = go.Figure()

    if 'minutes_asleep' in main_sleep.columns:
        fig.add_trace(go.Bar(
            x=main_sleep['date'],
            y=main_sleep['minutes_asleep'] / 60,
            name='Sleep duration',
            marker_color='#2D9966',
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Sleep: %{y:.1f} h<extra></extra>'
        ))

    fig.add_hrect(y0=7, y1=9, line_width=0, fillcolor="green", opacity=0.1,
                  annotation_text="Recommended (7-9 h)", annotation_position="right")

    fig.update_layout(
        title=dict(text="Sleep Duration", font=dict(size=16)),
        xaxis_title="Date",
        yaxis_title="Sleep (hours)",
        hovermode='x unified',
        template='plotly_dark',
        height=400,
        margin=dict(l=60, r=40, t=60, b=60),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,29,39,1)',
    )

    return fig

def create_sleep_stages_chart(sleep_df):
    """Create a sleep stages chart."""
    if sleep_df.empty:
        return None

    main_sleep = sleep_df[sleep_df['main_sleep'] == True].copy()
    if main_sleep.empty:
        return None

    has_stages = 'deep_minutes' in main_sleep.columns and main_sleep['deep_minutes'].notna().any()
    has_classic = 'restless_minutes' in main_sleep.columns and main_sleep['restless_minutes'].notna().any()

    fig = go.Figure()

    if has_stages:
        stages = [
            ('deep_minutes', 'Deep Sleep', '#4c1d95'),
            ('light_minutes', 'Light Sleep', '#7c3aed'),
            ('rem_minutes', 'REM Sleep', '#c084fc'),
            ('wake_minutes', 'Awake', '#fca5a5')
        ]

        for col, name, color in stages:
            if col in main_sleep.columns:
                fig.add_trace(go.Bar(
                    x=main_sleep['date'],
                    y=main_sleep[col],
                    name=name,
                    marker_color=color,
                    hovertemplate=f'<b>%{{x|%Y-%m-%d}}</b><br>{name}: %{{y:.0f}} min<extra></extra>'
                ))

        title = "Sleep Stages"

    elif has_classic:
        stages = [
            ('asleep_minutes', 'Asleep', '#7c3aed'),
            ('restless_minutes', 'Restless', '#fbbf24'),
            ('awake_minutes', 'Awake', '#fca5a5')
        ]

        for col, name, color in stages:
            if col in main_sleep.columns:
                fig.add_trace(go.Bar(
                    x=main_sleep['date'],
                    y=main_sleep[col],
                    name=name,
                    marker_color=color,
                    hovertemplate=f'<b>%{{x|%Y-%m-%d}}</b><br>{name}: %{{y:.0f}} min<extra></extra>'
                ))

        title = "Sleep Stages (classic mode)"
    else:
        return None

    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        xaxis_title="Date",
        yaxis_title="Minutes",
        barmode='stack',
        hovermode='x unified',
        template='plotly_dark',
        height=450,
        margin=dict(l=60, r=40, t=60, b=60),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,29,39,1)',
    )

    return fig

def create_hrv_chart(hrv_df):
    """Create an HRV chart."""
    if hrv_df.empty or 'rmssd' not in hrv_df.columns:
        return None

    fig = make_subplots(
        rows=2 if 'nremhr' in hrv_df.columns and hrv_df['nremhr'].notna().any() else 1,
        cols=1,
        shared_xaxes=True,
        subplot_titles=('HRV (RMSSD)', 'Sleep Heart Rate (NREM)') if 'nremhr' in hrv_df.columns else ('HRV (RMSSD)',),
        vertical_spacing=0.12
    )

    fig.add_trace(
        go.Scatter(
            x=hrv_df['timestamp'],
            y=hrv_df['rmssd'],
            mode='lines+markers',
            name='RMSSD',
            line=dict(color='#9b59b6', width=2),
            marker=dict(size=6),
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>RMSSD: %{y:.1f} ms<extra></extra>'
        ),
        row=1, col=1
    )

    if 'nremhr' in hrv_df.columns:
        valid_nrem = hrv_df[hrv_df['nremhr'] > 0]
        if not valid_nrem.empty:
            fig.add_trace(
                go.Scatter(
                    x=valid_nrem['timestamp'],
                    y=valid_nrem['nremhr'],
                    mode='lines+markers',
                    name='NREM HR',
                    line=dict(color='#e74c3c', width=2),
                    marker=dict(size=6),
                    hovertemplate='<b>%{x|%Y-%m-%d}</b><br>NREM HR: %{y:.1f} bpm<extra></extra>'
                ),
                row=2, col=1
            )

    fig.update_layout(
        title=dict(text="Heart Rate Variability", font=dict(size=16)),
        hovermode='x unified',
        template='plotly_dark',
        height=500,
        margin=dict(l=60, r=40, t=80, b=60),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,29,39,1)',
    )

    return fig

def create_spo2_chart(spo2_df):
    """Create a SpO2 chart."""
    if spo2_df.empty or 'average_value' not in spo2_df.columns:
        return None

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=spo2_df['timestamp'],
        y=spo2_df['average_value'],
        mode='lines+markers',
        name='Avg SpO2',
        line=dict(color='#3498db', width=2),
        marker=dict(size=6),
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>SpO2: %{y:.1f}%<extra></extra>'
    ))

    if 'lower_bound' in spo2_df.columns and 'upper_bound' in spo2_df.columns:
        fig.add_trace(go.Scatter(
            x=spo2_df['timestamp'],
            y=spo2_df['upper_bound'],
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=spo2_df['timestamp'],
            y=spo2_df['lower_bound'],
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(52, 152, 219, 0.2)',
            name='Range',
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Min: %{y:.1f}%<extra></extra>'
        ))

    fig.add_hline(y=95, line_dash="dash", line_color="green", annotation_text="Normal (95%)")
    fig.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="Low (90%)")

    fig.update_layout(
        title=dict(text="Oxygen Saturation (SpO2)", font=dict(size=16)),
        xaxis_title="Date",
        yaxis_title="SpO2 (%)",
        yaxis=dict(range=[85, 100]),
        hovermode='x unified',
        template='plotly_dark',
        height=400,
        margin=dict(l=60, r=40, t=60, b=60),
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,29,39,1)',
    )

    return fig

def create_stress_chart(stress_df):
    """Create a stress score chart."""
    if stress_df.empty or 'STRESS_SCORE' not in stress_df.columns:
        return None

    valid_stress = stress_df[stress_df['STRESS_SCORE'] > 0]
    if valid_stress.empty:
        return None

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=valid_stress['DATE'],
        y=valid_stress['STRESS_SCORE'],
        mode='lines+markers',
        name='Stress Score',
        line=dict(color='#e67e22', width=2),
        marker=dict(size=8),
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Stress: %{y:.0f}/100<extra></extra>'
    ))

    fig.add_hrect(y0=0, y1=25, line_width=0, fillcolor="red", opacity=0.1, annotation_text="High stress")
    fig.add_hrect(y0=25, y1=50, line_width=0, fillcolor="orange", opacity=0.05)
    fig.add_hrect(y0=50, y1=75, line_width=0, fillcolor="yellow", opacity=0.05)
    fig.add_hrect(y0=75, y1=100, line_width=0, fillcolor="green", opacity=0.1, annotation_text="Well recovered")

    fig.update_layout(
        title=dict(text="Stress Score", font=dict(size=16)),
        xaxis_title="Date",
        yaxis_title="Score (0-100)",
        yaxis=dict(range=[0, 100]),
        hovermode='x unified',
        template='plotly_dark',
        height=400,
        margin=dict(l=60, r=40, t=60, b=60),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,29,39,1)',
    )

    return fig

def create_hr_histogram(hr_df):
    """Create a heart rate distribution histogram."""
    if hr_df.empty or 'bpm' not in hr_df.columns:
        return None

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=hr_df['bpm'],
        nbinsx=50,
        marker_color='#1A6B45',
        opacity=0.7,
        hovertemplate='<b>%{x:.0f} bpm</b><br>Occurrences: %{y}<extra></extra>'
    ))

    avg_hr = hr_df['bpm'].mean()
    fig.add_vline(x=avg_hr, line_dash="dash", line_color="red",
                  annotation_text=f"avg {avg_hr:.1f}")

    fig.update_layout(
        title=dict(text="Heart Rate Distribution", font=dict(size=16)),
        xaxis_title="Heart Rate (bpm)",
        yaxis_title="Occurrences",
        template='plotly_dark',
        height=350,
        margin=dict(l=60, r=40, t=60, b=60),
        bargap=0.1,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,29,39,1)',
    )

    return fig

# ==============================================================================
# HEALTH ANALYSIS
# ==============================================================================

def analyze_health(hr_summary, sleep_df, hrv_df, spo2_df, stress_df):
    """Simplified health analysis without medical recommendations."""
    alerts = []
    warnings = []
    info = []

    # HR analysis
    if not hr_summary.empty and 'resting_hr' in hr_summary.columns:
        recent_hr = hr_summary['resting_hr'].dropna()
        if len(recent_hr) > 0:
            latest_hr = recent_hr.iloc[-1]
            avg_hr = recent_hr.mean()

            if latest_hr > 100:
                alerts.append(f"Elevated resting heart rate: {latest_hr:.1f} bpm (Normal: 60-100)")
            elif latest_hr < 50:
                warnings.append(f"Low resting heart rate: {latest_hr:.1f} bpm")
            else:
                info.append(f"Resting heart rate: {latest_hr:.1f} bpm (avg {avg_hr:.1f})")

    # SpO2 analysis
    if not spo2_df.empty and 'average_value' in spo2_df.columns:
        avg_spo2 = spo2_df['average_value'].mean()
        min_spo2 = spo2_df['lower_bound'].min() if 'lower_bound' in spo2_df.columns else spo2_df['average_value'].min()

        if min_spo2 < 90:
            alerts.append(f"Low oxygen saturation detected: {min_spo2:.1f}%")
        elif avg_spo2 < 94:
            warnings.append(f"Below-average SpO2: {avg_spo2:.1f}%")
        else:
            info.append(f"Oxygen saturation normal: {avg_spo2:.1f}%")

    # Sleep analysis
    if not sleep_df.empty and 'minutes_asleep' in sleep_df.columns:
        main_sleep = sleep_df[sleep_df['main_sleep'] == True]
        if not main_sleep.empty:
            avg_sleep = main_sleep['minutes_asleep'].mean() / 60

            if avg_sleep < 5:
                alerts.append(f"Insufficient sleep: {avg_sleep:.1f} h")
            elif avg_sleep < 6:
                warnings.append(f"Short sleep duration: {avg_sleep:.1f} h (recommended: 7-9 h)")
            elif avg_sleep > 10:
                warnings.append(f"Unusually long sleep: {avg_sleep:.1f} h")
            else:
                info.append(f"Sleep duration looks good: {avg_sleep:.1f} h")

    # HRV analysis
    if not hrv_df.empty and 'rmssd' in hrv_df.columns:
        avg_hrv = hrv_df['rmssd'].mean()
        if avg_hrv < 20:
            warnings.append(f"Low HRV: {avg_hrv:.1f} ms")
        else:
            info.append(f"HRV: {avg_hrv:.1f} ms")

    # Stress analysis
    if not stress_df.empty and 'STRESS_SCORE' in stress_df.columns:
        stress_data = stress_df[stress_df['STRESS_SCORE'] > 0]['STRESS_SCORE']
        if len(stress_data) > 0:
            avg_stress = stress_data.mean()
            if avg_stress < 30:
                warnings.append(f"Stress score low ({avg_stress:.0f}/100) -- body may need more recovery time")
            else:
                info.append(f"Stress score: {avg_stress:.0f}/100 (higher = better recovery)")

    return alerts, warnings, info

def display_alert(text, level):
    """Display an alert without medical recommendation."""
    css_class = {
        'alert': 'alert-critical',
        'warning': 'alert-warning',
        'info': 'alert-good'
    }.get(level, 'alert-info')

    st.markdown(f'<div class="{css_class}">{text}</div>', unsafe_allow_html=True)

def display_note(text):
    """Display an explanatory note."""
    st.markdown(f'<div class="comment-box">{text}</div>', unsafe_allow_html=True)

# ==============================================================================
# HTML / PDF REPORT GENERATION
# ==============================================================================

def generate_printable_html(profile, hr_summary, sleep_df, hrv_df, spo2_df, stress_df,
                            detailed_hr_df, detailed_steps_df, chart_images=None):
    """
    Generate a standalone HTML optimised for A4 printing with embedded PNG charts.
    """
    from datetime import datetime

    gen_date = datetime.now().strftime('%Y-%m-%d')
    chart_images = chart_images or {}

    # User info
    name = profile.get('display_name', 'N/A') if profile else 'N/A'
    age_gender = "N/A"
    height_weight_bmi = "N/A"

    if profile and 'date_of_birth' in profile:
        try:
            dob = datetime.strptime(profile['date_of_birth'], '%Y-%m-%d')
            age = int((datetime.now() - dob).days / 365.25)
            gender = profile.get('gender', '')
            age_gender = f"{age} yrs / {gender}"
        except:
            pass

    # Calculate BMI if height and weight available
    if profile:
        height = profile.get('height')
        weight = profile.get('weight')
        if isinstance(height, (int, float)) and isinstance(weight, (int, float)) and height > 0:
            height_m = height / 100
            bmi = weight / (height_m ** 2)
            height_weight_bmi = f"{int(height)} cm / {int(weight)} kg / BMI {bmi:.1f}"

    # Helper to create chart HTML
    def chart_html(chart_name, title):
        if chart_name in chart_images and chart_images[chart_name]:
            return f'''
            <div class="chart-container">
                <div class="chart-title">{title}</div>
                <img src="data:image/png;base64,{chart_images[chart_name]}" alt="{title}" />
            </div>
            '''
        return ''

    # Statistics and charts
    sections = []

    if not detailed_hr_df.empty:
        hr_chart = chart_html('heart_rate', 'Continuous Heart Rate')
        sections.append(f"""
        <div class="section">
            <div class="section-header">Heart Rate</div>
            <div class="metrics">
                <div class="metric"><div class="metric-label">Readings</div><div class="metric-value">{len(detailed_hr_df):,}</div></div>
                <div class="metric"><div class="metric-label">Average</div><div class="metric-value">{detailed_hr_df['bpm'].mean():.1f} bpm</div></div>
                <div class="metric"><div class="metric-label">Min/Max</div><div class="metric-value">{detailed_hr_df['bpm'].min():.0f}/{detailed_hr_df['bpm'].max():.0f}</div></div>
            </div>
            {hr_chart}
        </div>
        """)

    if not sleep_df.empty:
        sleep_chart = chart_html('sleep', 'Sleep Analysis')
        main_sleep = sleep_df[sleep_df['main_sleep'] == True]
        if not main_sleep.empty and 'minutes_asleep' in main_sleep.columns:
            avg_sleep = main_sleep['minutes_asleep'].mean() / 60
            sections.append(f"""
            <div class="section">
                <div class="section-header">Sleep</div>
                <div class="metrics">
                    <div class="metric"><div class="metric-label">Nights</div><div class="metric-value">{len(main_sleep)}</div></div>
                    <div class="metric"><div class="metric-label">Average</div><div class="metric-value">{avg_sleep:.1f}h</div></div>
                </div>
                {sleep_chart}
            </div>
            """)

    if not spo2_df.empty:
        spo2_chart = chart_html('spo2', 'Oxygen Saturation')
        avg_spo2 = spo2_df['average_value'].mean()
        min_spo2 = spo2_df['lower_bound'].min() if 'lower_bound' in spo2_df.columns else spo2_df['average_value'].min()
        sections.append(f"""
        <div class="section">
            <div class="section-header">Oxygen Saturation</div>
            <div class="metrics">
                <div class="metric"><div class="metric-label">Average</div><div class="metric-value">{avg_spo2:.1f}%</div></div>
                <div class="metric"><div class="metric-label">Minimum</div><div class="metric-value">{min_spo2:.1f}%</div></div>
            </div>
            {spo2_chart}
        </div>
        """)

    if not hrv_df.empty and 'rmssd' in hrv_df.columns:
        hrv_chart = chart_html('hrv', 'Heart Rate Variability')
        avg_hrv = hrv_df['rmssd'].mean()
        sections.append(f"""
        <div class="section">
            <div class="section-header">HRV</div>
            <div class="metrics">
                <div class="metric"><div class="metric-label">RMSSD</div><div class="metric-value">{avg_hrv:.1f} ms</div></div>
            </div>
            {hrv_chart}
        </div>
        """)

    if not detailed_steps_df.empty:
        activity_chart = chart_html('activity', 'Daily Activity')
        total_steps = detailed_steps_df['steps'].sum()
        sections.append(f"""
        <div class="section">
            <div class="section-header">Activity</div>
            <div class="metrics">
                <div class="metric"><div class="metric-label">Total Steps</div><div class="metric-value">{int(total_steps):,}</div></div>
            </div>
            {activity_chart}
        </div>
        """)

    # Alerts
    alerts, warnings, info = analyze_health(hr_summary, sleep_df, hrv_df, spo2_df, stress_df)
    alert_html = ""
    for alert in alerts:
        alert_html += f'<div class="alert alert-critical">{alert}</div>'
    for warning in warnings:
        alert_html += f'<div class="alert alert-warning">{warning}</div>'
    for i in info:
        alert_html += f'<div class="alert alert-good">{i}</div>'

    # Full HTML with embedded CSS optimised for printing
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fitbit Health Report - {name}</title>
    <style>
        /* Reset and base */
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.5;
            color: #333;
            background: white;
            padding: 15px;
            max-width: 210mm;
            margin: 0 auto;
        }}

        /* A4 page */
        @page {{
            size: A4 portrait;
            margin: 15mm;
        }}

        @media print {{
            body {{
                padding: 10px !important;
                font-size: 9pt !important;
            }}
            .no-print {{ display: none !important; }}
            .section {{
                margin-bottom: 15px !important;
                page-break-inside: avoid !important;
            }}
            .section-header {{
                font-size: 12pt !important;
                padding: 10px 15px !important;
                margin-bottom: 12px !important;
            }}
            .metrics {{
                gap: 10px !important;
                margin-bottom: 12px !important;
            }}
            .metric {{
                padding: 10px 15px !important;
                min-width: 120px !important;
            }}
            .metric-value {{
                font-size: 14pt !important;
            }}
            .chart-container {{
                margin: 15px 0 !important;
                page-break-inside: avoid !important;
            }}
            .chart-container img {{
                max-height: 280px !important;
                width: 100% !important;
            }}
            .footer {{
                margin-top: 30px !important;
                padding: 20px !important;
            }}
            .alert {{
                padding: 10px 15px !important;
                margin: 8px 0 !important;
            }}
        }}

        /* Header */
        .header {{
            text-align: center;
            border-bottom: 3px solid #1A6B45;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}

        .header h1 {{
            color: #1A6B45;
            font-size: 28pt;
            margin-bottom: 5px;
        }}

        .header .date {{
            color: #666;
            font-size: 11pt;
        }}

        /* Sections */
        .section {{
            margin-bottom: 20px;
            page-break-inside: avoid;
        }}

        .section-header {{
            background: #1A6B45;
            color: white;
            padding: 12px 18px;
            border-radius: 8px;
            font-size: 14pt;
            font-weight: 600;
            margin-bottom: 15px;
        }}

        /* Metrics */
        .metrics {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 15px;
        }}

        .metric {{
            background: #f8f9fa;
            border-left: 4px solid #1A6B45;
            padding: 12px 18px;
            border-radius: 6px;
            min-width: 140px;
            flex: 1;
        }}

        .metric-label {{
            font-size: 9pt;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}

        .metric-value {{
            font-size: 16pt;
            font-weight: 700;
            color: #333;
        }}

        /* Alerts */
        .alert {{
            padding: 12px 16px;
            border-radius: 6px;
            margin: 10px 0;
            font-size: 10pt;
            border-left: 4px solid;
        }}

        .alert-critical {{
            background: #ffebee;
            border-color: #c62828;
            color: #c62828;
        }}

        .alert-warning {{
            background: #fff3e0;
            border-color: #ef6c00;
            color: #ef6c00;
        }}

        .alert-good {{
            background: #e8f5e9;
            border-color: #2e7d32;
            color: #2e7d32;
        }}

        /* Print button */
        .print-btn {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #FF4B4B 0%, #e74c3c 100%);
            color: white;
            padding: 14px 28px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            border: none;
            box-shadow: 0 4px 12px rgba(231, 76, 60, 0.4);
            font-size: 14px;
            z-index: 1000;
        }}

        .print-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(231, 76, 60, 0.5);
        }}

        /* Footer */
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding: 25px;
            color: #666;
            border-top: 1px solid #E5E4E0;
            font-size: 9pt;
        }}

        .footer p {{
            margin: 5px 0;
        }}

        /* Instructions */
        .instructions {{
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin: 20px 0;
            border-radius: 0 6px 6px 0;
            font-size: 10pt;
        }}

        .instructions strong {{
            color: #1565c0;
        }}

        /* Chart containers */
        .chart-container {{
            margin: 20px 0;
            text-align: center;
            page-break-inside: avoid;
        }}

        .chart-title {{
            font-size: 10pt;
            color: #666;
            margin-bottom: 10px;
            text-align: center;
        }}

        .chart-container img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #eee;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <button class="print-btn no-print" onclick="window.print()">
        Print / Save as PDF
    </button>

    <div class="instructions no-print">
        <strong>To save as PDF:</strong><br>
        1. Click the red "Print / Save as PDF" button<br>
        2. In the dialog, choose "Save as PDF"<br>
        3. Select A4 format and default margins<br>
        4. Click Save
    </div>

    <div class="header">
        <h1>Fitbit AI Health Coach</h1>
        <div class="date">Health Report -- {gen_date}</div>
    </div>

    <div class="section">
        <div class="section-header">Profile</div>
        <div class="metrics">
            <div class="metric">
                <div class="metric-label">Name</div>
                <div class="metric-value">{name}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Age / Sex</div>
                <div class="metric-value">{age_gender}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Height / Weight / BMI</div>
                <div class="metric-value">{height_weight_bmi}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-header">Health Analysis</div>
        {alert_html if alert_html else '<p style="color: #666; padding: 10px;">No significant alerts detected.</p>'}
    </div>

    <div class="section">
        <div class="section-header">Detailed Statistics</div>
        {''.join(sections)}
    </div>

    <div class="footer">
        <p><strong>Fitbit AI Health Coach</strong></p>
        <p>Generated on {gen_date}</p>
        <p style="margin-top: 10px; font-size: 8pt;">
            This report is generated from your personal Fitbit data.
        </p>
    </div>

    <script>
        // Auto preparation for printing
        window.addEventListener('beforeprint', function() {{
            document.body.style.padding = '0';
        }});

        // Hide button and instructions after printing
        window.addEventListener('afterprint', function() {{
            document.body.style.padding = '20px';
        }});
    </script>
</body>
</html>"""

    return html

# ==============================================================================
# MAIN APPLICATION
# ==============================================================================

def extract_and_process_upload(uploaded_file):
    """
    Process the uploaded file (ZIP).
    Returns the path to the Fitbit data.
    """
    import tempfile
    import shutil

    temp_dir = tempfile.mkdtemp()

    if uploaded_file.name.endswith('.zip'):
        import zipfile
        zip_path = os.path.join(temp_dir, uploaded_file.name)
        with open(zip_path, 'wb') as f:
            f.write(uploaded_file.getvalue())

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        os.remove(zip_path)
    else:
        return None

    # Find the Fitbit folder
    patterns = [
        os.path.join(temp_dir, "Takeout*", "Fitbit", "Global Export Data"),
        os.path.join(temp_dir, "Takeout*", "Fitbit"),
        os.path.join(temp_dir, "Fitbit", "Global Export Data"),
        os.path.join(temp_dir, "Fitbit"),
        os.path.join(temp_dir, "**", "Fitbit", "Global Export Data"),
        os.path.join(temp_dir, "**", "Fitbit"),
    ]

    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            return matches[0]

    # If no Fitbit folder found, return the temp_dir
    return temp_dir

def main():
    # -- Session state init ----------------------------------------------------
    for key, default in [
        ('report_ready', False),
        ('html_report', ''),
        ('generate_clicked', False),
        ('ai_fitness_plan', ''),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    def on_generate_click():
        st.session_state['generate_clicked'] = True

    # -- Sidebar ---------------------------------------------------------------
    with st.sidebar:
        st.header("Fitbit AI Health Coach")

        # Data upload
        st.subheader("Fitbit Data")
        uploaded_file = st.file_uploader(
            "Upload Fitbit Takeout (.zip)",
            type=['zip'],
            help="Download your Takeout.zip from the Fitbit app and upload it here."
        )
        if uploaded_file is not None:
            st.success(f"Loaded: {uploaded_file.name}")

        st.markdown("---")

        # Gemini API key
        st.subheader("Gemini API Key")
        gemini_api_key = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="AIza...",
            help="Get a free key at aistudio.google.com. Required to use the AI Coach tab.",
        )
        if gemini_api_key:
            st.success("API key set")

        st.markdown("---")
        st.markdown("**Privacy:**")
        st.info("Your Fitbit files are processed locally. When you use the AI Coach, aggregated summaries (averages, not raw data) are sent to Google Gemini.")

        st.markdown("**Instructions:**")
        st.markdown("""
1. Download your Takeout.zip from the Fitbit app
2. Upload the ZIP file above
3. Switch to the AI Coach tab
4. Enter your goals and generate a plan
""")

        st.markdown("---")
        st.markdown("**Export PDF**")
        st.button("Generate & download report (PDF)", type="primary",
                  use_container_width=True, on_click=on_generate_click)

    # -- Page header -----------------------------------------------------------
    st.markdown(f'''
    <div class="print-header">
        <h1>Fitbit AI Health Coach</h1>
        <p style="color:var(--text-muted); font-size:0.85em; margin:4px 0 0 0;">
            {datetime.now().strftime("%Y-%m-%d")}
        </p>
    </div>
    ''', unsafe_allow_html=True)

    # -- Resolve data source ---------------------------------------------------
    if uploaded_file is not None:
        with st.spinner('Extracting ZIP...'):
            base_path = extract_and_process_upload(uploaded_file)
        if base_path is None:
            st.error("Could not extract Fitbit data. Check the file format.")
            return
        st.success("Data loaded successfully!")
    else:
        base_path = find_takeout_folder()
        if base_path is None:
            st.info(
                "No data loaded yet. Upload your Fitbit Takeout.zip from the sidebar. "
                "Data is processed in-memory and never stored."
            )
            return

    # -- Load all data ---------------------------------------------------------
    with st.spinner('Loading your Fitbit data...'):
        profile = parse_profile(base_path)

        detailed_hr_df    = parse_detailed_heart_rate(base_path)
        detailed_steps_df = parse_detailed_steps(base_path)
        detailed_cals_df  = parse_detailed_calories(base_path)

        hr_summary_df  = parse_heart_rate_summary(base_path)
        sleep_df       = parse_sleep_data(base_path)
        sleep_score_df = parse_sleep_score(base_path)
        hrv_df         = parse_hrv(base_path)
        spo2_df        = parse_spo2(base_path)
        stress_df      = parse_stress_score(base_path)
        exercise_df    = parse_exercise_data(base_path)
        azm_df         = parse_azm(base_path)
        temp_df        = parse_temperature(base_path)

    # Pre-build health summary (used in AI Coach tab)
    health_summary = create_health_summary(
        profile, hr_summary_df, sleep_df, sleep_score_df,
        hrv_df, spo2_df, stress_df,
        detailed_steps_df, detailed_cals_df, exercise_df,
        detailed_hr_df=detailed_hr_df,
        azm_df=azm_df,
        temp_df=temp_df,
    )

    # -- Tabs ------------------------------------------------------------------
    tab_dashboard, tab_ai = st.tabs(["Health Dashboard", "AI Coach"])

    with tab_ai:
        show_ai_coach_tab(health_summary, gemini_api_key)

    with tab_dashboard:

        # Report generation if requested - with chart to PNG conversion
        if st.session_state.get('generate_clicked', False):
            # Reset to allow regeneration
            st.session_state['generate_clicked'] = False

            with st.spinner("Generating report..."):
                chart_images = {}

                if not detailed_hr_df.empty:
                    fig_hr = create_continuous_hr_chart(detailed_hr_df)
                    if fig_hr:
                        chart_images['heart_rate'] = fig_to_png_base64(fig_hr)

                if not sleep_df.empty:
                    fig_sleep = create_sleep_chart(sleep_df)
                    if fig_sleep:
                        chart_images['sleep'] = fig_to_png_base64(fig_sleep)

                if not spo2_df.empty:
                    fig_spo2 = create_spo2_chart(spo2_df)
                    if fig_spo2:
                        chart_images['spo2'] = fig_to_png_base64(fig_spo2)

                if not hrv_df.empty:
                    fig_hrv = create_hrv_chart(hrv_df)
                    if fig_hrv:
                        chart_images['hrv'] = fig_to_png_base64(fig_hrv)

                if not detailed_steps_df.empty:
                    fig_activity = create_continuous_activity_chart(detailed_steps_df, detailed_cals_df)
                    if fig_activity:
                        chart_images['activity'] = fig_to_png_base64(fig_activity)

                html_content = generate_printable_html(
                    profile, hr_summary_df, sleep_df, hrv_df, spo2_df, stress_df,
                    detailed_hr_df, detailed_steps_df, chart_images
                )

                pdf_bytes = generate_pdf_from_html(html_content)

                if pdf_bytes:
                    st.success("PDF report generated! Downloading...")

                    import base64
                    b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                    filename = f"Fitbit_Health_Report_{datetime.now().strftime('%Y%m%d')}.pdf"

                    download_link = f'''
                    <script>
                        var link = document.createElement('a');
                        link.href = 'data:application/pdf;base64,{b64_pdf}';
                        link.download = '{filename}';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                    </script>
                    <p style="color: var(--green); font-size: 14px;">
                        Your PDF has been downloaded. If not,
                        <a href="data:application/pdf;base64,{b64_pdf}" download="{filename}">click here</a>.
                    </p>
                    '''
                    st.markdown(download_link, unsafe_allow_html=True)

                    st.download_button(
                        label="Download manually (if auto-download failed)",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.warning("PDF generation unavailable, offering HTML download")
                    st.download_button(
                        label="Download report (HTML)",
                        data=html_content.encode('utf-8'),
                        file_name=f"Fitbit_Health_Report_{datetime.now().strftime('%Y%m%d')}.html",
                        mime="text/html",
                        use_container_width=True
                    )

        # Profile information
        st.markdown('<div class="section-header">Profile</div>', unsafe_allow_html=True)

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            if profile and 'date_of_birth' in profile:
                try:
                    dob = datetime.strptime(profile['date_of_birth'], '%Y-%m-%d')
                    age = int((datetime.now() - dob).days / 365.25)
                    st.metric("Age", f"{age} yrs")
                except:
                    st.metric("Age", "N/A")
            else:
                st.metric("Age", "N/A")

        with col2:
            if profile:
                gender = profile.get('gender', profile.get('sex', 'N/A'))
                st.metric("Sex", str(gender) if gender else "N/A")
            else:
                st.metric("Sex", "N/A")

        with col3:
            if profile:
                height = profile.get('height', 'N/A')
                if isinstance(height, (int, float)):
                    st.metric("Height", f"{int(height)} cm")
                else:
                    st.metric("Height", str(height))
            else:
                st.metric("Height", "N/A")

        with col4:
            if profile:
                weight = profile.get('weight', 'N/A')
                if isinstance(weight, (int, float)):
                    st.metric("Weight", f"{int(weight)} kg")
                else:
                    st.metric("Weight", str(weight))
            else:
                st.metric("Weight", "N/A")

        with col5:
            if profile:
                height_val = profile.get('height', 0)
                weight_val = profile.get('weight', 0)
                if isinstance(height_val, (int, float)) and isinstance(weight_val, (int, float)) and height_val > 0:
                    bmi = weight_val / (height_val / 100) ** 2
                    st.metric("BMI", f"{bmi:.1f}")
                else:
                    st.metric("BMI", "N/A")
            else:
                st.metric("BMI", "N/A")

        # Data availability summary
        data_info = []
        if not detailed_hr_df.empty:
            data_info.append(f"HR: {len(detailed_hr_df):,} readings")
        if not detailed_steps_df.empty:
            data_info.append(f"Steps: {len(detailed_steps_df):,} min")
        if not sleep_df.empty:
            data_info.append(f"Sleep: {len(sleep_df)} nights")
        if not hrv_df.empty:
            data_info.append(f"HRV: {len(hrv_df)} days")
        if not spo2_df.empty:
            data_info.append(f"SpO2: {len(spo2_df)} days")

        if data_info:
            st.markdown("**Available data:** " + " | ".join(data_info))

        st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)

        # Health alerts
        st.markdown('<div class="section-header">Health Analysis</div>', unsafe_allow_html=True)

        alerts, warnings, info = analyze_health(hr_summary_df, sleep_df, hrv_df, spo2_df, stress_df)

        if alerts:
            for alert in alerts:
                display_alert(alert, 'alert')

        if warnings:
            for warning in warnings:
                display_alert(warning, 'warning')

        if info:
            for i in info:
                display_alert(i, 'info')

        if not any([alerts, warnings, info]):
            st.info("Not enough data for analysis.")

        st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)

        # Continuous Heart Rate
        st.markdown('<div class="section-header">Continuous Heart Rate</div>', unsafe_allow_html=True)

        display_note("Continuous heart rate readings from your Fitbit. "
                    "Each dot is a real-time measurement. "
                    "Use the mouse to zoom into specific periods.")

        if not detailed_hr_df.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Readings", f"{len(detailed_hr_df):,}")
            with col2:
                st.metric("Avg Heart Rate", f"{detailed_hr_df['bpm'].mean():.1f} bpm")
            with col3:
                st.metric("Min HR", f"{detailed_hr_df['bpm'].min():.0f} bpm")
            with col4:
                st.metric("Max HR", f"{detailed_hr_df['bpm'].max():.0f} bpm")

            fig = create_continuous_hr_chart(detailed_hr_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

            # Distribution
            hist_fig = create_hr_histogram(detailed_hr_df)
            if hist_fig:
                st.plotly_chart(hist_fig, use_container_width=True)
        else:
            st.info("Detailed heart rate data not available.")

        st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)

        # Daily Activity
        st.markdown('<div class="section-header">Daily Activity</div>', unsafe_allow_html=True)

        display_note("Minute-by-minute activity from your Fitbit. "
                    "Identify activity peaks and rest periods.")

        if not detailed_steps_df.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                total_steps = detailed_steps_df['steps'].sum()
                st.metric("Total Steps", f"{int(total_steps):,}")
            with col2:
                avg_daily = detailed_steps_df.groupby(detailed_steps_df['timestamp'].dt.date)['steps'].sum().mean()
                st.metric("Daily Average", f"{int(avg_daily):,}")
            with col3:
                active_minutes = len(detailed_steps_df[detailed_steps_df['steps'] > 0])
                st.metric("Active Minutes", f"{active_minutes:,}")

            fig = create_continuous_activity_chart(detailed_steps_df, detailed_cals_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Detailed activity data not available.")

        st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)

        # Sleep
        st.markdown('<div class="section-header">Sleep Analysis</div>', unsafe_allow_html=True)

        display_note("Sleep duration and quality. 7-9 hours per night is the recommended range for adults. "
                    "Sleep efficiency (time asleep / time in bed) should ideally exceed 85%.")

        if not sleep_df.empty:
            main_sleep = sleep_df[sleep_df['main_sleep'] == True]

            col1, col2, col3 = st.columns(3)
            with col1:
                if 'minutes_asleep' in main_sleep.columns:
                    avg_hours = main_sleep['minutes_asleep'].mean() / 60
                    st.metric("Avg Duration", f"{avg_hours:.1f} h")
            with col2:
                if 'efficiency' in main_sleep.columns:
                    avg_eff = main_sleep['efficiency'].mean()
                    st.metric("Efficiency", f"{avg_eff:.0f}%")
            with col3:
                if not sleep_score_df.empty and 'overall_score' in sleep_score_df.columns:
                    avg_score = sleep_score_df['overall_score'].mean()
                    st.metric("Sleep Score", f"{avg_score:.0f}/100")

            fig = create_sleep_chart(sleep_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

            stages_fig = create_sleep_stages_chart(sleep_df)
            if stages_fig:
                st.plotly_chart(stages_fig, use_container_width=True)
        else:
            st.info("Sleep data not available.")

        st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)

        # HRV
        st.markdown('<div class="section-header">Heart Rate Variability</div>', unsafe_allow_html=True)

        display_note("HRV (RMSSD) reflects how well your autonomic nervous system recovers. "
                    "Higher values generally indicate better recovery and lower stress.")

        if not hrv_df.empty and 'rmssd' in hrv_df.columns:
            col1, col2 = st.columns(2)
            with col1:
                avg_hrv = hrv_df['rmssd'].mean()
                st.metric("Avg RMSSD", f"{avg_hrv:.1f} ms")
            with col2:
                latest_hrv = hrv_df['rmssd'].iloc[-1]
                st.metric("Latest RMSSD", f"{latest_hrv:.1f} ms")

            fig = create_hrv_chart(hrv_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("HRV data not available.")

        st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)

        # SpO2
        st.markdown('<div class="section-header">Oxygen Saturation</div>', unsafe_allow_html=True)

        display_note("Blood oxygen saturation (SpO2) measures how much oxygen your blood carries. "
                    "A healthy range is 95-100%.")

        if not spo2_df.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_spo2 = spo2_df['average_value'].mean()
                st.metric("Avg SpO2", f"{avg_spo2:.1f}%")
            with col2:
                min_spo2 = spo2_df['lower_bound'].min() if 'lower_bound' in spo2_df.columns else spo2_df['average_value'].min()
                st.metric("Min SpO2", f"{min_spo2:.1f}%")
            with col3:
                max_spo2 = spo2_df['upper_bound'].max() if 'upper_bound' in spo2_df.columns else spo2_df['average_value'].max()
                st.metric("Max SpO2", f"{max_spo2:.1f}%")

            fig = create_spo2_chart(spo2_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("SpO2 data not available.")

        st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)

        # Stress
        st.markdown('<div class="section-header">Stress & Recovery</div>', unsafe_allow_html=True)

        display_note("The stress score combines multiple body metrics. "
                    "A consistently low score may indicate a need for more recovery.")

        if not stress_df.empty:
            stress_data = stress_df[stress_df['STRESS_SCORE'] > 0]
            if not stress_data.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    avg_stress = stress_data['STRESS_SCORE'].mean()
                    st.metric("Avg Stress", f"{avg_stress:.0f}/100")
                with col2:
                    if 'SLEEP_POINTS' in stress_data.columns:
                        avg_sleep_pts = stress_data['SLEEP_POINTS'].mean()
                        st.metric("Sleep Points", f"{avg_sleep_pts:.0f}")
                with col3:
                    if 'EXERTION_POINTS' in stress_data.columns:
                        avg_exert = stress_data['EXERTION_POINTS'].mean()
                        st.metric("Exertion Points", f"{avg_exert:.0f}")

                fig = create_stress_chart(stress_df)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Stress data present but no valid scores found.")
        else:
            st.info("Stress data not available.")

        # Footer
        st.markdown(f'''
        <div style="text-align: center; margin-top: 50px; padding: 25px; color: var(--text-muted);
                    border-top: 1px solid var(--border); background: var(--bg-card); border-radius: 10px;">
            <p style="font-size: 1.1em; margin-bottom: 10px;"><b>Fitbit AI Health Coach</b></p>
            <p style="font-size: 0.9em; color: var(--text-muted);">
                Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}
            </p>
            <p style="font-size: 0.85em; color: var(--text-faint); margin-top: 15px;">
                Your health data, visualised.
            </p>
        </div>
        ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
