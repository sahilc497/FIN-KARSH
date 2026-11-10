import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import {
  Radio,
  MessageSquare,
  Newspaper,
  Send,
  Sparkles,
  TrendingUp,
  RefreshCw,
  ArrowRightLeft,
  ThumbsUp,
  MessageCircle,
} from 'lucide-react';

export const SentimentExplorerPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'comparison' | 'news' | 'reddit' | 'classifier'>('comparison');
  const [inputText, setInputText] = useState<string>(
    'Tata Motors EV deliveries surge 25% YoY with strong order backlog in commercial vehicles'
  );
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [liveResult, setLiveResult] = useState<any>(null);
  const [overview, setOverview] = useState<any>(null);
  const [comparison, setComparison] = useState<any[]>([]);
  const [news, setNews] = useState<any[]>([]);
  const [reddit, setReddit] = useState<any[]>([]);
  const [redditTrends, setRedditTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [syncingReddit, setSyncingReddit] = useState<boolean>(false);

  const fetchSentimentData = async () => {
    try {
      const [ovRes, compRes, newsRes, redRes, trendsRes] = await Promise.all([
        api.getSentimentOverview(),
        api.getSentimentComparison().catch(() => []),
        api.getFinancialNews(undefined, 25),
        api.getRedditDiscussions(25),
        api.getRedditTrends(10).catch(() => []),
      ]);
      setOverview(ovRes);
      setComparison(compRes || []);
      setNews(newsRes || []);
      setReddit(redRes || []);
      setRedditTrends(trendsRes || []);
    } catch (err) {
      console.error('Failed to load sentiment data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSentimentData();
  }, []);

  const handleSyncReddit = async () => {
    setSyncingReddit(true);
    try {
      await api.syncReddit();
      await fetchSentimentData();
    } catch (err) {
      console.error('Sync failed:', err);
    } finally {
      setSyncingReddit(false);
    }
  };

  const handleClassifyText = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    setAnalyzing(true);
    try {
      const res = await api.analyzeText(inputText);
      setLiveResult(res);
    } catch (err) {
      console.error('Classification error:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-slate-400 gap-3">
        <RefreshCw className="w-8 h-8 animate-spin text-sky-400" />
        <span className="font-mono text-sm">Aggregating FinBERT news and Reddit sentiment feeds...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="pb-4 border-b border-[#334155] flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold font-mono tracking-tight text-slate-100 flex items-center gap-2">
            <Radio className="w-5 h-5 text-emerald-400" />
            FINBERT SENTIMENT INTELLIGENCE ENGINE
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Dual-channel NLP analysis separating official financial media from Reddit retail investor discussions.
          </p>
        </div>

        <button
          onClick={handleSyncReddit}
          disabled={syncingReddit}
          className="px-3 py-1.5 rounded bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-mono font-medium flex items-center gap-2 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${syncingReddit ? 'animate-spin' : ''}`} />
          {syncingReddit ? 'Ingesting Reddit...' : 'Sync Reddit & Feeds'}
        </button>
      </div>

      {/* Sentiment Channel Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-4">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1">
            <span>COMBINED MARKET SENTIMENT</span>
            <Radio className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400">
            {overview?.market_sentiment_score !== undefined
              ? (overview.market_sentiment_score > 0 ? `+${overview.market_sentiment_score}` : overview.market_sentiment_score)
              : '+0.42'}
          </div>
          <div className="text-xs font-mono text-slate-400 mt-2">
            Status: <strong className="text-slate-200">{overview?.market_sentiment_label || 'Bullish'}</strong>
          </div>
        </div>

        <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-4">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1">
            <span>FINANCIAL NEWS MEDIA SENTIMENT</span>
            <Newspaper className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-slate-100">
            {overview?.market_news_sentiment !== undefined
              ? (overview.market_news_sentiment > 0 ? `+${overview.market_news_sentiment}` : overview.market_news_sentiment)
              : '+0.45'}
          </div>
          <div className="text-xs font-mono text-slate-400 mt-2">
            Sources: Moneycontrol RSS, NSE Corporate Announcements
          </div>
        </div>

        <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-4">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1">
            <span>REDDIT RETAIL SENTIMENT</span>
            <MessageSquare className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-sky-400">
            {overview?.market_reddit_sentiment !== undefined
              ? (overview.market_reddit_sentiment > 0 ? `+${overview.market_reddit_sentiment}` : overview.market_reddit_sentiment)
              : '+0.38'}
          </div>
          <div className="text-xs font-mono text-slate-400 mt-2">
            Communities: r/IndianStockMarket, r/IndiaInvestments
          </div>
        </div>
      </div>

      {/* Tabs Header */}
      <div className="flex items-center gap-2 border-b border-[#1e293b] pb-2 font-mono text-xs">
        <button
          onClick={() => setActiveTab('comparison')}
          className={`px-3 py-1.5 rounded transition flex items-center gap-1.5 ${
            activeTab === 'comparison'
              ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <ArrowRightLeft className="w-3.5 h-3.5" />
          News vs. Reddit Comparison
        </button>
        <button
          onClick={() => setActiveTab('reddit')}
          className={`px-3 py-1.5 rounded transition flex items-center gap-1.5 ${
            activeTab === 'reddit'
              ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <MessageSquare className="w-3.5 h-3.5" />
          Reddit Retail Buzz ({reddit.length})
        </button>
        <button
          onClick={() => setActiveTab('news')}
          className={`px-3 py-1.5 rounded transition flex items-center gap-1.5 ${
            activeTab === 'news'
              ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Newspaper className="w-3.5 h-3.5" />
          Financial News Feed ({news.length})
        </button>
        <button
          onClick={() => setActiveTab('classifier')}
          className={`px-3 py-1.5 rounded transition flex items-center gap-1.5 ${
            activeTab === 'classifier'
              ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          Live FinBERT Classifier
        </button>
      </div>

      {/* Tab 1: Comparison & Divergence */}
      {activeTab === 'comparison' && (
        <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-5">
          <div className="flex items-center justify-between pb-3 border-b border-[#1e293b] mb-4">
            <h2 className="text-sm font-bold font-mono uppercase tracking-wider text-slate-200">
              Side-by-Side Channel Breakdown & Sentiment Divergence
            </h2>
            <span className="text-[11px] font-mono text-slate-400">
              *Divergence = Reddit Sentiment - News Sentiment
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#1e293b] text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="py-2.5 px-3">TICKER</th>
                  <th className="py-2.5 px-3">NAME</th>
                  <th className="py-2.5 px-3">NEWS SENTIMENT</th>
                  <th className="py-2.5 px-3">REDDIT SENTIMENT</th>
                  <th className="py-2.5 px-3">COMBINED</th>
                  <th className="py-2.5 px-3">DIVERGENCE</th>
                  <th className="py-2.5 px-3 text-right">ALIGNMENT STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {comparison.map((item: any) => {
                  const div = item.divergence ?? 0;
                  return (
                    <tr key={item.symbol} className="hover:bg-slate-800/40 transition">
                      <td className="py-2.5 px-3 font-bold text-slate-100">{item.symbol}</td>
                      <td className="py-2.5 px-3 text-slate-300">{item.name}</td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`font-bold ${
                            item.news_sentiment > 0 ? 'text-emerald-400' : item.news_sentiment < 0 ? 'text-rose-400' : 'text-slate-400'
                          }`}
                        >
                          {item.news_sentiment > 0 ? `+${item.news_sentiment}` : item.news_sentiment}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`font-bold ${
                            item.reddit_sentiment > 0 ? 'text-sky-400' : item.reddit_sentiment < 0 ? 'text-rose-400' : 'text-slate-400'
                          }`}
                        >
                          {item.reddit_sentiment > 0 ? `+${item.reddit_sentiment}` : item.reddit_sentiment}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-bold text-slate-100">
                        {item.combined_sentiment > 0 ? `+${item.combined_sentiment}` : item.combined_sentiment}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={div > 0 ? 'text-sky-400 font-bold' : div < 0 ? 'text-amber-400 font-bold' : 'text-slate-400'}>
                          {div > 0 ? `+${div}` : div}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            item.alignment === 'Aligned'
                              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                              : item.alignment === 'Retail More Bullish'
                              ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
                              : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                          }`}
                        >
                          {item.alignment}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Reddit Retail Buzz */}
      {activeTab === 'reddit' && (
        <div className="space-y-6">
          {/* Trending Tickers in Reddit */}
          <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-5">
            <h2 className="text-sm font-bold font-mono uppercase tracking-wider text-slate-200 mb-4 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-sky-400" />
              Most Discussed Tickers Across Indian Subreddits
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
              {redditTrends.map((t: any) => (
                <div key={t.symbol} className="p-3 rounded bg-slate-900/60 border border-[#1e293b]">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-xs text-slate-100">{t.symbol}</span>
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.2 rounded font-bold ${
                        t.reddit_sentiment_score > 0.05
                          ? 'bg-emerald-500/15 text-emerald-400'
                          : t.reddit_sentiment_score < -0.05
                          ? 'bg-rose-500/15 text-rose-400'
                          : 'bg-slate-700 text-slate-300'
                      }`}
                    >
                      {t.sentiment_label}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono mt-1">{t.name}</div>
                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-400">
                    <span>{t.mentions} posts</span>
                    <span>Score: {t.reddit_sentiment_score > 0 ? `+${t.reddit_sentiment_score}` : t.reddit_sentiment_score}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Reddit Posts List */}
          <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-5">
            <h2 className="text-sm font-bold font-mono uppercase tracking-wider text-slate-200 mb-4">
              Recent Retail Discussion Threads
            </h2>
            <div className="space-y-3">
              {reddit.map((post: any) => (
                <div key={post.id} className="p-3.5 rounded bg-slate-900/50 border border-[#1e293b] hover:border-slate-700 transition">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[11px] font-mono text-sky-400 font-semibold">r/{post.subreddit}</span>
                        <span className="text-slate-600">•</span>
                        <span className="text-[11px] font-mono text-slate-400">{new Date(post.created_at).toLocaleDateString()}</span>
                        {post.ticker_mentions && (
                          <span className="px-1.5 py-0.2 rounded bg-slate-800 text-[10px] font-mono text-emerald-400 border border-slate-700">
                            {post.ticker_mentions}
                          </span>
                        )}
                      </div>
                      <h3 className="text-xs font-medium text-slate-100 leading-snug">{post.title}</h3>
                      {post.text && <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{post.text}</p>}
                    </div>
                    {post.sentiment_label && (
                      <span
                        className={`shrink-0 px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          post.sentiment_label === 'Positive'
                            ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                            : post.sentiment_label === 'Negative'
                            ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                            : 'bg-slate-700 text-slate-300'
                        }`}
                      >
                        {post.sentiment_label} ({post.sentiment_score > 0 ? `+${post.sentiment_score}` : post.sentiment_score})
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 mt-2.5 pt-2 border-t border-slate-800/60 text-[10px] font-mono text-slate-400">
                    <span className="flex items-center gap-1">
                      <ThumbsUp className="w-3 h-3 text-sky-400" /> {post.score} upvotes
                    </span>
                    <span className="flex items-center gap-1">
                      <MessageCircle className="w-3 h-3 text-slate-400" /> {post.num_comments} comments
                    </span>
                    <span>Upvote Ratio: {((post.upvote_ratio || 1) * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Financial News Feed */}
      {activeTab === 'news' && (
        <div className="bg-[#0f172a] border border-[#1e293b] rounded-lg p-5">
          <h2 className="text-sm font-bold font-mono uppercase tracking-wider text-slate-200 mb-4">
            Curated Financial News Articles & FinBERT Scoring
          </h2>
          <div className="space-y-3">
            {news.map((item: any) => (
              <div key={item.id} className="p-3.5 rounded bg-slate-900/50 border border-[#1e293b] hover:border-slate-700 transition">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs font-medium text-slate-100 hover:text-sky-400 transition leading-snug"
                    >
                      {item.headline}
                    </a>
                    {item.summary && <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{item.summary}</p>}
                  </div>
                  {item.sentiment_label && (
                    <span
                      className={`shrink-0 px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        item.sentiment_label === 'Positive'
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                          : item.sentiment_label === 'Negative'
                          ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                          : 'bg-slate-700 text-slate-300'
                      }`}
                    >
                      {item.sentiment_label}
                    </span>
                  )}
                </div>
                <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-slate-800/60 text-[10px] font-mono text-slate-400">
                  <span className="text-sky-400 font-semibold">{item.source}</span>
                  <span>{new Date(item.published_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 4: Live FinBERT Text Classifier */}
      {activeTab === 'classifier' && (
        <div className="bg-[#0f172a] border border-[#334155] rounded-lg p-5">
          <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-200 mb-3 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-sky-400" />
            Interactive FinBERT Text Classifier
          </h2>
          <form onSubmit={handleClassifyText} className="space-y-3">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              rows={3}
              className="w-full bg-[#1e293b] border border-[#334155] rounded p-3 text-xs font-mono text-slate-100 focus:outline-none focus:border-sky-400 placeholder-slate-500"
              placeholder="Type or paste any financial headline, statement, or earnings quote..."
            />
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={analyzing}
                className="px-4 py-2 rounded bg-sky-500 hover:bg-sky-400 text-slate-950 font-mono font-bold text-xs flex items-center gap-2 transition-colors disabled:opacity-50"
              >
                {analyzing ? 'Inference Running...' : 'Classify Sentiment'} <Send className="w-3.5 h-3.5" />
              </button>
            </div>
          </form>

          {liveResult && (
            <div className="mt-4 pt-4 border-t border-[#334155] grid grid-cols-2 sm:grid-cols-5 gap-3">
              <div className="bg-[#1e293b] p-3 rounded border border-[#334155]">
                <div className="text-[11px] font-mono text-slate-400">P(POSITIVE)</div>
                <div className="text-lg font-bold font-mono text-emerald-400">
                  {(liveResult.p_positive * 100).toFixed(1)}%
                </div>
              </div>
              <div className="bg-[#1e293b] p-3 rounded border border-[#334155]">
                <div className="text-[11px] font-mono text-slate-400">P(NEGATIVE)</div>
                <div className="text-lg font-bold font-mono text-rose-400">
                  {(liveResult.p_negative * 100).toFixed(1)}%
                </div>
              </div>
              <div className="bg-[#1e293b] p-3 rounded border border-[#334155]">
                <div className="text-[11px] font-mono text-slate-400">P(NEUTRAL)</div>
                <div className="text-lg font-bold font-mono text-slate-300">
                  {(liveResult.p_neutral * 100).toFixed(1)}%
                </div>
              </div>
              <div className="bg-[#1e293b] p-3 rounded border border-[#334155]">
                <div className="text-[11px] font-mono text-slate-400">NUMERICAL SCORE</div>
                <div className="text-lg font-bold font-mono text-sky-400">
                  {liveResult.sentiment_score > 0 ? `+${liveResult.sentiment_score}` : liveResult.sentiment_score}
                </div>
              </div>
              <div className="bg-[#1e293b] p-3 rounded border border-[#334155]">
                <div className="text-[11px] font-mono text-slate-400">CONFIDENCE</div>
                <div className="text-lg font-bold font-mono text-slate-100">
                  {(liveResult.confidence * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
