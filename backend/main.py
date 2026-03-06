from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import engine, Base
from api import strategies, backtest, signals, notify, watchlist, stocks

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(notify.router, prefix="/api/notify", tags=["notify"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])

@app.get("/")
def root():
    return {"message": "Quant Trader API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
