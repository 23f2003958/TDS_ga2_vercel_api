import os
from fastapi import FastAPI, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
from typing import List

app = FastAPI()

# 1. Standard FastAPI CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=False, # Must be False if allow_origins is "*"
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, "q-vercel-latency.json")

try:
    df = pd.read_json(JSON_PATH)
except Exception as e:
    print(f"File Load Error: {e}")
    df = pd.DataFrame()

# 2. Manual OPTIONS handler (Backup for Vercel Pre-flights)
@app.options("/{rest_of_path:path}")
async def preflight_handler():
    return JSONResponse(
        content="OK",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

@app.post("/api/metrics")
async def get_metrics(regions: List[str] = Body(...), threshold_ms: int = Body(...)):
    if df.empty:
        return JSONResponse(status_code=500, content={"error": "Data not loaded"})
        
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
