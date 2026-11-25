"""Score new work sessions.

Usage:  python src/predict.py data/work_sessions.csv --top 10
The CSV needs the raw feature columns listed in src/features.py.
"""
import argparse
from pathlib import Path

import joblib
import pandas as pd

from features import FEATURES, RAW_FEATURES, add_features

ROOT = Path(__file__).resolve().parents[1]


def explain(row: pd.Series, bundle: dict, k: int = 3) -> str:
    """Top-k signals that differ most from a typical genuine session (z-score)."""
    z = {f: (row[f] - bundle["genuine_median"][f]) / (bundle["genuine_std"][f] or 1) for f in FEATURES}
    top = sorted(z, key=lambda f: abs(z[f]), reverse=True)[:k]
    return "; ".join(f"{f} {'high' if z[f] > 0 else 'low'} ({z[f]:+.1f}σ)" for f in top)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    bundle = joblib.load(ROOT / "models" / "detector.joblib")
    raw = pd.read_csv(args.csv)
    missing = [c for c in RAW_FEATURES if c not in raw.columns]
    if missing:
        raise SystemExit(f"Missing columns: {missing}")
    df = add_features(raw)
    raw["fake_probability"] = bundle["model"].predict_proba(df[FEATURES])[:, 1].round(3)
    raw["flagged"] = raw["fake_probability"] >= bundle["threshold"]
    top = raw.sort_values("fake_probability", ascending=False).head(args.top)
    for idx, r in top.iterrows():
        sid = r.get("session_id", idx)
        print(f"{sid}  p(fake)={r.fake_probability:.2f}  flagged={r.flagged}  <- {explain(df.loc[idx], bundle)}")
    print(f"\n{int(raw.flagged.sum())} of {len(raw)} sessions flagged for human review.")


if __name__ == "__main__":
    main()
