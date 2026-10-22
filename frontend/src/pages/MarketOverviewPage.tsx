import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  TrendingUp,
  TrendingDown,
  Newspaper,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  BarChart3,
  ExternalLink,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
} from 'recharts';
import { apiClient } from '../api/client';
import { useNavigate } from 'react-router-dom';

export const MarketOverviewPage: React.FC = () => {
  const navigate = useNavigate();

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['sentimentOverview'],
    queryFn: apiClient.getSentimentOverview,
    refetchInterval: 10000,
  });

  const { data: status } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: apiClient.getSystemStatus,
    refetchInterval: 10000,
  });

  const { data: newsData } = useQuery({
    queryKey: ['recentNews'],
    queryFn: () => apiClient.getNews({ page: 1, page_size: 6 }),
    refetchInterval: 15000,
  });

  const { data: reliancePrices } = useQuery({
    queryKey: ['stockPrices', 'RELIANCE'],
    queryFn: () => apiClient.getStockPrices('RELIANCE', 30),
  });

  const latestPrice = reliancePrices && reliancePrices.length > 0 ? reliancePrices[reliancePrices.length - 1] : null;
  const prevPrice = reliancePrices && reliancePrices.length > 1 ? reliancePrices[reliancePrices.length - 2] : null;
  const priceChange = latestPrice && prevPrice ? ((latestPrice.close - prevPrice.close) / prevPrice.close) * 100 : 0;

  const marketScore = overview?.overall_market_sentiment ?? 0;
  const isMarketBullish = marketScore > 0.05;
  const isMarketBearish = marketScore < -0.05;

  const dist = overview?.sentiment_distribution || {};
  const posCount = dist.positive || 0;
  const negCount = dist.negative || 0;
  const neuCount = dist.neutral || 0;
  const totalArticles = posCount + negCount + neuCount;

  return (
    <div className="p-6 space-y-6">
      {/* Top Banner / Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white font-mono flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            NIFTY 50 INTELLIGENCE & SENTIMENT RADAR
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time local FinBERT NLP inference merged with technical market data.
          </p>
        </div>

        {/* Selected Stock Benchmark Ticker */}
        {latestPrice && (
          <div className="flex items-center gap-4 bg-[#0e1626] border border-slate-800 px-4 py-2 rounded-lg font-mono">
            <div>
              <div className="text-[10px] text-slate-400 uppercase tracking-wider">Benchmark: RELIANCE</div>
              <div className="text-sm font-bold text-white">₹{latestPrice.close.toFixed(2)}</div>
            </div>
            <div
              className={`flex items-center text-xs font-semibold px-2 py-0.5 rounded ${
                priceChange >= 0
                  ? 'text-emerald-400 bg-emerald-950/50 border border-emerald-800/60'
                  : 'text-rose-400 bg-rose-950/50 border border-rose-800/60'
              }`}
            >
              {priceChange >= 0 ? <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" /> : <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />}
              {priceChange >= 0 ? '+' : ''}
              {priceChange.toFixed(2)}%
            </div>
          </div>
        )}
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Overall Market Sentiment */}
        <div className="bg-[#0e1526]/80 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>FINBERT MARKET SENTIMENT</span>
            {isMarketBullish ? (
              <TrendingUp className="w-4 h-4 text-emerald-400" />
            ) : isMarketBearish ? (
              <TrendingDown className="w-4 h-4 text-rose-400" />
            ) : (
              <span className="w-2 h-2 rounded-full bg-slate-500" />
            )}
          </div>
          <div className="my-2 flex items-baseline gap-2">
            <span
              className={`text-2xl font-mono font-bold ${
                isMarketBullish ? 'text-emerald-400' : isMarketBearish ? 'text-rose-400' : 'text-slate-300'
              }`}
            >
              {marketScore > 0 ? `+${marketScore.toFixed(3)}` : marketScore.toFixed(3)}
            </span>
            <span className="text-[11px] font-mono uppercase text-slate-400">
              {isMarketBullish ? 'BULLISH' : isMarketBearish ? 'BEARISH' : 'NEUTRAL'}
            </span>
          </div>
          <div className="w-full bg-slate-800/60 h-1.5 rounded-full overflow-hidden flex">
            <div
              className="bg-emerald-500 h-full transition-all"
              style={{ width: `${totalArticles ? (posCount / totalArticles) * 100 : 33}%` }}
              title={`Positive: ${posCount}`}
            />
            <div
              className="bg-slate-500 h-full transition-all"
              style={{ width: `${totalArticles ? (neuCount / totalArticles) * 100 : 34}%` }}
              title={`Neutral: ${neuCount}`}
            />
            <div
              className="bg-rose-500 h-full transition-all"
              style={{ width: `${totalArticles ? (negCount / totalArticles) * 100 : 33}%` }}
              title={`Negative: ${negCount}`}
            />
          </div>
        </div>

        {/* KPI 2: Bullish vs Bearish Count */}
        <div className="bg-[#0e1526]/80 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>NEWS SENTIMENT BREAKDOWN</span>
            <Newspaper className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="my-2 flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-xs text-slate-400 font-mono">Bullish News</span>
              <span className="text-xl font-bold font-mono text-emerald-400">{posCount}</span>
            </div>
            <div className="text-slate-600 font-mono text-sm">/</div>
            <div className="flex flex-col text-right">
              <span className="text-xs text-slate-400 font-mono">Bearish News</span>
              <span className="text-xl font-bold font-mono text-rose-400">{negCount}</span>
            </div>
          </div>
          <div className="text-[11px] text-slate-500 font-mono">
            {neuCount} neutral / background reports
          </div>
        </div>

        {/* KPI 3: Ingested Articles */}
        <div className="bg-[#0e1526]/80 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>TOTAL ARTICLES INGESTED</span>
            <Layers className="w-4 h-4 text-sky-400" />
          </div>
          <div className="my-2">
            <span className="text-2xl font-mono font-bold text-white">
              {status?.total_articles || 0}
            </span>
          </div>
          <div className="text-[11px] text-slate-400 font-mono">
            Analyzed by FinBERT: <span className="text-cyan-400">{status?.total_sentiment_analyzed || 0}</span>
          </div>
        </div>

        {/* KPI 4: Active Tracked Stocks */}
        <div className="bg-[#0e1526]/80 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>COVERAGE UNIVERSE</span>
            <span className="text-xs font-mono text-cyan-400">NSE</span>
          </div>
          <div className="my-2">
            <span className="text-2xl font-mono font-bold text-white">
              {status?.total_stocks || 20} Stocks
            </span>
          </div>
          <div className="text-[11px] text-slate-400 font-mono">
            Nifty 50 Large-Cap Equities
          </div>
        </div>
      </div>

      {/* Main Grid: Top Rankings & Benchmark Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Bullish & Bearish Rankings */}
        <div className="lg:col-span-2 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Top Bullish Stocks */}
            <div className="bg-[#0e1526]/80 border border-slate-800/80 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3 pb-2 border-b border-slate-800/80">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider">
                  Top Bullish Momentum
                </span>
              </div>
              <div className="space-y-2">
                {overview?.bullish_ranking && overview.bullish_ranking.length > 0 ? (
                  overview.bullish_ranking.map((s: any) => (
                    <div
                      key={s.symbol}
                      onClick={() => navigate(`/research?symbol=${s.symbol}`)}
                      className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800/60 border border-slate-800/40 cursor-pointer transition-all"
                    >
                      <div>
                        <div className="text-xs font-mono font-bold text-white">{s.symbol}</div>
                        <div className="text-[10px] text-slate-400 truncate max-w-[150px]">{s.company_name}</div>
                      </div>
                      <div className="text-right font-mono">
                        <div className="text-xs font-bold text-emerald-400">
                          {s.score > 0 ? `+${s.score.toFixed(3)}` : s.score.toFixed(3)}
                        </div>
                        <div className="text-[10px] text-slate-500">{s.article_count} articles</div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-xs font-mono text-slate-500 text-center py-6">
                    Run sentiment analysis to generate stock rankings.
                  </div>
                )}
              </div>
            </div>

            {/* Top Bearish Stocks */}
            <div className="bg-[#0e1526]/80 border border-slate-800/80 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3 pb-2 border-b border-slate-800/80">
                <TrendingDown className="w-4 h-4 text-rose-400" />
                <span className="text-xs font-mono font-bold text-rose-400 uppercase tracking-wider">
                  Top Bearish Momentum
                </span>
              </div>
              <div className="space-y-2">
                {overview?.bearish_ranking && overview.bearish_ranking.length > 0 ? (
                  overview.bearish_ranking.map((s: any) => (
                    <div
                      key={s.symbol}
                      onClick={() => navigate(`/research?symbol=${s.symbol}`)}
                      className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800/60 border border-slate-800/40 cursor-pointer transition-all"
                    >
                      <div>
                        <div className="text-xs font-mono font-bold text-white">{s.symbol}</div>
                        <div className="text-[10px] text-slate-400 truncate max-w-[150px]">{s.company_name}</div>
                      </div>
                      <div className="text-right font-mono">
                        <div className="text-xs font-bold text-rose-400">
                          {s.score.toFixed(3)}
                        </div>
                        <div className="text-[10px] text-slate-500">{s.article_count} articles</div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-xs font-mono text-slate-500 text-center py-6">
                    Run sentiment analysis to generate stock rankings.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Benchmark Trend Chart */}
          <div className="bg-[#0e1526]/80 border border-slate-800/80 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800/80">
              <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                Benchmark Price Trend (RELIANCE.NS)
              </span>
              <span className="text-[10px] font-mono text-slate-400">Daily Close & 20-Day Moving Average</span>
            </div>
            <div className="h-64 w-full">
              {reliancePrices && reliancePrices.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={reliancePrices} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="relianceGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(val) => val.split('T')[0].slice(5)}
                      stroke="#64748b"
                      fontSize={11}
                    />
                    <YAxis
                      domain={['auto', 'auto']}
                      stroke="#64748b"
                      fontSize={11}
                      tickFormatter={(val) => `₹${val}`}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '12px' }}
                      labelFormatter={(label) => `Date: ${String(label).split('T')[0]}`}
                      formatter={(val: any) => [`₹${Number(val).toFixed(2)}`, 'Close Price']}
                    />
                    <Area
                      type="monotone"
                      dataKey="close"
                      stroke="#38bdf8"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#relianceGrad)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-slate-500 font-mono text-xs">
                  Loading market data...
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Col: Live News Feed Preview */}
        <div className="bg-[#0e1526]/80 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800/80">
              <span className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Newspaper className="w-3.5 h-3.5 text-cyan-400" />
                Latest Market Feed
              </span>
              <button
                onClick={() => navigate('/news')}
                className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300"
              >
                View All &rarr;
              </button>
            </div>

            <div className="space-y-3">
              {newsData?.items && newsData.items.length > 0 ? (
                newsData.items.map((art) => {
                  const sent = art.sentiment;
                  const isPos = sent?.sentiment_label === 'positive';
                  const isNeg = sent?.sentiment_label === 'negative';

                  return (
                    <div
                      key={art.id}
                      className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/60 flex flex-col gap-1.5"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] font-mono text-slate-400 truncate max-w-[140px]">
                          {art.source}
                        </span>
                        {sent ? (
                          <span
                            className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded ${
                              isPos
                                ? 'text-emerald-400 bg-emerald-950/80 border border-emerald-800/60'
                                : isNeg
                                ? 'text-rose-400 bg-rose-950/80 border border-rose-800/60'
                                : 'text-slate-400 bg-slate-800/80 border border-slate-700/60'
                            }`}
                          >
                            {sent.sentiment_label.toUpperCase()} ({sent.sentiment_score > 0 ? '+' : ''}
                            {sent.sentiment_score.toFixed(2)})
                          </span>
                        ) : (
                          <span className="text-[9px] font-mono text-amber-400 bg-amber-950/40 border border-amber-800/40 px-1.5 py-0.5 rounded">
                            PENDING
                          </span>
                        )}
                      </div>

                      <a
                        href={art.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs font-medium text-slate-200 hover:text-cyan-300 transition-colors line-clamp-2 leading-snug"
                      >
                        {art.title}
                      </a>

                      {art.mapped_stocks && art.mapped_stocks.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {art.mapped_stocks.map((sym) => (
                            <span
                              key={sym}
                              onClick={() => navigate(`/research?symbol=${sym}`)}
                              className="text-[9px] font-mono bg-cyan-950/40 text-cyan-300 border border-cyan-800/40 px-1 rounded cursor-pointer hover:bg-cyan-900/40"
                            >
                              ${sym}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })
              ) : (
                <div className="text-xs font-mono text-slate-500 text-center py-12">
                  No articles found. Click "Fetch News RSS" to ingest live feeds.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
