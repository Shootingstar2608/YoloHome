# ML: Occupancy detection

Steps:

1. Generate dataset from logs:

```
python ml/prepare_dataset.py
```

2. Train model (will save to `models/occupancy_model.joblib`):

```
python ml/train_model.py
```

Requirements: see `requirements.txt` (pandas, scikit-learn, joblib)
