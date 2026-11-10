import React from 'react';

interface FinbertStatusBadgeProps {
  score: number;
  confidence?: number;
  momentum?: number;
  showDetails?: boolean;
}

export const FinbertStatusBadge: React.FC<FinbertStatusBadgeProps> = ({
  score,
  confidence,
  momentum,
  showDetails = false,
}) => {
  let label = 'NEUTRAL';
  let badgeColor = 'bg-slate-800 text-slate-300 border-slate-700';

  if (score >= 0.25) {
    label = 'BULLISH';
    badgeColor = 'bg-emerald-950/80 text-emerald-400 border-emerald-800';
  } else if (score <= -0.25) {
    label = 'BEARISH';
    badgeColor = 'bg-rose-950/80 text-rose-400 border-rose-800';
  }

  return (
    <div className="inline-flex items-center gap-2">
      <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-medium border ${badgeColor}`}>
        {label} ({score > 0 ? `+${score.toFixed(2)}` : score.toFixed(2)})
      </span>
      {showDetails && momentum !== undefined && (
        <span className="text-xs font-mono text-slate-400">
          5d Δ: <span className={momentum >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
            {momentum >= 0 ? `+${momentum.toFixed(2)}` : momentum.toFixed(2)}
          </span>
        </span>
      )}
    </div>
  );
};

