import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from './layouts/DashboardLayout';
import { DashboardPage } from './pages/DashboardPage';
import { MarketOverviewPage } from './pages/MarketOverviewPage';
import { StockResearchPage } from './pages/StockResearchPage';
import { SentimentExplorerPage } from './pages/SentimentExplorerPage';
import { BacktestingLabPage } from './pages/BacktestingLabPage';
import { PortfolioSimulatorPage } from './pages/PortfolioSimulatorPage';
import { RAGAssistantPage } from './pages/RAGAssistantPage';
import { WatchlistPage } from './pages/WatchlistPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="market" element={<MarketOverviewPage />} />
          <Route path="stocks" element={<StockResearchPage />} />
          <Route path="research" element={<Navigate to="/stocks" replace />} />
          <Route path="sentiment" element={<SentimentExplorerPage />} />
          <Route path="assistant" element={<RAGAssistantPage />} />
          <Route path="backtesting" element={<BacktestingLabPage />} />
          <Route path="portfolio" element={<PortfolioSimulatorPage />} />
          <Route path="watchlist" element={<WatchlistPage />} />
          <Route path="ml-lab" element={<Navigate to="/stocks" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
