"""
Comprehensive Structured Financial Knowledge Base for SENTIMENT-APLHA.
Covers core concepts: Stock market fundamentals, NSE & NIFTY, IPOs, Equity,
Mutual Funds, ETFs, P/E, EPS, Market Cap, Fundamental Analysis, Technical Analysis,
Risk Management, Portfolio Diversification, and Investment Terminology.
"""

from typing import Dict, List, Any

FINANCIAL_KNOWLEDGE_DOCS: List[Dict[str, Any]] = [
    {
        "id": "kb_nse_nifty",
        "title": "NSE & NIFTY 50 Index Fundamentals",
        "category": "Market Fundamentals",
        "keywords": ["nse", "nifty", "nifty 50", "national stock exchange", "index", "benchmark", "derivatives"],
        "content": (
            "The National Stock Exchange of India (NSE) is India's leading financial exchange, incorporated in 1992 and "
            "commencing operations in 1994 as the first demutualized electronic exchange in the country. "
            "The NIFTY 50 is the benchmark stock market index representing the weighted average of 50 of the largest "
            "and most liquid Indian companies listed on the NSE across 13 sectors. "
            "The NIFTY 50 uses the free-float market capitalization methodology, meaning index weight is proportional to "
            "shares available for public trading rather than total shares issued. "
            "It serves as the premier barometer of the Indian economy and underpins global ETF and derivatives volume."
        )
    },
    {
        "id": "kb_pe_eps",
        "title": "Price-to-Earnings (P/E) Ratio and Earnings Per Share (EPS)",
        "category": "Valuation Metrics",
        "keywords": ["pe", "pe ratio", "p/e", "eps", "earnings per share", "valuation", "trailing pe", "forward pe"],
        "content": (
            "Earnings Per Share (EPS) represents a company's net profit divided by the total number of outstanding common shares: "
            "EPS = (Net Income - Preferred Dividends) / End-of-period Shares. Diluted EPS factors in convertible securities and options.\n"
            "The Price-to-Earnings (P/E) ratio measures the price investors pay for each rupee of annual earnings: "
            "P/E = Current Share Price / EPS. "
            "Trailing P/E uses EPS from the past 12 months (TTM), whereas Forward P/E uses projected consensus analyst earnings. "
            "A high P/E indicates elevated market growth expectations, whereas a low P/E may signify either an undervalued bargain "
            "or structural deterioration (value trap). Comparisons should always be made against sector peers and historical medians."
        )
    },
    {
        "id": "kb_market_cap",
        "title": "Market Capitalization and Classification",
        "category": "Market Structure",
        "keywords": ["market cap", "market capitalization", "large cap", "mid cap", "small cap", "sebi categorization"],
        "content": (
            "Market Capitalization is the total market value of a publicly traded company's outstanding equity shares: "
            "Market Cap = Current Market Price * Total Outstanding Shares.\n"
            "Under SEBI (Securities and Exchange Board of India) categorization:\n"
            "- Large Cap: Top 100 companies by market cap (e.g. Reliance, TCS, HDFC Bank). Typically blue-chip, highly liquid, lower volatility.\n"
            "- Mid Cap: 101st to 250th companies by market cap. Higher growth potential with moderate risk.\n"
            "- Small Cap: 251st company onwards. Highest potential growth but significant liquidity and drawdown risk."
        )
    },
    {
        "id": "kb_fundamental_analysis",
        "title": "Fundamental Analysis: Financial Statements and Return Ratios",
        "category": "Analysis",
        "keywords": ["fundamental analysis", "balance sheet", "income statement", "cash flow", "roe", "roce", "debt to equity", "free cash flow"],
        "content": (
            "Fundamental analysis assesses a business's intrinsic economic value by scrutinizing financial statements:\n"
            "1. Income Statement: Revenue, operating margins (EBITDA), Net Profit Margin, and EPS progression.\n"
            "2. Balance Sheet: Assets, liabilities, working capital, and leverage. Debt-to-Equity = Total Debt / Shareholder Equity (under 0.5 is conservative).\n"
            "3. Cash Flow Statement: Operating Cash Flow (OCF) versus Net Profit. Free Cash Flow (FCF = OCF - CapEx) indicates real distributable cash.\n"
            "4. Return on Equity (ROE): Net Income / Shareholder Equity. Measures how efficiently shareholder capital generates profit (target > 15%).\n"
            "5. Return on Capital Employed (ROCE): EBIT / (Total Assets - Current Liabilities). Evaluates total capital efficiency."
        )
    },
    {
        "id": "kb_technical_analysis",
        "title": "Technical Analysis & Key Indicators (RSI, MACD, Moving Averages)",
        "category": "Analysis",
        "keywords": ["technical analysis", "rsi", "macd", "moving averages", "bollinger bands", "sma", "ema", "support", "resistance"],
        "content": (
            "Technical analysis studies price action, volume, and chart patterns to identify supply/demand imbalances:\n"
            "- Moving Averages: Simple (SMA) and Exponential (EMA). The 50-day and 200-day moving averages define primary trend direction. A Golden Cross (50 EMA crosses above 200 EMA) is bullish.\n"
            "- Relative Strength Index (RSI): Momentum oscillator bounded between 0 and 100. Values above 70 indicate overbought conditions; values below 30 indicate oversold conditions.\n"
            "- MACD (Moving Average Convergence Divergence): Difference between 12-period and 26-period EMAs plotted with a 9-period signal line. Signal line crossovers show momentum shifts.\n"
            "- Bollinger Bands: 20-period SMA flanked by +/- 2 standard deviations. Volatility contraction (squeeze) often precedes breakout expansions."
        )
    },
    {
        "id": "kb_ipos",
        "title": "Initial Public Offerings (IPOs) in the Indian Market",
        "category": "Capital Markets",
        "keywords": ["ipo", "initial public offering", "drhp", "rhp", "listing", "anchor investor", "retail quota"],
        "content": (
            "An Initial Public Offering (IPO) is the process by which a privately held corporation offers shares to the public to raise equity capital. "
            "In India, companies file a Draft Red Herring Prospectus (DRHP) with SEBI for regulatory approval, followed by the final RHP stating the price band. "
            "Tranches are allocated among Qualified Institutional Buyers (QIB - 50%), Non-Institutional Investors (NII/HNI - 15%), and Retail Individual Investors (RII - 35%). "
            "Anchor investors commit capital one day prior to public opening. Listing day trading determines initial market price discovery. "
            "Investors must evaluate prospectus use of proceeds, promoter pedigree, offer for sale (OFS) vs fresh issue ratio, and post-listing valuation."
        )
    },
    {
        "id": "kb_mutual_funds_etfs",
        "title": "Mutual Funds, ETFs, and Systematic Investment Plans (SIP)",
        "category": "Investment Vehicles",
        "keywords": ["mutual funds", "etf", "exchange traded funds", "sip", "nav", "passive investing", "expense ratio"],
        "content": (
            "Mutual Funds pool capital from numerous investors to invest in a diversified portfolio of securities managed by an Asset Management Company (AMC):\n"
            "- Active Funds: Fund managers pick securities aiming to beat a benchmark; carry higher Total Expense Ratios (TER 1.0% - 2.25%).\n"
            "- Index Funds & ETFs (Exchange Traded Funds): Passively replicate an index (e.g. NIFTY 50 via NIFTYBEES) with minimal expense ratios (0.05% - 0.20%). ETFs trade continuously on stock exchanges at live market prices, unlike mutual funds which settle at end-of-day NAV.\n"
            "- Systematic Investment Plan (SIP): Automated periodic investment (monthly/quarterly) that enforces rupee cost averaging, reducing timing risk over multi-year horizons."
        )
    },
    {
        "id": "kb_risk_management",
        "title": "Quantitative Risk Management & Capital Preservation",
        "category": "Risk Management",
        "keywords": ["risk management", "stop loss", "position sizing", "drawdown", "max drawdown", "var", "risk reward"],
        "content": (
            "Capital preservation is the bedrock of quantitative investing. Core risk principles include:\n"
            "1. Position Sizing: Never allocate more than 2% to 5% of total portfolio equity to any single speculative position.\n"
            "2. Stop-Loss Orders: Predetermined price threshold where a losing position is automatically closed to prevent catastrophic capital impairment.\n"
            "3. Risk-to-Reward Ratio: Target setups with at least 1:2 or 1:3 risk-to-reward (risking ₹1 to gain ₹2 to ₹3).\n"
            "4. Maximum Drawdown (MDD): The peak-to-trough decline during a specific period. Lower drawdown protects compounding velocity.\n"
            "5. Volatility & Beta: Beta measures sensitivity relative to the NIFTY 50 (Beta > 1 is higher volatility; Beta < 1 is defensive)."
        )
    },
    {
        "id": "kb_diversification",
        "title": "Portfolio Diversification & Asset Allocation",
        "category": "Portfolio Theory",
        "keywords": ["diversification", "asset allocation", "correlation", "core satellite", "rebalancing", "modern portfolio theory"],
        "content": (
            "Modern Portfolio Theory (Harry Markowitz) demonstrates that combining non-correlated assets reduces overall portfolio risk without sacrificing expected return:\n"
            "- Asset Classes: Equities (capital appreciation), Debt/Fixed Income (capital preservation & cashflow), Gold/Commodities (inflation hedge), Cash equivalents (liquidity).\n"
            "- Sector Diversification: Limiting single sector exposure (e.g. IT, Banking, Auto, Pharma) to under 25% prevents systemic sector shocks.\n"
            "- Core-Satellite Framework: 70-80% in low-cost index ETFs or blue-chips (Core), 20-30% in high-conviction thematic or quantitative momentum strategies (Satellite).\n"
            "- Annual Rebalancing: Periodically trimming winning overweighted assets to re-enter underweighted assets locks in profits and maintains target risk tolerances."
        )
    },
    {
        "id": "kb_terminology",
        "title": "Essential Financial & Stock Market Terminology",
        "category": "Glossary",
        "keywords": ["terminology", "alpha", "beta", "sharpe ratio", "bull market", "bear market", "liquidity", "circuit breaker"],
        "content": (
            "Crucial market vocabulary for investors:\n"
            "- Alpha: The excess return generated by an active strategy or stock over its benchmark index after adjusting for risk.\n"
            "- Beta: Measure of systematic risk or volatility compared to the benchmark index (NIFTY 50 has a Beta of 1.0).\n"
            "- Sharpe Ratio: (Portfolio Return - Risk-Free Rate) / Portfolio Standard Deviation. Measures risk-adjusted excess return (Sharpe > 1.0 is good, > 1.5 is excellent).\n"
            "- Bull Market: Sustained period of rising asset prices and positive economic sentiment (typically >20% gain from troughs).\n"
            "- Bear Market: Prolonged price decline (>20% drop from recent peaks) accompanied by widespread pessimism.\n"
            "- Circuit Breakers: Coordinated exchange-wide trading halts (10%, 15%, 20% index movements) designed to prevent disorderly panic selling."
        )
    }
]


def search_knowledge_base(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Retrieves the most relevant financial knowledge documents matching query keywords.
    """
    q_tokens = set(query.lower().split())
    scored = []

    for doc in FINANCIAL_KNOWLEDGE_DOCS:
        score = 0
        doc_text = f"{doc['title']} {doc['category']} {' '.join(doc['keywords'])} {doc['content']}".lower()

        for token in q_tokens:
            if len(token) <= 2:
                continue
            if token in doc['keywords']:
                score += 5
            elif token in doc['title'].lower():
                score += 3
            elif token in doc_text:
                score += 1

        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]

