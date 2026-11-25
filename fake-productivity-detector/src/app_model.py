"""Data science core of the Fake Productivity Detector web app.

Inputs (same 5 fields as the app / CSV template):
    Task_Hours, Idle_Hours, Social_Media_Usage, Break_Frequency, Tasks_Completed
Output: productivity score 0-100 -> category
    >= 80  Highly Productive
    50-79  Moderately Productive
    < 50   Fake Productivity  (looks busy, little real output)

Run:  python src/app_model.py        # builds dataset, trains, evaluates, saves model + metrics
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import confusion_matrix, f1_score, mean_absolute_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
SEED = 42

RAW = ["task_hours", "idle_hours", "social_hours", "break_frequency", "tasks_completed"]
CSV_COLUMNS = ["Task_Hours", "Idle_Hours", "Social_Media_Usage", "Break_Frequency", "Tasks_Completed"]
CSV_TO_RAW = dict(zip(CSV_COLUMNS, RAW))
FEATS = RAW + ["total_hours", "productive_ratio", "idle_ratio", "social_ratio",
               "tasks_per_task_hour", "breaks_per_hour"]
CATEGORIES = ["Fake Productivity", "Moderately Productive", "Highly Productive"]


def featurize(df: pd.DataFrame) -> pd.DataFrame:
    """Raw 5 inputs -> model features (ratios capture 'time logged vs output')."""
    d = df[RAW].astype(float).copy()
    d["total_hours"] = (d.task_hours + d.idle_hours + d.social_hours).clip(lower=0.25)
    d["productive_ratio"] = d.task_hours / d.total_hours
    d["idle_ratio"] = d.idle_hours / d.total_hours
    d["social_ratio"] = d.social_hours / d.total_hours
    d["tasks_per_task_hour"] = d.tasks_completed / (d.task_hours + 0.5)
    d["breaks_per_hour"] = d.break_frequency / d.total_hours
    return d[FEATS]


def category(score: float) -> str:
    return CATEGORIES[2] if score >= 80 else CATEGORIES[1] if score >= 50 else CATEGORIES[0]


def category_index(scores) -> np.ndarray:
    s = np.asarray(scores)
    return np.where(s >= 80, 2, np.where(s >= 50, 1, 0))


# --------------------------------------------------------------------------- data
def _latent_score(d: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    """Hidden 'true productivity' used only to create labelled training data."""
    f = featurize(d)
    s = (0.30 * np.clip(f.productive_ratio / 0.75, 0, 1)
         + 0.45 * np.clip(f.tasks_per_task_hour / 1.0, 0, 1)
         + 0.15 * (1 - np.clip(f.social_ratio / 0.35, 0, 1))
         + 0.10 * (1 - np.clip(f.idle_ratio / 0.30, 0, 1))) * 100
    s -= np.clip(f.breaks_per_hour - 0.6, 0, None) * 10      # excessive break penalty
    s += rng.normal(0, 4, len(d))                            # measurement / human noise
    return np.clip(s, 0, 100)


ARCH = {  # share, (mean, sd) for task, idle, social, break-poisson-lambda, tasks
    "high":            (0.30, (7.5, 1.2), (0.9, 0.4), (1.2, 0.5), 3, (9.0, 2.0)),
    "moderate":        (0.30, (6.0, 1.3), (1.8, 0.6), (2.2, 0.7), 4, (5.5, 1.6)),
    "low_output":      (0.15, (5.0, 1.3), (2.8, 0.8), (3.8, 1.0), 6, (2.0, 1.2)),
    "fake_busy":       (0.15, (8.5, 1.2), (1.5, 0.6), (2.0, 0.8), 3, (1.0, 0.8)),  # long hours, little done
    "disengaged":      (0.07, (2.5, 1.0), (4.0, 1.0), (4.5, 1.2), 8, (1.0, 0.8)),
}


def generate(n: int = 8000, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    names = list(ARCH)
    shares = np.array([ARCH[a][0] for a in names] + [0.03])      # +3% extreme manual-style inputs
    counts = rng.multinomial(n, shares / shares.sum())
    parts = []
    for name, c in zip(names, counts[:-1]):
        _, t, i, s, b, k = ARCH[name]
        parts.append(pd.DataFrame({
            "task_hours": rng.normal(*t, c), "idle_hours": rng.normal(*i, c),
            "social_hours": rng.normal(*s, c), "break_frequency": rng.poisson(b, c),
            "tasks_completed": rng.normal(*k, c), "profile": name}))
    c = counts[-1]
    parts.append(pd.DataFrame({
        "task_hours": rng.uniform(0, 24, c), "idle_hours": rng.uniform(0, 12, c),
        "social_hours": rng.uniform(0, 16, c), "break_frequency": rng.integers(0, 16, c),
        "tasks_completed": rng.uniform(0, 20, c), "profile": "extreme"}))
    df = pd.concat(parts, ignore_index=True)
    for col, hi in [("task_hours", 24), ("idle_hours", 12), ("social_hours", 16)]:
        df[col] = df[col].clip(0, hi).round(1)
    df["tasks_completed"] = df["tasks_completed"].clip(0, 30).round().astype(int)
    df["break_frequency"] = df["break_frequency"].clip(0, 20).astype(int)
    df["productivity_score"] = _latent_score(df, rng).round(1)
    df["category"] = [category(x) for x in df.productivity_score]
    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


# --------------------------------------------------------------------------- training
def train() -> dict:
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "models").mkdir(exist_ok=True)
    (ROOT / "reports").mkdir(exist_ok=True)

    df = generate()
    out = df.rename(columns={v: k for k, v in CSV_TO_RAW.items()})
    out.drop(columns=["profile"]).to_csv(ROOT / "data" / "productivity_dataset.csv", index=False)

    X, y = featurize(df), df["productivity_score"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=SEED,
                                              stratify=df["category"])
    candidates = {
        "Ridge Regression": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "Random Forest": RandomForestRegressor(n_estimators=250, min_samples_leaf=3, n_jobs=-1, random_state=SEED),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=300, learning_rate=0.05,
                                                       max_depth=3, subsample=0.8, random_state=SEED),
    }
    cv = KFold(5, shuffle=True, random_state=SEED)
    cv_rows = []
    for name, mdl in candidates.items():
        mae = -cross_val_score(mdl, X_tr, y_tr, cv=cv, scoring="neg_mean_absolute_error", n_jobs=-1).mean()
        r2 = cross_val_score(mdl, X_tr, y_tr, cv=cv, scoring="r2", n_jobs=-1).mean()
        cv_rows.append({"model": name, "cv_mae": round(float(mae), 3), "cv_r2": round(float(r2), 4)})
        print(f"{name:20s} CV MAE={mae:.2f}  R2={r2:.3f}")
    best_name = min(cv_rows, key=lambda r: r["cv_mae"])["model"]
    best = candidates[best_name].fit(X_tr, y_tr)

    pred = np.clip(best.predict(X_te), 0, 100)
    true_c, pred_c = category_index(y_te), category_index(pred)
    pi = permutation_importance(best, X_te, y_te, n_repeats=8, random_state=SEED,
                                scoring="neg_mean_absolute_error", n_jobs=-1)
    imp = pd.Series(pi.importances_mean, index=FEATS).sort_values(ascending=False)

    metrics = {
        "best_model": best_name, "n_rows": int(len(df)), "n_train": int(len(X_tr)), "n_test": int(len(X_te)),
        "cv": cv_rows,
        "test": {"mae": round(float(mean_absolute_error(y_te, pred)), 3),
                 "r2": round(float(r2_score(y_te, pred)), 4),
                 "category_accuracy": round(float((true_c == pred_c).mean()), 4),
                 "category_macro_f1": round(float(f1_score(true_c, pred_c, average="macro")), 4)},
        "categories": CATEGORIES,
        "confusion_matrix": confusion_matrix(true_c, pred_c, labels=[0, 1, 2]).tolist(),
        "feature_importance": {k: round(float(v), 3) for k, v in imp.head(8).items()},
        "class_distribution": df["category"].value_counts().reindex(CATEGORIES).astype(int).to_dict(),
        "thresholds": {"fake_below": 50, "highly_from": 80},
    }
    joblib.dump({"model": best, "features": FEATS}, ROOT / "models" / "productivity_model.joblib")
    (ROOT / "reports" / "app_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics["test"], indent=2))
    return metrics


if __name__ == "__main__":
    train()
