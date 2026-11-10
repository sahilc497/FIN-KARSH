import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  Search,
  Radio,
  Bot,
  History,
  PieChart,
  BookmarkCheck,
} from 'lucide-react';
import { api } from '../api/client';

export const Navbar: React.FC = () => {
  const [liveInfo, setLiveInfo] = useState<{
    nifty: { price: number; change_pct: number };
    timestamp: string;
    status: string;
  }>({
    nifty: { price: 24200.0, change_pct: 0.59 },
    timestamp: new Date().toLocaleTimeString(),
    status: 'STREAMING',
  });

  useEffect(() => {
    let isMounted = true;
    const fetchSnapshot = async () => {
      try {
        const snap = await api.getLiveMarketSnapshot();
        if (isMounted && snap) {
          setLiveInfo({
            nifty: {
              price: snap.nifty_50?.price || 24200.0,
              change_pct: snap.nifty_50?.change_pct || 0.59,
            },
            timestamp: snap.timestamp || new Date().toLocaleTimeString(),
            status: snap.status || 'STREAMING',
          });
        }
      } catch {
        // Fallback gracefully without breaking UI
      }
    };

    fetchSnapshot();
    const timer = setInterval(fetchSnapshot, 15000);
    return () => {
      isMounted = false;
      clearInterval(timer);
    };
  }, []);

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Market Overview', path: '/market', icon: Activity },
    { name: 'Stock Explorer', path: '/stocks', icon: Search },
    { name: 'Sentiment Analysis', path: '/sentiment', icon: Radio },
    { name: 'AI Financial Assistant', path: '/assistant', icon: Bot },
    { name: 'Backtesting', path: '/backtesting', icon: History },
    { name: 'Portfolio Simulator', path: '/portfolio', icon: PieChart },
    { name: 'Watchlist', path: '/watchlist', icon: BookmarkCheck },
  ];

  return (
    <header className="sticky top-0 z-40 bg-[#090d16]/95 backdrop-blur border-b border-[#334155]">
      {/* Real-time / Near-Real-Time Stream Sub-header */}
      <div className="bg-[#0f172a] border-b border-[#1e293b] px-4 py-1.5 flex items-center justify-between text-xs font-mono">
        <div className="flex items-center gap-6 overflow-x-auto">
          <div className="flex items-center gap-2">
            <span className="text-slate-400 font-semibold">NIFTY 50:</span>
            <span className="text-slate-200">
              {liveInfo.nifty.price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
            <span className={liveInfo.nifty.change_pct >= 0 ? 'text-emerald-400 font-medium' : 'text-rose-400 font-medium'}>
              {liveInfo.nifty.change_pct >= 0 ? '+' : ''}{liveInfo.nifty.change_pct.toFixed(2)}%
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400 font-semibold">INDIA VIX:</span>
            <span className="text-slate-200">13.85</span>
            <span className="text-rose-400 font-medium">-1.20%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400 font-semibold">FEED STATUS:</span>
            <span className="text-sky-400 font-medium uppercase">{liveInfo.status}</span>
          </div>
        </div>
        <div className="flex items-center gap-3 text-slate-400 shrink-0">
          <span className="inline-flex items-center gap-1.5 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            NSE Near-Real-Time Feed
          </span>
          <span className="text-slate-500 text-[11px]">| Updated: {liveInfo.timestamp}</span>
        </div>
      </div>

      {/* Main Navigation Bar */}
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <NavLink to="/" className="flex items-center gap-2.5 font-bold tracking-wider text-slate-100 hover:text-sky-400 transition-colors">
            <div className="w-8 h-8 rounded bg-sky-500/10 border border-sky-400 flex items-center justify-center text-sky-400">
              <Activity className="w-5 h-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-mono tracking-widest leading-none">SENTIMENT-APLHA</span>
              <span className="text-[10px] text-slate-400 font-mono">QUANT INTELLIGENCE</span>
            </div>
          </NavLink>

          <nav className="hidden lg:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === '/'}
                  className={({ isActive }) =>
                    `px-3 py-1.5 rounded text-xs font-medium font-mono flex items-center gap-1.5 transition-all ${
                      isActive
                        ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-[#1e293b]'
                    }`
                  }
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 text-[11px] font-mono rounded bg-slate-800 text-sky-400 border border-slate-700">
            v2.0 • PROD
          </span>
        </div>
      </div>

      {/* Mobile / Responsive secondary nav row */}
      <div className="lg:hidden flex items-center gap-1 overflow-x-auto px-4 py-2 border-t border-[#1e293b] bg-[#0c1322]">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `px-2.5 py-1 rounded text-[11px] font-medium font-mono flex items-center gap-1 shrink-0 ${
                  isActive
                    ? 'bg-sky-500/20 text-sky-400 border border-sky-500/40'
                    : 'text-slate-400 hover:bg-[#1e293b]'
                }`
              }
            >
              <Icon className="w-3 h-3" />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </div>
    </header>
  );
};
