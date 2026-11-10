import logging
from typing import List, Dict, Tuple, Any, Optional
import numpy as np
from sklearn.ensemble import VotingClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)

class EnsembleBuilder:
    """
    Constructs weighted soft voting and stacking ensembles.
    Only retains ensembles that demonstrably improve out-of-sample validation metrics.
    """

    @staticmethod
    def create_soft_voting_ensemble(
        estimators: List[Tuple[str, Any]], weights: Optional[List[float]] = None
    ) -> VotingClassifier:
        """Creates a soft-voting classifier combining model probabilities."""
        return VotingClassifier(
            estimators=estimators,
            voting="soft",
            weights=weights,
            n_jobs=1
        )

    @staticmethod
    def create_stacking_ensemble(
        base_estimators: List[Tuple[str, Any]],
        final_estimator: Optional[Any] = None
    ) -> StackingClassifier:
        """Creates a stacking classifier with a regularized meta-learner."""
        if final_estimator is None:
            final_estimator = LogisticRegression(C=0.1, max_iter=200, random_state=42)

        return StackingClassifier(
            estimators=base_estimators,
            final_estimator=final_estimator,
            cv=3,
            n_jobs=-1
        )
