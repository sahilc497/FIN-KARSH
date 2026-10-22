import json
import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from app.database.models import (
    Stock,
    Article,
    ArticleStockMapping,
    SentimentResult,
    PriceHistory,
    SentimentFactor,
    ModelRun,
    Prediction,
    TradingSignal,
    BacktestRun,
    BacktestTrade,
    PipelineJob,
)

class StockRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, active_only: bool = True) -> List[Stock]:
        q = self.db.query(Stock)
        if active_only:
            q = q.filter(Stock.is_active == True)
        return q.order_by(Stock.symbol).all()

    def get_by_id(self, stock_id: int) -> Optional[Stock]:
        return self.db.query(Stock).filter(Stock.id == stock_id).first()

    def get_by_symbol(self, symbol: str) -> Optional[Stock]:
        clean = symbol.upper().strip().replace(".NS", "")
        return self.db.query(Stock).filter(Stock.symbol == clean).first()

    def add_or_update(self, symbol: str, ticker: str, company_name: str, sector: str = None, aliases: str = None) -> Stock:
        stock = self.get_by_symbol(symbol)
        if not stock:
            stock = Stock(
                symbol=symbol.upper().strip(),
                ticker=ticker.strip(),
                company_name=company_name.strip(),
                sector=sector,
                aliases=aliases,
                is_active=True,
            )
            self.db.add(stock)
            self.db.commit()
            self.db.refresh(stock)
        else:
            stock.ticker = ticker
            stock.company_name = company_name
            stock.sector = sector or stock.sector
            stock.aliases = aliases or stock.aliases
            self.db.commit()
            self.db.refresh(stock)
        return stock


class ArticleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_fingerprint(self, fingerprint: str) -> Optional[Article]:
        return self.db.query(Article).filter(Article.content_fingerprint == fingerprint).first()

    def get_by_url(self, url: str) -> Optional[Article]:
        return self.db.query(Article).filter(Article.url == url).first()

    def create(self, title: str, description: str, url: str, source: str, published_at: datetime.datetime, fingerprint: str, raw_text: str = None) -> Optional[Article]:
        if self.get_by_url(url) or self.get_by_fingerprint(fingerprint):
            return None  # Duplicate article
        article = Article(
            title=title,
            description=description,
            url=url,
            source=source,
            published_at=published_at,
            content_fingerprint=fingerprint,
            raw_text=raw_text,
        )
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        return article

    def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        symbol: Optional[str] = None,
        sentiment_label: Optional[str] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Article], int]:
        q = self.db.query(Article)

        if symbol:
            clean_sym = symbol.upper().strip().replace(".NS", "")
            q = q.join(ArticleStockMapping).join(Stock).filter(Stock.symbol == clean_sym)

        if sentiment_label:
            q = q.join(SentimentResult).filter(SentimentResult.sentiment_label == sentiment_label.lower())

        if source:
            q = q.filter(Article.source.ilike(f"%{source}%"))

        if search:
            q = q.filter(Article.title.ilike(f"%{search}%") | Article.description.ilike(f"%{search}%"))

        total = q.count()
        items = q.order_by(desc(Article.published_at)).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def get_unprocessed_for_sentiment(self, limit: int = 100) -> List[Article]:
        # Articles that do not have a successful sentiment result
        stmt = self.db.query(SentimentResult.article_id).filter(SentimentResult.inference_status == "ready")
        return self.db.query(Article).filter(~Article.id.in_(stmt)).order_by(desc(Article.published_at)).limit(limit).all()


class ArticleStockMappingRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_mapping(self, article_id: int, stock_id: int, matched_term: str, confidence: float = 1.0) -> Optional[ArticleStockMapping]:
        existing = (
            self.db.query(ArticleStockMapping)
            .filter(ArticleStockMapping.article_id == article_id, ArticleStockMapping.stock_id == stock_id)
            .first()
        )
        if existing:
            return existing
        mapping = ArticleStockMapping(
            article_id=article_id,
            stock_id=stock_id,
            matched_term=matched_term,
            confidence=confidence,
        )
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def get_mapped_symbols_for_article(self, article_id: int) -> List[str]:
        rows = (
            self.db.query(Stock.symbol)
            .join(ArticleStockMapping)
            .filter(ArticleStockMapping.article_id == article_id)
            .all()
        )
        return [r[0] for r in rows]


class SentimentRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_result(
        self,
        article_id: int,
        model_name: str,
        model_version: str,
        label: str,
        pos_prob: float,
        neg_prob: float,
        neu_prob: float,
        score: float,
        status: str = "ready",
        error_message: str = None,
    ) -> SentimentResult:
        res = self.db.query(SentimentResult).filter(SentimentResult.article_id == article_id).first()
        if not res:
            res = SentimentResult(
                article_id=article_id,
                model_name=model_name,
                model_version=model_version,
                sentiment_label=label,
                positive_probability=pos_prob,
                negative_probability=neg_prob,
                neutral_probability=neu_prob,
                sentiment_score=score,
                inference_status=status,
                error_message=error_message,
                inference_timestamp=datetime.datetime.utcnow(),
            )
            self.db.add(res)
        else:
            res.model_name = model_name
            res.model_version = model_version
            res.sentiment_label = label
            res.positive_probability = pos_prob
            res.negative_probability = neg_prob
            res.neutral_probability = neu_prob
            res.sentiment_score = score
            res.inference_status = status
            res.error_message = error_message
            res.inference_timestamp = datetime.datetime.utcnow()
        self.db.commit()
        self.db.refresh(res)
        return res


class PriceRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_prices(self, stock_id: int, records: List[Dict[str, Any]]) -> int:
        count = 0
        for rec in records:
            dt = rec["date"]
            if isinstance(dt, str):
                dt = datetime.datetime.fromisoformat(dt)
            elif hasattr(dt, "to_pydatetime"):
                dt = dt.to_pydatetime()
            # Normalize to date midnight
            dt = datetime.datetime(dt.year, dt.month, dt.day)

            existing = (
                self.db.query(PriceHistory)
                .filter(PriceHistory.stock_id == stock_id, PriceHistory.date == dt)
                .first()
            )
            if existing:
                for k, v in rec.items():
                    if k != "date" and hasattr(existing, k) and v is not None:
                        setattr(existing, k, float(v) if isinstance(v, (int, float)) else v)
            else:
                ph = PriceHistory(
                    stock_id=stock_id,
                    date=dt,
                    open=float(rec.get("open", 0.0)),
                    high=float(rec.get("high", 0.0)),
                    low=float(rec.get("low", 0.0)),
                    close=float(rec.get("close", 0.0)),
                    volume=float(rec.get("volume", 0.0)),
                    returns_1d=rec.get("returns_1d"),
                    momentum_5d=rec.get("momentum_5d"),
                    momentum_20d=rec.get("momentum_20d"),
                    momentum_60d=rec.get("momentum_60d"),
                    ma_20=rec.get("ma_20"),
                    ma_50=rec.get("ma_50"),
                    rsi_14=rec.get("rsi_14"),
                    macd=rec.get("macd"),
                    macd_signal=rec.get("macd_signal"),
                    volatility_20d=rec.get("volatility_20d"),
                    volume_ratio=rec.get("volume_ratio"),
                )
                self.db.add(ph)
                count += 1
        self.db.commit()
        return count

    def get_by_stock(self, stock_id: int, limit: int = 180) -> List[PriceHistory]:
        return (
            self.db.query(PriceHistory)
            .filter(PriceHistory.stock_id == stock_id)
            .order_by(PriceHistory.date.asc())
            .all()[-limit:]
        )


class FactorRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_factor(self, stock_id: int, date: datetime.datetime, factor_dict: Dict[str, Any]) -> SentimentFactor:
        dt = datetime.datetime(date.year, date.month, date.day)
        existing = (
            self.db.query(SentimentFactor)
            .filter(SentimentFactor.stock_id == stock_id, SentimentFactor.date == dt)
            .first()
        )
        if not existing:
            sf = SentimentFactor(stock_id=stock_id, date=dt, **factor_dict)
            self.db.add(sf)
            self.db.commit()
            self.db.refresh(sf)
            return sf
        else:
            for k, v in factor_dict.items():
                if hasattr(existing, k):
                    setattr(existing, k, v)
            self.db.commit()
            self.db.refresh(existing)
            return existing

    def get_by_stock(self, stock_id: int, limit: int = 180) -> List[SentimentFactor]:
        return (
            self.db.query(SentimentFactor)
            .filter(SentimentFactor.stock_id == stock_id)
            .order_by(SentimentFactor.date.asc())
            .all()[-limit:]
        )


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_job(self, job_id: str, job_type: str, total_items: int = 0) -> PipelineJob:
        job = PipelineJob(
            job_id=job_id,
            job_type=job_type,
            status="queued",
            progress_pct=0,
            total_items=total_items,
            processed_items=0,
            message="Job queued",
            started_at=datetime.datetime.utcnow(),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress_pct: Optional[int] = None,
        processed_items: Optional[int] = None,
        total_items: Optional[int] = None,
        message: Optional[str] = None,
        error_details: Optional[str] = None,
    ) -> Optional[PipelineJob]:
        job = self.db.query(PipelineJob).filter(PipelineJob.job_id == job_id).first()
        if not job:
            return None
        if status:
            job.status = status
            if status in ("completed", "failed"):
                job.completed_at = datetime.datetime.utcnow()
        if progress_pct is not None:
            job.progress_pct = progress_pct
        if processed_items is not None:
            job.processed_items = processed_items
        if total_items is not None:
            job.total_items = total_items
        if message is not None:
            job.message = message
        if error_details is not None:
            job.error_details = error_details
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_job(self, job_id: str) -> Optional[PipelineJob]:
        return self.db.query(PipelineJob).filter(PipelineJob.job_id == job_id).first()

    def get_recent_jobs(self, limit: int = 20) -> List[PipelineJob]:
        return self.db.query(PipelineJob).order_by(desc(PipelineJob.started_at)).limit(limit).all()
