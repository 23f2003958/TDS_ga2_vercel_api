import os
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from typing import List

app = FastAPI()

# Enable CORS for POST and OPTIONS (pre-flight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Use absolute path to find the JSON file in the root
# __file__ is /var/task/api/index.py, so we go up one level to find the root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, "q-vercel-latency.json")

# Pre-load data to keep the endpoint fast
try:
    df = pd.read_json(JSON_PATH)
except Exception as e:
    print(f"CRITICAL ERROR: Could not load data from {JSON_PATH}: {e}")
    df = pd.DataFrame()

@app.post("/api/metrics")
async def get_metrics(regions: List[str] = Body(...), threshold_ms: int = Body(...)):
    if df.empty:
        return {"error": "Telemetry data unavailable on server"}
        
    results = {}
    
    for region in regions:
        # Filter for the specific region (case-insensitive)
        region_df = df[df['region'].str.lower() == region.lower()]
        
        if region_df.empty:
            continue

        latencies = region_df['latency_ms']
        uptimes = region_df['uptime']
        
        # Calculate required metrics
        results[region] = {
            "avg_latency": float(latencies.mean()),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(uptimes.mean()),
            "breaches": int((latencies > threshold_ms).sum())
        }
        
    return results
