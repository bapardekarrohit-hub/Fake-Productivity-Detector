"""Feature engineering shared by training and prediction."""
import numpy as np
import pandas as pd

RAW_FEATURES = [
    "hours_logged", "idle_minutes", "keystrokes_per_hr", "keystroke_interval_cv",
    "mouse_events_per_hr", "mouse_repetitive_ratio", "app_switches_per_hr",
    "productive_app_pct", "distraction_app_pct", "meeting_hours", "tasks_closed",
    "avg_task_complexity", "deliverables", "review_quality", "rework_rate",
    "after_hours_minutes",
]

ENGINEERED = [
    "idle_ratio", "focus_hours", "output_per_focus_hr", "task_value",
    "input_to_output_ratio", "quality_adjusted_output", "switch_to_output",
]

FEATURES = RAW_FEATURES + ENGINEERED


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add ratio features that capture 'activity without output'."""
    d = df.copy()
    d["idle_ratio"] = d["idle_minutes"] / (d["hours_logged"] * 60)
    # hours that are neither meetings nor idle time
    d["focus_hours"] = (d["hours_logged"] - d["meeting_hours"] - d["idle_minutes"] / 60).clip(lower=0.25)
    d["output_per_focus_hr"] = d["deliverables"] / d["focus_hours"]
    d["task_value"] = d["tasks_closed"] * d["avg_task_complexity"]
    raw_input = d["keystrokes_per_hr"] + d["mouse_events_per_hr"]
    d["input_to_output_ratio"] = np.log1p(raw_input * d["focus_hours"] / (d["task_value"] + 1))
    d["quality_adjusted_output"] = d["deliverables"] * d["review_quality"] * (1 - d["rework_rate"])
    d["switch_to_output"] = d["app_switches_per_hr"] / (d["deliverables"] + 1)
    return d
