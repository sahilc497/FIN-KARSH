import pytest
from backend.database.connection import SessionLocal
from backend.sentiment.finbert_analyzer import FinBERTSentimentAnalyzer

def test_finbert_sentiment_classification():
    db = SessionLocal()
    try:
        analyzer = FinBERTSentimentAnalyzer(db)
        
        # Test positive financial text
        pos_text = "Reliance Retail reports historic record profit surge and rapid store expansion"
        pos_res = analyzer.analyze_text(pos_text)
        assert pos_res["sentiment_score"] > 0.0
        assert pos_res["p_positive"] > pos_res["p_negative"]
        
        # Test negative financial text
        neg_text = "Operating margins collapse amid severe debt default and sharp revenue decline"
        neg_res = analyzer.analyze_text(neg_text)
        assert neg_res["sentiment_score"] < 0.0
        assert neg_res["p_negative"] > neg_res["p_positive"]
    finally:
        db.close()
