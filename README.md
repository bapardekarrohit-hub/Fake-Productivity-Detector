# Fake Productivity Detector

A data science web app that scores how productive a work day really is and flags **fake productivity**: days that look busy but contain little real output.

- **Machine learning:** scikit-learn Gradient Boosting predicts a 0-100 productivity score from 5 inputs
- **Web app:** login, dashboard, CSV upload, manual analysis, reports, history and a Model Insights page
- **What-if suggestions:** the model estimates how much each change (less social media, more finished tasks) would raise the score

**Full documentation, results and code: [fake-productivity-detector/](./fake-productivity-detector)**

## Run it
```bash
cd fake-productivity-detector
pip install -r requirements.txt
python src/app_model.py
python webapp/server.py
```
Open http://127.0.0.1:8000 and sign in with `demo` / `demo12345`.

*Note: the dataset is synthetic, because real employee data is private.*
