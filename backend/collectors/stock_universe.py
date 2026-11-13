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
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries Ltd", "sector": "Energy", "index": "NIFTY 50", "pe": 24.8, "roe": 9.2, "market_cap": 17200000000000.0, "base_price": 1339.70},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services Ltd", "sector": "Information Technology", "index": "NIFTY 50", "pe": 29.5, "roe": 48.5, "market_cap": 15100000000000.0, "base_price": 4145.00},
    {"symbol": "INFY.NS", "name": "Infosys Ltd", "sector": "Information Technology", "index": "NIFTY 50", "pe": 25.2, "roe": 31.4, "market_cap": 7800000000000.0, "base_price": 1865.00},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Ltd", "sector": "Financial Services", "index": "NIFTY 50", "pe": 18.6, "roe": 15.8, "market_cap": 13300000000000.0, "base_price": 1748.00},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank Ltd", "sector": "Financial Services", "index": "NIFTY 50", "pe": 17.8, "roe": 18.2, "market_cap": 8900000000000.0, "base_price": 1268.00},
    {"symbol": "TATAMOTORS.NS", "name": "Tata Motors Ltd", "sector": "Automobile", "index": "NIFTY 50", "pe": 15.4, "roe": 26.5, "market_cap": 2900000000000.0, "base_price": 788.00},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "sector": "Financial Services", "index": "NIFTY 50", "pe": 10.8, "roe": 16.9, "market_cap": 7300000000000.0, "base_price": 818.00},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel Ltd", "sector": "Telecommunication", "index": "NIFTY 50", "pe": 48.2, "roe": 19.4, "market_cap": 9400000000000.0, "base_price": 1585.00},
    {"symbol": "ITC.NS", "name": "ITC Ltd", "sector": "Consumer Goods", "index": "NIFTY 50", "pe": 26.8, "roe": 29.8, "market_cap": 5900000000000.0, "base_price": 472.50},
    {"symbol": "LT.NS", "name": "Larsen & Toubro Ltd", "sector": "Capital Goods", "index": "NIFTY 50", "pe": 36.2, "roe": 14.5, "market_cap": 4900000000000.0, "base_price": 3585.00},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank Ltd", "sector": "Financial Services", "index": "NIFTY 50", "pe": 21.4, "roe": 14.2, "market_cap": 3600000000000.0, "base_price": 1780.00},
    {"symbol": "AXISBANK.NS", "name": "Axis Bank Ltd", "sector": "Financial Services", "index": "NIFTY 50", "pe": 13.9, "roe": 16.1, "market_cap": 3500000000000.0, "base_price": 1150.00},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever Ltd", "sector": "Consumer Goods", "index": "NIFTY 50", "pe": 54.2, "roe": 20.3, "market_cap": 5700000000000.0, "base_price": 2420.00},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance Ltd", "sector": "Financial Services", "index": "NIFTY 50", "pe": 28.6, "roe": 22.1, "market_cap": 4300000000000.0, "base_price": 6950.00},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki India Ltd", "sector": "Automobile", "index": "NIFTY 50", "pe": 27.4, "roe": 16.8, "market_cap": 3700000000000.0, "base_price": 11800.00},
    {"symbol": "SUNPHARMA.NS", "name": "Sun Pharmaceutical Industries Ltd", "sector": "Healthcare", "index": "NIFTY 50", "pe": 35.8, "roe": 15.6, "market_cap": 4200000000000.0, "base_price": 1780.00},
    {"symbol": "TITAN.NS", "name": "Titan Company Ltd", "sector": "Consumer Discretionary", "index": "NIFTY 50", "pe": 82.5, "roe": 31.2, "market_cap": 2980000000000.0, "base_price": 3350.00},
    {"symbol": "TATASTEEL.NS", "name": "Tata Steel Ltd", "sector": "Metals & Mining", "index": "NIFTY 50", "pe": 42.1, "roe": 4.8, "market_cap": 1800000000000.0, "base_price": 145.00},
    {"symbol": "ASIANPAINT.NS", "name": "Asian Paints Ltd", "sector": "Consumer Discretionary", "index": "NIFTY 50", "pe": 52.4, "roe": 24.5, "market_cap": 2400000000000.0, "base_price": 2520.00},
    {"symbol": "NTPC.NS", "name": "NTPC Ltd", "sector": "Utilities", "index": "NIFTY 50", "pe": 18.2, "roe": 13.9, "market_cap": 3700000000000.0, "base_price": 385.00},
    {"symbol": "POWERGRID.NS", "name": "Power Grid Corporation of India", "sector": "Utilities", "index": "NIFTY 50", "pe": 19.5, "roe": 19.8, "market_cap": 2980000000000.0, "base_price": 320.00},
    {"symbol": "M&M.NS", "name": "Mahindra & Mahindra Ltd", "sector": "Automobile", "index": "NIFTY 50", "pe": 29.8, "roe": 18.5, "market_cap": 3500000000000.0, "base_price": 2920.00},
    {"symbol": "WIPRO.NS", "name": "Wipro Ltd", "sector": "Information Technology", "index": "NIFTY 50", "pe": 21.0, "roe": 15.2, "market_cap": 2900000000000.0, "base_price": 560.00},
    {"symbol": "ADANIENT.NS", "name": "Adani Enterprises Ltd", "sector": "Metals & Mining", "index": "NIFTY 50", "pe": 95.0, "roe": 8.5, "market_cap": 3350000000000.0, "base_price": 2950.00},
    {"symbol": "ADANIPORTS.NS", "name": "Adani Ports and Special Economic Zone", "sector": "Services", "index": "NIFTY 50", "pe": 34.2, "roe": 17.5, "market_cap": 2750000000000.0, "base_price": 1280.00},

    # --- NIFTY NEXT 50 High-Growth Equities ---
    {"symbol": "ZOMATO.NS", "name": "Zomato Ltd", "sector": "Consumer Services", "index": "NIFTY NEXT 50", "pe": 115.0, "roe": 7.4, "market_cap": 2350000000000.0, "base_price": 265.00},
    {"symbol": "JIOFIN.NS", "name": "Jio Financial Services Ltd", "sector": "Financial Services", "index": "NIFTY NEXT 50", "pe": 135.0, "roe": 1.2, "market_cap": 2000000000000.0, "base_price": 315.00},
    {"symbol": "HAL.NS", "name": "Hindustan Aeronautics Ltd", "sector": "Capital Goods", "index": "NIFTY NEXT 50", "pe": 38.5, "roe": 26.2, "market_cap": 2900000000000.0, "base_price": 4350.00},
    {"symbol": "BEL.NS", "name": "Bharat Electronics Ltd", "sector": "Capital Goods", "index": "NIFTY NEXT 50", "pe": 48.0, "roe": 24.5, "market_cap": 2080000000000.0, "base_price": 285.00},
    {"symbol": "TRENT.NS", "name": "Trent Ltd", "sector": "Consumer Discretionary", "index": "NIFTY NEXT 50", "pe": 140.0, "roe": 28.5, "market_cap": 2360000000000.0, "base_price": 6650.00},
    {"symbol": "VBL.NS", "name": "Varun Beverages Ltd", "sector": "Consumer Goods", "index": "NIFTY NEXT 50", "pe": 72.0, "roe": 33.1, "market_cap": 2000000000000.0, "base_price": 615.00},
    {"symbol": "VEDL.NS", "name": "Vedanta Ltd", "sector": "Metals & Mining", "index": "NIFTY NEXT 50", "pe": 14.2, "roe": 28.0, "market_cap": 1720000000000.0, "base_price": 445.00},
    {"symbol": "DLF.NS", "name": "DLF Ltd", "sector": "Realty", "index": "NIFTY NEXT 50", "pe": 65.0, "roe": 8.4, "market_cap": 2020000000000.0, "base_price": 815.00},
    {"symbol": "CHOLAFIN.NS", "name": "Cholamandalam Investment and Finance", "sector": "Financial Services", "index": "NIFTY NEXT 50", "pe": 32.5, "roe": 20.1, "market_cap": 1160000000000.0, "base_price": 1380.00},
    {"symbol": "TVSMOTOR.NS", "name": "TVS Motor Company Ltd", "sector": "Automobile", "index": "NIFTY NEXT 50", "pe": 54.0, "roe": 29.5, "market_cap": 1160000000000.0, "base_price": 2450.00},

    # --- NIFTY 100 / 200 / 500 Leaders ---
    {"symbol": "PAYTM.NS", "name": "One97 Communications Ltd (Paytm)", "sector": "Financial Services", "index": "NIFTY 500", "pe": None, "roe": -12.5, "market_cap": 528000000000.0, "base_price": 830.00},
    {"symbol": "MRF.NS", "name": "MRF Ltd", "sector": "Automobile", "index": "NIFTY 200", "pe": 26.5, "roe": 13.8, "market_cap": 560000000000.0, "base_price": 132000.00},
    {"symbol": "IRCTC.NS", "name": "Indian Railway Catering and Tourism Corp", "sector": "Services", "index": "NIFTY 200", "pe": 62.0, "roe": 41.5, "market_cap": 670000000000.0, "base_price": 840.00},
    {"symbol": "POLYCAB.NS", "name": "Polycab India Ltd", "sector": "Capital Goods", "index": "NIFTY 200", "pe": 52.0, "roe": 22.4, "market_cap": 970000000000.0, "base_price": 6450.00},
    {"symbol": "DIXON.NS", "name": "Dixon Technologies (India) Ltd", "sector": "Consumer Durables", "index": "NIFTY 200", "pe": 110.0, "roe": 29.8, "market_cap": 850000000000.0, "base_price": 14200.00},
    {"symbol": "SUZLON.NS", "name": "Suzlon Energy Ltd", "sector": "Capital Goods", "index": "NIFTY 500", "pe": 68.0, "roe": 18.2, "market_cap": 845000000000.0, "base_price": 62.00},
    {"symbol": "^NSEI", "name": "NIFTY 50 Benchmark Index", "sector": "Index", "index": "Benchmark", "pe": 22.4, "roe": 16.0, "market_cap": 180000000000000.0, "base_price": 24148.00},
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
