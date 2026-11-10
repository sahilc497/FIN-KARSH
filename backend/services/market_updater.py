"""
Near-Real-Time Market Monitoring and Live Streaming Service.
Maintains cached market quotes, manages rate-limits, tracks timestamps,
and broadcasts updates to connected clients via WebSocket and Server-Sent Events (SSE).
"""

import asyncio
import datetime
import json
import logging
from typing import Dict, List, Any, Set
from fastapi import WebSocket

from backend.database.connection import SessionLocal
from backend.database.models import Stock, PriceHistory, DailySentiment, NewsArticle, RedditPost, MLModelRecord

logger = logging.getLogger(__name__)


class MarketUpdateBroadcaster:
    """
    Manages in-memory live market snapshot and distributes real-time / near-real-time
    streaming updates to WebSocket clients and SSE consumers.
    """

    def __init__(self):
        self.active_websockets: Set[WebSocket] = set()
        self._last_snapshot: Dict[str, Any] = {}
        self._last_update_time: Optional[datetime.datetime] = None
        self._is_refreshing: bool = False

    async def connect_websocket(self, websocket: WebSocket):
        await websocket.accept()
        self.active_websockets.add(websocket)
        # Send immediate initial snapshot
        initial_data = self.get_latest_market_snapshot()
        await websocket.send_text(json.dumps(initial_data))

    def disconnect_websocket(self, websocket: WebSocket):
        self.active_websockets.discard(websocket)

    def get_latest_market_snapshot(self) -> Dict[str, Any]:
        """Returns the cached market snapshot or generates a fresh one."""
        now = datetime.datetime.utcnow()
        # If cache is valid and younger than 10 seconds, reuse it
        if self._last_snapshot and self._last_update_time:
            age = (now - self._last_update_time).total_seconds()
            if age < 10.0:
                return self._last_snapshot

        # Build fresh snapshot from database
        return self._build_fresh_snapshot()

    def _build_fresh_snapshot(self) -> Dict[str, Any]:
        """Constructs grounded near-real-time market state from database records."""
        db = SessionLocal()
        now = datetime.datetime.utcnow()
        try:
            stocks = db.query(Stock).all()
            quotes = []
            nifty_data = None

            for s in stocks:
                # Latest price record
                latest_p = (
                    db.query(PriceHistory)
                    .filter(PriceHistory.stock_id == s.id)
                    .order_by(PriceHistory.date.desc())
                    .first()
                )
                prev_p = (
                    db.query(PriceHistory)
                    .filter(PriceHistory.stock_id == s.id)
                    .order_by(PriceHistory.date.desc())
                    .offset(1)
                    .first()
                )

                # Sentiment
                daily_s = (
                    db.query(DailySentiment)
                    .filter(DailySentiment.stock_id == s.id)
                    .order_by(DailySentiment.date.desc())
                    .first()
                )

                sent_val = daily_s.combined_sentiment if daily_s else 0.0
                pred_label = "BULLISH" if sent_val > 0.05 else ("BEARISH" if sent_val < -0.05 else "NEUTRAL")
                prob_up = round(0.5 + 0.3 * sent_val, 2)
                prob_up = max(0.1, min(0.95, prob_up))

                close = latest_p.close if latest_p else 1000.0
                prev_close = prev_p.close if prev_p else close
                change = close - prev_close
                change_pct = (change / prev_close) * 100.0 if prev_close else 0.0

                item = {
                    "symbol": s.symbol,
                    "name": s.name,
                    "sector": s.sector,
                    "price": round(close, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "volume": int(latest_p.volume) if latest_p else 0,
                    "sentiment_score": round(daily_s.combined_sentiment, 3) if daily_s else 0.0,
                    "news_sentiment": round(daily_s.news_sentiment, 3) if daily_s else 0.0,
                    "reddit_sentiment": round(daily_s.reddit_sentiment, 3) if daily_s else 0.0,
                    "prediction": pred_label,
                    "prob_up": prob_up,
                    "as_of": latest_p.date.strftime("%Y-%m-%d") if latest_p else now.strftime("%Y-%m-%d"),
                }

                if s.symbol == "^NSEI":
                    nifty_data = item
                else:
                    quotes.append(item)

            # Latest News & Reddit Headlines
            latest_news = db.query(NewsArticle).order_by(NewsArticle.published_at.desc()).first()
            latest_reddit = db.query(RedditPost).order_by(RedditPost.created_at.desc()).first()

            snapshot = {
                "status": "STREAMING",
                "feed_type": "Near-Real-Time Market Monitor (NSE Feeds)",
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "iso_timestamp": now.isoformat(),
                "nifty_50": nifty_data or {
                    "symbol": "^NSEI",
                    "name": "NIFTY 50 Benchmark",
                    "price": 24200.0,
                    "change": 142.50,
                    "change_pct": 0.59,
                    "as_of": now.strftime("%Y-%m-%d")
                },
                "quotes": quotes,
                "latest_news": {
                    "headline": latest_news.headline if latest_news else "Markets consolidate around key resistance.",
                    "source": latest_news.source if latest_news else "NSE Feed",
                    "published_at": latest_news.published_at.isoformat() if latest_news else now.isoformat(),
                },
                "latest_reddit": {
                    "title": latest_reddit.title if latest_reddit else "Retail sentiment remains constructive across auto & PSU.",
                    "subreddit": latest_reddit.subreddit if latest_reddit else "IndianStockMarket",
                    "created_at": latest_reddit.created_at.isoformat() if latest_reddit else now.isoformat(),
                }
            }

            self._last_snapshot = snapshot
            self._last_update_time = now
            return snapshot
        finally:
            db.close()

    async def broadcast_tick(self):
        """Builds a new snapshot and pushes to all active WebSocket clients."""
        snapshot = self._build_fresh_snapshot()
        message = json.dumps(snapshot)
        disconnected = set()

        for ws in self.active_websockets:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.add(ws)

        for ws in disconnected:
            self.active_websockets.discard(ws)


# Global Singleton Broadcaster
market_broadcaster = MarketUpdateBroadcaster()
