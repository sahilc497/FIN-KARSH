import axios from 'axios';

export const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export const api = {
  // Stocks & Universe
  getStocks: async () => (await apiClient.get('/stocks/')).data,
  searchStocks: async (q: string) => (await apiClient.get('/stocks/search', { params: { q } })).data,
  onboardStock: async (symbol: string) => (await apiClient.post(`/stocks/onboard/${symbol}`)).data,
  syncLivePrices: async () => (await apiClient.post('/stocks/sync-live')).data,
  getStockDetail: async (symbol: string) => (await apiClient.get(`/stocks/${symbol}`)).data,
  getHistoricalOHLCV: async (symbol: string, limit = 180) =>
    (await apiClient.get(`/stocks/${symbol}/ohlcv`, { params: { limit } })).data,

  // Sentiment (News + Reddit Separated)
  getSentimentOverview: async () => (await apiClient.get('/sentiment/overview')).data,
  getSentimentComparison: async () => (await apiClient.get('/sentiment/comparison')).data,
  getRedditTrends: async (limit = 10) => (await apiClient.get('/sentiment/reddit/trends', { params: { limit } })).data,
  getFinancialNews: async (symbol?: string, limit = 20) =>
    (await apiClient.get('/sentiment/news', { params: { symbol, limit } })).data,
  getRedditDiscussions: async (limit = 20, symbol?: string) =>
    (await apiClient.get('/sentiment/reddit', { params: { limit, symbol } })).data,
  syncReddit: async () => (await apiClient.post('/sentiment/reddit/sync')).data,
  analyzeText: async (text: string) => (await apiClient.post('/sentiment/analyze-text', { text })).data,

  // Live Market Snapshot
  getLiveMarketSnapshot: async () => (await apiClient.get('/market/live-snapshot')).data,

  // ML Models
  getModelLeaderboard: async (symbol?: string, horizon_days = 5) =>
    (await apiClient.get('/models/leaderboard', { params: { symbol, horizon_days } })).data,
  getModelDetails: async (modelId: string) => (await apiClient.get(`/models/${modelId}`)).data,
  trainModels: async (symbol: string, horizon_days = 5) =>
    (await apiClient.post('/models/train', { symbol, horizon_days })).data,

  // Recommendations & Watchlist
  getRecommendations: async (horizon_days = 5) =>
    (await apiClient.get('/recommendations/', { params: { horizon_days } })).data,
  getStockRecommendation: async (symbol: string, horizon_days = 5) =>
    (await apiClient.get(`/recommendations/${symbol}`, { params: { horizon_days } })).data,
  getWatchlist: async () => (await apiClient.get('/recommendations/watchlist/all')).data,
  addToWatchlist: async (symbol: string, target_price?: number, notes?: string) =>
    (await apiClient.post('/recommendations/watchlist/add', { symbol, target_price, notes })).data,
  removeFromWatchlist: async (symbol: string) =>
    (await apiClient.delete(`/recommendations/watchlist/${symbol}`)).data,

  // Backtest
  runBacktest: async (payload: {
    symbol: string;
    initial_capital: number;
    horizon_days: number;
    strategy: string;
    fee_pct: number;
    slippage_pct: number;
  }) => (await apiClient.post('/backtest/run', payload)).data,
  getBacktestHistory: async (symbol?: string) =>
    (await apiClient.get('/backtest/history', { params: { symbol } })).data,

  // Portfolio
  simulatePortfolio: async (payload: {
    capital: number;
    allocations: Array<{ symbol: string; weight: number }>;
    horizon_days: number;
  }) => (await apiClient.post('/portfolio/simulate', payload)).data,

  // RAG / Gemini Assistant
  queryAssistant: async (prompt: string) =>
    (await apiClient.post('/assistant/query', { prompt })).data,
  getExamplePrompts: async () => (await apiClient.get('/assistant/prompts')).data,
  getAssistantStatus: async () => (await apiClient.get('/assistant/status')).data,

  // Health
  getSystemHealth: async () => (await apiClient.get('/health/')).data,
};
