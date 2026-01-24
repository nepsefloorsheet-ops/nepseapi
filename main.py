from fastapi import FastAPI, HTTPException
import httpx
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn

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
    "https://nepselytics-6d61dea19f30.herokuapp.com/api/nepselytics/live-nepse"
)

# -------------------------------------------------
# Root
# -------------------------------------------------
@app.get("/")
def root():
    return {
        "status": "Live NEPSE API Running",
        "endpoint": "/live-nepse"
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
# Run Server
# -------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
