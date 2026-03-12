from fastapi import APIRouter, HTTPException, Depends, status
from app.models import UserRegister, UserLogin, Token, UserOut
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.database import get_db
import aiosqlite

router = APIRouter()

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: aiosqlite.Connection = Depends(get_db)):
    try:
        async with db.execute("SELECT id FROM users WHERE email = ?", (data.email,)) as cursor:
            existing = await cursor.fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed = hash_password(data.password)
        cursor = await db.execute(
            "INSERT INTO users (name, email, hashed_password) VALUES (?, ?, ?)",
            (data.name, data.email, hashed)
        )
        await db.commit()
        user_id = cursor.lastrowid

        async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            user = dict(await cursor.fetchone())

        token = create_access_token({"sub": str(user["id"])})
        return Token(
            access_token=token,
            user=UserOut(id=user["id"], name=user["name"], email=user["email"], created_at=user["created_at"])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: aiosqlite.Connection = Depends(get_db)):
    try:
        async with db.execute("SELECT * FROM users WHERE email = ?", (data.email,)) as cursor:
            user = await cursor.fetchone()
        if not user or not verify_password(data.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user = dict(user)
        token = create_access_token({"sub": str(user["id"])})
        return Token(
            access_token=token,
            user=UserOut(id=user["id"], name=user["name"], email=user["email"], created_at=user["created_at"])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user)):
    return UserOut(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        created_at=current_user["created_at"]
    )