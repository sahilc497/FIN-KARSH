import logging
from typing import Optional, Any
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression

logger = logging.getLogger(__name__)

class ProbabilityCalibrator:
    """
    Fits probability calibration (Platt scaling / Sigmoid or Isotonic)
    strictly on validation data to prevent overconfident or skewed probabilities.
    """

    def __init__(self, method: str = "sigmoid"):
        self.method = method  # "sigmoid" (Platt) or "isotonic"
        self.calibrator = None

    def fit_calibrator(self, base_estimator: Any, X_val: np.ndarray, y_val: np.ndarray) -> Any:
        """
        Calibrates estimator probabilities using validation split.
        """
        # If model doesn't support probability or has custom wrapper, return base
        if not hasattr(base_estimator, "predict_proba"):
            return base_estimator

        try:
            calibrated = CalibratedClassifierCV(
                estimator=base_estimator,
                method=self.method,
                cv="prefit"
            )
            calibrated.fit(X_val, y_val)
            self.calibrator = calibrated
            return calibrated
        except Exception:
            # Fallback to uncalibrated base estimator
            return base_estimator

    def predict_calibrated_proba(self, X: np.ndarray) -> np.ndarray:
        if self.calibrator is not None:
            return self.calibrator.predict_proba(X)
        return np.array([[0.5, 0.5]] * len(X))
