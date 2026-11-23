# Fake Productivity Detector

A data science web app that scores how productive a work day really is and flags **fake productivity**:
days that look busy (long logged hours, lots of breaks and tasks "in progress") but contain little real output.

- **Machine learning** (scikit-learn Gradient Boosting) predicts a 0-100 productivity score from 5 inputs.
- **Web app** (Python standard library + vanilla JS, no framework needed) with login, dashboard, CSV upload,
  manual analysis, reports, history, profile and a **Model Insights** page.
- **What-if suggestions**: the model itself is asked "what if you moved 1h from social media to focused work?"
  and the estimated gain is shown as the improvement suggestion.

| Score | Category |
|---|---|
| 80 - 100 | Highly Productive |
| 50 - 79 | Moderately Productive |
| below 50 | Fake Productivity |

## Quick start
```bash
pip install -r requirements.txt
python src/app_model.py          # builds data/productivity_dataset.csv, trains, saves model + reports/app_metrics.json
python webapp/server.py          # open http://127.0.0.1:8000
```
Demo login (created on first run): **demo / demo12345**. You can also create your own account on the login page.

## Inputs (same as the CSV template)
`Task_Hours, Idle_Hours, Social_Media_Usage, Break_Frequency, Tasks_Completed`

From these the model builds ratio features (productive/idle/social share of time, tasks per task-hour,
breaks per hour). The key idea: **"fake productivity" is time logged without matching output**, so tasks per
task-hour matters more than hours alone.

## Data science pipeline (`src/app_model.py`)
1. **Data**: 8,000 synthetic days from five behaviour profiles (high performer, moderate, low output,
   *fake busy* = long hours but almost no finished tasks, disengaged) plus 3% extreme inputs.
2. **Features**: 6 engineered ratio features on top of the 5 raw inputs.
3. **Models compared** with 5-fold CV: Ridge, Random Forest, Gradient Boosting (best CV error wins).
4. **Evaluation on a held-out 20%**: MAE, R-squared, and category accuracy / confusion matrix after applying the thresholds.
5. **Explainability**: permutation importance (shown on the Model Insights page) and per-input what-if suggestions.

Current results (held-out test set): MAE about 3.3 score points, R-squared about 0.97, category accuracy about 91%.
Exact numbers are in `reports/app_metrics.json` and on the Model Insights page.

## Pages
Login, Dashboard (totals, category pie, recent activity bars, trend), Upload CSV (template download, batch results,
export), Manual Analysis (score gauge, breakdown, suggestions, export), Reports (filters, sorting, export),
History (trend, delete all), Model Insights, Profile.

## Honest limitations
- **The training data is synthetic.** Real employee data is private, so the labels come from a documented scoring
  formula plus noise. The model therefore learns that formula; 97% R-squared shows the pipeline works, **not** that
  it would be this accurate on real people.
- Self-reported hours are easy to game, and the app cannot tell *why* someone has low output (meetings, blocked work).
  Use scores to start a conversation, never to judge someone on their own.
- Google login is shown on the login page but not connected (needs Google OAuth credentials).
- The server is a local project server: passwords are hashed and sessions use HttpOnly cookies, but there is no
  HTTPS or rate limiting. Do not put it on the public internet as-is.

## Ideas to extend
- Replace the synthetic data with a real public time-tracking dataset and re-evaluate.
- Add Google OAuth, SHAP explanations, and a Docker file for deployment.

## Advanced module: session-level telemetry model
`src/generate_data.py`, `src/features.py`, `src/train.py`, `src/predict.py` contain a second, more detailed
classifier (16 signals such as keystroke regularity, mouse repetition and app switching; F1 about 0.93 on synthetic
data) for spotting mouse-jiggler style behaviour. Run `python src/generate_data.py && python src/train.py`.
It is separate from the web app.

## Project layout
```
data/                productivity_dataset.csv (web app), work_sessions.csv (advanced module)
src/app_model.py     web app model: data generation, features, training, evaluation
webapp/server.py     backend API + SQLite storage
webapp/static/       index.html, style.css, app.js (frontend)
models/              trained models (.joblib)
reports/             metrics and figures
```
