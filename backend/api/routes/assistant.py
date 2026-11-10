from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database.connection import get_db
from backend.rag.assistant import RAGFinancialAssistant
from backend.rag.gemini_service import GeminiService

router = APIRouter(prefix="/assistant", tags=["RAG Assistant"])


class QueryRequest(BaseModel):
    prompt: str


@router.post("/query")
def chat_with_rag_assistant(req: QueryRequest, db: Session = Depends(get_db)):
    assistant = RAGFinancialAssistant(db)
    response = assistant.query(req.prompt)
    return response


@router.get("/status")
def get_assistant_engine_status():
    """Returns AI model configuration status (Gemini API vs Local Quant RAG Engine)."""
    gemini = GeminiService()
    is_active = gemini.is_configured()
    return {
        "engine": "Google Gemini API" if is_active else "SENTIMENT-APLHA Local Quant RAG",
        "gemini_active": is_active,
        "model": gemini.model if is_active else "Loughran-McDonald Grounded Engine",
        "features": [
            "Financial Knowledge Base (NSE, NIFTY, IPOs, P/E, EPS, ETFs, Mutual Funds)",
            "Grounded Multi-Source Context (Prices, Fundamentals, News & Reddit Sentiment)",
            "Machine Learning Directional Predictions & Factor Attribution",
            "Zero Hallucination Constraint with Citations & Risk Disclaimers"
        ]
    }


@router.get("/prompts")
def get_example_prompts():
    """Returns curated example prompts for interactive testing across all domains."""
    return [
        "What is the difference between NIFTY 50 and NIFTY NEXT 50?",
        "Explain P/E ratio and EPS with examples from Indian stocks.",
        "Analyse Reliance Industries using its latest available financial data.",
        "Compare TCS, Infosys and Wipro.",
        "Show the sentiment of recent news and Reddit retail buzz about Tata Motors.",
        "How do IPO anchor investors and retail quotas work in India?",
        "I have ₹10,000 available for investment. Explain possible investment approaches.",
        "My monthly salary is ₹50,000 and my monthly expenses are ₹25,000. How much can I potentially save?",
        "What happened to NIFTY 50 over the past 10 days?",
        "Explain why this stock received a high model score."
    ]
