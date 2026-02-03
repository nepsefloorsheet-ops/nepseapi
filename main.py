from fastapi import FastAPI, HTTPException
import httpx
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
from datetime import datetime

app = FastAPI(
    title="Live NEPSE API",
    description="Standalone API for Live NEPSE Index Data",
    version="1.0.0"
)

# -------------------------------------------------
# CORS settings
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NEPSELYTICS_LIVE_NEPSE_URL = (
    "https://sharehubnepal.com/live/api/v2/nepselive/live-nepse"
)

MARKET_DEPTH_BASE_URL = (
    "https://sharehubnepal.com/live/api/v1/nepselive/market-depth"
)

BROKER_SNAPSHOT_URL = (
    "https://api.nepalytix.com/api/broker-daily-snapshot/filter/"
)

# Cache for symbol to ID mapping to avoid repetitive calls
symbol_to_id_cache = {}

# -------------------------------------------------
# Root
# -------------------------------------------------
@app.get("/")
def root():
    return {
        "status": "Live NEPSE API Running",
        "version": "1.0.0",
        "available_endpoints": {
            "/live-nepse": "Real-time NEPSE index and scrip data",
            "/market-depth/{symbol}": "Live L2 Order Book / Market Depth for a specific symbol",
            "/broker-snapshot": "Daily broker-wise buy/sell snapshot (supports ?date=YYYY-MM-DD)",
            "/docs": "Interactive Swagger API documentation"
        }
    }

# -------------------------------------------------
# Live NEPSE Endpoint
# -------------------------------------------------
@app.get("/live-nepse")
async def live_nepse():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            NEPSELYTICS_LIVE_NEPSE_URL,
            headers=headers
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail="Failed to fetch live NEPSE data"
        )

    return resp.json()

# -------------------------------------------------
# Market Depth Endpoint
# -------------------------------------------------
@app.get("/market-depth/{symbol}")
async def get_market_depth(symbol: str):
    symbol = symbol.upper()
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient(timeout=15) as client:
        # Step 1: Find security_id if not in cache
        security_id = symbol_to_id_cache.get(symbol)
        
        if not security_id:
            live_resp = await client.get(NEPSELYTICS_LIVE_NEPSE_URL, headers=headers)
            if live_resp.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch live data for mapping")
            
            live_data = live_resp.json()
            # live-nepse usually returns a list of objects like {"symbol": "ADBL", "security_id": 123, ...}
            # Or it might be nested in "data" or "results"
            
            # Find the security_id
            found = False
            # Check if it's a list or dictionary
            items = live_data if isinstance(live_data, list) else live_data.get("data", [])
            
            for item in items:
                if item.get("symbol") == symbol:
                    security_id = item.get("securityId") or item.get("security_id") or item.get("id")
                    if security_id:
                        symbol_to_id_cache[symbol] = security_id
                        found = True
                        break
            
            if not found:
                raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

        # Step 2: Fetch market depth using security_id
        depth_url = f"{MARKET_DEPTH_BASE_URL}/{security_id}"
        depth_resp = await client.get(depth_url, headers=headers)

    if depth_resp.status_code != 200:
        raise HTTPException(
            status_code=depth_resp.status_code,
            detail="Failed to fetch market depth"
        )

    return depth_resp.json()

# -------------------------------------------------
# Broker Daily Snapshot Endpoint
# -------------------------------------------------
@app.get("/broker-snapshot")
async def get_broker_snapshot(date: str = None):
    """
    Fetches the broker daily snapshot. 
    Defaults to today's date if 'date' query parameter is not provided.
    Format: YYYY-MM-DD
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
        
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient(timeout=15) as client:
        url = f"{BROKER_SNAPSHOT_URL}?date={date}"
        resp = await client.get(url, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Failed to fetch broker snapshot for date {date}"
        )

    return resp.json()

# -------------------------------------------------
# Run Server
# -------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
