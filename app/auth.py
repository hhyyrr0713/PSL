import os
import hashlib
import hmac

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from database import get_connection, init_db
except ImportError:
    from app.database import get_connection, init_db


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000
    )

    return salt.hex() + ":" + password_hash.hex()


def verify_password(password: str, stored_password_hash: str) -> bool:
    try:
        salt_hex, hash_hex = stored_password_hash.split(":")
    except ValueError:
        return False

    salt = bytes.fromhex(salt_hex)
    saved_hash = bytes.fromhex(hash_hex)

    input_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000
    )

    return hmac.compare_digest(input_hash, saved_hash)


@router.post("/register")
def register(request: RegisterRequest):
    init_db()

    username = request.username.strip()
    password = request.password.strip()

    if not username:
        raise HTTPException(status_code=400, detail="아이디를 입력해주세요.")

    if len(password) < 4:
        raise HTTPException(status_code=400, detail="비밀번호는 4자 이상 입력해주세요.")

    password_hash = hash_password(password)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
        """, (username, password_hash))

        conn.commit()
        user_id = cursor.lastrowid

    except Exception:
        conn.close()
        raise HTTPException(status_code=400, detail="이미 사용 중인 아이디입니다.")

    conn.close()

    return {
        "message": "회원가입 성공",
        "user_id": user_id,
        "username": username
    }


@router.post("/login")
def login(request: LoginRequest):
    init_db()

    username = request.username.strip()
    password = request.password.strip()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, username, password_hash
        FROM users
        WHERE username = ?
    """, (username,))

    user = cursor.fetchone()
    conn.close()

    if user is None:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    is_valid = verify_password(password, user["password_hash"])

    if not is_valid:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    return {
        "message": "로그인 성공",
        "user_id": user["user_id"],
        "username": user["username"]
    }