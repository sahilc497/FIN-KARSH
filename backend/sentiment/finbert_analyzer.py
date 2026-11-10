import logging
import re
import datetime
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.models import Stock, NewsArticle, RedditPost, SentimentRecord, DailySentiment
from backend.config import settings

logger = logging.getLogger(__name__)

# Specialized Financial Sentiment Lexicon (Loughran-McDonald & Financial PhraseBank cues)
FINANCIAL_POSITIVE_TERMS = {
    "surge": 1.5, "surges": 1.5, "surged": 1.5, "profit": 1.2, "profits": 1.2,
    "growth": 1.3, "record": 1.2, "breakout": 1.4, "outperform": 1.6, "bullish": 1.5,
    "expansion": 1.2, "expanded": 1.2, "rally": 1.4, "rallies": 1.4, "upside": 1.3,
    "dividend": 1.1, "gain": 1.2, "gains": 1.2, "gained": 1.2, "boost": 1.3,
    "boosts": 1.3, "boosted": 1.3, "rebound": 1.3, "highest": 1.2, "jump": 1.3,
    "jumps": 1.3, "jumped": 1.3, "upgrade": 1.5, "upgrades": 1.5, "upgraded": 1.5,
    "beat": 1.4, "beats": 1.4, "beating": 1.4, "strong": 1.2, "robust": 1.3,
    "resilient": 1.2, "deal": 1.1, "order": 1.1, "recovery": 1.2, "turnaround": 1.4,
}

FINANCIAL_NEGATIVE_TERMS = {
    "fall": 1.3, "falls": 1.3, "fell": 1.3, "drop": 1.3, "drops": 1.3, "dropped": 1.3,
    "loss": 1.4, "losses": 1.4, "decline": 1.3, "declines": 1.3, "declined": 1.3,
    "slump": 1.5, "slumps": 1.5, "slumped": 1.5, "bearish": 1.5, "plunge": 1.6,
    "plunges": 1.6, "plunged": 1.6, "downside": 1.3, "downgrade": 1.6, "downgraded": 1.6,
    "miss": 1.4, "misses": 1.4, "missed": 1.4, "weak": 1.3, "slowdown": 1.4,
    "headwinds": 1.3, "headwind": 1.3, "penalty": 1.5, "inflation": 1.1, "debt": 1.1,
    "deficit": 1.3, "contraction": 1.4, "contracted": 1.4, "probe": 1.4, "investigation": 1.4,
    "default": 1.8, "defaults": 1.8, "bankrupt": 2.0, "fraud": 2.0, "risk": 1.1,
}

class FinBERTSentimentAnalyzer:
    """
    FinBERT sentiment analysis engine with Hugging Face transformers pipeline
    and high-performance financial lexicon fallback.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.pipeline = None
        self.model_loaded = False
        self._init_model()

    def _init_model(self):
        """Initializes ProsusAI/finbert pipeline if available and enabled."""
        if settings.FINBERT_OFFLINE or settings.LIGHTWEIGHT_MODE:
            logger.info("FinBERT configured in offline/fast mode. Utilizing Financial Sentiment Lexicon.")
            return

        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
            logger.info(f"Loading {settings.FINBERT_MODEL_NAME} on device: {settings.FINBERT_DEVICE}")
            tokenizer = AutoTokenizer.from_pretrained(settings.FINBERT_MODEL_NAME)
            model = AutoModelForSequenceClassification.from_pretrained(settings.FINBERT_MODEL_NAME)
            self.pipeline = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                device=0 if settings.FINBERT_DEVICE == "cuda" else -1,
                top_k=None,
            )
            self.model_loaded = True
            logger.info("FinBERT Transformer model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load Hugging Face FinBERT: {e}. Falling back to Financial Lexicon.")
            self.model_loaded = False

    def analyze_text(self, text: str) -> Dict[str, float]:
        """
        Classifies financial text into Positive, Negative, Neutral probabilities
        and computes the numerical sentiment score: P(Positive) - P(Negative).
        """
        if not text or len(text.strip()) == 0:
            return {"p_positive": 0.33, "p_negative": 0.33, "p_neutral": 0.34, "sentiment_score": 0.0, "confidence": 0.34}

        # If transformer model is loaded, use it
        if self.model_loaded and self.pipeline is not None:
            try:
                # Truncate text to max length
                truncated = text[:1000]
                results = self.pipeline(truncated)[0]
                prob_map = {item["label"].lower(): float(item["score"]) for item in results}
                p_pos = prob_map.get("positive", 0.0)
                p_neg = prob_map.get("negative", 0.0)
                p_neu = prob_map.get("neutral", 0.0)
                
                score = p_pos - p_neg
                confidence = max(p_pos, p_neg, p_neu)
                return {
                    "p_positive": round(p_pos, 4),
                    "p_negative": round(p_neg, 4),
                    "p_neutral": round(p_neu, 4),
                    "sentiment_score": round(score, 4),
                    "confidence": round(confidence, 4)
                }
            except Exception as e:
                logger.warning(f"Transformer inference error: {e}. Using lexicon fallback.")

        # Financial Lexicon Fallback (Loughran-McDonald scoring)
        words = re.findall(r"\b[A-Za-z]+\b", text.lower())
        pos_weight = 0.0
        neg_weight = 0.0
        
        for w in words:
            if w in FINANCIAL_POSITIVE_TERMS:
                pos_weight += FINANCIAL_POSITIVE_TERMS[w]
            elif w in FINANCIAL_NEGATIVE_TERMS:
                neg_weight += FINANCIAL_NEGATIVE_TERMS[w]

        total_words = max(len(words), 1)
        # Softmax-style scaling over intensities
        scale = 1.0 + (pos_weight + neg_weight) / 2.0
        p_pos = (pos_weight + 0.5) / (pos_weight + neg_weight + 1.5)
        p_neg = (neg_weight + 0.5) / (pos_weight + neg_weight + 1.5)
        p_neu = 1.0 - (p_pos + p_neg)
        
        if p_neu < 0.1:
            p_neu = 0.1
            norm = (p_pos + p_neg + p_neu)
            p_pos /= norm
            p_neg /= norm
            p_neu /= norm

        score = float(np.clip(p_pos - p_neg, -1.0, 1.0))
        confidence = float(max(p_pos, p_neg, p_neu))
        
        return {
            "p_positive": round(float(p_pos), 4),
            "p_negative": round(float(p_neg), 4),
            "p_neutral": round(float(p_neu), 4),
            "sentiment_score": round(score, 4),
            "confidence": round(confidence, 4),
        }

    def process_pending_articles(self) -> int:
        """Analyzes all news articles without existing sentiment records."""
        articles = (
            self.db.query(NewsArticle)
            .outerjoin(SentimentRecord, SentimentRecord.news_article_id == NewsArticle.id)
            .filter(SentimentRecord.id == None)  # noqa: E711
            .all()
        )
        count = 0
        for art in articles:
            if not art.stock_id:
                continue
            text = f"{art.headline}. {art.summary or ''}"
            res = self.analyze_text(text)
            
            rec = SentimentRecord(
                stock_id=art.stock_id,
                source_type="news",
                reference_id=str(art.id),
                news_article_id=art.id,
                timestamp=art.published_at,
                p_positive=res["p_positive"],
                p_negative=res["p_negative"],
                p_neutral=res["p_neutral"],
                sentiment_score=res["sentiment_score"],
                confidence=res["confidence"],
            )
            self.db.add(rec)
            count += 1

        self.db.commit()
        logger.info(f"Analyzed and recorded sentiment for {count} news articles.")
        return count

    def process_reddit_posts(self) -> int:
        """Analyzes all Reddit posts and records sentiment per mentioned stock."""
        posts = self.db.query(RedditPost).all()
        stocks_by_sym = {s.symbol: s.id for s in self.db.query(Stock).all()}
        count = 0
        
        for post in posts:
            if not post.ticker_mentions:
                continue
            text = f"{post.title}. {post.text or ''}"
            res = self.analyze_text(text)
            
            tickers = [t.strip() for t in post.ticker_mentions.split(",") if t.strip()]
            for ticker in tickers:
                stock_id = stocks_by_sym.get(ticker)
                if not stock_id:
                    continue
                
                # Check if already processed
                existing = (
                    self.db.query(SentimentRecord)
                    .filter(
                        SentimentRecord.stock_id == stock_id,
                        SentimentRecord.source_type == "reddit",
                        SentimentRecord.reference_id == post.post_id
                    )
                    .first()
                )
                if not existing:
                    rec = SentimentRecord(
                        stock_id=stock_id,
                        source_type="reddit",
                        reference_id=post.post_id,
                        timestamp=post.created_at,
                        p_positive=res["p_positive"],
                        p_negative=res["p_negative"],
                        p_neutral=res["p_neutral"],
                        sentiment_score=res["sentiment_score"],
                        confidence=res["confidence"],
                    )
                    self.db.add(rec)
                    count += 1

        self.db.commit()
        logger.info(f"Analyzed and recorded sentiment for {count} Reddit mentions.")
        return count

    def aggregate_daily_sentiments(self) -> int:
        """
        Aggregates daily sentiment, computes 5-day sentiment momentum
        and 14-day rolling sentiment volatility per stock.
        """
        stocks = self.db.query(Stock).all()
        total_days_updated = 0
        
        for stock in stocks:
            records = (
                self.db.query(SentimentRecord)
                .filter(SentimentRecord.stock_id == stock.id)
                .order_by(SentimentRecord.timestamp.asc())
                .all()
            )
            if not records:
                continue

            # Group by calendar date
            by_date: Dict[datetime.date, List[SentimentRecord]] = {}
            for r in records:
                d = r.timestamp.date()
                by_date.setdefault(d, []).append(r)

            sorted_dates = sorted(by_date.keys())
            sentiment_series = []

            for d in sorted_dates:
                day_recs = by_date[d]
                news_scores = [r.sentiment_score for r in day_recs if r.source_type == "news"]
                reddit_scores = [r.sentiment_score for r in day_recs if r.source_type == "reddit"]

                news_avg = float(np.mean(news_scores)) if news_scores else 0.0
                reddit_avg = float(np.mean(reddit_scores)) if reddit_scores else 0.0

                # Weighted combined sentiment (News: 70% credibility, Reddit: 30%)
                if news_scores and reddit_scores:
                    combined = 0.7 * news_avg + 0.3 * reddit_avg
                elif news_scores:
                    combined = news_avg
                elif reddit_scores:
                    combined = reddit_avg
                else:
                    combined = 0.0

                sentiment_series.append(combined)

                # Sentiment Momentum (5-day delta)
                if len(sentiment_series) >= 5:
                    momentum = sentiment_series[-1] - sentiment_series[-5]
                else:
                    momentum = 0.0

                # Sentiment Volatility (rolling 14-day standard deviation)
                window = sentiment_series[-14:]
                volatility = float(np.std(window)) if len(window) > 1 else 0.0

                dt_obj = datetime.datetime.combine(d, datetime.time.min)
                existing = (
                    self.db.query(DailySentiment)
                    .filter(DailySentiment.stock_id == stock.id, DailySentiment.date == dt_obj)
                    .first()
                )
                if existing:
                    existing.news_sentiment = round(news_avg, 4)
                    existing.reddit_sentiment = round(reddit_avg, 4)
                    existing.combined_sentiment = round(combined, 4)
                    existing.sentiment_momentum = round(momentum, 4)
                    existing.sentiment_volatility = round(volatility, 4)
                    existing.article_count = len(news_scores)
                    existing.discussion_volume = len(reddit_scores)
                else:
                    daily = DailySentiment(
                        stock_id=stock.id,
                        date=dt_obj,
                        news_sentiment=round(news_avg, 4),
                        reddit_sentiment=round(reddit_avg, 4),
                        combined_sentiment=round(combined, 4),
                        sentiment_momentum=round(momentum, 4),
                        sentiment_volatility=round(volatility, 4),
                        article_count=len(news_scores),
                        discussion_volume=len(reddit_scores),
                    )
                    self.db.add(daily)
                    total_days_updated += 1

        self.db.commit()
        logger.info(f"Aggregated daily sentiment for {total_days_updated} stock-day pairs.")
        return total_days_updated

