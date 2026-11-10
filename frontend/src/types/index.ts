export interface Stock {
  id: number;
  symbol: string;
  name: string;
  sector: string;
  industry: string;
  exchange: string;
  currency: string;
  market_cap?: number;
  pe_ratio?: number;
  pb_ratio?: number;
  eps?: number;
  dividend_yield?: number;
  roe?: number;
  debt_to_equity?: number;
}

export interface StockDetail extends Stock {
  current_price: number | null;
  last_updated: string | null;
  returns_1d: number;
  volatility_20d: number;
}

export interface OHLCVRecord {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  adj_close: number;
  volume: number;
  returns_1d: number;
}

export interface StockRecommendation {
  symbol: string;
  name: string;
  sector: string;
  current_price: number;
  price_timestamp: string;
  prediction_horizon_days: number;
  predicted_direction: string;
  signal: string;
  composite_score: number;
  model_probability: number;
  model_name: string;
  sentiment_score: number;
  sentiment_momentum: number;
  risk_score: number;
  fundamentals: {
    pe_ratio?: number;
    pb_ratio?: number;
    eps?: number;
    dividend_yield?: number;
    roe?: number;
    debt_to_equity?: number;
    market_cap?: number;
  };
  supporting_news: Array<{
    headline: string;
    source: string;
    url: string;
    published_at: string;
  }>;
  explanation: string;
}

export interface SentimentOverview {
  market_sentiment_score: number;
  market_sentiment_label: string;
  top_positive: Array<{
    symbol: string;
    name: string;
    sector: string;
    sentiment_score: number;
    sentiment_momentum: number;
    article_count: number;
  }>;
  top_negative: Array<{
    symbol: string;
    name: string;
    sector: string;
    sentiment_score: number;
    sentiment_momentum: number;
    article_count: number;
  }>;
  all_stocks: Array<any>;
}

export interface MLModelLeaderboardItem {
  id: number;
  model_id: string;
  model_name: string;
  target_type: string;
  horizon_days: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number;
  mcc: number;
  strategy_sharpe: number;
  strategy_drawdown: number;
  win_rate: number;
  created_at: string;
}

export interface BacktestResult {
  symbol: string;
  strategy: string;
  horizon_days: number;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_equity: number;
  total_return_pct: number;
  benchmark_return_pct: number;
  annualized_return_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown_pct: number;
  win_rate_pct: number;
  profit_factor: number;
  total_trades: number;
  trades: Array<{
    date: string;
    action: string;
    price: number;
    shares: number;
    cost?: number;
    proceeds?: number;
  }>;
  equity_curve: Array<{
    date: string;
    portfolio: number;
    benchmark: number;
    drawdown_pct: number;
  }>;
}

export interface PortfolioSimulationResult {
  initial_capital: number;
  horizon_days: number;
  annualized_return_pct: number;
  annualized_volatility_pct: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  diversification_score: number;
  allocations: Array<{
    symbol: string;
    weight_pct: number;
    allocated_amount: number;
    sector: string;
  }>;
  sector_breakdown: Array<{
    sector: string;
    weight: number;
  }>;
  scenario_projections: Array<{
    day: number;
    expected: number;
    optimistic: number;
    pessimistic: number;
  }>;
  projected_outcomes: {
    expected_final: number;
    optimistic_final: number;
    pessimistic_final: number;
  };
}

export interface RAGCitation {
  source: string;
  timestamp: string;
  datapoints: string;
}

export interface RAGResponse {
  query: string;
  answer: string;
  citations: RAGCitation[];
}

