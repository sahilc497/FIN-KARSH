import json
import uuid
import datetime
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.database.models import ModelRun
from app.ml.model_registry import model_registry
from app.services.feature_engineering import FeatureEngineeringService, FEATURE_COLUMNS

class MLModelService:
    def __init__(self, db: Session):
        self.db = db
        self.feat_service = FeatureEngineeringService(db)

    def train_model(
        self,
        model_type: str = "RandomForestClassifier",
        target_horizon: int = 5,
        feature_subset: Optional[List[str]] = None,
        test_size: float = 0.2,
        purge_overlap: bool = True,
    ) -> Dict[str, Any]:
        """
        Trains and validates a financial ML prediction model using chronological walk-forward
        purged validation. Saves artifact and persists metrics to DB.
        """
        features_to_use = feature_subset or FEATURE_COLUMNS
        logger.info(f"Preparing dataset for {model_type} (horizon={target_horizon}d)...")

        dataset = self.feat_service.prepare_dataset(target_horizon=target_horizon)
        if dataset.empty or len(dataset) < 40:
            raise ValueError(f"Insufficient historical data ({len(dataset)} samples) to train model.")

        # Ensure all requested feature columns exist
        available_features = [f for f in features_to_use if f in dataset.columns]
        if not available_features:
            raise ValueError("None of the specified features are available in dataset.")

        # Chronological split with purging
        train_df, test_df = self.feat_service.split_chronological_purged(
            dataset,
            test_size=test_size,
            horizon=target_horizon,
            purge_overlap=purge_overlap,
        )

        X_train = train_df[available_features].values
        y_train = train_df["target_direction"].values
        X_test = test_df[available_features].values
        y_test = test_df["target_direction"].values

        # Build pipeline with imputer for robust missing value handling
        if model_type == "LogisticRegression":
            clf = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(random_state=42, max_iter=1000, C=1.0)),
            ])
            hyperparams = {"C": 1.0, "max_iter": 1000, "solver": "lbfgs"}
        else:
            model_type = "RandomForestClassifier"
            clf = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", RandomForestClassifier(
                    n_estimators=100,
                    max_depth=6,
                    min_samples_split=5,
                    random_state=42,
                    n_jobs=-1,
                )),
            ])
            hyperparams = {"n_estimators": 100, "max_depth": 6, "min_samples_split": 5}

        logger.info(f"Training {model_type} on {len(X_train)} chronological samples, testing on {len(X_test)} samples...")
        clf.fit(X_train, y_train)

        # Held-out evaluation
        y_pred = clf.predict(X_test)
        y_prob = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else None

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        roc_auc = float(roc_auc_score(y_test, y_prob)) if y_prob is not None and len(np.unique(y_test)) > 1 else None

        # Feature importances
        model_step = clf.named_steps["model"]
        feature_importance_dict: Dict[str, float] = {}
        if hasattr(model_step, "feature_importances_"):
            for feat_name, imp in zip(available_features, model_step.feature_importances_):
                feature_importance_dict[feat_name] = round(float(imp), 4)
        elif hasattr(model_step, "coef_"):
            for feat_name, coef in zip(available_features, model_step.coef_[0]):
                feature_importance_dict[feat_name] = round(float(abs(coef)), 4)

        # Sort feature importance
        feature_importance_dict = dict(sorted(feature_importance_dict.items(), key=lambda x: x[1], reverse=True))

        # Generate unique Model ID and persist
        model_id = f"model_{model_type.lower()}_{uuid.uuid4().hex[:8]}"
        metadata = {
            "model_id": model_id,
            "model_type": model_type,
            "target_horizon": target_horizon,
            "validation_method": "walk_forward_purged",
            "features_used": available_features,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "metrics": {
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1": round(f1, 4),
                "roc_auc": round(roc_auc, 4) if roc_auc else None,
            },
            "feature_importance": feature_importance_dict,
            "hyperparameters": hyperparams,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }

        model_path = model_registry.save_model(model_id, clf, metadata)

        # Persist to database
        db_run = ModelRun(
            model_id=model_id,
            model_type=model_type,
            target_horizon=target_horizon,
            validation_method="walk_forward_purged",
            features_used=json.dumps(available_features),
            train_samples=len(X_train),
            test_samples=len(X_test),
            accuracy=round(acc, 4),
            precision=round(prec, 4),
            recall=round(rec, 4),
            f1=round(f1, 4),
            roc_auc=round(roc_auc, 4) if roc_auc else None,
            feature_importance=json.dumps(feature_importance_dict),
            hyperparameters=json.dumps(hyperparams),
            model_path=str(model_path),
            created_at=datetime.datetime.utcnow(),
        )
        self.db.add(db_run)
        self.db.commit()
        self.db.refresh(db_run)

        logger.info(f"Model {model_id} trained: Accuracy={acc:.3f}, F1={f1:.3f}, AUC={roc_auc if roc_auc else 0:.3f}")
        return {
            "model_id": model_id,
            "model_type": model_type,
            "target_horizon": target_horizon,
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "roc_auc": round(roc_auc, 4) if roc_auc else None,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "feature_importance": feature_importance_dict,
        }

    def predict_latest_for_stock(self, symbol: str, model_id: Optional[str] = None) -> Dict[str, Any]:
        """Generates ML prediction for the latest observation of a stock"""
        # Find latest model if not specified
        if not model_id:
            latest_run = self.db.query(ModelRun).order_by(ModelRun.created_at.desc()).first()
            if not latest_run:
                return {"prediction": "HOLD", "probability": 0.5, "model_id": None}
            model_id = latest_run.model_id

        clf, metadata = model_registry.load_model(model_id)
        features_used = metadata.get("features_used", FEATURE_COLUMNS)

        dataset = self.feat_service.prepare_dataset(symbol=symbol)
        if dataset.empty:
            return {"prediction": "HOLD", "probability": 0.5, "model_id": model_id}

        latest_row = dataset.iloc[[-1]]
        X = latest_row[features_used].values
        prob = float(clf.predict_proba(X)[0, 1])

        direction = "BUY" if prob >= 0.55 else ("SELL" if prob <= 0.45 else "HOLD")
        return {
            "prediction": direction,
            "probability": round(prob, 4),
            "model_id": model_id,
            "date": latest_row["date"].iloc[0].isoformat(),
        }
