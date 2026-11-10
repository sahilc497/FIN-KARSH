import logging
from typing import Dict, Any, Optional
import numpy as np
import torch
import torch.nn as nn
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    ExtraTreesClassifier, ExtraTreesRegressor,
    HistGradientBoostingClassifier, HistGradientBoostingRegressor
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.svm import SVC, SVR

logger = logging.getLogger(__name__)

# PyTorch Deep Learning Architectures
class PyTorchLSTM(nn.Module):
    """2-layer LSTM with Dropout and Dense classification/regression head."""
    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2, output_dim: int = 2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0.0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, output_dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, seq_len, input_dim)
        lstm_out, _ = self.lstm(x)
        # Use final time step
        out = self.fc(lstm_out[:, -1, :])
        return out


class PyTorchGRU(nn.Module):
    """2-layer GRU network for financial sequence modeling."""
    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2, output_dim: int = 2):
        super().__init__()
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0.0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, output_dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        gru_out, _ = self.gru(x)
        out = self.fc(gru_out[:, -1, :])
        return out


class PyTorchSeqWrapper(BaseEstimator, ClassifierMixin):
    """Scikit-learn compatible wrapper for PyTorch LSTM/GRU classifiers."""
    _estimator_type = "classifier"

    def __init__(self, model_type: str = "lstm", input_dim: int = 30, epochs: int = 10, lr: float = 0.003):
        self.model_type = model_type
        self.input_dim = input_dim
        self.epochs = epochs
        self.lr = lr
        self.model = None
        self.classes_ = np.array([0, 1])

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.input_dim = X.shape[1]
        if self.model_type == "lstm":
            self.model = PyTorchLSTM(input_dim=self.input_dim, output_dim=2)
        else:
            self.model = PyTorchGRU(input_dim=self.input_dim, output_dim=2)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr, weight_decay=1e-4)
        criterion = nn.CrossEntropyLoss()

        # Reshape to 3D tensor: (samples, 1, features)
        X_t = torch.tensor(X[:, np.newaxis, :], dtype=torch.float32)
        y_t = torch.tensor(y, dtype=torch.long)

        self.model.train()
        for _ in range(self.epochs):
            optimizer.zero_grad()
            preds = self.model(X_t)
            loss = criterion(preds, y_t)
            loss.backward()
            optimizer.step()
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        self.model.eval()
        with torch.no_grad():
            X_t = torch.tensor(X[:, np.newaxis, :], dtype=torch.float32)
            logits = self.model(X_t)
            probs = torch.softmax(logits, dim=1).numpy()
        return probs

    def predict(self, X: np.ndarray) -> np.ndarray:
        probs = self.predict_proba(X)
        return np.argmax(probs, axis=1)


class ModelFactory:
    """
    Factory creating diverse, production-quality algorithms with
    intelligent fallback mechanics.
    """

    @staticmethod
    def create_classifier(name: str, random_state: int = 42) -> Any:
        name_lower = name.lower()
        if "xgboost" in name_lower or "xgb" in name_lower:
            try:
                import xgboost as xgb
                return xgb.XGBClassifier(
                    n_estimators=100, max_depth=4, learning_rate=0.05,
                    subsample=0.8, colsample_bytree=0.8, random_state=random_state,
                    eval_metric="logloss"
                )
            except ImportError:
                logger.info("XGBoost library not found; utilizing HistGradientBoostingClassifier.")
                return HistGradientBoostingClassifier(
                    max_iter=100, max_depth=4, learning_rate=0.05, random_state=random_state
                )

        elif "lightgbm" in name_lower or "lgb" in name_lower:
            try:
                import lightgbm as lgb
                return lgb.LGBMClassifier(
                    n_estimators=100, max_depth=4, learning_rate=0.05,
                    random_state=random_state, verbose=-1
                )
            except ImportError:
                logger.info("LightGBM library not found; utilizing HistGradientBoostingClassifier.")
                return HistGradientBoostingClassifier(
                    max_iter=100, max_depth=4, learning_rate=0.05, random_state=random_state
                )

        elif "catboost" in name_lower:
            try:
                import catboost as cb
                return cb.CatBoostClassifier(
                    iterations=100, depth=4, learning_rate=0.05,
                    random_seed=random_state, verbose=0
                )
            except ImportError:
                logger.info("CatBoost library not found; utilizing ExtraTreesClassifier.")
                return ExtraTreesClassifier(
                    n_estimators=100, max_depth=6, random_state=random_state
                )

        elif "randomforest" in name_lower or "rf" in name_lower:
            return RandomForestClassifier(
                n_estimators=100, max_depth=5, min_samples_split=4,
                random_state=random_state, n_jobs=1
            )

        elif "extratrees" in name_lower:
            return ExtraTreesClassifier(
                n_estimators=100, max_depth=5, min_samples_split=4,
                random_state=random_state, n_jobs=1
            )

        elif "logistic" in name_lower:
            return LogisticRegression(
                C=0.1, penalty="l2", solver="lbfgs", max_iter=500, random_state=random_state
            )

        elif "svm" in name_lower or "svc" in name_lower:
            return SVC(
                C=1.0, kernel="rbf", probability=True, random_state=random_state
            )

        elif "histgradient" in name_lower:
            return HistGradientBoostingClassifier(
                max_iter=120, max_depth=5, learning_rate=0.05, random_state=random_state
            )

        elif "lstm" in name_lower:
            return PyTorchSeqWrapper(model_type="lstm", epochs=15)

        elif "gru" in name_lower:
            return PyTorchSeqWrapper(model_type="gru", epochs=15)

        else:
            return RandomForestClassifier(n_estimators=100, max_depth=5, random_state=random_state)
