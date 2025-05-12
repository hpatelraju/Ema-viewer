from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import requests
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

COINGECKO_API = "https://api.coingecko.com/api/v3"

# EMA periods by timeframe
EMA_PERIODS = {
    "1m": [5, 10],
    "5m": [5, 15],
    "15m": [10, 25],
    "30m": [10, 30],
    "1h": [10, 50],
    "2h": [20, 60],
    "4h": [25, 75],
    "6h": [30, 90],
    "8h": [35, 105],
    "12h": [40, 120],
    "1d": [10, 20, 50, 100],
    "3d": [20, 50, 100],
    "1w": [10, 20, 50],
    "1M": [10, 20, 50]
}

@app.get("/api/ema")
def fetch_ema(
    coin_id: str = Query("dogecoin", description="Coin ID (e.g., dogecoin)"),
    vs_currency: str = Query("usd", description="Target currency (e.g., usd)")
):
    try:
        url = f"{COINGECKO_API}/coins/{coin_id}/market_chart?vs_currency={vs_currency}&days=90"
        response = requests.get(url)
        if response.status_code != 200:
            return {"error": f"Failed to fetch data: {response.text}"}

        data = response.json().get("prices", [])
        df = pd.DataFrame(data, columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        result = {}
        for tf, periods in EMA_PERIODS.items():
            ema_vals = {}
            for p in periods:
                ema = df["price"].ewm(span=p, adjust=False).mean().iloc[-1]
                ema_vals[f"EMA_{p}"] = round(ema, 6)
            result[tf] = ema_vals

        return result

    except Exception as e:
        return {"error": str(e)}