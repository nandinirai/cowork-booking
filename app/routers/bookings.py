from fastapi import APIRouter, HTTPException, Depends, status
from app.models import BookingCreate, BookingOut
from app.auth import get_current_user
from app.database import get_db
from typing import List
from datetime import datetime
import aiosqlite

router = APIRouter()

PRICE_FIELD_MAP = {
    "hourly": "price_hourly",
    "daily": "price_daily",
    "weekly": "price_weekly",
    "monthly": "price_monthly",
}

DURATION_HOURS = {
    "hourly": 1,
    "daily": 24,
    "weekly": 24 * 7,
    "monthly": 24 * 30,
}

def calculate_price(seat: dict, booking_type: str, start: datetime, end: datetime) -> float:
    price_field = PRICE_FIELD_MAP.get(booking_type)
    if not price_field:
        raise HTTPException(status_code=400, detail="Invalid booking type")
    unit_price = seat[price_field]
    delta = end - start
    total_hours = delta.total_seconds() / 3600

    if booking_type == "hourly":
        units = max(1, round(total_hours))
    elif booking_type == "daily":
        units = max(1, round(total_hours / 24))
    elif booking_type == "weekly":
        units = max(1, round(total_hours / (24 * 7)))
    elif booking_type == "monthly":
        units = max(1, round(total_hours / (24 * 30)))
    else:
        units = 1

    return round(unit_price * units, 2)

@router.post("/", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    current_user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    if data.booking_type not in PRICE_FIELD_MAP:
        raise HTTPException(status_code=400, detail="Invalid booking type. Use: hourly, daily, weekly, monthly")

    if data.start_time >= data.end_time:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")

    # TRANSACTION: check seat + check overlap + insert atomically
    async with db.execute("SELECT * FROM seats WHERE id = ? AND is_active = 1", (data.seat_id,)) as cursor:
        seat = await cursor.fetchone()
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found or unavailable")

    seat = dict(seat)

    # Check for overlapping bookings (transactional)
    await db.execute("BEGIN IMMEDIATE")
    try:
        async with db.execute("""
            SELECT id FROM bookings
            WHERE seat_id = ? AND status = 'confirmed'
            AND NOT (end_time <= ? OR start_time >= ?)
        """, (data.seat_id, data.start_time.isoformat(), data.end_time.isoformat())) as cursor:
            conflict = await cursor.fetchone()

        if conflict:
            await db.execute("ROLLBACK")
            raise HTTPException(status_code=409, detail="Seat already booked for the selected time slot")

        total_price = calculate_price(seat, data.booking_type, data.start_time, data.end_time)

        async with db.execute("""
            INSERT INTO bookings (user_id, seat_id, booking_type, start_time, end_time, total_price, status)
            VALUES (?, ?, ?, ?, ?, ?, 'confirmed')
            RETURNING *
        """, (
            current_user["id"],
            data.seat_id,
            data.booking_type,
            data.start_time.isoformat(),
            data.end_time.isoformat(),
            total_price
        )) as cursor:
            booking = dict(await cursor.fetchone())

        await db.execute("COMMIT")
    except HTTPException:
        raise
    except Exception as e:
        await db.execute("ROLLBACK")
        raise HTTPException(status_code=500, detail=f"Booking failed: {str(e)}")

    return BookingOut(
        **booking,
        seat_name=seat["name"],
        room_type=seat["room_type"]
    )

@router.get("/", response_model=List[BookingOut])
async def list_my_bookings(
    current_user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    async with db.execute("""
        SELECT b.*, s.name as seat_name, s.room_type
        FROM bookings b
        JOIN seats s ON b.seat_id = s.id
        WHERE b.user_id = ?
        ORDER BY b.created_at DESC
    """, (current_user["id"],)) as cursor:
        rows = await cursor.fetchall()
    return [BookingOut(**dict(r)) for r in rows]

@router.delete("/{booking_id}", response_model=BookingOut)
async def cancel_booking(
    booking_id: int,
    current_user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db)
):
    async with db.execute("""
        SELECT b.*, s.name as seat_name, s.room_type
        FROM bookings b JOIN seats s ON b.seat_id = s.id
        WHERE b.id = ? AND b.user_id = ?
    """, (booking_id, current_user["id"])) as cursor:
        booking = await cursor.fetchone()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = dict(booking)
    if booking["status"] != "confirmed":
        raise HTTPException(status_code=400, detail="Only confirmed bookings can be cancelled")

    await db.execute("BEGIN IMMEDIATE")
    try:
        await db.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?", (booking_id,))
        await db.execute("COMMIT")
    except Exception as e:
        await db.execute("ROLLBACK")
        raise HTTPException(status_code=500, detail=f"Cancellation failed: {str(e)}")

    booking["status"] = "cancelled"
    return BookingOut(**booking)

@router.get("/availability/{seat_id}")
async def check_availability(seat_id: int, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("""
        SELECT start_time, end_time FROM bookings
        WHERE seat_id = ? AND status = 'confirmed' AND end_time > CURRENT_TIMESTAMP
        ORDER BY start_time ASC
    """, (seat_id,)) as cursor:
        slots = await cursor.fetchall()
    return {"seat_id": seat_id, "booked_slots": [dict(s) for s in slots]}
