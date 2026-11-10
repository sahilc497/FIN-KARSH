from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel

from backend.database.connection import get_db
from backend.database.models import Stock, DailySentiment, NewsArticle, RedditPost, SentimentRecord
from backend.sentiment.finbert_analyzer import FinBERTSentimentAnalyzer
from backend.collectors.reddit_collector import RedditCollector

router = APIRouter(prefix="/sentiment", tags=["Sentiment"])


class AnalyzeTextRequest(BaseModel):
    text: str


@router.post("/analyze-text")
def analyze_arbitrary_text(req: AnalyzeTextRequest, db: Session = Depends(get_db)):
    analyzer = FinBERTSentimentAnalyzer(db)
    result = analyzer.analyze_text(req.text)
    return result


@router.get("/overview")
def get_sentiment_overview(db: Session = Depends(get_db)):
    """
    Provides market-wide FinBERT sentiment overview, separating News and Reddit retail sentiment,
    highlighting top positive/negative stocks and retail vs media divergence.
    """
    stocks = db.query(Stock).filter(Stock.symbol != "^NSEI").all()
    stock_sentiments = []

    for stock in stocks:
        latest = (
            db.query(DailySentiment)
            .filter(DailySentiment.stock_id == stock.id)
            .order_by(DailySentiment.date.desc())
            .first()
        )
        news_score = latest.news_sentiment if latest and latest.news_sentiment is not None else 0.0
        reddit_score = latest.reddit_sentiment if latest and latest.reddit_sentiment is not None else 0.0
        combined_score = latest.combined_sentiment if latest and latest.combined_sentiment is not None else 0.0
        momentum = latest.sentiment_momentum if latest and latest.sentiment_momentum is not None else 0.0

        divergence = round(reddit_score - news_score, 3)

        stock_sentiments.append({
            "symbol": stock.symbol,
            "name": stock.name,
            "sector": stock.sector,
            "sentiment_score": round(combined_score, 3),
            "news_sentiment": round(news_score, 3),
            "reddit_sentiment": round(reddit_score, 3),
            "sentiment_divergence": divergence,
            "sentiment_momentum": round(momentum, 3),
            "article_count": latest.article_count if latest else 0,
            "discussion_volume": latest.discussion_volume if latest else 0,
        })

    stock_sentiments.sort(key=lambda x: x["sentiment_score"], reverse=True)
    all_combined = [s["sentiment_score"] for s in stock_sentiments]
    all_news = [s["news_sentiment"] for s in stock_sentiments]
    all_reddit = [s["reddit_sentiment"] for s in stock_sentiments]

    market_sentiment = float(sum(all_combined) / max(len(all_combined), 1))
    market_news = float(sum(all_news) / max(len(all_news), 1))
    market_reddit = float(sum(all_reddit) / max(len(all_reddit), 1))

    return {
        "market_sentiment_score": round(market_sentiment, 3),
        "market_sentiment_label": "Bullish" if market_sentiment > 0.15 else "Bearish" if market_sentiment < -0.15 else "Neutral",
        "market_news_sentiment": round(market_news, 3),
        "market_reddit_sentiment": round(market_reddit, 3),
        "top_positive": stock_sentiments[:3],
        "top_negative": stock_sentiments[-3:] if len(stock_sentiments) >= 3 else [],
        "all_stocks": stock_sentiments,
    }


@router.get("/comparison")
def get_sentiment_comparison(db: Session = Depends(get_db)):
    """
    Returns side-by-side comparison of Financial News Sentiment vs Reddit Retail Sentiment
    for each equity in the platform.
    """
    stocks = db.query(Stock).filter(Stock.symbol != "^NSEI").all()
    comparison = []

    for stock in stocks:
        latest = (
            db.query(DailySentiment)
            .filter(DailySentiment.stock_id == stock.id)
            .order_by(DailySentiment.date.desc())
            .first()
        )
        news_score = latest.news_sentiment if latest and latest.news_sentiment is not None else 0.0
        reddit_score = latest.reddit_sentiment if latest and latest.reddit_sentiment is not None else 0.0
        combined = latest.combined_sentiment if latest and latest.combined_sentiment is not None else 0.0

        comparison.append({
            "symbol": stock.symbol,
            "name": stock.name,
            "sector": stock.sector,
            "news_sentiment": round(news_score, 3),
            "reddit_sentiment": round(reddit_score, 3),
            "combined_sentiment": round(combined, 3),
            "news_articles": latest.article_count if latest else 0,
            "reddit_discussions": latest.discussion_volume if latest else 0,
            "divergence": round(reddit_score - news_score, 3),
            "alignment": "Aligned" if abs(reddit_score - news_score) < 0.25 else ("Retail More Bullish" if reddit_score > news_score else "Media More Bullish"),
        })

    return comparison


@router.get("/reddit/trends")
def get_reddit_trends(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Returns top trending tickers and sentiment breakdown from recent Reddit activity."""
    collector = RedditCollector(db)
    return collector.get_reddit_trends(limit=limit)


@router.post("/reddit/sync")
def trigger_reddit_collection(db: Session = Depends(get_db)):
    """Triggers Reddit collection and FinBERT sentiment scoring."""
    collector = RedditCollector(db)
    posts = collector.collect_posts(limit=30)
    result = collector.save_and_analyze_posts(posts)
    return {
        "status": "success",
        "collected_posts": len(posts),
        "details": result,
    }


@router.get("/news")
def get_latest_financial_news(
    symbol: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(NewsArticle).order_by(NewsArticle.published_at.desc())
    if symbol:
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if stock:
            query = query.filter(NewsArticle.stock_id == stock.id)

    articles = query.limit(limit).all()
    results = []
    for a in articles:
        # Check if there is an associated sentiment record
        rec = db.query(SentimentRecord).filter(
            SentimentRecord.news_article_id == a.id
        ).first()

        results.append({
            "id": a.id,
            "headline": a.headline,
            "source": a.source,
            "url": a.url,
            "summary": a.summary,
            "published_at": a.published_at.isoformat(),
            "stock_symbol": a.stock.symbol if a.stock else None,
            "sentiment_score": round(rec.sentiment_score, 3) if rec else None,
            "sentiment_label": ("Positive" if rec.sentiment_score > 0.1 else ("Negative" if rec.sentiment_score < -0.1 else "Neutral")) if rec else "Neutral",
        })
    return results


@router.get("/reddit")
def get_reddit_discussions(
    limit: int = Query(default=20, ge=1, le=50),
    symbol: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(RedditPost).order_by(RedditPost.created_at.desc())
    if symbol:
        query = query.filter(RedditPost.ticker_mentions.like(f"%{symbol}%"))

    posts = query.limit(limit).all()
    results = []
    for p in posts:
        # Check sentiment record for this post
        rec = db.query(SentimentRecord).filter(
            SentimentRecord.reference_id == p.post_id,
            SentimentRecord.source_type == "reddit"
        ).first()

        results.append({
            "id": p.post_id,
            "subreddit": p.subreddit,
            "title": p.title,
            "text": p.text[:300] if p.text else "",
            "score": p.score,
            "num_comments": p.num_comments,
            "upvote_ratio": p.upvote_ratio,
            "ticker_mentions": p.ticker_mentions,
            "created_at": p.created_at.isoformat(),
            "sentiment_score": round(rec.sentiment_score, 3) if rec else None,
            "sentiment_label": ("Positive" if rec.sentiment_score > 0.1 else ("Negative" if rec.sentiment_score < -0.1 else "Neutral")) if rec else "Neutral",
        })
    return results
