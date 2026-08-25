from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from database import get_connection, init_db
except ImportError:
    from app.database import get_connection, init_db


router = APIRouter(prefix="/users", tags=["user_profiles"])


class UserProfileRequest(BaseModel):
    preferred_mood: str = ""
    preferred_brands: str = ""
    preferred_price_range: str = ""
    preferred_fit: str = ""
    preferred_colors: str = ""
    main_occasion: str = ""


def row_to_dict(row):
    if row is None:
        return None

    return {
        "profile_id": row["profile_id"],
        "user_id": row["user_id"],
        "preferred_mood": row["preferred_mood"] or "",
        "preferred_brands": row["preferred_brands"] or "",
        "preferred_price_range": row["preferred_price_range"] or "",
        "preferred_fit": row["preferred_fit"] or "",
        "preferred_colors": row["preferred_colors"] or "",
        "main_occasion": row["main_occasion"] or "",
        "updated_at": row["updated_at"]
    }


@router.get("/{user_id}/profile")
def get_user_profile(user_id: int):
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    user = cursor.fetchone()

    if user is None:
        conn.close()
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    cursor.execute("""
        SELECT profile_id, user_id, preferred_mood, preferred_brands,
               preferred_price_range, preferred_fit, preferred_colors,
               main_occasion, updated_at
        FROM user_profiles
        WHERE user_id = ?
    """, (user_id,))

    profile = cursor.fetchone()
    conn.close()

    if profile is None:
        return {
            "user_id": user_id,
            "profile": None
        }

    return {
        "user_id": user_id,
        "profile": row_to_dict(profile)
    }


@router.put("/{user_id}/profile")
def save_user_profile(user_id: int, request: UserProfileRequest):
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    user = cursor.fetchone()

    if user is None:
        conn.close()
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    cursor.execute("""
        INSERT INTO user_profiles (
            user_id,
            preferred_mood,
            preferred_brands,
            preferred_price_range,
            preferred_fit,
            preferred_colors,
            main_occasion,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            preferred_mood = excluded.preferred_mood,
            preferred_brands = excluded.preferred_brands,
            preferred_price_range = excluded.preferred_price_range,
            preferred_fit = excluded.preferred_fit,
            preferred_colors = excluded.preferred_colors,
            main_occasion = excluded.main_occasion,
            updated_at = CURRENT_TIMESTAMP
    """, (
        user_id,
        request.preferred_mood.strip(),
        request.preferred_brands.strip(),
        request.preferred_price_range.strip(),
        request.preferred_fit.strip(),
        request.preferred_colors.strip(),
        request.main_occasion.strip()
    ))

    conn.commit()

    cursor.execute("""
        SELECT profile_id, user_id, preferred_mood, preferred_brands,
               preferred_price_range, preferred_fit, preferred_colors,
               main_occasion, updated_at
        FROM user_profiles
        WHERE user_id = ?
    """, (user_id,))

    saved_profile = cursor.fetchone()
    conn.close()

    return {
        "message": "스타일 프로필이 저장되었습니다.",
        "profile": row_to_dict(saved_profile)
    }