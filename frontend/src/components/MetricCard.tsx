import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: string | number;
  isPositive?: boolean;
  icon?: React.ReactNode;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  change,
  isPositive,
  icon,
}) => {
  return (
    <div className="bg-[#0f172a] border border-[#334155] rounded-lg p-4 hover:border-slate-500 transition-colors">
      <div className="flex items-center justify-between text-slate-400 mb-2">
        <span className="text-xs uppercase tracking-wider font-medium">{title}</span>
        {icon && <span className="text-slate-400">{icon}</span>}
      </div>
      <div className="flex items-baseline justify-between">
        <div className="text-2xl font-bold font-mono text-slate-100">{value}</div>
        {change !== undefined && (
          <span
            className={`text-xs font-mono font-semibold ${
              isPositive ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {isPositive ? '▲ ' : '▼ '}
            {change}
          </span>
        )}
      </div>
      {subtitle && <div className="text-xs text-slate-400 mt-1">{subtitle}</div>}
    </div>
  );
};

