"""Same FastAPI process serves the frontend and API locally and in any Docker host."""
import asyncio
import os
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
from .services import places, weather, ai
from .scoring import crowd_estimate

ROOT=Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
app=FastAPI(title="BerlinBite",version="1.0.0",docs_url="/api/docs",openapi_url="/api/openapi.json")
# Bounded process-local guard. AWS WAF is the distributed production control.
hits=defaultdict(deque)

@app.middleware("http")
async def safety(request:Request, call_next):
    if request.url.path.startswith("/api/") and request.url.path not in ("/api/health","/api/config"):
        now=time.monotonic()
        ip=request.client.host if request.client else "unknown"
        if len(hits)>5000: hits.clear()
        q=hits[ip]
        while q and q[0]<now-60: q.popleft()
        if len(q)>=int(os.getenv("MAX_REQUESTS_PER_MINUTE","20")):
            return JSONResponse({"detail":"Too many requests. Please wait a minute."},429,headers={"Retry-After":"60"})
        q.append(now)
    response=await call_next(request)
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["Referrer-Policy"]="strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"]="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    if request.url.path.startswith('/api/'):
        response.headers["Cache-Control"]="no-store"
    return response

@app.exception_handler(places.ServiceError)
async def service_error(request, exc): return JSONResponse({"detail":exc.message},exc.status)

@app.get("/api/health")
async def health(): return {"status":"ok"}

@app.get("/api/config")
async def config(): return {"places_ready":bool(os.getenv("GOOGLE_PLACES_API_KEY","").strip()),"ai_ready":bool(os.getenv("OPENAI_API_KEY","").strip())}

@app.get("/api/search")
async def search(q:str=Query(min_length=2,max_length=120)):
    q=q.strip()
    if len(q)<2: raise places.ServiceError("Enter at least two characters.",422)
    return {"places":await places.search(q)}

@app.get("/api/places/{place_id}")
async def detail(place_id:str):
    validate_id(place_id)
    return await places.details(place_id)

def validate_id(value):
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]{5,200}",value):
        raise places.ServiceError("Invalid restaurant identifier.",422)

class InsightRequest(BaseModel):
    place_id:str=Field(min_length=5,max_length=200,pattern=r"^[A-Za-z0-9_-]+$")
    visit_at:datetime
    @field_validator("visit_at")
    @classmethod
    def valid_time(cls,v):
        if v.tzinfo is None: raise ValueError("Visit time must include a timezone.")
        if not -3600 <= (v-datetime.now(timezone.utc)).total_seconds() <= 7*86400:
            raise ValueError("Choose a time within the next seven days.")
        return v

@app.post("/api/insight")
async def insight(body:InsightRequest):
    p=await places.details(body.place_id)
    estimate=crowd_estimate(body.visit_at)
    conditions,tip=await asyncio.gather(weather.current(p["lat"],p["lon"]),ai.advice(estimate))
    fallback="For a calmer visit, consider going outside dinner hours. This is a general estimate; contact the restaurant to confirm."
    return {"place":p,"crowd":estimate,"weather":conditions,"advice":tip or fallback,
        "advice_source":"AI-generated general advice" if tip else "General dining guidance",
        "english":"Not verified. Ask the restaurant directly.",
        "reservation":"Contact the restaurant to check availability; BerlinBite does not make bookings.",
        "visit_at":body.visit_at.isoformat(),"fetched_at":datetime.now(timezone.utc).isoformat()}

app.mount("/static",StaticFiles(directory=ROOT/"frontend"),name="static")
@app.get("/")
async def index(): return FileResponse(ROOT/"frontend"/"index.html")
@app.get("/privacy")
async def privacy(): return FileResponse(ROOT/"frontend"/"privacy.html")
@app.get("/terms")
async def terms(): return FileResponse(ROOT/"frontend"/"terms.html")
