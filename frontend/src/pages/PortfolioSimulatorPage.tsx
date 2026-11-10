import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import {
  PieChart as PieIcon,
  Play,
  Plus,
  Trash2,
  TrendingUp,
  Shield,
  Layers,
  HelpCircle,
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
  PieChart,
  Pie,
  Cell,
} from 'recharts';

export const PortfolioSimulatorPage: React.FC = () => {
  const [stocks, setStocks] = useState<any[]>([]);
  const [capital, setCapital] = useState<number>(200000);
  const [horizon, setHorizon] = useState<number>(30);
  const [allocations, setAllocations] = useState<Array<{ symbol: string; weight: number }>>([
    { symbol: 'RELIANCE.NS', weight: 0.35 },
    { symbol: 'TCS.NS', weight: 0.35 },
    { symbol: 'HDFCBANK.NS', weight: 0.30 },
  ]);

  const [simulating, setSimulating] = useState<boolean>(false);
  const [results, setResults] = useState<any>(null);

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
    runSimulation();
  }, []);

  const runSimulation = async () => {
    setSimulating(true);
    try {
      const res = await api.simulatePortfolio({
        capital,
        allocations,
        horizon_days: horizon,
      });
      setResults(res);
    } catch (err) {
      console.error('Simulation error:', err);
    } finally {
      setSimulating(false);
    }
  };

  const handleAddStock = () => {
    const available = stocks.find((s) => !allocations.some((a) => a.symbol === s.symbol));
    if (available) {
      setAllocations([...allocations, { symbol: available.symbol, weight: 0.2 }]);
    }
  };

  const handleRemoveStock = (index: number) => {
    if (allocations.length <= 1) return;
    const updated = allocations.filter((_, i) => i !== index);
    setAllocations(updated);
  };

  const handleWeightChange = (index: number, val: number) => {
    const updated = [...allocations];
    updated[index].weight = val;
    setAllocations(updated);
  };

  const COLORS = ['#38bdf8', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#64748b'];

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="pb-4 border-b border-[#334155]">
        <h1 className="text-xl font-bold font-mono tracking-tight text-slate-100 flex items-center gap-2">
          <PieIcon className="w-5 h-5 text-sky-400" />
          MULTI-ASSET PORTFOLIO SIMULATOR & SCENARIO ENGINE
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Model hypothetical capital allocations across Indian equities. Computes portfolio covariance,
          diversification indices, and Monte Carlo scenario trajectories (Expected, 95% Optimistic, 5% Pessimistic).
        </p>
      </div>

      {/* Allocation Configuration Grid */}
      <div className="bg-[#0f172a] border border-[#334155] rounded-lg p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4 pb-3 border-b border-[#334155]">
          <div className="flex items-center gap-4">
            <div>
              <label className="text-xs font-mono font-semibold text-slate-400 block mb-1">TOTAL CAPITAL (₹):</label>
              <input
                type="number"
                value={capital}
                onChange={(e) => setCapital(Number(e.target.value))}
                step={25000}
                className="bg-[#1e293b] border border-[#334155] rounded px-3 py-1.5 text-xs font-mono text-slate-100 focus:outline-none focus:border-sky-400"
              />
            </div>
            <div>
              <label className="text-xs font-mono font-semibold text-slate-400 block mb-1">HORIZON (DAYS):</label>
              <select
                value={horizon}
                onChange={(e) => setHorizon(Number(e.target.value))}
                className="bg-[#1e293b] border border-[#334155] rounded px-3 py-1.5 text-xs font-mono text-slate-100 focus:outline-none focus:border-sky-400"
              >
                <option value={5}>5 Trading Days</option>
                <option value={10}>10 Trading Days</option>
                <option value={30}>30 Trading Days</option>
                <option value={90}>90 Trading Days</option>
              </select>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleAddStock}
              className="px-3 py-1.5 rounded bg-[#1e293b] hover:bg-slate-700 text-sky-400 text-xs font-mono flex items-center gap-1 border border-[#334155]"
            >
              <Plus className="w-3.5 h-3.5" /> Add Holding
            </button>
            <button
              onClick={runSimulation}
              disabled={simulating}
              className="px-4 py-1.5 rounded bg-sky-500 hover:bg-sky-400 text-slate-950 font-mono font-bold text-xs flex items-center gap-1.5 transition-colors disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 ${simulating ? 'animate-spin' : ''}`} />
              {simulating ? 'Simulating...' : 'Run Simulation'}
            </button>
          </div>
        </div>

        {/* Dynamic Holding Weight Sliders */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {allocations.map((item, idx) => (
            <div key={idx} className="bg-[#1e293b]/70 border border-[#334155] p-3 rounded">
              <div className="flex items-center justify-between mb-2">
                <select
                  value={item.symbol}
                  onChange={(e) => {
                    const updated = [...allocations];
                    updated[idx].symbol = e.target.value;
                    setAllocations(updated);
                  }}
                  className="bg-[#0f172a] border border-[#334155] rounded px-2 py-1 text-xs font-mono text-slate-100"
                >
                  {stocks.map((s) => (
                    <option key={s.symbol} value={s.symbol}>
                      {s.symbol}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => handleRemoveStock(idx)}
                  className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1">
                <span>Weight Allocation:</span>
                <span className="text-sky-400 font-bold">{(item.weight * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="1.0"
                step="0.05"
                value={item.weight}
                onChange={(e) => handleWeightChange(idx, Number(e.target.value))}
                className="w-full accent-sky-400"
              />
            </div>
          ))}
        </div>
      </div>

      {results && (
        <>
          {/* Key Portfolio Characteristics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-[#0f172a] p-4 rounded-lg border border-[#334155]">
              <div className="text-xs font-mono text-slate-400">ANNUALIZED RETURN</div>
              <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                {results.annualized_return_pct >= 0 ? `+${results.annualized_return_pct}%` : `${results.annualized_return_pct}%`}
              </div>
              <div className="text-xs text-slate-400 mt-1">Historical Compound</div>
            </div>

            <div className="bg-[#0f172a] p-4 rounded-lg border border-[#334155]">
              <div className="text-xs font-mono text-slate-400">ANNUALIZED VOLATILITY</div>
              <div className="text-2xl font-bold font-mono text-slate-100 mt-1">
                {results.annualized_volatility_pct}%
              </div>
              <div className="text-xs text-slate-400 mt-1">Historical σ</div>
            </div>

            <div className="bg-[#0f172a] p-4 rounded-lg border border-[#334155]">
              <div className="text-xs font-mono text-slate-400">PORTFOLIO SHARPE</div>
              <div className="text-2xl font-bold font-mono text-sky-400 mt-1">
                {results.sharpe_ratio}
              </div>
              <div className="text-xs text-slate-400 mt-1">Risk-adjusted return</div>
            </div>

            <div className="bg-[#0f172a] p-4 rounded-lg border border-[#334155]">
              <div className="text-xs font-mono text-slate-400">DIVERSIFICATION SCORE</div>
              <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                {results.diversification_score} / 100
              </div>
              <div className="text-xs text-slate-400 mt-1">Herfindahl Multi-Sector</div>
            </div>
          </div>

          {/* Monte Carlo Scenario Projections Chart */}
          <div className="bg-[#0f172a] border border-[#334155] rounded-lg p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-200">
                Monte Carlo Forward Simulation ({horizon} Trading Days Trajectory)
              </h2>
              <span className="text-xs text-slate-400 font-mono">500 Geometric Paths</span>
            </div>

            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={results.scenario_projections}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 10 }} label={{ value: 'Day', position: 'insideBottom', offset: -5 }} />
                  <YAxis
                    stroke="#94a3b8"
                    tick={{ fontSize: 11 }}
                    domain={['auto', 'auto']}
                    tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }}
                    formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, 'Portfolio Value']}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px' }} />
                  <Line
                    type="monotone"
                    name="Optimistic Path (95th Percentile)"
                    dataKey="optimistic"
                    stroke="#10b981"
                    strokeWidth={1.5}
                    strokeDasharray="4 4"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    name="Expected Path (Mean Outcome)"
                    dataKey="expected"
                    stroke="#38bdf8"
                    strokeWidth={2.5}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    name="Pessimistic Path (5th Percentile)"
                    dataKey="pessimistic"
                    stroke="#f43f5e"
                    strokeWidth={1.5}
                    strokeDasharray="4 4"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Projected Terminal Outcomes Summary */}
            <div className="mt-4 pt-3 border-t border-[#334155] grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono text-center">
              <div className="bg-[#1e293b] p-2.5 rounded">
                <span className="text-rose-400 block font-semibold">Pessimistic 5% Outcome:</span>
                <span className="text-slate-100 font-bold text-sm">
                  ₹{results.projected_outcomes.pessimistic_final.toLocaleString()}
                </span>
              </div>
              <div className="bg-[#1e293b] p-2.5 rounded">
                <span className="text-sky-400 block font-semibold">Expected Mean Outcome:</span>
                <span className="text-slate-100 font-bold text-sm">
                  ₹{results.projected_outcomes.expected_final.toLocaleString()}
                </span>
              </div>
              <div className="bg-[#1e293b] p-2.5 rounded">
                <span className="text-emerald-400 block font-semibold">Optimistic 95% Outcome:</span>
                <span className="text-slate-100 font-bold text-sm">
                  ₹{results.projected_outcomes.optimistic_final.toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* Holding Breakdown and Sector Allocation */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Holdings Table */}
            <div className="bg-[#0f172a] border border-[#334155] rounded-lg p-5">
              <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-200 mb-4">
                Simulated Capital Distribution
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-[#1e293b] text-slate-400 border-b border-[#334155]">
                    <tr>
                      <th className="py-2 px-3">TICKER</th>
                      <th className="py-2 px-3">SECTOR</th>
                      <th className="py-2 px-3">WEIGHT</th>
                      <th className="py-2 px-3 text-right">CAPITAL ALLOCATED</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1e293b]">
                    {results.allocations.map((a: any, i: number) => (
                      <tr key={i} className="hover:bg-[#1e293b]/40">
                        <td className="py-2.5 px-3 font-bold text-slate-100">{a.symbol}</td>
                        <td className="py-2.5 px-3 text-slate-400">{a.sector}</td>
                        <td className="py-2.5 px-3 font-semibold text-sky-400">{a.weight_pct}%</td>
                        <td className="py-2.5 px-3 text-right text-slate-200 font-bold">
                          ₹{a.allocated_amount.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Sector Diversification Pie Chart */}
            <div className="bg-[#0f172a] border border-[#334155] rounded-lg p-5">
              <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-200 mb-4">
                Sector Allocation Weights (%)
              </h2>
              <div className="h-48 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={results.sector_breakdown}
                      dataKey="weight"
                      nameKey="sector"
                      cx="50%"
                      cy="50%"
                      outerRadius={70}
                      label={({ sector, weight }) => `${sector} (${weight}%)`}
                    >
                      {results.sector_breakdown.map((_: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }}
                      formatter={(val: any) => [`${val}%`, 'Sector Weight']}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

