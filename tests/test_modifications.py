import pytest
from backend.database.connection import SessionLocal
from backend.collectors.stock_universe import StockUniverseManager, EXPANDED_NSE_UNIVERSE
from backend.collectors.reddit_collector import RedditCollector
from backend.rag.knowledge_base import search_knowledge_base
from backend.rag.gemini_service import GeminiService
from backend.rag.assistant import RAGFinancialAssistant
from backend.services.market_updater import market_broadcaster
from backend.api.routes import sentiment, assistant, stocks


def test_stock_universe_search():
    db = SessionLocal()
    try:
        manager = StockUniverseManager(db)
        # Search for Zomato
        zomato_results = manager.search("ZOMATO")
        assert len(zomato_results) > 0
        assert any(r["symbol"] == "ZOMATO.NS" for r in zomato_results)

        # Search for HAL (Hindustan Aeronautics)
        hal_results = manager.search("HAL")
        assert len(hal_results) > 0
        assert any(r["symbol"] == "HAL.NS" for r in hal_results)

        # Search for Reliance
        ril_results = manager.search("Reliance")
        assert len(ril_results) > 0
    finally:
        db.close()


def test_reddit_collector_filtering_and_ticker_extraction():
    db = SessionLocal()
    try:
        collector = RedditCollector(db)

        # Spam filtering test
        assert collector.filter_noise_and_spam("Valid analysis of Tata Motors EV market share", "Looking at Nexon sales.") is True
        assert collector.filter_noise_and_spam("Join our telegram for 100% guarantee calls", "DM for tips") is False
        assert collector.filter_noise_and_spam("Short", "too short") is False

        # Ticker extraction test
        tickers = collector.extract_ticker_mentions("Why Tata Motors and Reliance look strong while JLR deleverages")
        assert "TATAMOTORS.NS" in tickers
        assert "RELIANCE.NS" in tickers

        # Reddit trends test
        trends = collector.get_reddit_trends(limit=5)
        assert isinstance(trends, list)
    finally:
        db.close()


def test_knowledge_base_retrieval():
    # Test P/E and EPS retrieval
    pe_docs = search_knowledge_base("Explain P/E ratio and EPS valuation")
    assert len(pe_docs) > 0
    assert any("P/E" in d["title"] for d in pe_docs)

    # Test IPO retrieval
    ipo_docs = search_knowledge_base("What is an IPO DRHP and anchor investor?")
    assert len(ipo_docs) > 0
    assert any("IPO" in d["title"] for d in ipo_docs)

    # Test Mutual Funds & ETFs retrieval
    etf_docs = search_knowledge_base("Difference between mutual funds and ETFs")
    assert len(etf_docs) > 0
    assert any("ETF" in d["title"] for d in etf_docs)


def test_gemini_service_resilience():
    service = GeminiService()
    # When no real API key is configured, is_configured should return False and generate returns None gracefully
    if not service.is_configured():
        res = service.generate("What is NIFTY 50?", "NIFTY 50 is an Indian index")
        assert res is None  # Graceful fallback without crashing


def test_rag_assistant_with_new_topics():
    db = SessionLocal()
    try:
        rag = RAGFinancialAssistant(db)

        # Query 1: IPO mechanics
        res_ipo = rag.query("How do IPOs and anchor investors work in India?")
        assert "IPO" in res_ipo["answer"]
        assert len(res_ipo["citations"]) > 0

        # Query 2: P/E and EPS
        res_pe = rag.query("Explain P/E ratio and EPS")
        assert "P/E" in res_pe["answer"]

        # Query 3: Multi-stock comparison
        res_comp = rag.query("Compare TCS, Infosys and Wipro")
        assert "TCS" in res_comp["answer"]
    finally:
        db.close()


def test_live_market_snapshot_service():
    snapshot = market_broadcaster.get_latest_market_snapshot()
    assert snapshot["status"] == "STREAMING"
    assert "nifty_50" in snapshot
    assert "quotes" in snapshot
    assert len(snapshot["quotes"]) > 0
    assert "timestamp" in snapshot


def test_sentiment_comparison_endpoint():
    db = SessionLocal()
    try:
        comp = sentiment.get_sentiment_comparison(db=db)
        assert isinstance(comp, list)
        assert len(comp) > 0
        first = comp[0]
        assert "news_sentiment" in first
        assert "reddit_sentiment" in first
        assert "divergence" in first
        assert "alignment" in first
    finally:
        db.close()


def test_assistant_status_endpoint():
    status = assistant.get_assistant_engine_status()
    assert "engine" in status
    assert "gemini_active" in status
    assert len(status["features"]) > 0

