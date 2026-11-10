import pytest
from backend.database.connection import SessionLocal
from backend.rag.assistant import RAGFinancialAssistant

def test_rag_salary_savings():
    db = SessionLocal()
    try:
        assistant = RAGFinancialAssistant(db)
        prompt = "My monthly salary is ₹50,000 and my monthly expenses are ₹25,000. How much can I potentially save?"
        res = assistant.query(prompt)
        assert "₹25,000" in res["answer"]
        assert len(res["citations"]) > 0
    finally:
        db.close()

def test_rag_stock_analysis():
    db = SessionLocal()
    try:
        assistant = RAGFinancialAssistant(db)
        prompt = "Analyse Reliance Industries using its latest available financial data."
        res = assistant.query(prompt)
        assert "Reliance Industries" in res["answer"]
        assert "P/E" in res["answer"]
        assert len(res["citations"]) > 0
    finally:
        db.close()

