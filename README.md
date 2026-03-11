# CoWork — Seat Booking App

A co-working space booking app built with FastAPI + vanilla HTML/CSS/JS.

---

## Features

- **4 Space Types**: Hot Desk, Private Office, Meeting Room, Conference Hall
- **2 Pricing Tiers**: Basic & Premium
- **4 Booking Durations**: Hourly, Daily, Weekly, Monthly
- **User Auth**: Register & Login with JWT tokens
- **Transactional Bookings**: Overlap detection with SQLite WAL + `BEGIN IMMEDIATE`
- **Cancel Bookings**: Cancel confirmed bookings
- **Availability Check**: API endpoint to check existing bookings per seat

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI (Python) |
| Database | SQLite + aiosqlite (async) |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Frontend | Vanilla HTML + CSS + JS (single file) |
| Templating | Jinja2 |

---

## Project Structure

```
cowork-booking/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app + lifespan
│   ├── database.py      # SQLite init + seed data
│   ├── models.py        # Pydantic schemas
│   ├── auth.py          # JWT + password utils
│   └── routers/
│       ├── __init__.py
│       ├── auth.py      # /api/auth/*
│       ├── seats.py     # /api/seats/*
│       └── bookings.py  # /api/bookings/*
├── templates/
│   └── index.html       # Single-page frontend
├── requirements.txt
├── run.py
└── README.md
```

---

## Setup & Run

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd cowork-booking
python3.12 -m venv venv
pip install -r requirements.txt
```

### 2. Run the Server

```bash
python run.py
uvicorn app.main:app --reload
```

Visit: http://localhost:8000

### 3. API Docs (Swagger)

Visit: http://localhost:8000/docs


---

## Pricing

| Space | Tier | Hourly | Daily | Weekly | Monthly |
|-------|------|--------|-------|--------|---------|
| Hot Desk | Basic | $5 | $30 | $150 | $450 |
| Hot Desk | Premium | $10 | $55 | $280 | $850 |
| Private Office | Basic | $20 | $120 | $600 | $1,800 |
| Private Office | Premium | $35 | $200 | $1,000 | $3,000 |
| Meeting Room | Basic | $25 | $150 | $750 | $2,200 |
| Meeting Room | Premium | $45 | $260 | $1,300 | $3,800 |
| Conference Hall | Premium | $150 | $800 | $4,000 | $12,000 |

---

## Transactional Design

We're using SQLite's `BEGIN IMMEDIATE` to prevent double-bookings:

1. Acquire write lock immediately
2. Check for time-slot conflicts
3. Insert booking atomically
4. Commit or rollback on error

This ensures no two users can book the same seat for overlapping times.
