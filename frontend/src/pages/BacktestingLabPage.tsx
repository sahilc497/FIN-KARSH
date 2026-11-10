import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import {
  History,
  Play,
  TrendingUp,
  ShieldAlert,
  Sliders,
  DollarSign,
  Percent,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  AreaChart,
  Area,
} from 'recharts';

export const BacktestingLabPage: React.FC = () => {
  const [stocks, setStocks] = useState<any[]>([]);
  const [symbol, setSymbol] = useState<string>('RELIANCE.NS');
  const [capital, setCapital] = useState<number>(100000);
  const [horizon, setHorizon] = useState<number>(5);
  const [strategy, setStrategy] = useState<string>('threshold_filtered');
  const [feeBps, setFeeBps] = useState<number>(5); // 0.05%
  const [slippageBps, setSlippageBps] = useState<number>(5); // 0.05%

  const [running, setRunning] = useState<boolean>(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    const fetchStocks = async () => {
      try {
        const res = await api.getStocks();
        const activeStocks = res.filter((s: any) => s.symbol !== '^NSEI');
        setStocks(activeStocks);
        if (activeStocks.length > 0) {
          // Run default initial backtest
          runSimulation(activeStocks[0].symbol);
        }
      } catch (err) {
        console.error('Failed to load stocks:', err);
      }
    };
    fetchStocks();
  }, []);

  const runSimulation = async (selectedSym = symbol) => {
    setRunning(true);
    try {
      const res = await api.runBacktest({
        symbol: selectedSym,
        initial_capital: capital,
        horizon_days: horizon,
        strategy: strategy,
        fee_pct: feeBps / 10000.0,
        slippage_pct: slippageBps / 10000.0,
      });
      setResult(res);
    } catch (err) {
      console.error('Backtest error:', err);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="pb-4 border-b border-[#334155]">
        <h1 className="text-xl font-bold font-mono tracking-tight text-slate-100 flex items-center gap-2">
          <History className="w-5 h-5 text-sky-400" />
          HISTORICAL BACKTESTING ENGINE & STRATEGY SIMULATOR
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Rigorous chronological event-driven simulation with realistic transaction friction, slippage, and zero look-ahead bias.
        </p>
      </div>

      {/* Configuration Controls */}
      <div className="bg-[#0f172a] border border-[#334155] rounded-lg p-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4 items-end">
          <div>
            <label className="text-xs font-mono font-semibold text-slate-300 block mb-1">EQUITY:</label>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="w-full bg-[#1e293b] border border-[#334155] rounded px-3 py-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-sky-400"
            >
              {stocks.map((s) => (
                <option key={s.symbol} value={s.symbol}>
                  {s.symbol}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-mono font-semibold text-slate-300 block mb-1">INITIAL CAPITAL (₹):</label>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(Number(e.target.value))}
              step={10000}
              className="w-full bg-[#1e293b] border border-[#334155] rounded px-3 py-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-sky-400"
            />
          </div>

          <div>
            <label className="text-xs font-mono font-semibold text-slate-300 block mb-1">HORIZON:</label>
            <select
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
              className="w-full bg-[#1e293b] border border-[#334155] rounded px-3 py-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-sky-400"
            >
              <option value={1}>1 Trading Day</option>
              <option value={5}>5 Trading Days</option>
              <option value={10}>10 Trading Days</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-mono font-semibold text-slate-300 block mb-1">STRATEGY TYPE:</label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              className="w-full bg-[#1e293b] border border-[#334155] rounded px-3 py-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-sky-400"
            >
              <option value="threshold_filtered">Trend + Rebound Filtered</option>
              <option value="long_only">Long Only Momentum</option>
              <option value="long_short">Long / Short Regime</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-mono font-semibold text-slate-300 block mb-1">FRICTION (BPS):</label>
            <div className="flex gap-2">
              <input
                type="number"
                value={feeBps}
                onChange={(e) => setFeeBps(Number(e.target.value))}
                title="Brokerage BPS"
                className="w-1/2 bg-[#1e293b] border border-[#334155] rounded px-2 py-2 text-xs font-mono text-slate-100 text-center"
              />
              <input
                type="number"
                value={slippageBps}
                onChange={(e) => setSlippageBps(Number(e.target.value))}
                title="Slippage BPS"
                className="w-1/2 bg-[#1e293b] border border-[#334155] rounded px-2 py-2 text-xs font-mono text-slate-100 text-center"
              />
            </div>
          </div>

          <div>
            <button
              onClick={() => runSimulation()}
              disabled={running}
              className="w-full py-2 rounded bg-sky-500 hover:bg-sky-400 text-slate-950 text-xs font-mono font-bold flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 ${running ? 'animate-spin' : ''}`} />
              {running ? 'Simulating...' : 'Run Backtest'}
            </button>
          </div>
        </div>
      </div>

      {result && (
        <>
          {/* Key Metric Highlights */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
            <div className="bg-[#0f172a] p-3 rounded-lg border border-[#334155]">
              <div className="text-[11px] font-mono text-slate-400">TOTAL RETURN</div>
              <div className={`text-lg font-bold font-mono ${result.total_return_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {result.total_return_pct >= 0 ? `+${result.total_return_pct}%` : `${result.total_return_pct}%`}
              </div>
              <div className="text-[10px] text-slate-400">Benchmark: {result.benchmark_return_pct}%</div>
            </div>

            <div className="bg-[#0f172a] p-3 rounded-lg border border-[#334155]">
              <div className="text-[11px] font-mono text-slate-400">FINAL EQUITY</div>
              <div className="text-lg font-bold font-mono text-slate-100">
                ₹{result.final_equity.toLocaleString()}
              </div>
              <div className="text-[10px] text-slate-400">Initial: ₹{result.initial_capital.toLocaleString()}</div>
            </div>

            <div className="bg-[#0f172a] p-3 rounded-lg border border-[#334155]">
              <div className="text-[11px] font-mono text-slate-400">SHARPE RATIO</div>
              <div className="text-lg font-bold font-mono text-sky-400">
                {result.sharpe_ratio}
              </div>
              <div className="text-[10px] text-slate-400">Sortino: {result.sortino_ratio}</div>
            </div>

            <div className="bg-[#0f172a] p-3 rounded-lg border border-[#334155]">
              <div className="text-[11px] font-mono text-slate-400">MAX DRAWDOWN</div>
              <div className="text-lg font-bold font-mono text-rose-400">
                {result.max_drawdown_pct}%
              </div>
              <div className="text-[10px] text-slate-400">Peak-to-Trough</div>
            </div>

            <div className="bg-[#0f172a] p-3 rounded-lg border border-[#334155]">
              <div className="text-[11px] font-mono text-slate-400">WIN RATE</div>
              <div className="text-lg font-bold font-mono text-emerald-400">
                {result.win_rate_pct}%
              </div>
              <div className="text-[10px] text-slate-400">Profit Factor: {result.profit_factor}</div>
            </div>

            <div className="bg-[#0f172a] p-3 rounded-lg border border-[#334155]">
              <div className="text-[11px] font-mono text-slate-400">TOTAL TRADES</div>
              <div className="text-lg font-bold font-mono text-slate-100">
                {result.total_trades}
              </div>
              <div className="text-[10px] text-slate-400">{result.start_date} to {result.end_date}</div>
            </div>
          </div>

          {/* Equity Curve Chart vs Benchmark */}
          <div className="bg-[#0f172a] border border-[#334155] rounded-lg p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-200">
                Portfolio Equity Curve vs Buy & Hold Benchmark (₹)
              </h2>
              <span className="text-xs text-slate-400 font-mono">Net of Brokerage & Slippage</span>
            </div>

            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={result.equity_curve}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis
                    stroke="#94a3b8"
                    tick={{ fontSize: 11 }}
                    tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }}
                    formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, 'Equity']}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px' }} />
                  <Line
                    type="monotone"
                    name="ML Strategy Portfolio"
                    dataKey="portfolio"
                    stroke="#38bdf8"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    name="Buy & Hold Benchmark"
                    dataKey="benchmark"
                    stroke="#64748b"
                    strokeWidth={1.5}
                    strokeDasharray="4 4"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Drawdown Curve Chart */}
          <div className="bg-[#0f172a] border border-[#334155] rounded-lg p-5">
            <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-200 mb-4">
              Historical Drawdown Profile (%)
            </h2>
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={result.equity_curve}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} domain={[-40, 0]} tickFormatter={(v) => `${v}%`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }}
                    formatter={(val: any) => [`${val}%`, 'Drawdown']}
                  />
                  <Area type="monotone" dataKey="drawdown_pct" stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Trade Execution Log */}
          <div className="bg-[#0f172a] border border-[#334155] rounded-lg p-5">
            <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-200 mb-3">
              Executed Trades Log (Recent Order Activity)
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#1e293b] text-slate-400 border-b border-[#334155]">
                  <tr>
                    <th className="py-2 px-3">DATE</th>
                    <th className="py-2 px-3">ACTION</th>
                    <th className="py-2 px-3">PRICE</th>
                    <th className="py-2 px-3">QUANTITY</th>
                    <th className="py-2 px-3 text-right">TOTAL CASH IMPACT</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1e293b]">
                  {result.trades.map((t: any, idx: number) => (
                    <tr key={idx} className="hover:bg-[#1e293b]/40">
                      <td className="py-2 px-3 text-slate-300">{t.date}</td>
                      <td className="py-2 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            t.action === 'BUY'
                              ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                              : 'bg-rose-950 text-rose-400 border border-rose-800'
                          }`}
                        >
                          {t.action}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-slate-200">₹{t.price}</td>
                      <td className="py-2 px-3 text-slate-300">{t.shares}</td>
                      <td className="py-2 px-3 text-right font-bold text-slate-100">
                        ₹{(t.cost || t.proceeds)?.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

