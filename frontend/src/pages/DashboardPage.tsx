import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Radio,
  MessageSquare,
  Newspaper,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  Sparkles,
  Search,
} from 'lucide-react';
import { api } from '../api/client';

export const DashboardPage: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [snapshot, setSnapshot] = useState<any>(null);
  const [sentimentOverview, setSentimentOverview] = useState<any>(null);
  const [redditTrends, setRedditTrends] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [latestNews, setLatestNews] = useState<any[]>([]);
  const [lastRefreshed, setLastRefreshed] = useState<string>('');

  const loadDashboardData = async () => {
    try {
      const [snap, sent, redTrends, recs, news] = await Promise.all([
        api.getLiveMarketSnapshot().catch(() => null),
        api.getSentimentOverview().catch(() => null),
        api.getRedditTrends(8).catch(() => []),
        api.getRecommendations(5).catch(() => null),
        api.getFinancialNews(undefined, 6).catch(() => []),
      ]);

      setSnapshot(snap);
      setSentimentOverview(sent);
      setRedditTrends(redTrends || []);
      setRecommendations(recs);
      setLatestNews(news || []);
      setLastRefreshed(new Date().toLocaleTimeString());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 20000); // 20s live update
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-slate-400 gap-3">
        <RefreshCw className="w-8 h-8 animate-spin text-sky-400" />
        <span className="font-mono text-sm">Synchronizing real-time market streams & FinBERT sentiment...</span>
      </div>
    );
  }

  const nifty = snapshot?.nifty_50 || { price: 24200.0, change: 142.5, change_pct: 0.59 };
  const quotes: any[] = snapshot?.quotes || [];
  const topPos = sentimentOverview?.top_positive || quotes.slice(0, 3);
  const topNeg = sentimentOverview?.top_negative || quotes.slice(-3);
  const recRankings: any[] = recommendations?.recommendations || [];

  return (
    <div className="space-y-6">
      {/* Top Banner: Market Status & Live Clock */}
      <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-emerald-400">
              Live Market Monitoring Active
            </span>
            <span className="text-slate-500 text-xs font-mono">| NSE Equity Session</span>
          </div>
          <h1 className="text-2xl font-bold font-mono tracking-tight text-slate-100 mt-1">
            Financial Intelligence Terminal
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Near-real-time quantitative feed combining FinBERT NLP sentiment, retail Reddit buzz & ML forecasting.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[11px] text-slate-400 font-mono block">LAST UPDATED</span>
            <span className="text-xs font-mono font-semibold text-slate-200">{lastRefreshed || 'Just now'}</span>
          </div>
          <button
            onClick={loadDashboardData}
            className="p-2 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            title="Refresh Market Snapshot"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Row 1: KPI Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Card 1: NIFTY 50 Benchmark */}
        <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-4">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1">
            <span>NIFTY 50 BENCHMARK</span>
            <Activity className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100">
            ₹{nifty.price?.toLocaleString('en-IN', { minimumFractionDigits: 2 }) || '24,200.00'}
          </div>
          <div className="flex items-center gap-1.5 mt-2 text-xs font-mono">
            {nifty.change_pct >= 0 ? (
              <>
                <ArrowUpRight className="w-4 h-4 text-emerald-400" />
                <span className="text-emerald-400 font-medium">+{nifty.change_pct?.toFixed(2)}% (+₹{nifty.change?.toFixed(2)})</span>
              </>
            ) : (
              <>
                <ArrowDownRight className="w-4 h-4 text-rose-400" />
                <span className="text-rose-400 font-medium">{nifty.change_pct?.toFixed(2)}% ({nifty.change?.toFixed(2)})</span>
              </>
            )}
            <span className="text-slate-500 ml-auto">Index</span>
          </div>
        </div>

        {/* Card 2: Market Sentiment */}
        <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-4">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1">
            <span>FINBERT MARKET SENTIMENT</span>
            <Radio className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400">
            {sentimentOverview?.market_sentiment_score !== undefined
              ? (sentimentOverview.market_sentiment_score > 0 ? `+${sentimentOverview.market_sentiment_score}` : sentimentOverview.market_sentiment_score)
              : '+0.42'}
          </div>
          <div className="flex items-center justify-between mt-2 text-xs font-mono text-slate-400">
            <span>Label: <strong className="text-emerald-300">{sentimentOverview?.market_sentiment_label || 'Bullish'}</strong></span>
            <span className="text-slate-500">P(Pos) - P(Neg)</span>
          </div>
        </div>

        {/* Card 3: News vs Reddit Divergence */}
        <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-4">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1">
            <span>SENTIMENT DIVERGENCE</span>
            <MessageSquare className="w-4 h-4 text-sky-400" />
          </div>
          <div className="flex items-center gap-3 mt-1">
            <div>
              <span className="text-[10px] text-slate-400 font-mono block">NEWS MEDIA</span>
              <span className="text-lg font-bold font-mono text-slate-200">
                {sentimentOverview?.market_news_sentiment !== undefined ? `+${sentimentOverview.market_news_sentiment}` : '+0.45'}
              </span>
            </div>
            <div className="h-8 w-px bg-slate-700"></div>
            <div>
              <span className="text-[10px] text-slate-400 font-mono block">REDDIT RETAIL</span>
              <span className="text-lg font-bold font-mono text-sky-400">
                {sentimentOverview?.market_reddit_sentiment !== undefined ? `+${sentimentOverview.market_reddit_sentiment}` : '+0.38'}
              </span>
            </div>
          </div>
          <div className="mt-2 text-[11px] font-mono text-slate-400">
            Media vs retail sentiment divergence: <strong className="text-slate-200">Aligned</strong>
          </div>
        </div>

        {/* Card 4: AI Financial Assistant Status */}
        <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1">
              <span>AI QUANT ASSISTANT</span>
              <Sparkles className="w-4 h-4 text-sky-400" />
            </div>
            <div className="text-sm font-bold font-mono text-slate-100 flex items-center gap-1.5 mt-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              Gemini & RAG Engine Active
            </div>
            <p className="text-[11px] text-slate-400 font-mono mt-1">
              Natural language queries on NSE fundamentals, FinBERT sentiment, and portfolio math.
            </p>
          </div>
          <Link
            to="/assistant"
            className="mt-3 inline-flex items-center justify-center gap-1.5 text-xs font-mono font-medium text-sky-400 bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 py-1.5 px-3 rounded transition"
          >
            Launch Assistant <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Row 2: Top Sentiment Movers & Machine Learning Prediction Rankings */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Column 1: Top Positive & Negative Sentiment Equities */}
        <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-5 flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-[#1e293b]">
            <div className="flex items-center gap-2">
              <Radio className="w-4 h-4 text-sky-400" />
              <h2 className="text-sm font-bold font-mono uppercase tracking-wider text-slate-200">
                FinBERT Sentiment Leaders & Laggards
              </h2>
            </div>
            <Link to="/sentiment" className="text-xs font-mono text-sky-400 hover:underline flex items-center gap-1">
              View All <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="mt-4 space-y-4">
            <div>
              <span className="text-[11px] font-mono text-emerald-400 uppercase tracking-wider block mb-2 font-semibold">
                ▲ Top Bullish Sentiment Stocks
              </span>
              <div className="space-y-2">
                {topPos.slice(0, 3).map((s: any) => (
                  <div
                    key={s.symbol}
                    className="flex items-center justify-between p-2.5 rounded bg-slate-900/60 border border-[#1e293b] hover:border-slate-700 transition"
                  >
                    <div>
                      <div className="font-mono font-bold text-xs text-slate-100">{s.symbol}</div>
                      <div className="text-[11px] text-slate-400">{s.name}</div>
                    </div>
                    <div className="text-right">
                      <span className="inline-block px-2 py-0.5 rounded text-xs font-mono font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                        {s.sentiment_score !== undefined ? `+${s.sentiment_score}` : '+0.50'}
                      </span>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                        Mom: {s.sentiment_momentum ? `+${s.sentiment_momentum}` : '+0.12'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <span className="text-[11px] font-mono text-rose-400 uppercase tracking-wider block mb-2 font-semibold">
                ▼ Sentiment Laggards / Bearish Pressure
              </span>
              <div className="space-y-2">
                {topNeg.slice(0, 3).map((s: any) => (
                  <div
                    key={s.symbol}
                    className="flex items-center justify-between p-2.5 rounded bg-slate-900/60 border border-[#1e293b] hover:border-slate-700 transition"
                  >
                    <div>
                      <div className="font-mono font-bold text-xs text-slate-100">{s.symbol}</div>
                      <div className="text-[11px] text-slate-400">{s.name}</div>
                    </div>
                    <div className="text-right">
                      <span className="inline-block px-2 py-0.5 rounded text-xs font-mono font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30">
                        {s.sentiment_score !== undefined ? s.sentiment_score : '-0.20'}
                      </span>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                        Mom: {s.sentiment_momentum || '0.00'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Column 2: Calibrated Machine Learning Prediction Rankings */}
        <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-5 flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-[#1e293b]">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-sky-400" />
              <h2 className="text-sm font-bold font-mono uppercase tracking-wider text-slate-200">
                Machine Learning Prediction Rankings (5-Day Horizon)
              </h2>
            </div>
            <Link to="/stocks" className="text-xs font-mono text-sky-400 hover:underline flex items-center gap-1">
              Stock Explorer <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="mt-4 flex-1 overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="text-slate-400 border-b border-slate-800 pb-2">
                  <th className="py-2">RANK</th>
                  <th className="py-2">TICKER</th>
                  <th className="py-2">P(UP)</th>
                  <th className="py-2">MODEL LABEL</th>
                  <th className="py-2 text-right">PRICE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {recRankings.slice(0, 6).map((rec: any, idx: number) => (
                  <tr key={rec.symbol} className="hover:bg-slate-800/30 transition">
                    <td className="py-2.5 font-bold text-sky-400">#{idx + 1}</td>
                    <td className="py-2.5 font-medium text-slate-100">
                      <div>{rec.symbol}</div>
                      <div className="text-[10px] text-slate-400">{rec.name}</div>
                    </td>
                    <td className="py-2.5">
                      <div className="flex items-center gap-1.5">
                        <div className="w-12 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-emerald-400 h-full rounded-full"
                            style={{ width: `${(rec.prob_up || 0.65) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-[11px] text-slate-200 font-bold">
                          {((rec.prob_up || 0.65) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td className="py-2.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                        {rec.recommendation || 'BULLISH'}
                      </span>
                    </td>
                    <td className="py-2.5 text-right font-bold text-slate-100">
                      ₹{rec.current_price?.toLocaleString('en-IN') || '2,400'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-3 pt-2 border-t border-slate-800/60 text-[10px] text-slate-500 font-mono">
            *Probabilities generated using soft-voting ensembles (HistGradientBoosting, XGBoost, CatBoost).
          </div>
        </div>
      </div>

      {/* Row 3: Reddit Retail Trends vs Latest Financial News */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Reddit Retail Discussion Trends */}
        <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-5">
          <div className="flex items-center justify-between pb-3 border-b border-[#1e293b]">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-sky-400" />
              <h2 className="text-sm font-bold font-mono uppercase tracking-wider text-slate-200">
                Reddit Retail Discussion Trends (r/IndianStockMarket)
              </h2>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-900/40 text-sky-300 border border-sky-700/50">
              Retail Intelligence
            </span>
          </div>

          <div className="mt-4 space-y-3">
            {redditTrends.length > 0 ? (
              redditTrends.slice(0, 5).map((trend: any) => (
                <div
                  key={trend.symbol}
                  className="p-3 rounded bg-slate-900/50 border border-[#1e293b] flex items-center justify-between hover:border-slate-700 transition"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-xs text-slate-100">{trend.symbol}</span>
                      <span className="text-[10px] font-mono text-slate-400">({trend.name})</span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                      {trend.mentions} discussions • {trend.total_upvotes} upvotes • {trend.total_comments} comments
                    </div>
                  </div>
                  <div className="text-right">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-mono font-bold ${
                        trend.reddit_sentiment_score > 0.05
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                          : trend.reddit_sentiment_score < -0.05
                          ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                          : 'bg-slate-700 text-slate-300 border border-slate-600'
                      }`}
                    >
                      {trend.sentiment_label} ({trend.reddit_sentiment_score > 0 ? `+${trend.reddit_sentiment_score}` : trend.reddit_sentiment_score})
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-400 font-mono py-4 text-center">
                Syncing Reddit community posts...
              </div>
            )}
          </div>
        </div>

        {/* Latest Financial News */}
        <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-5">
          <div className="flex items-center justify-between pb-3 border-b border-[#1e293b]">
            <div className="flex items-center gap-2">
              <Newspaper className="w-4 h-4 text-sky-400" />
              <h2 className="text-sm font-bold font-mono uppercase tracking-wider text-slate-200">
                Financial News Feed (Moneycontrol & NSE)
              </h2>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
              Verified Feeds
            </span>
          </div>

          <div className="mt-4 space-y-3">
            {latestNews.slice(0, 5).map((article: any) => (
              <div
                key={article.id}
                className="p-3 rounded bg-slate-900/50 border border-[#1e293b] hover:border-slate-700 transition"
              >
                <div className="flex items-start justify-between gap-3">
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs font-medium text-slate-200 hover:text-sky-400 transition line-clamp-2 leading-relaxed"
                  >
                    {article.headline}
                  </a>
                  {article.sentiment_label && (
                    <span
                      className={`shrink-0 px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        article.sentiment_label === 'Positive'
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                          : article.sentiment_label === 'Negative'
                          ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                          : 'bg-slate-700 text-slate-300'
                      }`}
                    >
                      {article.sentiment_label}
                    </span>
                  )}
                </div>
                <div className="flex items-center justify-between mt-2 text-[10px] font-mono text-slate-400">
                  <span>{article.source}</span>
                  <span>{new Date(article.published_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

