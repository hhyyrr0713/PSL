import os
import pandas as pd

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from database import get_connection, init_db
except ImportError:
    from app.database import get_connection, init_db


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "master_table_step5_image.csv")

def load_product_df():
    df = pd.read_csv(DATA_PATH)
    df["product_code"] = df["product_code"].astype(str)
    return df


router = APIRouter(prefix="/users", tags=["favorites"])


class FavoriteProductRequest(BaseModel):
    product_code: str


@router.post("/{user_id}/favorites/products")
def add_favorite_product(user_id: int, request: FavoriteProductRequest):
    init_db()

    product_code = request.product_code.strip()

    if not product_code:
        raise HTTPException(status_code=400, detail="상품코드가 필요합니다.")

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

    try:
        cursor.execute("""
            INSERT INTO favorite_products (user_id, product_code)
            VALUES (?, ?)
        """, (user_id, product_code))

        conn.commit()

    except Exception:
        conn.close()
        raise HTTPException(status_code=400, detail="이미 위시리스트에 추가된 상품입니다.")

    conn.close()

    return {
        "message": "위시리스트에 추가되었습니다.",
        "user_id": user_id,
        "product_code": product_code
    }


@router.get("/{user_id}/favorites/products")
def get_favorite_products(user_id: int):
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
        SELECT favorite_id, product_code, created_at
        FROM favorite_products
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    favorites = cursor.fetchall()
    conn.close()

    df = load_product_df()

    result = []

    for favorite in favorites:
        favorite_id = favorite["favorite_id"]
        product_code = favorite["product_code"]
        created_at = favorite["created_at"]

        matched = df[df["product_code"] == str(product_code)]

        if matched.empty:
            result.append({
                "favorite_id": favorite_id,
                "product_code": product_code,
                "created_at": created_at,
                "product_name": "",
                "brand_name": "",
                "sale_price": None,
                "image_url": "",
                "image_url_00": "",
                "image_url_01": "",
                "image_url_02": ""
            })
            continue

        product = matched.iloc[0]

        result.append({
            "favorite_id": favorite_id,
            "product_code": product_code,
            "created_at": created_at,
            "product_name": str(product.get("product_name", "")),
            "brand_name": str(product.get("brand_name", "")),
            "sale_price": int(product.get("sale_price", 0)) if pd.notna(product.get("sale_price", None)) else None,
            "image_url": str(product.get("image_url", "")),
            "image_url_00": str(product.get("image_url_00", "")),
            "image_url_01": str(product.get("image_url_01", "")),
            "image_url_02": str(product.get("image_url_02", "")),
            "item_role": str(product.get("item_role", "")),
            "category_name": str(product.get("category_name", "")),
            "price_range": str(product.get("price_range", ""))
        })

    return result


@router.delete("/{user_id}/favorites/products/{product_code}")
def delete_favorite_product(user_id: int, product_code: str):
    init_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM favorite_products
        WHERE user_id = ? AND product_code = ?
    """, (user_id, product_code))

    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="위시리스트에서 해당 상품을 찾을 수 없습니다.")

    return {
        "message": "위시리스트에서 삭제되었습니다.",
        "user_id": user_id,
        "product_code": product_code
    }