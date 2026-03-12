from fastapi import APIRouter, Depends, Query
from app.models import SeatOut
from app.database import get_db
from typing import List, Optional
import aiosqlite

router = APIRouter()

@router.get("/", response_model=List[SeatOut])
async def list_seats(
    room_type: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    db: aiosqlite.Connection = Depends(get_db)
):
    query = "SELECT * FROM seats WHERE is_active = 1"
    params = []
    if room_type:
        query += " AND room_type = ?"
        params.append(room_type)
    if tier:
        query += " AND tier = ?"
        params.append(tier)

    async with db.execute(query, params) as cursor:
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]

@router.get("/{seat_id}", response_model=SeatOut)
async def get_seat(seat_id: int, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT * FROM seats WHERE id = ? AND is_active = 1", (seat_id,)) as cursor:
        seat = await cursor.fetchone()
    if not seat:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Seat not found")
    return dict(seat)
