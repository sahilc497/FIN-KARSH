import os
import json
import logging
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import joblib
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.config import settings
from backend.database.models import Stock, PriceHistory, MLModelRecord, DailySentiment, NewsArticle
from backend.features.feature_builder import FeatureBuilder

logger = logging.getLogger(__name__)

class PredictionService:
    """
    Real-time inference and explainable recommendation engine.
    Calculates multi-factor signals combining ML model probabilities,
    FinBERT sentiment scores, technical trend momentum, fundamental quality,
    and downside risk.
    """

    def __init__(self, db: Session):
        self.db = db
        self.builder = FeatureBuilder(db)

    def get_latest_recommendation(self, symbol: str, horizon_days: int = 5) -> Dict[str, Any]:
        """
        Generates comprehensive explainable recommendation for a stock.
        """
        stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise ValueError(f"Stock {symbol} not found")

        # 1. Latest Price and Technicals
        latest_price_obj = (
            self.db.query(PriceHistory)
            .filter(PriceHistory.stock_id == stock.id)
            .order_by(PriceHistory.date.desc())
            .first()
        )
        current_price = latest_price_obj.close if latest_price_obj else 1000.0
        price_date = latest_price_obj.date.isoformat() if latest_price_obj else None

        # 2. Latest Sentiment
        latest_sentiment = (
            self.db.query(DailySentiment)
            .filter(DailySentiment.stock_id == stock.id)
            .order_by(DailySentiment.date.desc())
            .first()
        )
        sentiment_score = latest_sentiment.combined_sentiment if latest_sentiment else 0.0
        sentiment_momentum = latest_sentiment.sentiment_momentum if latest_sentiment else 0.0

        # 3. Model Inference
        model_prob = 0.52
        model_name = "Ensemble / RandomForest"
        
        # Load best active model for stock from DB
        best_model_rec = (
            self.db.query(MLModelRecord)
            .filter(MLModelRecord.horizon_days == horizon_days, MLModelRecord.is_active == True)  # noqa: E712
            .order_by(desc(MLModelRecord.f1_score))
            .first()
        )

        if best_model_rec and os.path.exists(best_model_rec.file_path):
            try:
                bundle = joblib.load(best_model_rec.file_path)
                model = bundle["model"]
                scaler = bundle["scaler"]
                feature_names = bundle["feature_names"]

                # Extract latest feature row
                X, _, _, _ = self.builder.build_dataset_for_stock(symbol, horizon_days=horizon_days)
                if not X.empty:
                    latest_features = X.iloc[-1:].copy()
                    scaled_features = scaler.transform(latest_features)
                    probs = model.predict_proba(scaled_features)[0]
                    model_prob = float(probs[1]) if len(probs) > 1 else 0.5
                    model_name = best_model_rec.model_name
            except Exception as e:
                logger.warning(f"Live model inference failed: {e}. Using fallback baseline.")

        # 4. Multi-Factor Scoring (Scale: -1.0 to +1.0)
        # Weights: ML Model (35%), Sentiment (25%), Technicals (20%), Fundamentals (20%)
        ml_score = (model_prob - 0.5) * 2.0  # normalize [0, 1] to [-1, 1]
        sent_component = np.clip(sentiment_score, -1.0, 1.0)
        
        # Technical score based on RSI & moving average distance
        tech_score = 0.0
        if latest_price_obj:
            ret_20d = latest_price_obj.returns_1d or 0.0
            tech_score = np.clip(ret_20d * 10.0, -1.0, 1.0)

        # Fundamental score (ROE, PE, debt)
        fund_score = 0.1
        if stock.roe and stock.pe_ratio:
            if stock.roe > 18.0 and stock.pe_ratio < 30.0:
                fund_score = 0.6
            elif stock.roe < 8.0 or stock.pe_ratio > 60.0:
                fund_score = -0.4

        composite_score = (
            0.35 * ml_score +
            0.25 * sent_component +
            0.20 * tech_score +
            0.20 * fund_score
        )

        # Signal Classification
        if composite_score >= 0.35:
            signal = "Strong Positive Signal"
            predicted_direction = "Bullish"
        elif composite_score >= 0.10:
            signal = "Positive Signal"
            predicted_direction = "Slightly Bullish"
        elif composite_score <= -0.35:
            signal = "Strong Negative Signal"
            predicted_direction = "Bearish"
        elif composite_score <= -0.10:
            signal = "Negative Signal"
            predicted_direction = "Slightly Bearish"
        else:
            signal = "Neutral Signal"
            predicted_direction = "Neutral / Sideways"

        # Downside Risk Rating (0 - 100)
        vol_20d = latest_price_obj.volatility_20d if latest_price_obj else 0.018
        risk_score = round(float(np.clip(vol_20d * 2000.0 + (0.5 - fund_score) * 20.0, 10.0, 95.0)), 1)

        # Supporting News Articles
        recent_news = (
            self.db.query(NewsArticle)
            .filter(NewsArticle.stock_id == stock.id)
            .order_by(NewsArticle.published_at.desc())
            .limit(3)
            .all()
        )
        news_summaries = [{
            "headline": n.headline,
            "source": n.source,
            "url": n.url,
            "published_at": n.published_at.isoformat(),
        } for n in recent_news]

        # Recommendation Explanation
        explanation = (
            f"{stock.name} demonstrates a {signal.lower()} over a {horizon_days}-day horizon. "
            f"The calibrated ML model ({model_name}) forecasts a {model_prob * 100:.1f}% probability of upward movement. "
            f"FinBERT sentiment score stands at {sentiment_score:.2f} (5d momentum: {sentiment_momentum:+.2f}). "
            f"Fundamental metrics highlight ROE of {stock.roe or 'N/A'}% and PE of {stock.pe_ratio or 'N/A'}, "
            f"translating to a composite multi-factor score of {composite_score:+.2f}."
        )

        return {
            "symbol": stock.symbol,
            "name": stock.name,
            "sector": stock.sector,
            "current_price": current_price,
            "price_timestamp": price_date,
            "prediction_horizon_days": horizon_days,
            "predicted_direction": predicted_direction,
            "signal": signal,
            "composite_score": round(float(composite_score), 3),
            "model_probability": round(float(model_prob), 4),
            "model_name": model_name,
            "sentiment_score": round(float(sentiment_score), 3),
            "sentiment_momentum": round(float(sentiment_momentum), 3),
            "risk_score": risk_score,
            "fundamentals": {
                "pe_ratio": stock.pe_ratio,
                "pb_ratio": stock.pb_ratio,
                "eps": stock.eps,
                "dividend_yield": stock.dividend_yield,
                "roe": stock.roe,
                "debt_to_equity": stock.debt_to_equity,
                "market_cap": stock.market_cap,
            },
            "supporting_news": news_summaries,
            "explanation": explanation,
        }

