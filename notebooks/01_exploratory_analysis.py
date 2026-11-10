"""
SENTIMENT-APLHA — Quantitative Research & Exploratory Analysis
Examines multi-year NSE market returns, FinBERT sentiment distributions,
correlation matrices, and model feature importances.
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np
from backend.database.connection import SessionLocal
from backend.database.models import Stock, PriceHistory, DailySentiment, MLModelRecord

def run_analysis():
    db = SessionLocal()
    try:
        stocks = db.query(Stock).all()
        print(f"Total Tracked Indian Equities: {len(stocks)}")
        for s in stocks:
            print(f"- {s.symbol} ({s.name}) | Sector: {s.sector} | PE: {s.pe_ratio} | ROE: {s.roe}%")

        models = db.query(MLModelRecord).order_by(MLModelRecord.f1_score.desc()).all()
        print(f"\nTop Performing Calibrated Models (Test Set F1 Ranking):")
        for m in models[:5]:
            print(f"[{m.model_name}] F1: {m.f1_score:.3f} | Accuracy: {m.accuracy*100:.1f}% | ROC-AUC: {m.roc_auc:.3f} | Sharpe: {m.strategy_sharpe:.2f}")

    finally:
        db.close()

if __name__ == "__main__":
    run_analysis()

