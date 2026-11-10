import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

from backend.config import settings
from backend.database.connection import init_db, SessionLocal
from backend.database.models import Stock
from backend.api.routes import stocks, sentiment, models, recommendations, backtest, portfolio, assistant, health
from backend.services.market_updater import market_broadcaster

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sentiment_alpha")


async def periodic_market_broadcast():
    """Background task to broadcast market ticks periodically to streaming consumers."""
    while True:
        try:
            await asyncio.sleep(15)  # 15s refresh interval
            await market_broadcaster.broadcast_tick()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Broadcast cycle notice: {e}")
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB tables exist
    logger.info("Initializing database tables...")
    init_db()

    # Check if database is empty; if so, trigger initial seed
    db = SessionLocal()
    try:
        stock_count = db.query(Stock).count()
        if stock_count == 0:
            logger.info("Database empty. Auto-seeding initial stock universe and financial records...")
            from backend.collectors.stock_universe import StockUniverseManager
            manager = StockUniverseManager(db)
            manager.seed_core_universe()
            logger.info("Initial stock universe seeded successfully.")
    except Exception as e:
        logger.warning(f"Auto-seeding encountered notice: {e}")
    finally:
        db.close()

    # Start background market stream broadcaster
    broadcast_task = asyncio.create_task(periodic_market_broadcast())

    yield

    # Shutdown
    broadcast_task.cancel()
    try:
        await broadcast_task
    except asyncio.CancelledError:
        pass
    logger.info("Application shutdown.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Stock Market Sentiment Analysis, Prediction & Intelligent Investment Assistant",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(stocks.router, prefix=settings.API_PREFIX)
app.include_router(sentiment.router, prefix=settings.API_PREFIX)
app.include_router(models.router, prefix=settings.API_PREFIX)
app.include_router(recommendations.router, prefix=settings.API_PREFIX)
app.include_router(backtest.router, prefix=settings.API_PREFIX)
app.include_router(portfolio.router, prefix=settings.API_PREFIX)
app.include_router(assistant.router, prefix=settings.API_PREFIX)


# ==========================================
# Near-Real-Time Streaming Endpoints
# ==========================================

@app.websocket("/api/ws/market")
@app.websocket("/ws/market")
async def websocket_market_endpoint(websocket: WebSocket):
    """Real-time / Near-Real-Time WebSocket market quote and sentiment stream."""
    await market_broadcaster.connect_websocket(websocket)
    try:
        while True:
            # Keep connection open, receive ping or client commands
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        market_broadcaster.disconnect_websocket(websocket)
    except Exception:
        market_broadcaster.disconnect_websocket(websocket)


async def sse_market_generator() -> AsyncGenerator[str, None]:
    """Generates Server-Sent Events with latest market snapshot."""
    while True:
        snapshot = market_broadcaster.get_latest_market_snapshot()
        data_str = json.dumps(snapshot)
        yield f"data: {data_str}\n\n"
        await asyncio.sleep(12)


@app.get("/api/stream/market")
def stream_market_events():
    """Server-Sent Events (SSE) live market stream for HTTP clients."""
    return StreamingResponse(
        sse_market_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get(f"{settings.API_PREFIX}/market/live-snapshot")
@app.get("/api/market/live-snapshot")
def get_live_market_snapshot():
    """Provides instantaneous cached market snapshot with explicit timestamp and feed status."""
    return market_broadcaster.get_latest_market_snapshot()


@app.get("/")
def root_index():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "documentation": "/docs",
        "api_prefix": settings.API_PREFIX,
        "live_stream": {
            "websocket": "/api/ws/market",
            "sse": "/api/stream/market",
            "snapshot": "/api/market/live-snapshot"
        }
    }
