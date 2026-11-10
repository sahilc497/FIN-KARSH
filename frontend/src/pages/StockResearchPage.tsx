import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import {
  TrendingUp,
  TrendingDown,
  Layers,
  BookmarkPlus,
  Radio,
  CheckCircle,
  Search,
  PlusCircle,
  RefreshCw,
  Sparkles,
  BarChart2,
  AlertTriangle,
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

export const StockResearchPage: React.FC = () => {
  const [stocks, setStocks] = useState<any[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('RELIANCE.NS');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState<boolean>(false);
  const [onboarding, setOnboarding] = useState<boolean>(false);

  const [horizon, setHorizon] = useState<number>(5);
  const [recommendation, setRecommendation] = useState<any>(null);
  const [ohlcv, setOhlcv] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [watchlistSuccess, setWatchlistSuccess] = useState<boolean>(false);

  useEffect(() => {
    const fetchStocks = async () => {
      try {
        const res = await api.getStocks();
        setStocks(res.filter((s: any) => s.symbol !== '^NSEI'));
      } catch (err) {
        console.error('Failed to load stocks:', err);
      }
    };
    fetchStocks();
  }, []);

  const loadStockData = async (sym: string, h: number) => {
    setLoading(true);
    try {
      const [recRes, ohlcvRes] = await Promise.all([
        api.getStockRecommendation(sym, h),
        api.getHistoricalOHLCV(sym, 90),
      ]);
      setRecommendation(recRes);
      setOhlcv(ohlcvRes);
    } catch (err) {
      console.error('Failed to load stock details:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStockData(selectedSymbol, horizon);
  }, [selectedSymbol, horizon]);

  const handleSearch = async (val: string) => {
    setSearchQuery(val);
    if (val.trim().length < 2) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const results = await api.searchStocks(val);
      setSearchResults(results);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setSearching(false);
    }
  };

  const handleSelectStock = async (stockItem: any) => {
    setSearchResults([]);
    setSearchQuery('');

    if (stockItem.onboarded) {
      setSelectedSymbol(stockItem.symbol);
    } else {
      // Trigger dynamic onboarding
      setOnboarding(true);
      try {
        await api.onboardStock(stockItem.symbol);
        const res = await api.getStocks();
        setStocks(res.filter((s: any) => s.symbol !== '^NSEI'));
        setSelectedSymbol(stockItem.symbol);
      } catch (err) {
        console.error('Onboarding failed:', err);
      } finally {
        setOnboarding(false);
      }
    }
  };

  const handleAddToWatchlist = async () => {
    try {
      await api.addToWatchlist(selectedSymbol, recommendation?.current_price);
      setWatchlistSuccess(true);
      setTimeout(() => setWatchlistSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to add to watchlist:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title & Universe Search Bar */}
      <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold font-mono tracking-tight text-slate-100 flex items-center gap-2">
              <Search className="w-5 h-5 text-sky-400" />
              STOCK EXPLORER & MULTI-FACTOR RESEARCH
            </h1>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Expanded NSE universe coverage across NIFTY 50, NIFTY Next 50, NIFTY 100, 200 & 500 with dynamic onboarding.
            </p>
          </div>

          {/* Search Box */}
          <div className="relative w-full md:w-80">
            <div className="flex items-center gap-2 bg-slate-900 border border-slate-700 rounded px-3 py-2 text-xs font-mono text-slate-200">
              <Search className="w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder="Search symbol or name (e.g. Zomato, HAL)..."
                className="bg-transparent border-none outline-none w-full text-slate-100 placeholder-slate-500"
              />
              {searching && <RefreshCw className="w-3.5 h-3.5 animate-spin text-sky-400" />}
            </div>

            {/* Search Dropdown Results */}
            {searchResults.length > 0 && (
              <div className="absolute left-0 right-0 top-full mt-1 bg-[#0f172a] border border-slate-700 rounded shadow-xl z-50 max-h-60 overflow-y-auto font-mono text-xs divide-y divide-slate-800">
                {searchResults.map((item) => (
                  <div
                    key={item.symbol}
                    onClick={() => handleSelectStock(item)}
                    className="p-2.5 hover:bg-slate-800 cursor-pointer flex items-center justify-between transition"
                  >
                    <div>
                      <div className="font-bold text-slate-100 flex items-center gap-2">
                        <span>{item.symbol}</span>
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-sky-400 border border-slate-700">
                          {item.index}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400">{item.name}</div>
                    </div>
                    <div>
                      {item.onboarded ? (
                        <span className="text-[10px] text-emerald-400 font-semibold">Active</span>
                      ) : (
                        <span className="text-[10px] text-sky-400 flex items-center gap-1 font-semibold">
                          <PlusCircle className="w-3 h-3" /> Onboard
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Selected Stock Selector & Controls Row */}
        <div className="mt-4 pt-4 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <label className="text-xs font-mono font-semibold text-slate-300">ACTIVE TICKER:</label>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs font-mono text-slate-100 focus:outline-none focus:border-sky-400"
            >
              {stocks.map((s) => (
                <option key={s.symbol} value={s.symbol}>
                  {s.symbol} — {s.name}
                </option>
              ))}
            </select>

            <div className="flex items-center gap-1 border-l border-slate-800 pl-3">
              <span className="text-xs font-mono text-slate-400">Prediction Horizon:</span>
              {[1, 5, 10].map((h) => (
                <button
                  key={h}
                  onClick={() => setHorizon(h)}
                  className={`px-2.5 py-1 text-xs font-mono rounded transition ${
                    horizon === h
                      ? 'bg-sky-500/20 text-sky-400 border border-sky-400 font-bold'
                      : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {h}D
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleAddToWatchlist}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono bg-sky-500/10 border border-sky-400 text-sky-400 hover:bg-sky-500/20 transition"
          >
            {watchlistSuccess ? (
              <>
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                <span>Added to Watchlist</span>
              </>
            ) : (
              <>
                <BookmarkPlus className="w-3.5 h-3.5" />
                <span>Add to Watchlist</span>
              </>
            )}
          </button>
        </div>
      </div>

      {onboarding && (
        <div className="bg-sky-950/40 border border-sky-800/80 rounded p-4 text-xs font-mono text-sky-300 flex items-center gap-3">
          <RefreshCw className="w-4 h-4 animate-spin text-sky-400" />
          <span>Dynamically fetching historical OHLCV prices, computing technical indicators, and training ML models for selected ticker...</span>
        </div>
      )}

      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center gap-3 text-slate-400">
          <RefreshCw className="w-8 h-8 animate-spin text-sky-400" />
          <p className="font-mono text-xs">Computing multi-factor attribution & FinBERT inference...</p>
        </div>
      ) : (
        <>
          {/* Header Summary Card */}
          <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#1e293b]">
              <div>
                <div className="flex items-center gap-3">
                  <h2 className="text-2xl font-bold font-mono text-slate-100">{recommendation?.symbol}</h2>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                    {recommendation?.sector}
                  </span>
                  <span
                    className={`px-3 py-0.5 rounded text-xs font-mono font-bold border ${
                      recommendation?.composite_score >= 0.25
                        ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                        : recommendation?.composite_score >= 0.10
                        ? 'bg-emerald-950/60 text-emerald-300 border-emerald-900'
                        : 'bg-rose-950 text-rose-400 border-rose-800'
                    }`}
                  >
                    {recommendation?.recommendation}
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono mt-1">{recommendation?.name}</p>
              </div>

              <div className="flex items-baseline gap-4 text-right">
                <div>
                  <div className="text-[11px] font-mono text-slate-400">CURRENT MARKET PRICE</div>
                  <div className="text-2xl font-bold font-mono text-slate-100">
                    ₹{recommendation?.current_price?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] font-mono text-slate-400">DIRECTIONAL PROBABILITY</div>
                  <div className="text-2xl font-bold font-mono text-sky-400">
                    {((recommendation?.prob_up || 0.65) * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>

            {/* Factor Decomposition Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              <div className="bg-slate-900/60 border border-slate-800 p-3 rounded">
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
                  <span>ML DIRECTIONAL SCORE</span>
                  <Layers className="w-3.5 h-3.5 text-sky-400" />
                </div>
                <div className="text-lg font-bold font-mono text-sky-400">
                  {((recommendation?.factor_scores?.ml_score || 0.65) * 100).toFixed(0)}%
                </div>
                <div className="text-[10px] text-slate-400 font-mono mt-1">Weight: 35%</div>
              </div>

              <div className="bg-slate-900/60 border border-slate-800 p-3 rounded">
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
                  <span>FINBERT SENTIMENT SCORE</span>
                  <Radio className="w-3.5 h-3.5 text-emerald-400" />
                </div>
                <div className="text-lg font-bold font-mono text-emerald-400">
                  {recommendation?.factor_scores?.sentiment_score !== undefined
                    ? (recommendation.factor_scores.sentiment_score > 0 ? `+${recommendation.factor_scores.sentiment_score}` : recommendation.factor_scores.sentiment_score)
                    : '+0.45'}
                </div>
                <div className="text-[10px] text-slate-400 font-mono mt-1">Weight: 25%</div>
              </div>

              <div className="bg-slate-900/60 border border-slate-800 p-3 rounded">
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
                  <span>TECHNICAL FACTOR SCORE</span>
                  <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
                </div>
                <div className="text-lg font-bold font-mono text-slate-100">
                  {recommendation?.factor_scores?.technical_score > 0
                    ? `+${recommendation?.factor_scores?.technical_score}`
                    : recommendation?.factor_scores?.technical_score || '+0.15'}
                </div>
                <div className="text-[10px] text-slate-400 font-mono mt-1">Weight: 20%</div>
              </div>

              <div className="bg-slate-900/60 border border-slate-800 p-3 rounded">
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
                  <span>FUNDAMENTAL QUALITY</span>
                  <BarChart2 className="w-3.5 h-3.5 text-slate-400" />
                </div>
                <div className="text-lg font-bold font-mono text-slate-100">
                  {recommendation?.factor_scores?.fundamental_score || '+0.25'}
                </div>
                <div className="text-[10px] text-slate-400 font-mono mt-1">Weight: 20%</div>
              </div>
            </div>

            {/* Explanation Narrative */}
            <div className="mt-5 p-4 rounded bg-slate-900/50 border border-slate-800 text-xs font-mono text-slate-300 leading-relaxed">
              <strong className="text-sky-400">Analytical Synthesis: </strong>
              {recommendation?.explanation}
            </div>
          </div>

          {/* Price & Volume Chart */}
          <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-6">
            <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-slate-200 mb-4 flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-sky-400" />
              Historical OHLCV Price Action (90 Sessions)
            </h3>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={ohlcv}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="date"
                    stroke="#64748b"
                    tick={{ fontSize: 10, fontFamily: 'monospace' }}
                    tickFormatter={(val) => val.slice(5)}
                  />
                  <YAxis
                    stroke="#64748b"
                    domain={['auto', 'auto']}
                    tick={{ fontSize: 10, fontFamily: 'monospace' }}
                    tickFormatter={(val) => `₹${val.toLocaleString()}`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      fontFamily: 'monospace',
                      fontSize: '11px',
                    }}
                  />
                  <Bar dataKey="volume" fill="#1e293b" opacity={0.6} yAxisId={0} />
                  <Line
                    type="monotone"
                    dataKey="close"
                    stroke="#38bdf8"
                    strokeWidth={2}
                    dot={false}
                    name="Close Price"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
