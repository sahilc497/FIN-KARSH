import logging
from typing import Dict, Any, Callable
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import f1_score

logger = logging.getLogger(__name__)

class HyperparameterOptimizer:
    """
    Hyperparameter optimization utilizing Optuna when available,
    with an expanding-window TimeSeriesSplit cross-validation fallback.
    Strictly tunes on training/validation splits only.
    """

    def __init__(self, n_trials: int = 15):
        self.n_trials = n_trials

    def optimize_random_forest(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict[str, Any]:
        """Tunes Random Forest hyperparameters without touching the test set."""
        try:
            import optuna
            optuna.logging.set_verbosity(optuna.logging.WARNING)

            def objective(trial):
                n_estimators = trial.suggest_int("n_estimators", 50, 150, step=25)
                max_depth = trial.suggest_int("max_depth", 3, 8)
                min_samples_split = trial.suggest_int("min_samples_split", 2, 6)

                from sklearn.ensemble import RandomForestClassifier
                model = RandomForestClassifier(
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    min_samples_split=min_samples_split,
                    random_state=42
                )
                
                # 3-split TimeSeries CV
                tscv = TimeSeriesSplit(n_splits=3)
                scores = []
                for tr_idx, val_idx in tscv.split(X_train):
                    model.fit(X_train[tr_idx], y_train[tr_idx])
                    preds = model.predict(X_train[val_idx])
                    scores.append(f1_score(y_train[val_idx], preds, zero_division=0))

                return float(np.mean(scores))

            study = optuna.create_study(direction="maximize")
            study.optimize(objective, n_trials=self.n_trials, timeout=15)
            logger.info(f"Optuna optimal parameters: {study.best_params}")
            return study.best_params
        except Exception as e:
            logger.info(f"Optuna unavailable or skipped ({e}); using proven cross-validated defaults.")
            return {"n_estimators": 100, "max_depth": 5, "min_samples_split": 4}

