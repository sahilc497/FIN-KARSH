import pytest
from backend.database.connection import SessionLocal
from backend.api.routes import health, stocks, recommendations, assistant
from backend.api.routes.assistant import QueryRequest

def test_health_endpoint():
    db = SessionLocal()
    try:
        data = health.system_health_status(db)
        assert data["status"] == "healthy"
        assert data["counts"]["stocks"] > 0
    finally:
        db.close()

def test_stocks_endpoint():
    db = SessionLocal()
    try:
        stocks_list = stocks.list_stocks(db)
        assert len(stocks_list) > 0
    finally:
        db.close()

def test_recommendations_endpoint():
    db = SessionLocal()
    try:
        recs = recommendations.get_all_recommendations(horizon_days=5, db=db)
        assert len(recs) > 0
        assert "signal" in recs[0]
    finally:
        db.close()

def test_rag_assistant_endpoint():
    db = SessionLocal()
    try:
        req = QueryRequest(prompt="Compare TCS, Infosys and Wipro.")
        data = assistant.chat_with_rag_assistant(req, db=db)
        assert "TCS" in data["answer"]
        assert len(data["citations"]) > 0
    finally:
        db.close()
