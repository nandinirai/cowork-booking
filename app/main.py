from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.routers import auth, seats, bookings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="CoWork Space Booking API",
    description="Seat and room booking for co-working spaces",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(seats.router, prefix="/api/seats", tags=["Seats"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["Bookings"])

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "ok"}
