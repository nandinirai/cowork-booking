from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Auth
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    created_at: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# Seats
class SeatOut(BaseModel):
    id: int
    name: str
    room_type: str
    tier: str
    capacity: int
    amenities: str
    is_active: int
    price_hourly: float
    price_daily: float
    price_weekly: float
    price_monthly: float

# Bookings
class BookingCreate(BaseModel):
    seat_id: int
    booking_type: str  # hourly, daily, weekly, monthly
    start_time: datetime
    end_time: datetime

class BookingOut(BaseModel):
    id: int
    user_id: int
    seat_id: int
    seat_name: Optional[str] = None
    room_type: Optional[str] = None
    booking_type: str
    start_time: str
    end_time: str
    total_price: float
    status: str
    created_at: str

class BookingCancelRequest(BaseModel):
    booking_id: int
