"""Train, evaluate and explain the Fake Productivity Detector.

Run:  python src/train.py
Outputs: models/detector.joblib, reports/metrics.json, reports/figures/*.png
"""
import json
import warnings
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay, PrecisionRecallDisplay, RocCurveDisplay,
    average_precision_score, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_validate, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from features import FEATURES, add_features

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"
SEED = 42
GENUINE_C, FAKE_C, INK, MUTED = "#2a6fbb", "#d9731a", "#222222", "#6b7280"

plt.rcParams.update({
    "figure.dpi": 140, "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#9ca3af", "axes.labelcolor": INK, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.titleweight": "bold", "axes.titlesize": 11,
    "axes.grid": True, "grid.color": "#e5e7eb", "grid.linewidth": 0.6,
    "axes.axisbelow": True, "font.size": 9,
})


def eda_figures(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    for lab, col, name in [(0, GENUINE_C, "Genuine"), (1, FAKE_C, "Fake productive")]:
        s = df[df.is_fake == lab]
        ax[0].scatter(s.keystrokes_per_hr + s.mouse_events_per_hr, s.quality_adjusted_output,
                      s=7, alpha=0.35, color=col, label=name, edgecolor="none")
    ax[0].set_xlabel("Raw input events per hour (keys + mouse)")
    ax[0].set_ylabel("Quality-adjusted output")
    ax[0].set_title("Fake workers: high activity, low real output")
    ax[0].legend(frameon=False, markerscale=2)
    for lab, col in [(0, GENUINE_C), (1, FAKE_C)]:
        ax[1].hist(df[df.is_fake == lab].keystroke_interval_cv, bins=40, alpha=0.6, color=col)
    ax[1].set_xlabel("Keystroke interval variability (CV)")
    ax[1].set_ylabel("Sessions")
    ax[1].set_title("Scripted input is unnaturally regular")
    fig.tight_layout()
    fig.savefig(FIG / "01_eda.png")
    plt.close(fig)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    (ROOT / "models").mkdir(exist_ok=True)
    raw = pd.read_csv(ROOT / "data" / "work_sessions.csv")
    df = add_features(raw)
    eda_figures(df)

    X, y = df[FEATURES], df["is_fake"]
    X_tr, X_te, y_tr, y_te, arch_tr, arch_te = train_test_split(
        X, y, df["archetype"], test_size=0.2, stratify=y, random_state=SEED)

    models = {
        "Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0)),
        "Random Forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=3,
                                                class_weight="balanced", n_jobs=-1, random_state=SEED),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=250, learning_rate=0.05,
                                                        max_depth=3, subsample=0.8, random_state=SEED),
    }
    cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
    cv_rows = {}
    for name, mdl in models.items():
        res = cross_validate(mdl, X_tr, y_tr, cv=cv, n_jobs=-1,
                             scoring=["roc_auc", "average_precision", "f1"])
        cv_rows[name] = {k: float(res[f"test_{k}"].mean()) for k in ["roc_auc", "average_precision", "f1"]}
        print(f"{name:20s} CV ROC-AUC={cv_rows[name]['roc_auc']:.3f} "
              f"PR-AUC={cv_rows[name]['average_precision']:.3f} F1={cv_rows[name]['f1']:.3f}")

    best_name = max(cv_rows, key=lambda k: cv_rows[k]["average_precision"])
    best = models[best_name]
    print(f"\nBest by CV PR-AUC: {best_name}")

    # Choose decision threshold on out-of-fold predictions (never on the test set).
    oof = cross_val_predict(best, X_tr, y_tr, cv=cv, method="predict_proba", n_jobs=-1)[:, 1]
    grid = np.linspace(0.1, 0.9, 81)
    f1s = [f1_score(y_tr, oof >= t) for t in grid]
    thr = float(grid[int(np.argmax(f1s))])

    best.fit(X_tr, y_tr)
    proba = best.predict_proba(X_te)[:, 1]
    pred = (proba >= thr).astype(int)
    metrics = {
        "best_model": best_name, "threshold": thr, "cv": cv_rows,
        "test": {
            "roc_auc": float(roc_auc_score(y_te, proba)),
            "pr_auc": float(average_precision_score(y_te, proba)),
            "precision": float(precision_score(y_te, pred)),
            "recall": float(recall_score(y_te, pred)),
            "f1": float(f1_score(y_te, pred)),
            "fake_prevalence": float(y_te.mean()),
        },
    }
    print("Test:", json.dumps(metrics["test"], indent=2))

    # Error analysis by archetype (does the model punish honest meeting-heavy people?)
    err = pd.DataFrame({"archetype": arch_te.values, "y": y_te.values, "pred": pred})
    by_arch = err.groupby("archetype").agg(n=("y", "size"), flagged_rate=("pred", "mean"))
    print("\nFlag rate by archetype:\n", by_arch.round(3))
    metrics["flag_rate_by_archetype"] = by_arch["flagged_rate"].round(4).to_dict()

    # Baseline: a naive rule a manager might use ("lots of activity = productive")
    naive = ((X_te.keystrokes_per_hr + X_te.mouse_events_per_hr) < 3000).astype(int)
    metrics["naive_low_activity_rule_f1"] = float(f1_score(y_te, naive))

    # --- Figures ---
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    for name, mdl in models.items():
        mdl.fit(X_tr, y_tr)
        lw = 2.2 if name == best_name else 1.2
        RocCurveDisplay.from_estimator(mdl, X_te, y_te, ax=ax[0], name=name)
        ax[0].lines[-1].set_linewidth(lw)
        PrecisionRecallDisplay.from_estimator(mdl, X_te, y_te, ax=ax[1], name=name)
        ax[1].lines[-1].set_linewidth(lw)
    ax[0].plot([0, 1], [0, 1], ls=":", color=MUTED)
    ax[0].set_title("ROC curves (test set)")
    ax[1].set_title("Precision-recall curves (test set)")
    for a in ax:
        a.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "02_model_curves.png")
    plt.close(fig)
    best.fit(X_tr, y_tr)  # refit best (loop above refit it too, keep explicit)

    fig, ax = plt.subplots(figsize=(4.2, 4))
    ConfusionMatrixDisplay(confusion_matrix(y_te, pred),
                           display_labels=["Genuine", "Fake"]).plot(ax=ax, cmap="Blues", colorbar=False)
    ax.grid(False)
    ax.set_title(f"Confusion matrix (threshold {thr:.2f})")
    fig.tight_layout()
    fig.savefig(FIG / "03_confusion_matrix.png")
    plt.close(fig)

    pi = permutation_importance(best, X_te, y_te, n_repeats=10, random_state=SEED,
                                scoring="average_precision", n_jobs=-1)
    imp = pd.Series(pi.importances_mean, index=FEATURES).sort_values().tail(12)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.barh(imp.index, imp.values, color=GENUINE_C, height=0.6)
    ax.set_xlabel("Drop in PR-AUC when feature is shuffled")
    ax.set_title("What the detector relies on (permutation importance)")
    fig.tight_layout()
    fig.savefig(FIG / "04_feature_importance.png")
    plt.close(fig)
    metrics["top_features"] = imp.sort_values(ascending=False).round(4).to_dict()

    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    order = by_arch.sort_values("flagged_rate")
    colors = [FAKE_C if a.startswith("fake") else GENUINE_C for a in order.index]
    ax.barh(order.index, order.flagged_rate, color=colors, height=0.6)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of sessions flagged as fake")
    ax.set_title("Flag rate by behaviour type (orange = truly fake)")
    fig.tight_layout()
    fig.savefig(FIG / "05_flag_rate_by_archetype.png")
    plt.close(fig)

    joblib.dump({"model": best, "threshold": thr, "features": FEATURES,
                 "genuine_median": df[df.is_fake == 0][FEATURES].median().to_dict(),
                 "genuine_std": df[df.is_fake == 0][FEATURES].std().to_dict()},
                ROOT / "models" / "detector.joblib")
    (ROOT / "reports" / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print("\nSaved model, metrics and figures.")


if __name__ == "__main__":
    main()
