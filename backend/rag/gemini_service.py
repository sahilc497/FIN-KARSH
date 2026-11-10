"""
Dedicated Backend Service for Google Gemini API integration.
Manages API requests, system instruction grounding, security (API key kept strictly backend-side),
and graceful fallback handling.
"""

import os
import logging
from typing import Optional, Dict, Any, List
import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

GEMINI_SYSTEM_INSTRUCTION = """You are SENTIMENT-APLHA's Senior AI Financial Analyst and Quantitative Researcher.
You specialize in Indian capital markets (NSE, NIFTY 50), fundamental analysis, technical indicators,
FinBERT news & Reddit sentiment analysis, and machine learning directional predictions.

Strict Rules of Conduct:
1. Ground your answers strictly in the retrieved context, factual market data, and financial principles provided.
2. Provide source references and timestamps for all financial facts, prices, and metrics.
3. Clearly distinguish between HISTORICAL FACTS (past prices, financial statement ratios, historical news) and PREDICTIONS / MODEL PROJECTIONS.
4. DO NOT invent or hallucinate financial figures. If a metric or figure is not present in the provided context, explicitly state that it is unavailable.
5. Clearly explain the downside financial risks and market volatility for any discussed asset or strategy.
6. NEVER guarantee investment returns or provide direct unsolicited buy/sell mandates. All statements must be educational and risk-calibrated.
7. Format responses using clean markdown: headers, bullet points, and tables where comparative data is discussed.
"""

class GeminiService:
    """Dedicated backend client communicating with Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        # Filter out placeholder keys
        if self.api_key in ["your_gemini_api_key_here", "AIzaSy_placeholder", ""]:
            self.api_key = ""

        self.model = model or settings.GEMINI_MODEL or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def is_configured(self) -> bool:
        """Returns True if a valid-looking Gemini API key is configured."""
        return bool(self.api_key and len(self.api_key) > 10)

    def generate(self, user_prompt: str, context_str: str) -> Optional[str]:
        """
        Sends grounded prompt and context to Gemini REST API.
        Returns generated text or None if offline/error.
        """
        if not self.is_configured():
            logger.info("Gemini API key not configured. Using grounded local RAG synthesis.")
            return None

        payload = {
            "system_instruction": {
                "parts": [{"text": GEMINI_SYSTEM_INSTRUCTION}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                f"=== RETRIEVED GROUNDED CONTEXT FROM SENTIMENT-APLHA DATABASE & KNOWLEDGE BASE ===\n"
                                f"{context_str}\n"
                                f"=== END RETRIEVED CONTEXT ===\n\n"
                                f"USER QUESTION: {user_prompt}\n\n"
                                f"Please analyze and answer accurately following all professional guidelines and citations."
                            )
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.85,
                "maxOutputTokens": 1500
            }
        }

        try:
            url = f"{self.endpoint}?key={self.api_key}"
            with httpx.Client(timeout=8.0) as client:
                response = client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                else:
                    logger.warning(f"Gemini API returned HTTP {response.status_code}: {response.text[:200]}")
                    return None
        except Exception as e:
            logger.warning(f"Gemini API request failed ({e}). Reverting to grounded local synthesis.")
            return None

        return None

