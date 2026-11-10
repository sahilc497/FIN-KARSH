from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from backend.database.connection import Base

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(30), unique=True, index=True, nullable=False)  # e.g., "RELIANCE.NS"
    name = Column(String(150), nullable=False)
    sector = Column(String(80), nullable=True)
    industry = Column(String(100), nullable=True)
    exchange = Column(String(20), default="NSE")
    currency = Column(String(10), default="INR")
    is_nifty50 = Column(Boolean, default=True)
    
    # Fundamental metrics
    market_cap = Column(Float, nullable=True)
    pe_ratio = Column(Float, nullable=True)
    pb_ratio = Column(Float, nullable=True)
    eps = Column(Float, nullable=True)
    dividend_yield = Column(Float, nullable=True)
    roe = Column(Float, nullable=True)
    debt_to_equity = Column(Float, nullable=True)
    revenue_growth = Column(Float, nullable=True)
    profit_growth = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    prices = relationship("PriceHistory", back_populates="stock", cascade="all, delete-orphan")
    news_articles = relationship("NewsArticle", back_populates="stock", cascade="all, delete-orphan")
    sentiment_records = relationship("SentimentRecord", back_populates="stock", cascade="all, delete-orphan")
    daily_sentiments = relationship("DailySentiment", back_populates="stock", cascade="all, delete-orphan")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    adj_close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    # Precomputed price derivatives
    returns_1d = Column(Float, nullable=True)
    log_returns_1d = Column(Float, nullable=True)
    volatility_20d = Column(Float, nullable=True)

    stock = relationship("Stock", back_populates="prices")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uix_stock_date"),
        Index("ix_stock_price_date", "stock_id", "date"),
    )


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="SET NULL"), nullable=True, index=True)
    headline = Column(String(500), nullable=False)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    summary = Column(Text, nullable=True)
    source = Column(String(100), nullable=False)
    published_at = Column(DateTime, nullable=False, index=True)
    raw_text = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True, index=True)

    stock = relationship("Stock", back_populates="news_articles")
    sentiment_records = relationship("SentimentRecord", back_populates="news_article")


class RedditPost(Base):
    __tablename__ = "reddit_posts"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(String(50), unique=True, nullable=False, index=True)
    subreddit = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    text = Column(Text, nullable=True)
    score = Column(Integer, default=0)
    num_comments = Column(Integer, default=0)
    upvote_ratio = Column(Float, default=1.0)
    created_at = Column(DateTime, nullable=False, index=True)
    ticker_mentions = Column(String(200), nullable=True)  # comma-separated tickers


class SentimentRecord(Base):
    __tablename__ = "sentiment_records"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(20), nullable=False)  # "news" or "reddit"
    reference_id = Column(String(100), nullable=True)
    news_article_id = Column(Integer, ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=True)
    
    timestamp = Column(DateTime, nullable=False, index=True)
    p_positive = Column(Float, nullable=False)
    p_negative = Column(Float, nullable=False)
    p_neutral = Column(Float, nullable=False)
    sentiment_score = Column(Float, nullable=False)  # P(pos) - P(neg)
    confidence = Column(Float, nullable=False)

    stock = relationship("Stock", back_populates="sentiment_records")
    news_article = relationship("NewsArticle", back_populates="sentiment_records")


class DailySentiment(Base):
    __tablename__ = "daily_sentiment"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    
    news_sentiment = Column(Float, default=0.0)
    reddit_sentiment = Column(Float, default=0.0)
    combined_sentiment = Column(Float, default=0.0)
    sentiment_momentum = Column(Float, default=0.0)  # 5-day delta
    sentiment_volatility = Column(Float, default=0.0)  # rolling std
    article_count = Column(Integer, default=0)
    discussion_volume = Column(Integer, default=0)

    stock = relationship("Stock", back_populates="daily_sentiments")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uix_stock_daily_sentiment"),
    )


class MLModelRecord(Base):
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(80), unique=True, index=True, nullable=False)
    model_name = Column(String(80), nullable=False)  # "RandomForest", "HistGradientBoosting", "LSTM", etc.
    target_type = Column(String(20), nullable=False)  # "classification" or "regression"
    horizon_days = Column(Integer, default=5)
    
    # Classification Metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    roc_auc = Column(Float, nullable=True)
    pr_auc = Column(Float, nullable=True)
    mcc = Column(Float, nullable=True)
    
    # Regression Metrics
    rmse = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    r2 = Column(Float, nullable=True)
    
    # Trading Strategy Backtest Metrics
    strategy_sharpe = Column(Float, nullable=True)
    strategy_drawdown = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    
    file_path = Column(String(255), nullable=False)
    metadata_json = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BacktestRecord(Base):
    __tablename__ = "backtest_records"

    id = Column(Integer, primary_key=True, index=True)
    stock_symbol = Column(String(30), nullable=False, index=True)
    model_id = Column(String(80), nullable=False)
    strategy = Column(String(50), default="threshold_filtered")
    horizon_days = Column(Integer, default=5)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    initial_capital = Column(Float, nullable=False)
    final_equity = Column(Float, nullable=False)
    total_return_pct = Column(Float, nullable=False)
    benchmark_return_pct = Column(Float, nullable=False)
    annualized_return_pct = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=False)
    sortino_ratio = Column(Float, nullable=False)
    max_drawdown_pct = Column(Float, nullable=False)
    win_rate_pct = Column(Float, nullable=False)
    profit_factor = Column(Float, nullable=False)
    total_trades = Column(Integer, nullable=False)
    
    execution_log_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(30), unique=True, nullable=False, index=True)
    target_price = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)


class RAGDocument(Base):
    __tablename__ = "rag_documents"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String(100), unique=True, index=True)
    title = Column(String(255), nullable=False)
    doc_type = Column(String(50), nullable=False)  # "stock_analysis", "news", "educational", "market_summary"
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

