"""Huấn luyện model occupancy từ `occupancy_dataset.csv` và lưu model.

Usage:
    python train_model.py

Output:
    ../models/occupancy_model.joblib
"""
import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

ROOT = os.path.dirname(__file__)
# Prepare_dataset writes to web_app/occupancy_dataset.csv (parent folder)
DATA_CSV = os.path.join(os.path.dirname(ROOT), 'occupancy_dataset.csv')
OUT_DIR = os.path.join(os.path.dirname(ROOT), 'models')
OUT_MODEL = os.path.join(OUT_DIR, 'occupancy_model.joblib')


def main():
    if not os.path.exists(DATA_CSV):
        print('Không tìm thấy dataset:', DATA_CSV)
        return
    df = pd.read_csv(DATA_CSV)
    if df.empty:
        print('Dataset rỗng')
        return

    # Features and label
    X = df[['hour', 'light', 'temp', 'pir_count', 'face_flag']].fillna(0)
    y = df['occupied']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    print('Accuracy:', accuracy_score(y_test, preds))
    print(classification_report(y_test, preds))

    os.makedirs(OUT_DIR, exist_ok=True)
    joblib.dump(clf, OUT_MODEL)
    print('Saved model to', OUT_MODEL)


if __name__ == '__main__':
    main()
