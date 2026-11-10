import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

export const DisclaimerFooter: React.FC = () => {
  return (
    <footer className="mt-12 pt-6 pb-8 border-t border-[#334155] text-xs text-slate-400">
      <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <p>
            <strong className="text-slate-300">Regulatory Disclaimer:</strong> SENTIMENT-APLHA is an analytical,
            machine learning quantitative research platform. All signals, model probabilities, backtesting results,
            and RAG assistant responses are hypothetical mathematical estimates and do not constitute registered
            investment advice, SEBI recommendations, or guaranteed capital returns.
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0 text-slate-400">
          <ShieldCheck className="w-4 h-4 text-sky-400" />
          <span>NSE India Equity Universe (Delayed Feed)</span>
        </div>
      </div>
    </footer>
  );
};

