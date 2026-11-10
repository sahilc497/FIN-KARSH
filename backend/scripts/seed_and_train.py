import os
import sys
import logging
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database.connection import init_db, SessionLocal
from backend.collectors.yahoo_finance import YahooFinanceCollector
from backend.collectors.moneycontrol_rss import MoneycontrolRSSCollector
from backend.collectors.reddit_collector import RedditCollector
from backend.sentiment.finbert_analyzer import FinBERTSentimentAnalyzer
from backend.ml.training import ModelTrainingPipeline
from backend.backtesting.engine import BacktestingEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_and_train")

def run_seed_and_train():
    logger.info("Initializing database...")
    init_db()
    db = SessionLocal()

    try:
        # Step 1: Sync Supported Stocks & Benchmark
        logger.info("--- Step 1: Syncing Stocks & Benchmark Index ---")
        yf_collector = YahooFinanceCollector(db)
        stocks = yf_collector.sync_supported_stocks()
        logger.info(f"Synchronized {len(stocks)} stocks.")

        # Step 2: Ingest 3-Year OHLCV Data
        logger.info("--- Step 2: Ingesting Historical OHLCV Series (3 Years) ---")
        for s in stocks:
            df = yf_collector.fetch_historical_ohlcv(s.symbol)
            saved = yf_collector.save_ohlcv_to_db(s.symbol, df)
            logger.info(f"{s.symbol}: Ingested {saved} price records.")

        # Step 3: Ingest News and Reddit Data
        logger.info("--- Step 3: Collecting Financial News & Reddit Discussions ---")
        mc_collector = MoneycontrolRSSCollector(db)
        articles = mc_collector.fetch_live_feeds()
        mc_collector.save_articles_to_db(articles)

        reddit_collector = RedditCollector(db)
        posts = reddit_collector.collect_posts()
        reddit_collector.save_posts_to_db(posts)

        # Step 4: FinBERT Sentiment Analysis
        logger.info("--- Step 4: Running FinBERT Sentiment Analysis ---")
        analyzer = FinBERTSentimentAnalyzer(db)
        analyzer.process_pending_articles()
        analyzer.process_reddit_posts()
        daily_updated = analyzer.aggregate_daily_sentiments()
        logger.info(f"Aggregated daily sentiment for {daily_updated} stock-day pairs.")

        # Step 5: Train, Validate, and Calibrate ML Models
        logger.info("--- Step 5: Training & Validating ML Models ---")
        pipeline = ModelTrainingPipeline(db)
        # Train for primary equities
        for sym in ["RELIANCE.NS", "TCS.NS", "TATAMOTORS.NS"]:
            results = pipeline.train_models_for_stock(symbol=sym, horizon_days=5)
            logger.info(f"Trained {len(results)} validated models for {sym}.")

        # Step 6: Execute Sample Backtests
        logger.info("--- Step 6: Executing Sample Historical Backtests ---")
        backtester = BacktestingEngine(db)
        for sym in ["RELIANCE.NS", "TATAMOTORS.NS"]:
            bt_res = backtester.run_backtest(symbol=sym, initial_capital=100000.0, horizon_days=5)
            logger.info(f"Backtest {sym}: Total Return: {bt_res['total_return_pct']}%, Sharpe: {bt_res['sharpe_ratio']}, MDD: {bt_res['max_drawdown_pct']}%")

        logger.info("==================================================")
        logger.info("SENTIMENT-APLHA Pipeline Completed Successfully!")
        logger.info("==================================================")

    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    run_seed_and_train()

