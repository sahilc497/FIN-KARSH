import os
import json
import uuid
import logging
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
import joblib
from sqlalchemy.orm import Session
from sklearn.preprocessing import StandardScaler

from backend.config import settings
from backend.database.models import MLModelRecord, Stock
from backend.features.feature_builder import FeatureBuilder
from backend.ml.models import ModelFactory
from backend.ml.evaluation import ModelEvaluator
from backend.ml.calibration import ProbabilityCalibrator
from backend.ml.ensemble import EnsembleBuilder

logger = logging.getLogger(__name__)

class ModelTrainingPipeline:
    """
    End-to-end Machine Learning training pipeline enforcing strict
    chronological splits (70% train / 15% val / 15% test), label embargoing,
    probability calibration, ensemble construction, and artifact serialization.
    """

    def __init__(self, db: Session):
        self.db = db
        self.builder = FeatureBuilder(db)

    def train_models_for_stock(
        self,
        symbol: str = "RELIANCE.NS",
        horizon_days: int = 5,
        target_type: str = "classification"
    ) -> List[Dict[str, Any]]:
        """
        Trains and validates full model suite for a stock, ranking on out-of-sample test set.
        """
        logger.info(f"Initiating model training for {symbol} (Horizon: {horizon_days}d)...")
        X, y_class, y_reg, feature_names = self.builder.build_dataset_for_stock(symbol, horizon_days=horizon_days)

        # Binary direction task: Filter out neutrals (class 2) to preserve sharp trading edge
        valid_idx = (y_class == 0) | (y_class == 1)
        X = X[valid_idx].reset_index(drop=True)
        y_class = y_class[valid_idx].reset_index(drop=True)
        y_reg = y_reg[valid_idx].reset_index(drop=True)

        n = len(X)
        if n < 80:
            raise ValueError(f"Insufficient training instances for {symbol}: {n} rows")

        # 1. Chronological Splits (70% Train, 15% Val, 15% Test)
        train_end = int(n * 0.70)
        val_end = int(n * 0.85)

        # Embargo period to eliminate label overlap between train and val
        embargo = horizon_days
        val_start = min(train_end + embargo, val_end - 5)
        test_start = min(val_end + embargo, n - 10)

        X_train, y_train = X.iloc[:train_end], y_class.iloc[:train_end]
        X_val, y_val = X.iloc[val_start:val_end], y_class.iloc[val_start:val_end]
        X_test, y_test = X.iloc[test_start:], y_class.iloc[test_start:]

        # 2. Fit Scaler ONLY on Training Data (Zero Leakage)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        X_test_scaled = scaler.transform(X_test)

        # Baseline Calculations
        baselines = ModelEvaluator.calculate_baselines(y_test.values, X_test["return_1d"].values)
        logger.info(f"Baselines on test set: {baselines}")

        # Models to evaluate
        candidate_models = [
            ("RandomForest", ModelFactory.create_classifier("randomforest")),
            ("ExtraTrees", ModelFactory.create_classifier("extratrees")),
            ("HistGradientBoosting", ModelFactory.create_classifier("histgradient")),
            ("LogisticRegression", ModelFactory.create_classifier("logistic")),
            ("SVM_RBF", ModelFactory.create_classifier("svm")),
            ("XGBoost", ModelFactory.create_classifier("xgboost")),
            ("LightGBM", ModelFactory.create_classifier("lightgbm")),
            ("PyTorch_LSTM", ModelFactory.create_classifier("lstm")),
        ]

        fitted_models: List[Tuple[str, Any]] = []
        evaluation_results: List[Dict[str, Any]] = []

        for model_name, model in candidate_models:
            try:
                # Train model on training set
                model.fit(X_train_scaled, y_train.values)
                
                # Calibrate probabilities strictly on validation set
                calibrator = ProbabilityCalibrator(method="sigmoid")
                calibrated_model = calibrator.fit_calibrator(model, X_val_scaled, y_val.values)
                fitted_models.append((model_name, calibrated_model))

                # Out-of-sample Evaluation on Test Set
                y_pred = calibrated_model.predict(X_test_scaled)
                y_prob = calibrated_model.predict_proba(X_test_scaled)

                metrics = ModelEvaluator.evaluate_classification(y_test.values, y_pred, y_prob)
                
                # Financial Strategy Performance on Test Set
                strategy_metrics = ModelEvaluator.evaluate_trading_strategy(
                    prices=X_test["return_1d"].values + 1.0,
                    signals=y_pred,
                    cost_bps=10.0
                )

                # Persist Artifact
                model_id = f"{symbol}_{model_name}_{uuid.uuid4().hex[:8]}"
                artifact_path = settings.MODELS_DIR / f"{model_id}.joblib"
                
                bundle = {
                    "model": calibrated_model,
                    "scaler": scaler,
                    "feature_names": feature_names,
                    "symbol": symbol,
                    "horizon_days": horizon_days,
                    "metrics": metrics,
                    "strategy_metrics": strategy_metrics,
                    "baselines": baselines,
                }
                joblib.dump(bundle, artifact_path)

                # Save metadata JSON
                meta_path = settings.MODELS_DIR / f"{model_id}.json"
                with open(meta_path, "w") as f:
                    json.dump({
                        "model_id": model_id,
                        "model_name": model_name,
                        "symbol": symbol,
                        "horizon_days": horizon_days,
                        "metrics": metrics,
                        "strategy_metrics": strategy_metrics,
                        "baselines": baselines,
                    }, f, indent=2)

                # Record in Database
                record = MLModelRecord(
                    model_id=model_id,
                    model_name=model_name,
                    target_type=target_type,
                    horizon_days=horizon_days,
                    accuracy=metrics["accuracy"],
                    precision=metrics["precision"],
                    recall=metrics["recall"],
                    f1_score=metrics["f1_score"],
                    roc_auc=metrics["roc_auc"],
                    pr_auc=metrics["pr_auc"],
                    mcc=metrics["mcc"],
                    strategy_sharpe=strategy_metrics.get("sharpe_ratio", 0.0),
                    strategy_drawdown=strategy_metrics.get("max_drawdown_pct", 0.0),
                    win_rate=strategy_metrics.get("win_rate_pct", 0.0),
                    file_path=str(artifact_path),
                    metadata_json=json.dumps({"features": feature_names, "baselines": baselines}),
                    is_active=True,
                )
                self.db.add(record)
                evaluation_results.append({
                    "model_id": model_id,
                    "model_name": model_name,
                    "metrics": metrics,
                    "strategy_metrics": strategy_metrics,
                })
            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")

        # 3. Ensemble Evaluation
        try:
            ensemble_estimators = [
                ("RandomForest", ModelFactory.create_classifier("randomforest")),
                ("ExtraTrees", ModelFactory.create_classifier("extratrees")),
                ("HistGradientBoosting", ModelFactory.create_classifier("histgradient")),
            ]
            soft_voting = EnsembleBuilder.create_soft_voting_ensemble(ensemble_estimators)
            soft_voting.fit(X_train_scaled, y_train.values)

            y_pred = soft_voting.predict(X_test_scaled)
            y_prob = soft_voting.predict_proba(X_test_scaled)
            ens_metrics = ModelEvaluator.evaluate_classification(y_test.values, y_pred, y_prob)
            ens_strat = ModelEvaluator.evaluate_trading_strategy(
                prices=X_test["return_1d"].values + 1.0, signals=y_pred
            )

            ens_id = f"{symbol}_SoftVotingEnsemble_{uuid.uuid4().hex[:8]}"
            ens_path = settings.MODELS_DIR / f"{ens_id}.joblib"
            joblib.dump({
                "model": soft_voting,
                "scaler": scaler,
                "feature_names": feature_names,
                "symbol": symbol,
                "horizon_days": horizon_days,
                "metrics": ens_metrics,
                "strategy_metrics": ens_strat,
            }, ens_path)

            record = MLModelRecord(
                model_id=ens_id,
                model_name="SoftVotingEnsemble",
                target_type=target_type,
                horizon_days=horizon_days,
                accuracy=ens_metrics["accuracy"],
                precision=ens_metrics["precision"],
                recall=ens_metrics["recall"],
                f1_score=ens_metrics["f1_score"],
                roc_auc=ens_metrics["roc_auc"],
                pr_auc=ens_metrics["pr_auc"],
                mcc=ens_metrics["mcc"],
                strategy_sharpe=ens_strat.get("sharpe_ratio", 0.0),
                strategy_drawdown=ens_strat.get("max_drawdown_pct", 0.0),
                win_rate=ens_strat.get("win_rate_pct", 0.0),
                file_path=str(ens_path),
                metadata_json=json.dumps({"type": "ensemble"}),
                is_active=True,
            )
            self.db.add(record)
            evaluation_results.append({
                "model_id": ens_id,
                "model_name": "SoftVotingEnsemble",
                "metrics": ens_metrics,
                "strategy_metrics": ens_strat,
            })
        except Exception as e:
            logger.error(f"Ensemble training error: {e}")

        self.db.commit()
        logger.info(f"Successfully trained and logged {len(evaluation_results)} models for {symbol}")
        return evaluation_results
