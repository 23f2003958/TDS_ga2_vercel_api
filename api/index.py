import os
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
from typing import List

app = FastAPI()

# We keep the middleware as a baseline safety net
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Your specific manual headers
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Expose-Headers": "Access-Control-Allow-Origin",
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, "q-vercel-latency.json")

try:
    df = pd.read_json(JSON_PATH)
except Exception:
    df = pd.DataFrame()

@app.get("/")
async def root():
    return JSONResponse(
        content={"message": "API is running", "endpoint": "/api/metrics"},
        headers=CORS_HEADERS
    )

@app.post("/api/metrics")
async def get_metrics(regions: List[str] = Body(...), threshold_ms: int = Body(...)):
    if df.empty:
        return JSONResponse(
            content={"error": "Telemetry data unavailable"}, 
            status_code=500,
            headers=CORS_HEADERS
        )
        
    results = {}
    for region in regions:
        region_df = df[df['region'].str.lower() == region.lower()]
        if region_df.empty:
            continue

        latencies = region_df['latency_ms']
        uptimes = region_df['uptime_pct']
        
        results[region] = {
            "avg_latency": float(latencies.mean()),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(uptimes.mean()),
            "breaches": int((latencies > threshold_ms).sum())
        }
    
    # Manually returning JSONResponse ensures your CORS_HEADERS are attached
    return JSONResponse(content=results, headers=CORS_HEADERS)
