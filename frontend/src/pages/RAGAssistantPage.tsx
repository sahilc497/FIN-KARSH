import React, { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';
import {
  Bot,
  User,
  Send,
  Sparkles,
  ShieldCheck,
  Clock,
  FileText,
  AlertTriangle,
  RefreshCw,
  Cpu,
} from 'lucide-react';

interface Citation {
  source: string;
  timestamp: string;
  datapoints: string;
}

interface ChatMessage {
  sender: 'user' | 'assistant';
  text: string;
  citations?: Citation[];
  isGeminiPowered?: boolean;
  modelUsed?: string;
}

export const RAGAssistantPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: 'assistant',
      text: `### Welcome to the SENTIMENT-APLHA Financial Intelligence Assistant\n\nI am grounded in verifiable Indian market data (NSE), audited corporate balance sheets, FinBERT sentiment records, and multi-factor ML models.\n\nAsk me about stock market fundamentals, NSE & NIFTY indices, P/E ratios, EPS, IPOs, mutual funds vs ETFs, risk management, or specific stock sentiment deep-dives.`,
    },
  ]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [examplePrompts, setExamplePrompts] = useState<string[]>([]);
  const [engineStatus, setEngineStatus] = useState<any>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchMeta = async () => {
      try {
        const [prompts, status] = await Promise.all([
          api.getExamplePrompts().catch(() => []),
          api.getAssistantStatus().catch(() => null),
        ]);
        setExamplePrompts(prompts || []);
        setEngineStatus(status);
      } catch (err) {
        console.error('Failed to load assistant metadata:', err);
      }
    };
    fetchMeta();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSubmit = async (textToSend: string) => {
    const prompt = textToSend.trim();
    if (!prompt || loading) return;

    setMessages((prev) => [...prev, { sender: 'user', text: prompt }]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.queryAssistant(prompt);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: res.answer,
          citations: res.citations,
          isGeminiPowered: res.is_gemini_powered,
          modelUsed: res.model_used,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: 'An error occurred while contacting the financial assistant service. Please check backend status.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Title & Engine Status Bar */}
      <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-emerald-400">
              RAG Knowledge Assistant Active
            </span>
            <span className="text-slate-500 text-xs font-mono">| Grounded Intelligence</span>
          </div>
          <h1 className="text-xl font-bold font-mono tracking-tight text-slate-100 mt-1 flex items-center gap-2">
            <Bot className="w-5 h-5 text-sky-400" />
            AI FINANCIAL KNOWLEDGE & QUANT ASSISTANT
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Strict source citations, zero hallucinated figures, risk-calibrated portfolio analysis, and no return guarantees.
          </p>
        </div>

        <div className="flex items-center gap-2.5 bg-slate-900 border border-slate-800 px-3 py-2 rounded-lg text-xs font-mono">
          <Cpu className="w-4 h-4 text-sky-400" />
          <div>
            <span className="text-slate-400 block text-[10px]">ACTIVE ENGINE</span>
            <span className="text-slate-200 font-bold">
              {engineStatus?.engine || 'Google Gemini / Local Quant RAG'}
            </span>
          </div>
        </div>
      </div>

      {/* Curated Financial Scenarios / Prompt Chips */}
      <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-4">
        <div className="text-xs font-mono font-semibold text-slate-300 mb-2.5 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          EXPLORE CURATED QUESTIONS & FINANCIAL SCENARIOS:
        </div>
        <div className="flex flex-wrap gap-2">
          {examplePrompts.map((p, idx) => (
            <button
              key={idx}
              onClick={() => handleSubmit(p)}
              disabled={loading}
              className="text-left px-3 py-1.5 rounded text-xs font-mono bg-slate-800/90 hover:bg-slate-700 text-slate-300 border border-slate-700 hover:border-sky-400 transition disabled:opacity-50"
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Thread */}
      <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-5 min-h-[460px] flex flex-col justify-between">
        <div className="space-y-6 overflow-y-auto max-h-[580px] pr-2">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3 text-xs leading-relaxed ${
                msg.sender === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {msg.sender === 'assistant' && (
                <div className="w-8 h-8 rounded bg-sky-500/10 border border-sky-400 flex items-center justify-center text-sky-400 shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-[85%] rounded-lg p-4 font-mono ${
                  msg.sender === 'user'
                    ? 'bg-sky-500/15 text-sky-100 border border-sky-500/30'
                    : 'bg-slate-900/90 text-slate-200 border border-slate-800'
                }`}
              >
                {/* Engine Badge if generated by Gemini or Quant engine */}
                {msg.sender === 'assistant' && msg.modelUsed && (
                  <div className="flex items-center gap-1.5 mb-2 pb-1.5 border-b border-slate-800 text-[10px] text-sky-400">
                    <ShieldCheck className="w-3 h-3 text-emerald-400" />
                    <span>Engine: {msg.modelUsed}</span>
                    {msg.isGeminiPowered && (
                      <span className="px-1.5 py-0.2 rounded bg-sky-900/60 text-sky-300 font-bold">
                        GEMINI
                      </span>
                    )}
                  </div>
                )}

                {/* Message Body */}
                <div className="prose prose-invert prose-xs max-w-none space-y-2 whitespace-pre-wrap">
                  {msg.text}
                </div>

                {/* Grounded Citations & Sources */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-slate-800 space-y-1.5">
                    <div className="text-[10px] font-bold text-slate-400 flex items-center gap-1 uppercase tracking-wider">
                      <FileText className="w-3 h-3 text-amber-400" />
                      Grounded Data Citations & Sources:
                    </div>
                    {msg.citations.map((c, cIdx) => (
                      <div
                        key={cIdx}
                        className="bg-slate-950/60 rounded p-2 text-[11px] text-slate-400 border border-slate-800/80 flex flex-col gap-0.5"
                      >
                        <div className="flex items-center justify-between text-slate-300 font-semibold">
                          <span>{c.source}</span>
                          <span className="text-[10px] text-slate-500 flex items-center gap-1">
                            <Clock className="w-2.5 h-2.5" /> {c.timestamp}
                          </span>
                        </div>
                        <div className="text-slate-400 text-[10px]">{c.datapoints}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {msg.sender === 'user' && (
                <div className="w-8 h-8 rounded bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0 mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-3 text-slate-400 font-mono text-xs p-3">
              <RefreshCw className="w-4 h-4 animate-spin text-sky-400" />
              <span>Synthesizing grounded market facts & FinBERT sentiment...</span>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit(input);
          }}
          className="mt-4 pt-3 border-t border-[#1e293b] flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder="Ask anything about NSE stocks, P/E ratio, IPOs, FinBERT sentiment, or savings..."
            className="flex-1 bg-slate-900 border border-[#334155] rounded px-4 py-2.5 text-xs font-mono text-slate-100 focus:outline-none focus:border-sky-400 placeholder-slate-500"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 py-2.5 rounded bg-sky-500 hover:bg-sky-400 text-slate-950 font-mono font-bold text-xs flex items-center gap-1.5 transition disabled:opacity-50"
          >
            Send <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>

      {/* Compliance & Risk Notice */}
      <div className="bg-slate-900/40 border border-slate-800 rounded p-3 text-[11px] font-mono text-slate-400 flex items-start gap-2">
        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <span>
          <strong>Regulatory Compliance Notice:</strong> SENTIMENT-APLHA provides quantitative financial analysis, NLP sentiment classification, and mathematical backtest models for research and education. Past performance is no guarantee of future returns. The platform never guarantees returns or provides individual buy/sell mandates.
        </span>
      </div>
    </div>
  );
};
