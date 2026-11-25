"""Generate a synthetic employee work-session dataset for the Fake Productivity Detector.

Why synthetic?  Real employee activity telemetry is private and not publicly
available, so this script simulates it.  Each row is one employee-day.  Rows are
drawn from six behavioural archetypes (3 genuine, 3 "fake productive") with
deliberate overlap and label noise so the modelling problem is not trivially
separable.  The archetype name is saved for error analysis ONLY and is never
used as a model feature.

Run:  python src/generate_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_ROWS = 6000
LABEL_NOISE = 0.03  # fraction of labels flipped (annotation / ground-truth error)

# name: (share of dataset, label, parameter dict of (mean, sd))
ARCHETYPES = {
    # ---- genuine ----
    "genuine_focused": (0.43, 0, dict(
        hours_logged=(7.5, 0.8), idle_minutes=(50, 20), keystrokes_per_hr=(3500, 800),
        keystroke_interval_cv=(1.1, 0.2), mouse_events_per_hr=(1500, 400),
        mouse_repetitive_ratio=(0.08, 0.04), app_switches_per_hr=(14, 5),
        productive_app_pct=(0.70, 0.10), distraction_app_pct=(0.08, 0.04),
        meeting_hours=(1.0, 0.6), tasks_closed=(6, 2), avg_task_complexity=(3.2, 0.7),
        deliverables=(5, 2), review_quality=(7.5, 1.0), rework_rate=(0.08, 0.05),
        after_hours_minutes=(15, 15))),
    # hard negative: looks "low output" but is legitimately busy in meetings
    "genuine_meeting_heavy": (0.20, 0, dict(
        hours_logged=(8.0, 0.8), idle_minutes=(70, 25), keystrokes_per_hr=(1500, 500),
        keystroke_interval_cv=(1.0, 0.2), mouse_events_per_hr=(1800, 450),
        mouse_repetitive_ratio=(0.10, 0.05), app_switches_per_hr=(20, 6),
        productive_app_pct=(0.45, 0.10), distraction_app_pct=(0.10, 0.05),
        meeting_hours=(4.0, 1.0), tasks_closed=(2.5, 1.2), avg_task_complexity=(3.0, 0.7),
        deliverables=(2, 1), review_quality=(7.0, 1.1), rework_rate=(0.10, 0.05),
        after_hours_minutes=(20, 20))),
    # hard negative: honest but slow / junior
    "genuine_slow": (0.12, 0, dict(
        hours_logged=(7.5, 0.9), idle_minutes=(90, 30), keystrokes_per_hr=(2200, 700),
        keystroke_interval_cv=(1.0, 0.25), mouse_events_per_hr=(1400, 400),
        mouse_repetitive_ratio=(0.10, 0.05), app_switches_per_hr=(16, 6),
        productive_app_pct=(0.55, 0.12), distraction_app_pct=(0.15, 0.07),
        meeting_hours=(1.2, 0.7), tasks_closed=(3, 1.2), avg_task_complexity=(2.5, 0.7),
        deliverables=(2.5, 1.2), review_quality=(6.0, 1.2), rework_rate=(0.15, 0.06),
        after_hours_minutes=(10, 12))),
    # ---- fake productive ----
    # mouse jiggler / key-repeater: lots of raw input, almost no real work
    "fake_jiggler": (0.08, 1, dict(
        hours_logged=(8.5, 0.8), idle_minutes=(30, 20), keystrokes_per_hr=(600, 400),
        keystroke_interval_cv=(0.35, 0.2), mouse_events_per_hr=(4500, 1000),
        mouse_repetitive_ratio=(0.60, 0.15), app_switches_per_hr=(5, 3),
        productive_app_pct=(0.20, 0.10), distraction_app_pct=(0.25, 0.10),
        meeting_hours=(0.8, 0.6), tasks_closed=(1, 1), avg_task_complexity=(2.0, 0.6),
        deliverables=(0.8, 0.8), review_quality=(4.5, 1.5), rework_rate=(0.25, 0.10),
        after_hours_minutes=(5, 8))),
    # busywork: many tiny tasks, constant app switching, long hours, shallow output
    "fake_busywork": (0.10, 1, dict(
        hours_logged=(9.0, 1.0), idle_minutes=(35, 20), keystrokes_per_hr=(4200, 900),
        keystroke_interval_cv=(0.9, 0.2), mouse_events_per_hr=(2500, 600),
        mouse_repetitive_ratio=(0.20, 0.08), app_switches_per_hr=(38, 8),
        productive_app_pct=(0.60, 0.12), distraction_app_pct=(0.15, 0.07),
        meeting_hours=(1.5, 0.8), tasks_closed=(9, 3), avg_task_complexity=(1.3, 0.3),
        deliverables=(1.5, 1.0), review_quality=(4.0, 1.2), rework_rate=(0.35, 0.10),
        after_hours_minutes=(70, 40))),
    # "online but absent": status shows active, long idle gaps, little output
    "fake_online_idle": (0.07, 1, dict(
        hours_logged=(9.0, 1.0), idle_minutes=(210, 50), keystrokes_per_hr=(900, 400),
        keystroke_interval_cv=(0.8, 0.25), mouse_events_per_hr=(700, 300),
        mouse_repetitive_ratio=(0.15, 0.08), app_switches_per_hr=(6, 3),
        productive_app_pct=(0.30, 0.12), distraction_app_pct=(0.40, 0.12),
        meeting_hours=(0.5, 0.5), tasks_closed=(1.2, 1.0), avg_task_complexity=(2.0, 0.6),
        deliverables=(1.0, 0.9), review_quality=(5.0, 1.4), rework_rate=(0.20, 0.10),
        after_hours_minutes=(30, 25))),
}

BOUNDS = {
    "hours_logged": (2, 12), "idle_minutes": (0, 400), "keystrokes_per_hr": (0, 9000),
    "keystroke_interval_cv": (0.05, 2.5), "mouse_events_per_hr": (0, 9000),
    "mouse_repetitive_ratio": (0, 1), "app_switches_per_hr": (0, 80),
    "productive_app_pct": (0, 1), "distraction_app_pct": (0, 1), "meeting_hours": (0, 8),
    "tasks_closed": (0, 25), "avg_task_complexity": (1, 5), "deliverables": (0, 15),
    "review_quality": (1, 10), "rework_rate": (0, 1), "after_hours_minutes": (0, 300),
}
INT_COLS = ["tasks_closed", "deliverables", "idle_minutes", "after_hours_minutes"]


def generate(n_rows: int = N_ROWS, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    names = list(ARCHETYPES)
    shares = np.array([ARCHETYPES[a][0] for a in names])
    counts = rng.multinomial(n_rows, shares / shares.sum())

    frames = []
    for name, n in zip(names, counts):
        _, label, params = ARCHETYPES[name]
        data = {col: rng.normal(mu, sd, n) for col, (mu, sd) in params.items()}
        df = pd.DataFrame(data)
        df["archetype"] = name
        df["is_fake"] = label
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)

    # Cross-archetype overlap: some rows get "bleed" from the opposite behaviour,
    # e.g. a genuine person with a bad day, a faker who does ship something.
    bleed = rng.random(len(df)) < 0.08
    df.loc[bleed, "deliverables"] += rng.normal(0, 2, bleed.sum())
    df.loc[bleed, "review_quality"] += rng.normal(0, 1.5, bleed.sum())
    df.loc[bleed, "keystrokes_per_hr"] += rng.normal(0, 800, bleed.sum())

    for col, (lo, hi) in BOUNDS.items():
        df[col] = df[col].clip(lo, hi)
    for col in INT_COLS:
        df[col] = df[col].round().astype(int)
    for col in ["keystrokes_per_hr", "mouse_events_per_hr"]:
        df[col] = df[col].round().astype(int)
    df = df.round({c: 3 for c in df.columns if df[c].dtype == float})

    # Label noise (ground truth is never perfect)
    flip = rng.random(len(df)) < LABEL_NOISE
    df.loc[flip, "is_fake"] = 1 - df.loc[flip, "is_fake"]

    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    df.insert(0, "session_id", [f"S{i:05d}" for i in range(len(df))])
    return df


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "data"
    out.mkdir(exist_ok=True)
    data = generate()
    data.to_csv(out / "work_sessions.csv", index=False)
    print(f"Wrote {len(data)} rows to {out / 'work_sessions.csv'}")
    print(f"Fake share: {data.is_fake.mean():.1%}")
    print(data.groupby("archetype").is_fake.agg(["count", "mean"]))
