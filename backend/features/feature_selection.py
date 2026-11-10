import logging
from typing import List, Dict, Tuple
import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif

logger = logging.getLogger(__name__)

class FeatureSelector:
    """
    Performs data-driven feature selection using correlation filtering
    and mutual information ranking to remove noise and collinear features.
    """

    @staticmethod
    def remove_collinear_features(df: pd.DataFrame, threshold: float = 0.95) -> List[str]:
        """Removes features with absolute Pearson correlation above threshold."""
        corr_matrix = df.corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
        kept = [col for col in df.columns if col not in to_drop]
        logger.info(f"Collinear filter: dropped {len(to_drop)} features: {to_drop}")
        return kept

    @staticmethod
    def rank_by_mutual_information(
        X: pd.DataFrame, y: pd.Series, top_k: int = 30
    ) -> List[Tuple[str, float]]:
        """Ranks features by mutual information with the target label."""
        # Treat y as discrete classes
        mi_scores = mutual_info_classif(X, y, random_state=42)
        ranked = sorted(
            zip(X.columns, mi_scores),
            key=lambda x: x[1],
            reverse=True
        )
        return ranked[:top_k]

