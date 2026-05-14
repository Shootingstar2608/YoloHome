"""Tiny inference helper to load the trained occupancy model and predict.
"""
import os
import joblib
import numpy as np


class OccupancyPredictor:
    def __init__(self, model_path=None):
        if model_path is None:
            # default path: ../models/occupancy_model.joblib (relative to this file)
            root = os.path.dirname(os.path.dirname(__file__))
            model_path = os.path.join(root, 'models', 'occupancy_model.joblib')
        self.model = None
        try:
            self.model = joblib.load(model_path)
        except Exception as e:
            print('[infer] Không thể load model:', e)

    def predict(self, hour, light, temp, pir_count, face_flag):
        if self.model is None:
            return {'occupied': 0, 'prob': 0.0}
        X = np.array([[hour, float(light), float(temp), float(pir_count), float(face_flag)]])
        pred = int(self.model.predict(X)[0])
        prob = 0.0
        try:
            if hasattr(self.model, 'predict_proba'):
                prob = float(self.model.predict_proba(X)[0, 1])
        except Exception:
            prob = 0.0
        return {'occupied': pred, 'prob': prob}
