import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { api } from '../api/client';
import { BookmarkCheck, Trash2, ArrowUpRight, TrendingUp, TrendingDown } from 'lucide-react';

export const WatchlistPage: React.FC = () => {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchWatchlist = async () => {
    try {
      const res = await api.getWatchlist();
      setItems(res);
    } catch (err) {
      console.error('Failed to load watchlist:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const handleRemove = async (sym: string) => {
    try {
      await api.removeFromWatchlist(sym);
      fetchWatchlist();
    } catch (err) {
      console.error('Failed to remove item:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="pb-4 border-b border-[#334155] flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold font-mono tracking-tight text-slate-100 flex items-center gap-2">
            <BookmarkCheck className="w-5 h-5 text-sky-400" />
            INVESTMENT WATCHLIST & ACTIVE SIGNALS
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time tracking of targeted equities with multi-factor signal ratings and FinBERT sentiment updates.
          </p>
        </div>
        <NavLink
          to="/research"
          className="px-3 py-1.5 rounded bg-sky-500/10 border border-sky-400 text-sky-400 text-xs font-mono font-bold hover:bg-sky-500/20"
        >
          + Add New Equities
        </NavLink>
      </div>

      {loading ? (
        <div className="py-20 text-center font-mono text-xs text-slate-400">Loading Watchlist...</div>
      ) : items.length === 0 ? (
        <div className="bg-[#0f172a] border border-[#334155] rounded-lg p-12 text-center font-mono space-y-3">
          <p className="text-slate-300 text-sm">Your watchlist is currently empty.</p>
          <p className="text-xs text-slate-500">
            Navigate to the Stock Research page to inspect any NIFTY 50 stock and add it to your watchlist.
          </p>
          <NavLink
            to="/research"
            className="inline-block mt-2 px-4 py-2 rounded bg-sky-500 text-slate-950 font-bold text-xs"
          >
            Go to Stock Research
          </NavLink>
        </div>
      ) : (
        <div className="bg-[#0f172a] border border-[#334155] rounded-lg overflow-hidden">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#1e293b] text-slate-400 border-b border-[#334155]">
              <tr>
                <th className="py-3 px-4">TICKER</th>
                <th className="py-3 px-4">CURRENT PRICE</th>
                <th className="py-3 px-4">QUANT SIGNAL</th>
                <th className="py-3 px-4">MODEL PROBABILITY</th>
                <th className="py-3 px-4">FINBERT SCORE</th>
                <th className="py-3 px-4">RISK</th>
                <th className="py-3 px-4 text-right">ACTIONS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e293b]">
              {items.map((item) => (
                <tr key={item.symbol} className="hover:bg-[#1e293b]/40 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-bold text-slate-100">{item.symbol}</div>
                    <div className="text-[11px] text-slate-400">{item.name}</div>
                  </td>
                  <td className="py-3 px-4 font-bold text-slate-200">
                    ₹{item.current_price?.toLocaleString()}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                        item.composite_score >= 0.25
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : item.composite_score >= 0.10
                          ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-900'
                          : item.composite_score <= -0.10
                          ? 'bg-rose-950 text-rose-400 border border-rose-800'
                          : 'bg-slate-800 text-slate-300 border border-slate-700'
                      }`}
                    >
                      {item.signal}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-bold text-sky-400">
                    {(item.model_probability * 100).toFixed(1)}%
                  </td>
                  <td className="py-3 px-4 text-slate-300">
                    {item.sentiment_score > 0 ? `+${item.sentiment_score}` : item.sentiment_score}
                  </td>
                  <td className="py-3 px-4 text-slate-300">{item.risk_score} / 100</td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <NavLink
                        to={`/research`}
                        className="p-1.5 rounded bg-[#1e293b] text-sky-400 hover:bg-slate-700"
                        title="Deep-dive in Stock Research"
                      >
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </NavLink>
                      <button
                        onClick={() => handleRemove(item.symbol)}
                        className="p-1.5 rounded bg-[#1e293b] text-slate-500 hover:text-rose-400 hover:bg-slate-700"
                        title="Remove from Watchlist"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

