import axios from 'axios';
import {
  Stock,
  ArticleListResponse,
  Article,
  PriceBar,
  SentimentFactor,
  ModelRun,
  TradingSignal,
  BacktestRun,
  BacktestTrade,
  PipelineJob,
  SystemStatus,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiClient = {
  // Health & System
  getHealth: async () => (await api.get('/health')).data,
  getSystemStatus: async (): Promise<SystemStatus> => (await api.get('/system/status')).data,

  // Stocks
  getStocks: async (activeOnly: boolean = true): Promise<Stock[]> =>
    (await api.get('/stocks', { params: { active_only: activeOnly } })).data,
  
  getStock: async (symbol: string): Promise<Stock> =>
    (await api.get(`/stocks/${symbol}`)).data,

  getStockPrices: async (symbol: string, limit: number = 180): Promise<PriceBar[]> =>
    (await api.get(`/stocks/${symbol}/prices`, { params: { limit } })).data,

  getStockFactors: async (symbol: string, limit: number = 180): Promise<SentimentFactor[]> =>
    (await api.get(`/stocks/${symbol}/factors`, { params: { limit } })).data,

  // News
  getNews: async (params: {
    page?: number;
    page_size?: number;
    symbol?: string;
    sentiment?: string;
    source?: string;
    search?: string;
  }): Promise<ArticleListResponse> => (await api.get('/news', { params })).data,

  getArticle: async (id: number): Promise<Article> =>
    (await api.get(`/news/${id}`)).data,

  // Sentiment Overview
  getSentimentOverview: async () => (await api.get('/sentiment/overview')).data,
  getStockSentimentDetail: async (symbol: string) =>
    (await api.get(`/sentiment/stocks/${symbol}`)).data,

  // Pipeline Jobs
  triggerIngestion: async (): Promise<{ job_id: string; message: string; status: string }> =>
    (await api.post('/pipeline/ingest')).data,

  triggerSentimentAnalysis: async (limit: number = 100): Promise<{ job_id: string; message: string; status: string }> =>
    (await api.post('/pipeline/analyze-sentiment', null, { params: { limit } })).data,

  getJob: async (jobId: string): Promise<PipelineJob> =>
    (await api.get(`/pipeline/jobs/${jobId}`)).data,

  listJobs: async (limit: number = 20): Promise<PipelineJob[]> =>
    (await api.get('/pipeline/jobs', { params: { limit } })).data,

  // Machine Learning
  trainModel: async (params: {
    model_type: string;
    target_horizon: number;
    features?: string[];
    test_size?: number;
    purge_overlap?: boolean;
  }): Promise<{ job_id: string; message: string; status: string }> =>
    (await api.post('/models/train', params)).data,

  getModels: async (): Promise<ModelRun[]> => (await api.get('/models')).data,
  getModelMetrics: async (modelId: string) => (await api.get(`/models/${modelId}/metrics`)).data,

  // Signals
  getSignals: async (params?: { symbol?: string; strategy?: string; refresh?: boolean }): Promise<TradingSignal[]> =>
    (await api.get('/signals', { params })).data,

  // Backtests
  runBacktest: async (params: {
    symbol: string;
    strategy_type: string;
    start_date?: string;
    end_date?: string;
    initial_capital?: number;
    entry_sentiment_threshold?: number;
    exit_sentiment_threshold?: number;
    transaction_cost_pct?: number;
    slippage_pct?: number;
  }): Promise<BacktestRun> => (await api.post('/backtests', params)).data,

  getBacktests: async (): Promise<BacktestRun[]> => (await api.get('/backtests')).data,
  getBacktest: async (backtestId: string): Promise<BacktestRun> => (await api.get(`/backtests/${backtestId}`)).data,
  getBacktestTrades: async (backtestId: string): Promise<BacktestTrade[]> =>
    (await api.get(`/backtests/${backtestId}/trades`)).data,
};

export default api;
