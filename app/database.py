import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "cowork.db")

async def get_db():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            PRAGMA journal_mode=WAL;

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS seats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                room_type TEXT NOT NULL CHECK(room_type IN ('hot_desk','private_office','meeting_room','conference_hall')),
                tier TEXT NOT NULL CHECK(tier IN ('basic','premium')),
                capacity INTEGER NOT NULL DEFAULT 1,
                amenities TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                price_hourly REAL NOT NULL,
                price_daily REAL NOT NULL,
                price_weekly REAL NOT NULL,
                price_monthly REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                seat_id INTEGER NOT NULL REFERENCES seats(id),
                booking_type TEXT NOT NULL CHECK(booking_type IN ('hourly','daily','weekly','monthly')),
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                total_price REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'confirmed' CHECK(status IN ('confirmed','cancelled','completed')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (seat_id) REFERENCES seats(id)
            );

            INSERT OR IGNORE INTO seats (name, room_type, tier, capacity, amenities, price_hourly, price_daily, price_weekly, price_monthly) VALUES
                ('Desk A1', 'hot_desk', 'basic', 1, 'WiFi, Power outlet', 5.0, 30.0, 150.0, 450.0),
                ('Desk A2', 'hot_desk', 'basic', 1, 'WiFi, Power outlet', 5.0, 30.0, 150.0, 450.0),
                ('Desk B1', 'hot_desk', 'premium', 1, 'WiFi, Power outlet, Monitor, Locker', 10.0, 55.0, 280.0, 850.0),
                ('Desk B2', 'hot_desk', 'premium', 1, 'WiFi, Power outlet, Monitor, Locker', 10.0, 55.0, 280.0, 850.0),
                ('Office 101', 'private_office', 'basic', 4, 'WiFi, Whiteboard, AC', 20.0, 120.0, 600.0, 1800.0),
                ('Office 102', 'private_office', 'basic', 4, 'WiFi, Whiteboard, AC', 20.0, 120.0, 600.0, 1800.0),
                ('Office 201', 'private_office', 'premium', 6, 'WiFi, Whiteboard, AC, TV, Coffee machine', 35.0, 200.0, 1000.0, 3000.0),
                ('Meeting Room Alpha', 'meeting_room', 'basic', 8, 'WiFi, Projector, Whiteboard', 25.0, 150.0, 750.0, 2200.0),
                ('Meeting Room Beta', 'meeting_room', 'premium', 10, 'WiFi, 4K Screen, Whiteboard, Video conferencing', 45.0, 260.0, 1300.0, 3800.0),
                ('Conference Hall', 'conference_hall', 'premium', 50, 'WiFi, Stage, PA System, 4K Projector, Catering support', 150.0, 800.0, 4000.0, 12000.0);
        """)
        await db.commit()
