import os
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
from typing import List

app = FastAPI()

# Standard CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"], # Allows GET, POST, OPTIONS, etc.
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, "q-vercel-latency.json")

try:
    df = pd.read_json(JSON_PATH)
except Exception as e:
    df = pd.DataFrame()

# 1. FIX: Add a GET route for the root "/"
@app.get("/")
async def root():
    return {"message": "API is running", "endpoint": "/api/metrics"}

# 2. FIX: Prevent 405 on favicon requests
@app.get("/favicon.ico")
async def favicon():
    return JSONResponse(content={})

# 3. Your main Metrics route
@app.post("/api/metrics")
async def get_metrics(regions: List[str] = Body(...), threshold_ms: int = Body(...)):
    if df.empty:
        return {"error": "Telemetry data unavailable"}
        
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
        
    return results
