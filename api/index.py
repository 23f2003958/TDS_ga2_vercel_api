from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Load data once at startup
df = pd.read_json("q-vercel-latency.json")

@app.post("/api/metrics")
async def get_metrics(regions: List[str] = Body(...), threshold_ms: int = Body(...)):
    results = {}
    
    for region in regions:
        # Filter data for the region
        region_df = df[df['region'] == region.lower()]
        
        if region_df.empty:
            continue

        latencies = region_df['latency_ms']
        uptimes = region_df['uptime']
        
        results[region] = {
            "avg_latency": float(latencies.mean()),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(uptimes.mean()),
            "breaches": int((latencies > threshold_ms).sum())
        }
        
    return results
