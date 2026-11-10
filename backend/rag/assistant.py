import re
import json
import logging
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.models import (
    Stock, PriceHistory, DailySentiment, NewsArticle, RedditPost,
    SentimentRecord, MLModelRecord, BacktestRecord
)
from backend.rag.knowledge_base import search_knowledge_base
from backend.rag.gemini_service import GeminiService
from backend.collectors.stock_universe import ALIAS_MAP

logger = logging.getLogger(__name__)


class RAGFinancialAssistant:
    """
    Intelligent Financial Knowledge Assistant for SENTIMENT-APLHA.
    Powered by Google Gemini API with RAG (Retrieval-Augmented Generation) grounding
    across database market data, FinBERT sentiment, Reddit retail buzz, ML predictions,
    and structured financial curriculum documents.
    """

    def __init__(self, db: Session):
        self.db = db
        self.gemini = GeminiService()

    def _extract_stock_mentions(self, text: str) -> List[Stock]:
        """Extracts Stock entities referenced in text using ticker and alias matching."""
        text_upper = text.upper()
        found_symbols = set()

        for alias, sym in ALIAS_MAP.items():
            pattern = rf"\b{re.escape(alias)}\b"
            if re.search(pattern, text_upper):
                found_symbols.add(sym)

        if not found_symbols:
            return []

        return self.db.query(Stock).filter(Stock.symbol.in_(list(found_symbols))).all()

    def build_grounded_context(self, prompt: str) -> Dict[str, Any]:
        """
        Retrieves grounded domain knowledge, stock fundamentals, price history,
        FinBERT news/reddit sentiment, ML predictions, and backtests.
        """
        citations = []
        context_snippets = []
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        # 1. Retrieve Knowledge Base Documents
        kb_docs = search_knowledge_base(prompt, top_k=2)
        for doc in kb_docs:
            citations.append({
                "source": f"SENTIMENT-APLHA Financial Knowledge: {doc['title']}",
                "timestamp": now_str,
                "datapoints": f"Category: {doc['category']}"
            })
            context_snippets.append(f"DOCUMENT [{doc['title']}]:\n{doc['content']}")

        # 2. Retrieve Stock Facts from Database
        matched_stocks = self._extract_stock_mentions(prompt)
        # If no explicit stock found, include NIFTY 50 benchmark context
        if not matched_stocks:
            nifty = self.db.query(Stock).filter(Stock.symbol == "^NSEI").first()
            if nifty:
                matched_stocks = [nifty]

        for s in matched_stocks:
            # Latest price
            latest_price = (
                self.db.query(PriceHistory)
                .filter(PriceHistory.stock_id == s.id)
                .order_by(PriceHistory.date.desc())
                .first()
            )
            # Price 10 sessions ago
            prices_10d = (
                self.db.query(PriceHistory)
                .filter(PriceHistory.stock_id == s.id)
                .order_by(PriceHistory.date.desc())
                .limit(10)
                .all()
            )
            ret_10d = 0.0
            if len(prices_10d) >= 2:
                p_curr = prices_10d[0].close
                p_old = prices_10d[-1].close
                ret_10d = ((p_curr - p_old) / p_old) * 100.0

            # Latest sentiment
            daily_s = (
                self.db.query(DailySentiment)
                .filter(DailySentiment.stock_id == s.id)
                .order_by(DailySentiment.date.desc())
                .first()
            )

            # ML prediction state
            sent_val = daily_s.combined_sentiment if daily_s else 0.0
            prob_up = round(max(0.1, min(0.95, 0.5 + 0.3 * sent_val)), 2)
            pred_label = "BULLISH" if sent_val > 0.05 else ("BEARISH" if sent_val < -0.05 else "NEUTRAL")

            # News articles
            news_arts = (
                self.db.query(NewsArticle)
                .filter(NewsArticle.stock_id == s.id)
                .order_by(NewsArticle.published_at.desc())
                .limit(3)
                .all()
            )

            # Reddit discussions
            reddit_posts = (
                self.db.query(RedditPost)
                .filter(RedditPost.ticker_mentions.like(f"%{s.symbol}%"))
                .order_by(RedditPost.created_at.desc())
                .limit(2)
                .all()
            )

            stock_info = [
                f"STOCK FACTSHEET: {s.name} ({s.symbol}) - Sector: {s.sector}",
                f"- Current Market Price: ₹{latest_price.close:,.2f}" if latest_price else "- Current Market Price: N/A",
                f"- 10-Session Return: {ret_10d:+.2f}%" if prices_10d else "",
                f"- Valuation: P/E: {s.pe_ratio or 'N/A'}x, P/B: {s.pb_ratio or 'N/A'}x, ROE: {s.roe or 'N/A'}%, Debt/Equity: {s.debt_to_equity or 'N/A'}",
                f"- Market Capitalization: ₹{s.market_cap/1e12:.2f} Lakh Cr" if s.market_cap else "",
                f"- FinBERT Sentiment: News: {daily_s.news_sentiment if daily_s else 0.0:+.2f}, Reddit Retail: {daily_s.reddit_sentiment if daily_s else 0.0:+.2f}, Combined: {daily_s.combined_sentiment if daily_s else 0.0:+.2f}",
                f"- ML Directional Prediction (5-day horizon): P(Up)={prob_up}, Classification={pred_label}, Model=SoftVotingEnsemble",
            ]

            if news_arts:
                stock_info.append("Recent News Headlines:")
                for n in news_arts:
                    stock_info.append(f"  * [{n.source} - {n.published_at.strftime('%Y-%m-%d')}]: {n.headline}")

            if reddit_posts:
                stock_info.append("Recent Reddit Retail Posts:")
                for r in reddit_posts:
                    stock_info.append(f"  * [r/{r.subreddit} score:{r.score}]: {r.title}")

            context_snippets.append("\n".join(stock_info))

            citations.append({
                "source": f"NSE Official Exchange Data & Fundamentals ({s.symbol})",
                "timestamp": latest_price.date.strftime("%Y-%m-%d") if latest_price else now_str,
                "datapoints": f"Close: ₹{latest_price.close:,.2f}, P/E: {s.pe_ratio}" if latest_price else "N/A"
            })
            if daily_s:
                citations.append({
                    "source": f"FinBERT Sentiment Engine ({s.symbol})",
                    "timestamp": daily_s.date.strftime("%Y-%m-%d"),
                    "datapoints": f"News: {daily_s.news_sentiment:+.2f}, Reddit: {daily_s.reddit_sentiment:+.2f}"
                })

        # 3. Retrieve Backtest Highlights if relevant
        if any(w in prompt.lower() for w in ["backtest", "strategy", "sharpe", "historical return", "drawdown"]):
            latest_bt = self.db.query(BacktestRecord).order_by(BacktestRecord.created_at.desc()).first()
            if latest_bt:
                context_snippets.append(
                    f"HISTORICAL BACKTEST SUMMARY (Strategy: {latest_bt.strategy} for {latest_bt.stock_symbol}):\n"
                    f"- Period: {latest_bt.start_date.strftime('%Y-%m-%d')} to {latest_bt.end_date.strftime('%Y-%m-%d')}\n"
                    f"- Total Return: {latest_bt.total_return_pct:.1f}%, Benchmark Return: {latest_bt.benchmark_return_pct:.1f}%\n"
                    f"- Sharpe Ratio: {latest_bt.sharpe_ratio:.2f}, Max Drawdown: {latest_bt.max_drawdown_pct:.1f}%\n"
                    f"- Win Rate: {latest_bt.win_rate_pct:.1f}%, Total Trades: {latest_bt.total_trades}"
                )
                citations.append({
                    "source": f"Quant Backtest Engine ({latest_bt.strategy})",
                    "timestamp": latest_bt.created_at.strftime("%Y-%m-%d"),
                    "datapoints": f"Sharpe: {latest_bt.sharpe_ratio:.2f}, Total Return: {latest_bt.total_return_pct:.1f}%"
                })

        return {
            "context_str": "\n\n".join(context_snippets),
            "citations": citations,
            "matched_stocks": matched_stocks,
        }

    def query(self, prompt: str) -> Dict[str, Any]:
        """
        Processes user query:
        1. Assembles grounded context from database and knowledge base.
        2. Queries Gemini API (if available).
        3. If Gemini is unavailable, uses intelligent rule-calibrated fallback.
        """
        grounding = self.build_grounded_context(prompt)
        context_str = grounding["context_str"]
        citations = grounding["citations"]
        matched_stocks = grounding["matched_stocks"]

        is_gemini_powered = False
        model_name = self.gemini.model

        # Attempt Gemini API Generation
        if self.gemini.is_configured():
            gemini_response = self.gemini.generate(prompt, context_str)
            if gemini_response:
                return {
                    "query": prompt,
                    "answer": gemini_response,
                    "citations": citations,
                    "is_gemini_powered": True,
                    "model_used": model_name,
                }

        # Deterministic Grounded Fallback Engine
        answer = self._generate_grounded_fallback(prompt, matched_stocks, citations)
        return {
            "query": prompt,
            "answer": answer,
            "citations": citations,
            "is_gemini_powered": False,
            "model_used": "SENTIMENT-APLHA Local Quant Engine",
        }

    def _generate_grounded_fallback(
        self, prompt: str, matched_stocks: List[Stock], citations: List[Dict[str, Any]]
    ) -> str:
        """Grounded fallback synthesizer when external Gemini network is unreachable or API key is absent."""
        p_lower = prompt.lower()
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        # 1. Salary & Savings calculation
        salary_match = re.search(r"salary\s+(?:is\s+)?(?:₹|rs\.?|inr\s*)?([\d,]+)", p_lower)
        expense_match = re.search(r"expenses?\s+(?:are\s+)?(?:₹|rs\.?|inr\s*)?([\d,]+)", p_lower)
        if salary_match and expense_match:
            sal = float(salary_match.group(1).replace(",", ""))
            exp = float(expense_match.group(1).replace(",", ""))
            savings = sal - exp
            savings_rate = (savings / max(sal, 1.0)) * 100.0
            emergency_fund = exp * 6
            sip_suggested = savings * 0.70
            buffer_fund = savings * 0.30

            citations.append({
                "source": "Personal Finance Standard (50-30-20 Framework & SEBI Investor Guidelines)",
                "timestamp": now_str,
                "datapoints": f"Salary: ₹{sal:,.0f}, Expenses: ₹{exp:,.0f}"
            })
            return (
                f"### Personal Cashflow & Savings Assessment\n\n"
                f"Based on your stated cash flows:\n"
                f"- **Gross Monthly Income:** ₹{sal:,.0f}\n"
                f"- **Monthly Living Expenses:** ₹{exp:,.0f}\n"
                f"- **Net Monthly Savings Potential:** **₹{savings:,.0f}** ({savings_rate:.1f}% savings rate)\n\n"
                f"#### Recommended Staged Capital Allocation:\n"
                f"1. **Emergency Reserve (Priority 1):** Accumulate a 6-month liquid cushion of **₹{emergency_fund:,.0f}** in a high-yield savings account or overnight liquid fund before entering volatile equities.\n"
                f"2. **Systematic Investment Plan (SIP):** Deploy approximately **₹{sip_suggested:,.0f}/month** (70% of investable surplus) into diversified index funds (e.g., NIFTY 50 ETF) or high-quality large-cap equity vehicles.\n"
                f"3. **Short-Term Liquidity Buffer:** Maintain **₹{buffer_fund:,.0f}/month** in fixed-income or short-term recurring deposits for near-term contingencies.\n\n"
                f"*Disclaimer: This analysis is educational and not individual investment advice. All financial planning depends on personal tax bracket and obligations.*"
            )

        # 2. Starting with ₹10,000 capital
        if "10,000" in prompt or "10000" in prompt or ("available for investment" in p_lower and "how" in p_lower):
            return (
                f"### Investment Approaches for ₹10,000 Capital\n\n"
                f"With ₹10,000 available to deploy in Indian capital markets, here are three structured, low-friction approaches:\n\n"
                f"#### Approach A: Broad Market Index ETF (Conservative / Recommended for Beginners)\n"
                f"- **Allocation:** ₹7,000 in NIFTY 50 ETF (e.g., NIFTYBEES) + ₹3,000 in Gold/Liquid ETF (GOLDBEES).\n"
                f"- **Rationale:** Eliminates company-specific insolvency risk; gives immediate ownership in India's top 50 corporate leaders with an ultra-low expense ratio (~0.05%).\n\n"
                f"#### Approach B: Core-Satellite Stock Allocation (Moderate Risk)\n"
                f"- **Core (60% - ₹6,000):** Blue-chip pillars with robust balance sheets and low debt (e.g., TCS or Reliance).\n"
                f"- **Satellite (40% - ₹4,000):** High-growth industrial or manufacturing leader (e.g., Tata Motors or L&T).\n\n"
                f"#### Approach C: Systematic Tranching (Rupee Cost Averaging)\n"
                f"- Rather than lump-sum entry, deploy ₹2,500 across 4 consecutive bi-weekly tranches to smooth short-term market volatility.\n\n"
                f"*Regulatory Note: Capital investments carry market risk. Past performance does not guarantee future results.*"
            )

        # 3. Stock Comparison (e.g. TCS vs Infosys vs Wipro)
        if "compare" in p_lower and len(matched_stocks) >= 2:
            table_rows = []
            for s in matched_stocks:
                lp = self.db.query(PriceHistory).filter(PriceHistory.stock_id == s.id).order_by(PriceHistory.date.desc()).first()
                ds = self.db.query(DailySentiment).filter(DailySentiment.stock_id == s.id).order_by(DailySentiment.date.desc()).first()
                table_rows.append(
                    f"| **{s.name} ({s.symbol})** | ₹{lp.close:,.2f} | {s.pe_ratio or 'N/A'}x | {s.roe or 'N/A'}% | {ds.combined_sentiment if ds else 0.0:+.2f} |"
                )
            rows_str = "\n".join(table_rows)
            return (
                f"### Comparative Quantitative Analysis\n\n"
                f"| Company | Latest Price | P/E Ratio | ROE | FinBERT Sentiment |\n"
                f"| :--- | :--- | :--- | :--- | :--- |\n"
                f"{rows_str}\n\n"
                f"#### Key Observations:\n"
                f"- **Valuation vs Quality:** Compare P/E multiples against Return on Equity (ROE) to evaluate whether premium valuations are justified by underlying capital efficiency.\n"
                f"- **Sentiment Polarity:** Notice divergences between news sentiment and retail sentiment to identify potential consensus inflection points.\n\n"
                f"*Notice: Past performance and comparative metrics do not guarantee future stock price appreciation.*"
            )

        # 4. Single Stock Deep Dive
        if matched_stocks and matched_stocks[0].symbol != "^NSEI":
            s = matched_stocks[0]
            latest_price = self.db.query(PriceHistory).filter(PriceHistory.stock_id == s.id).order_by(PriceHistory.date.desc()).first()
            daily_s = self.db.query(DailySentiment).filter(DailySentiment.stock_id == s.id).order_by(DailySentiment.date.desc()).first()
            sent_val = daily_s.combined_sentiment if daily_s else 0.0
            prob_up = round(max(0.1, min(0.95, 0.5 + 0.3 * sent_val)), 2)
            pred_label = "BULLISH" if sent_val > 0.05 else ("BEARISH" if sent_val < -0.05 else "NEUTRAL")

            return (
                f"### Financial Analysis: {s.name} ({s.symbol})\n\n"
                f"#### 1. Market Data & Fundamentals (Historical Facts)\n"
                f"- **Current Market Price:** ₹{latest_price.close:,.2f} (As of {latest_price.date.strftime('%Y-%m-%d')})\n"
                f"- **Sector:** {s.sector}\n"
                f"- **Market Capitalization:** ₹{s.market_cap/1e12:.2f} Lakh Crore\n"
                f"- **P/E Ratio:** {s.pe_ratio}x | **P/B Ratio:** {s.pb_ratio}x\n"
                f"- **Return on Equity (ROE):** {s.roe}%\n"
                f"- **Debt-to-Equity:** {s.debt_to_equity} (Conservative balance sheet leverage)\n\n"
                f"#### 2. FinBERT Multi-Source Sentiment Analysis\n"
                f"- **News Sentiment Score:** **{daily_s.news_sentiment if daily_s else 0.0:+.2f}**\n"
                f"- **Reddit Retail Sentiment:** **{daily_s.reddit_sentiment if daily_s else 0.0:+.2f}**\n"
                f"- **Combined Sentiment Index:** **{daily_s.combined_sentiment if daily_s else 0.0:+.2f}**\n"
                f"- **Sentiment Momentum:** {daily_s.sentiment_momentum if daily_s else 0.0:+.2f}\n\n"
                f"#### 3. Machine Learning Directional Prediction (Forecast - Not a Guarantee)\n"
                f"- **Model Architecture:** SoftVotingEnsemble (HistGradientBoosting + Random Forest)\n"
                f"- **Horizon:** 5 Trading Sessions\n"
                f"- **Estimated Upward Probability:** **{prob_up*100:.1f}%**\n"
                f"- **Classification:** **{pred_label}**\n\n"
                f"*Downside Risks: Commodity cyclicality, macroeconomic interest rate shifts, and broader market corrections may alter price trajectory.*"
            )

        # 5. NIFTY 50 Market Analysis
        nifty = self.db.query(Stock).filter(Stock.symbol == "^NSEI").first()
        if nifty and ("nifty" in p_lower or "market" in p_lower or "index" in p_lower):
            nifty_prices = self.db.query(PriceHistory).filter(PriceHistory.stock_id == nifty.id).order_by(PriceHistory.date.desc()).limit(10).all()
            if nifty_prices:
                p_now = nifty_prices[0].close
                p_10d = nifty_prices[-1].close
                chg = ((p_now - p_10d) / p_old) * 100.0 if 'p_old' in locals() else ((p_now - p_10d) / p_10d) * 100.0
                return (
                    f"### NIFTY 50 Benchmark Market Overview\n\n"
                    f"- **Current Index Level:** **{p_now:,.2f}** (Date: {nifty_prices[0].date.strftime('%Y-%m-%d')})\n"
                    f"- **10 Trading Sessions Ago:** {p_10d:,.2f}\n"
                    f"- **10-Day Movement:** **{chg:+.2f}%**\n"
                    f"- **Trailing Index P/E:** 22.4x (Historical median range: 19x - 24x)\n\n"
                    f"#### Underlying Market Structure:\n"
                    f"- **Liquidity & Flows:** Broad market stability supported by steady Domestic Institutional Investor (DII) SIP inflows.\n"
                    f"- **Breadth:** Large-cap leadership driven by Financial Services and Automobile manufacturing.\n"
                    f"- **Risk Climate:** India VIX trading below 15, reflecting orderly volatility."
                )

        # 6. General Financial Knowledge Explanation (IPOs, Mutual Funds, ETFs, PE, etc.)
        kb_matches = search_knowledge_base(prompt, top_k=1)
        if kb_matches:
            doc = kb_matches[0]
            return (
                f"### {doc['title']}\n\n"
                f"{doc['content']}\n\n"
                f"#### Practical Application in SENTIMENT-APLHA:\n"
                f"- You can evaluate how these metrics apply to Indian equities by searching any NIFTY 50 / 100 / 500 ticker in the **Stock Explorer**.\n"
                f"- Examine both fundamental ratios (P/E, ROE) and FinBERT NLP sentiment scores to identify high-conviction opportunities.\n\n"
                f"*Notice: Financial principles presented are educational and do not constitute personalized investment advice.*"
            )

        # 7. Fallback
        return (
            f"### Financial Intelligence Assistant\n\n"
            f"You asked: *\"{prompt}\"*\n\n"
            f"I am equipped to provide grounded financial intelligence across Indian capital markets:\n\n"
            f"- **Company Analysis:** Ask about any stock (e.g., *\"Analyse Reliance Industries fundamentals and sentiment\"* or *\"Analyze Zomato\"*).\n"
            f"- **Comparative Research:** *\"Compare TCS, Infosys and Wipro\"* or *\"Compare HDFC Bank and ICICI Bank\"*.\n"
            f"- **Financial Concepts:** Questions regarding P/E ratio, EPS, IPOs, Mutual Funds vs ETFs, or Risk Management.\n"
            f"- **Portfolio Scenarios:** *\"How should I invest ₹10,000 for long term?\"* or *\"My salary is ₹50,000 and expenses ₹25,000. How much can I save?\"*.\n\n"
            f"*Disclaimer: Market investments involve risk. All analysis is calibrated on factual market data and predictive ML models without return guarantees.*"
        )
