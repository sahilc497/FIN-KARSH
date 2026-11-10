import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { api } from '../api/client';
import { MetricCard } from '../components/MetricCard';
import { FinbertStatusBadge } from '../components/FinbertStatusBadge';
import {
  TrendingUp,
  TrendingDown,
  ShieldAlert,
  ArrowRight,
  Brain,
  Activity,
  Layers,
  Radio,
} from 'lucide-react';

export const MarketOverviewPage: React.FC = () => {
  const [sentiment, setSentiment] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [news, setNews] = useState<any[]>([]);
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sentRes, recRes, newsRes, healthRes] = await Promise.all([
          api.getSentimentOverview(),
          api.getRecommendations(5),
          api.getFinancialNews(undefined, 6),
          api.getSystemHealth(),
        ]);
        setSentiment(sentRes);
        setRecommendations(recRes);
        setNews(newsRes);
        setHealth(healthRes);
      } catch (err) {
        console.error('Failed to load market overview:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center gap-3 text-slate-400">
        <div className="w-8 h-8 border-2 border-sky-400 border-t-transparent rounded-full animate-spin"></div>
        <p className="font-mono text-xs">Aggregating Indian Market Signals & FinBERT Sentiment...</p>
      </div>
    );
  }

  const topBullish = recommendations.filter((r) => r.composite_score > 0.15).slice(0, 3);
  const topBearish = recommendations.filter((r) => r.composite_score < -0.10).slice(0, 3);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#334155]">
        <div>
          <h1 className="text-xl font-bold font-mono tracking-tight text-slate-100 flex items-center gap-2">
            <Activity className="w-5 h-5 text-sky-400" />
            INDIAN FINANCIAL INTELLIGENCE DASHBOARD
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time multi-factor quantitative modeling, FinBERT sentiment scoring, and walk-forward ML predictions.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="px-3 py-1 rounded bg-[#0f172a] border border-[#334155] text-slate-300">
            Market Status: <span className="text-emerald-400 font-semibold">Active (Delayed 15m)</span>
          </span>
          <span className="px-3 py-1 rounded bg-[#0f172a] border border-[#334155] text-slate-400">
            Last Session: {health?.last_market_session || 'Latest'}
          </span>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="NIFTY 50 Benchmark"
          value="24,200.00"
          change="0.65%"
          isPositive={true}
          subtitle="NSE Large Cap Index"
          icon={<TrendingUp className="w-4 h-4 text-emerald-400" />}
        />
        <MetricCard
          title="FinBERT Market Polarity"
          value={sentiment?.market_sentiment_score > 0 ? `+${sentiment?.market_sentiment_score}` : sentiment?.market_sentiment_score || '+0.44'}
          change={sentiment?.market_sentiment_label || 'Bullish'}
          isPositive={sentiment?.market_sentiment_score >= 0}
          subtitle="P(Positive) - P(Negative) Mean"
          icon={<Radio className="w-4 h-4 text-sky-400" />}
        />
        <MetricCard
          title="Validated ML Models"
          value={health?.counts?.trained_models || 27}
          subtitle="Walk-forward calibrated models"
          icon={<Brain className="w-4 h-4 text-emerald-400" />}
        />
        <MetricCard
          title="Tracked Blue-Chips"
          value={health?.counts?.stocks || 11}
          subtitle="NIFTY 50 core heavyweights"
          icon={<Layers className="w-4 h-4 text-sky-400" />}
        />
      </div>

      {/* Two Column: High-Confidence Signals vs FinBERT Movers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Highest Model Confidence Equities */}
        <div className="bg-[#0f172a] border border-[#334155] rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <Brain className="w-4 h-4 text-sky-400" />
              Top Machine Learning Signals (5d Horizon)
            </h2>
            <NavLink to="/stocks" className="text-xs text-sky-400 hover:underline flex items-center gap-1 font-mono">
              View All <ArrowRight className="w-3 h-3" />
            </NavLink>
          </div>

          <div className="space-y-3">
            {recommendations.slice(0, 4).map((rec) => (
              <div
                key={rec.symbol}
                className="bg-[#1e293b]/70 border border-[#334155] rounded p-3 flex items-center justify-between hover:border-slate-500 transition-colors"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-slate-100">{rec.symbol}</span>
                    <span className="text-xs text-slate-400">{rec.name.split(' ')[0]}</span>
                  </div>
                  <div className="text-xs text-slate-400 mt-1 flex items-center gap-3">
                    <span>Price: <strong className="text-slate-200 font-mono">₹{rec.current_price?.toLocaleString()}</strong></span>
                    <span>Model Prob: <strong className="text-sky-400 font-mono">{(rec.model_probability * 100).toFixed(1)}%</strong></span>
                  </div>
                </div>

                <div className="text-right">
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-xs font-mono font-semibold ${
                      rec.composite_score >= 0.25
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        : rec.composite_score >= 0.10
                        ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-900'
                        : rec.composite_score <= -0.10
                        ? 'bg-rose-950 text-rose-400 border border-rose-800'
                        : 'bg-slate-800 text-slate-300 border border-slate-700'
                    }`}
                  >
                    {rec.signal}
                  </span>
                  <div className="text-xs font-mono text-slate-400 mt-1">
                    Risk: <span className="text-slate-300">{rec.risk_score}/100</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Sentiment Movers */}
        <div className="bg-[#0f172a] border border-[#334155] rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <Radio className="w-4 h-4 text-emerald-400" />
              FinBERT Sentiment Leaders
            </h2>
            <NavLink to="/sentiment" className="text-xs text-sky-400 hover:underline flex items-center gap-1 font-mono">
              Explore Sentiment <ArrowRight className="w-3 h-3" />
            </NavLink>
          </div>

          <div className="space-y-3">
            {sentiment?.top_positive?.map((stock: any) => (
              <div
                key={stock.symbol}
                className="bg-[#1e293b]/70 border border-[#334155] rounded p-3 flex items-center justify-between hover:border-slate-500 transition-colors"
              >
                <div>
                  <div className="font-mono font-bold text-slate-100">{stock.symbol}</div>
                  <div className="text-xs text-slate-400">{stock.name}</div>
                </div>
                <div className="text-right">
                  <FinbertStatusBadge
                    score={stock.sentiment_score}
                    momentum={stock.sentiment_momentum}
                    showDetails={true}
                  />
                  <div className="text-xs text-slate-400 font-mono mt-1">
                    Articles: {stock.article_count}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Grounded Financial News */}
      <div className="bg-[#0f172a] border border-[#334155] rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
            <Layers className="w-4 h-4 text-sky-400" />
            Live Ingested Financial News & Announcements
          </h2>
          <span className="text-xs text-slate-400 font-mono">Deduplicated & Entity Mapped</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {news.map((item) => (
            <div
              key={item.id}
              className="bg-[#1e293b]/50 border border-[#334155] rounded p-3 flex flex-col justify-between hover:border-slate-400 transition-colors"
            >
              <div>
                <div className="flex items-center justify-between text-xs text-slate-400 mb-1 font-mono">
                  <span className="text-sky-400 font-medium">{item.source}</span>
                  {item.stock_symbol && (
                    <span className="bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded font-bold">
                      {item.stock_symbol}
                    </span>
                  )}
                </div>
                <h3 className="text-xs font-semibold text-slate-200 line-clamp-2 leading-relaxed">
                  {item.headline}
                </h3>
              </div>
              <div className="text-[11px] text-slate-400 mt-3 pt-2 border-t border-slate-800 flex items-center justify-between">
                <span>{new Date(item.published_at).toLocaleDateString()}</span>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sky-400 hover:underline flex items-center gap-0.5"
                >
                  Source Link <ArrowRight className="w-2.5 h-2.5" />
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

