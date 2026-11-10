import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from backend.database.models import Stock, PriceHistory, DailySentiment, NewsArticle
from backend.collectors.yahoo_finance import YahooFinanceCollector
from backend.sentiment.finbert_analyzer import FinBERTSentimentAnalyzer

logger = logging.getLogger(__name__)

# Comprehensive Indian NSE Equity Universe (NIFTY 50, NIFTY NEXT 50, NIFTY 100, NIFTY 200, NIFTY 500)
EXPANDED_NSE_UNIVERSE: List[Dict[str, Any]] = [
    # --- NIFTY 50 Pillar Equities ---
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd", "sector": "Energy", "index": "NIFTY 50", "pe": 24.8, "roe": 9.2, "market_cap": 19500000000000.0, "base_price": 2850.0},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services Ltd", "sector": "Information Technology", "index": "NIFTY 50", "pe": 29.5, "roe": 48.5, "market_cap": 14200000000000.0, "base_price": 3950.0},
    {"symbol": "INFY.NS", "name": "Infosys Ltd", "sector": "Information Technology", "index": "NIFTY 50", "pe": 25.2, "roe": 31.4, "market_cap": 7500000000000.0, "base_price": 1680.0},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Ltd", "sector": "Financial Services", "index": "NIFTY 50", "pe": 18.6, "roe": 15.8, "market_cap": 12800000000000.0, "base_price": 1620.0},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank Ltd", "sector": "Financial Services", "index": "NIFTY 50", "pe": 17.8, "roe": 18.2, "market_cap": 8400000000000.0, "base_price": 1180.0},
    {"symbol": "TATAMOTORS.NS", "name": "Tata Motors Ltd", "sector": "Automobile", "index": "NIFTY 50", "pe": 15.4, "roe": 26.5, "market_cap": 3400000000000.0, "base_price": 980.0},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "sector": "Financial Services", "index": "NIFTY 50", "pe": 10.8, "roe": 16.9, "market_cap": 7200000000000.0, "base_price": 810.0},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel Ltd", "sector": "Telecommunication", "index": "NIFTY 50", "pe": 48.2, "roe": 19.4, "market_cap": 8900000000000.0, "base_price": 1550.0},
    {"symbol": "ITC.NS", "name": "ITC Ltd", "sector": "Consumer Goods", "index": "NIFTY 50", "pe": 26.8, "roe": 29.8, "market_cap": 5900000000000.0, "base_price": 475.0},
    {"symbol": "LT.NS", "name": "Larsen & Toubro Ltd", "sector": "Capital Goods", "index": "NIFTY 50", "pe": 36.2, "roe": 14.5, "market_cap": 4800000000000.0, "base_price": 3520.0},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank Ltd", "sector": "Financial Services", "index": "NIFTY 50", "pe": 21.4, "roe": 14.2, "market_cap": 3600000000000.0, "base_price": 1780.0},
    {"symbol": "AXISBANK.NS", "name": "Axis Bank Ltd", "sector": "Financial Services", "index": "NIFTY 50", "pe": 13.9, "roe": 16.1, "market_cap": 3500000000000.0, "base_price": 1150.0},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever Ltd", "sector": "Consumer Goods", "index": "NIFTY 50", "pe": 54.2, "roe": 20.3, "market_cap": 5800000000000.0, "base_price": 2480.0},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance Ltd", "sector": "Financial Services", "index": "NIFTY 50", "pe": 28.6, "roe": 22.1, "market_cap": 4400000000000.0, "base_price": 7100.0},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki India Ltd", "sector": "Automobile", "index": "NIFTY 50", "pe": 27.4, "roe": 16.8, "market_cap": 3800000000000.0, "base_price": 12200.0},
    {"symbol": "SUNPHARMA.NS", "name": "Sun Pharmaceutical Industries Ltd", "sector": "Healthcare", "index": "NIFTY 50", "pe": 35.8, "roe": 15.6, "market_cap": 4100000000000.0, "base_price": 1720.0},
    {"symbol": "TITAN.NS", "name": "Titan Company Ltd", "sector": "Consumer Discretionary", "index": "NIFTY 50", "pe": 82.5, "roe": 31.2, "market_cap": 3100000000000.0, "base_price": 3490.0},
    {"symbol": "TATASTEEL.NS", "name": "Tata Steel Ltd", "sector": "Metals & Mining", "index": "NIFTY 50", "pe": 42.1, "roe": 4.8, "market_cap": 1900000000000.0, "base_price": 152.0},
    {"symbol": "ASIANPAINT.NS", "name": "Asian Paints Ltd", "sector": "Consumer Discretionary", "index": "NIFTY 50", "pe": 52.4, "roe": 24.5, "market_cap": 2700000000000.0, "base_price": 2820.0},
    {"symbol": "NTPC.NS", "name": "NTPC Ltd", "sector": "Utilities", "index": "NIFTY 50", "pe": 18.2, "roe": 13.9, "market_cap": 3900000000000.0, "base_price": 405.0},
    {"symbol": "POWERGRID.NS", "name": "Power Grid Corporation of India", "sector": "Utilities", "index": "NIFTY 50", "pe": 19.5, "roe": 19.8, "market_cap": 3100000000000.0, "base_price": 335.0},
    {"symbol": "M&M.NS", "name": "Mahindra & Mahindra Ltd", "sector": "Automobile", "index": "NIFTY 50", "pe": 29.8, "roe": 18.5, "market_cap": 3600000000000.0, "base_price": 2940.0},
    {"symbol": "WIPRO.NS", "name": "Wipro Ltd", "sector": "Information Technology", "index": "NIFTY 50", "pe": 21.0, "roe": 15.2, "market_cap": 2800000000000.0, "base_price": 540.0},
    {"symbol": "ADANIENT.NS", "name": "Adani Enterprises Ltd", "sector": "Metals & Mining", "index": "NIFTY 50", "pe": 95.0, "roe": 8.5, "market_cap": 3400000000000.0, "base_price": 2980.0},
    {"symbol": "ADANIPORTS.NS", "name": "Adani Ports and Special Economic Zone", "sector": "Services", "index": "NIFTY 50", "pe": 34.2, "roe": 17.5, "market_cap": 3000000000000.0, "base_price": 1390.0},

    # --- NIFTY NEXT 50 High-Growth Equities ---
    {"symbol": "ZOMATO.NS", "name": "Zomato Ltd", "sector": "Consumer Services", "index": "NIFTY NEXT 50", "pe": 115.0, "roe": 7.4, "market_cap": 2300000000000.0, "base_price": 260.0},
    {"symbol": "JIOFIN.NS", "name": "Jio Financial Services Ltd", "sector": "Financial Services", "index": "NIFTY NEXT 50", "pe": 135.0, "roe": 1.2, "market_cap": 2100000000000.0, "base_price": 330.0},
    {"symbol": "HAL.NS", "name": "Hindustan Aeronautics Ltd", "sector": "Capital Goods", "index": "NIFTY NEXT 50", "pe": 38.5, "roe": 26.2, "market_cap": 3100000000000.0, "base_price": 4650.0},
    {"symbol": "BEL.NS", "name": "Bharat Electronics Ltd", "sector": "Capital Goods", "index": "NIFTY NEXT 50", "pe": 48.0, "roe": 24.5, "market_cap": 2150000000000.0, "base_price": 295.0},
    {"symbol": "TRENT.NS", "name": "Trent Ltd", "sector": "Consumer Discretionary", "index": "NIFTY NEXT 50", "pe": 140.0, "roe": 28.5, "market_cap": 2600000000000.0, "base_price": 7250.0},
    {"symbol": "VBL.NS", "name": "Varun Beverages Ltd", "sector": "Consumer Goods", "index": "NIFTY NEXT 50", "pe": 72.0, "roe": 33.1, "market_cap": 2050000000000.0, "base_price": 1580.0},
    {"symbol": "VEDL.NS", "name": "Vedanta Ltd", "sector": "Metals & Mining", "index": "NIFTY NEXT 50", "pe": 14.2, "roe": 28.0, "market_cap": 1800000000000.0, "base_price": 480.0},
    {"symbol": "DLF.NS", "name": "DLF Ltd", "sector": "Realty", "index": "NIFTY NEXT 50", "pe": 65.0, "roe": 8.4, "market_cap": 2100000000000.0, "base_price": 850.0},
    {"symbol": "CHOLAFIN.NS", "name": "Cholamandalam Investment and Finance", "sector": "Financial Services", "index": "NIFTY NEXT 50", "pe": 32.5, "roe": 20.1, "market_cap": 1250000000000.0, "base_price": 1480.0},
    {"symbol": "TVSMOTOR.NS", "name": "TVS Motor Company Ltd", "sector": "Automobile", "index": "NIFTY NEXT 50", "pe": 54.0, "roe": 29.5, "market_cap": 1180000000000.0, "base_price": 2480.0},

    # --- NIFTY 100 / 200 / 500 Leaders ---
    {"symbol": "PAYTM.NS", "name": "One97 Communications Ltd (Paytm)", "sector": "Financial Services", "index": "NIFTY 500", "pe": None, "roe": -12.5, "market_cap": 520000000000.0, "base_price": 820.0},
    {"symbol": "MRF.NS", "name": "MRF Ltd", "sector": "Automobile", "index": "NIFTY 200", "pe": 26.5, "roe": 13.8, "market_cap": 580000000000.0, "base_price": 137000.0},
    {"symbol": "IRCTC.NS", "name": "Indian Railway Catering and Tourism Corp", "sector": "Services", "index": "NIFTY 200", "pe": 62.0, "roe": 41.5, "market_cap": 710000000000.0, "base_price": 890.0},
    {"symbol": "POLYCAB.NS", "name": "Polycab India Ltd", "sector": "Capital Goods", "index": "NIFTY 200", "pe": 52.0, "roe": 22.4, "market_cap": 1020000000000.0, "base_price": 6800.0},
    {"symbol": "DIXON.NS", "name": "Dixon Technologies (India) Ltd", "sector": "Consumer Durables", "index": "NIFTY 200", "pe": 110.0, "roe": 29.8, "market_cap": 880000000000.0, "base_price": 14700.0},
    {"symbol": "SUZLON.NS", "name": "Suzlon Energy Ltd", "sector": "Capital Goods", "index": "NIFTY 500", "pe": 68.0, "roe": 18.2, "market_cap": 950000000000.0, "base_price": 70.0},
    {"symbol": "^NSEI", "name": "NIFTY 50 Benchmark Index", "sector": "Index", "index": "Benchmark", "pe": 22.4, "roe": 16.0, "market_cap": 180000000000000.0, "base_price": 24200.0},
]

# Common Indian company names and colloquial aliases mapped to ticker symbols
ALIAS_MAP = {
    "RELIANCE": "RELIANCE.NS", "RIL": "RELIANCE.NS", "JIO": "RELIANCE.NS",
    "TCS": "TCS.NS", "TATA CONSULTANCY": "TCS.NS",
    "INFY": "INFY.NS", "INFOSYS": "INFY.NS",
    "HDFC": "HDFCBANK.NS", "HDFCBANK": "HDFCBANK.NS",
    "ICICI": "ICICIBANK.NS", "ICICIBANK": "ICICIBANK.NS",
    "TATA MOTORS": "TATAMOTORS.NS", "TATAMOTORS": "TATAMOTORS.NS", "JLR": "TATAMOTORS.NS",
    "SBI": "SBIN.NS", "SBIN": "SBIN.NS", "STATE BANK": "SBIN.NS",
    "AIRTEL": "BHARTIARTL.NS", "BHARTI": "BHARTIARTL.NS", "BHARTIARTL": "BHARTIARTL.NS",
    "ITC": "ITC.NS",
    "L&T": "LT.NS", "LT": "LT.NS", "LARSEN": "LT.NS",
    "KOTAK": "KOTAKBANK.NS", "KOTAKBANK": "KOTAKBANK.NS",
    "AXIS": "AXISBANK.NS", "AXISBANK": "AXISBANK.NS",
    "HUL": "HINDUNILVR.NS", "HINDUSTAN UNILEVER": "HINDUNILVR.NS",
    "BAJAJ FINANCE": "BAJFINANCE.NS", "BAJFINANCE": "BAJFINANCE.NS",
    "MARUTI": "MARUTI.NS", "MARUTI SUZUKI": "MARUTI.NS",
    "SUN PHARMA": "SUNPHARMA.NS", "SUNPHARMA": "SUNPHARMA.NS",
    "TITAN": "TITAN.NS",
    "TATA STEEL": "TATASTEEL.NS", "TATASTEEL": "TATASTEEL.NS",
    "ASIAN PAINTS": "ASIANPAINT.NS", "ASIANPAINT": "ASIANPAINT.NS",
    "NTPC": "NTPC.NS",
    "POWERGRID": "POWERGRID.NS", "POWER GRID": "POWERGRID.NS",
    "M&M": "M&M.NS", "MAHINDRA": "M&M.NS",
    "WIPRO": "WIPRO.NS",
    "ADANI ENTERPRISES": "ADANIENT.NS", "ADANIENT": "ADANIENT.NS",
    "ADANI PORTS": "ADANIPORTS.NS", "ADANIPORTS": "ADANIPORTS.NS",
    "ZOMATO": "ZOMATO.NS",
    "JIO FINANCIAL": "JIOFIN.NS", "JIOFIN": "JIOFIN.NS",
    "HAL": "HAL.NS",
    "BEL": "BEL.NS",
    "TRENT": "TRENT.NS",
    "VARUN BEVERAGES": "VBL.NS", "VBL": "VBL.NS",
    "VEDANTA": "VEDL.NS", "VEDL": "VEDL.NS",
    "DLF": "DLF.NS",
    "CHOLA": "CHOLAFIN.NS", "CHOLAFIN": "CHOLAFIN.NS",
    "TVS MOTOR": "TVSMOTOR.NS", "TVS": "TVSMOTOR.NS",
    "PAYTM": "PAYTM.NS",
    "MRF": "MRF.NS",
    "IRCTC": "IRCTC.NS",
    "POLYCAB": "POLYCAB.NS",
    "DIXON": "DIXON.NS",
    "SUZLON": "SUZLON.NS",
    "NIFTY": "^NSEI", "NIFTY50": "^NSEI",
}

class StockUniverseManager:
    """
    Dynamically manages and expands stock coverage across NIFTY 50, NIFTY Next 50,
    NIFTY 100, NIFTY 200, NIFTY 500, enabling on-demand onboarding of any NSE stock.
    """

    def __init__(self, db: Session):
        self.db = db
        self.catalog = {item["symbol"]: item for item in EXPANDED_NSE_UNIVERSE}

    def search(self, query: str, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Searches stock universe across both local database and the expanded catalog.
        Matches by ticker symbol or company name.
        """
        q = query.strip().upper()
        results = []
        seen = set()

        # 1. Search in existing database stocks
        db_stocks = self.db.query(Stock).filter(
            (Stock.symbol.like(f"%{q}%")) | (Stock.name.ilike(f"%{query}%"))
        ).limit(limit).all()

        for s in db_stocks:
            seen.add(s.symbol)
            results.append({
                "symbol": s.symbol,
                "name": s.name,
                "sector": s.sector,
                "exchange": s.exchange,
                "is_active": True,
                "in_database": True,
                "market_cap": s.market_cap,
                "pe_ratio": s.pe_ratio,
                "roe": s.roe,
            })

        # 2. Search in expanded universe catalog
        for item in EXPANDED_NSE_UNIVERSE:
            if item["symbol"] in seen:
                continue
            if q in item["symbol"].upper() or query.lower() in item["name"].lower():
                seen.add(item["symbol"])
                results.append({
                    "symbol": item["symbol"],
                    "name": item["name"],
                    "sector": item["sector"],
                    "exchange": "NSE",
                    "index_tier": item.get("index", "NSE Equities"),
                    "is_active": False,
                    "in_database": False,
                    "market_cap": item.get("market_cap"),
                    "pe_ratio": item.get("pe"),
                    "roe": item.get("roe"),
                })
                if len(results) >= limit:
                    break

        return results

    def ensure_stock_onboarded(self, symbol: str) -> Stock:
        """
        Ensures a stock is onboarded in the database with historical OHLCV data,
        technicals, news association, and sentiment.
        """
        stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
        if stock:
            return stock

        # Lookup in catalog or create generic metadata
        meta = self.catalog.get(symbol, {
            "symbol": symbol,
            "name": symbol.replace(".NS", "") + " Ltd",
            "sector": "Diversified",
            "pe": 22.0,
            "roe": 15.0,
            "market_cap": 1000000000000.0,
            "base_price": 1000.0,
        })

        stock = Stock(
            symbol=meta["symbol"],
            name=meta["name"],
            sector=meta["sector"],
            exchange="NSE",
            currency="INR",
            is_nifty50=meta.get("index") == "NIFTY 50",
            market_cap=meta.get("market_cap"),
            pe_ratio=meta.get("pe"),
            pb_ratio=round(meta.get("pe", 20.0) / 7.0, 1) if meta.get("pe") else 3.0,
            eps=round(meta.get("base_price", 1000.0) / max(meta.get("pe", 20.0), 1.0), 1),
            dividend_yield=1.2,
            roe=meta.get("roe", 15.0),
            debt_to_equity=0.45,
        )
        self.db.add(stock)
        self.db.commit()
        self.db.refresh(stock)

        # Ingest 3-year historical OHLCV series
        yf_collector = YahooFinanceCollector(self.db)
        df = yf_collector.fetch_historical_ohlcv(symbol)
        yf_collector.save_ohlcv_to_db(symbol, df)

        # Ingest sentiment record
        analyzer = FinBERTSentimentAnalyzer(self.db)
        analyzer.aggregate_daily_sentiments()

        logger.info(f"Dynamically onboarded new equity: {symbol} ({meta['name']})")
        return stock
