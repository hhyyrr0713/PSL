import os
import sys
import math

import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

try:
    from auth import router as auth_router
    from profile import router as profile_router
    from favorites import router as favorites_router
    from database import init_db, get_connection
except ImportError:
    from app.auth import router as auth_router
    from app.profile import router as profile_router
    from app.favorites import router as favorites_router
    from app.database import init_db, get_connection

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
STYLING_DIR = os.path.join(BASE_DIR, "styling")
ARCHIVE_DIR = os.path.join(BASE_DIR, "archive")

# Kaggle Fashion Product Images 데이터셋 사용
# 현재 프로젝트 구조 기준: archive/styles.csv, app/static/images 또는 app/static/kaggle_images
CSV_PATH = os.path.join(ARCHIVE_DIR, "styles.csv")

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from styling.styling_engine import build_styling_sets, get_anchor_item, load_master_table


app = FastAPI(title="PSL Personal Styling Lab API")

init_db()
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(favorites_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "app", "static")),
    name="static",
)


def get_static_image_path(product_id):
    """
    Kaggle 이미지 파일을 브라우저에서 접근 가능한 /static/... 경로로 변환한다.
    사용자가 이미지를 app/static/images 또는 app/static/kaggle_images 중 어디에 넣어도 동작하게 처리한다.
    """
    product_id = str(product_id)

    static_candidates = [
        ("kaggle_images", os.path.join(BASE_DIR, "app", "static", "kaggle_images", f"{product_id}.jpg")),
        ("images", os.path.join(BASE_DIR, "app", "static", "images", f"{product_id}.jpg")),
    ]

    for folder_name, local_path in static_candidates:
        if os.path.exists(local_path):
            return f"/static/{folder_name}/{product_id}.jpg"

    # 파일이 아직 복사되지 않은 경우에도 프론트에서 깨지지 않도록 기본 경로를 반환
    return f"/static/images/{product_id}.jpg"


def map_kaggle_item_role(row):
    """
    Kaggle의 subCategory/articleType을 PSL의 역할(top, bottom, outer)로 변환한다.
    """
    sub_category = str(row.get("subCategory", "") or "").lower()
    article_type = str(row.get("articleType", "") or "").lower()

    outer_types = [
        "jackets",
        "blazers",
        "sweaters",
        "sweatshirts",
        "waistcoat",
    ]

    bottom_types = [
        "jeans",
        "trousers",
        "shorts",
        "track pants",
        "pants",
    ]

    top_types = [
        "shirts",
        "tshirts",
        "tops",
        "kurtas",
        "innerwear vests",
    ]

    if any(word in article_type for word in outer_types):
        return "outer"

    if sub_category == "bottomwear" or any(word in article_type for word in bottom_types):
        return "bottom"

    if sub_category == "topwear" or any(word in article_type for word in top_types):
        return "top"

    return ""


def make_virtual_brand(product_id):
    """
    Kaggle styles.csv에는 브랜드 컬럼이 없으므로 추천 필터 테스트용 가상 브랜드를 생성한다.
    """
    brands = [
        "MONO STUDIO",
        "URBAN LINE",
        "CLASSIC WORKS",
        "SOFT STANDARD",
        "MODERN ARCHIVE",
        "DAILY FORM",
    ]

    try:
        return brands[int(product_id) % len(brands)]
    except Exception:
        return "MONO STUDIO"


def make_virtual_price(row):
    """
    Kaggle styles.csv에는 가격 컬럼이 없으므로 역할/카테고리 기준 테스트용 가격을 생성한다.
    product_id 기반으로 고정값을 만들어 서버 재시작 때마다 가격이 바뀌지 않게 한다.
    """
    try:
        seed_value = int(row.get("id", 0))
    except Exception:
        seed_value = 0

    role = row.get("item_role", "")
    article_type = str(row.get("articleType", "") or "").lower()

    if role == "outer":
        return 120000 + (seed_value % 200000)

    if role == "bottom":
        return 59000 + (seed_value % 120000)

    if "tshirts" in article_type:
        return 29000 + (seed_value % 70000)

    if "shirts" in article_type:
        return 49000 + (seed_value % 110000)

    return 39000 + (seed_value % 160000)


def make_price_range(price):
    try:
        price = float(price)
    except Exception:
        return ""

    if price <= 100000:
        return "10만원 이하"

    if price <= 500000:
        return "10만~50만원"

    if price <= 1000000:
        return "50만~100만원"

    return "100만원 이상"


def normalize_season(value):
    value = str(value or "").strip()

    if value in ["Spring", "Summer", "Fall", "Winter"]:
        return value

    return "All Season"


def map_season_weights(value):
    season = normalize_season(value)

    if season == "Summer":
        return 1.0, 0.2, 0.0, 0.10
    if season == "Spring":
        return 0.5, 1.0, 0.2, 0.35
    if season == "Fall":
        return 0.2, 1.0, 0.5, 0.60
    if season == "Winter":
        return 0.0, 0.2, 1.0, 0.90

    return 0.3, 0.6, 0.3, 0.50


def map_mood_vector(mood_label):
    mood = str(mood_label or "").strip().lower()

    result = {
        "mood_business_casual": 0.0,
        "mood_casual": 0.0,
        "mood_street": 0.0,
        "mood_minimal": 0.0,
        "mood_formal": 0.0,
    }

    if mood == "formal":
        result["mood_formal"] = 1.0
        result["mood_business_casual"] = 0.6
    elif mood == "classic":
        result["mood_business_casual"] = 0.8
        result["mood_minimal"] = 0.5
    elif mood == "minimal":
        result["mood_minimal"] = 1.0
        result["mood_business_casual"] = 0.3
    elif mood == "sporty":
        result["mood_casual"] = 0.7
        result["mood_street"] = 0.6
    else:
        result["mood_casual"] = 1.0
        result["mood_street"] = 0.3

    return result


def map_top_subtype(row):
    article = str(row.get("articleType", "") or "").lower()
    name = str(row.get("productDisplayName", "") or "").lower()

    text = f"{article} {name}"

    if "blazer" in text:
        return "jacket"
    if "jacket" in text:
        return "jacket"
    if "sweatshirt" in text:
        return "sweatshirt"
    if "sweater" in text:
        return "knit"
    if "shirt" in text and "tshirt" not in text:
        return "shirt"
    if "tshirt" in text or "t-shirt" in text or "tee" in text:
        return "tshirt"
    if "waistcoat" in text or "vest" in text:
        return "vest"

    return "unknown"


def map_bottom_subtype(row):
    article = str(row.get("articleType", "") or "").lower()
    name = str(row.get("productDisplayName", "") or "").lower()

    text = f"{article} {name}"

    if "jeans" in text or "denim" in text:
        return "denim"
    if "trousers" in text or "slacks" in text:
        return "slacks"
    if "shorts" in text:
        return "shorts"
    if "track pants" in text or "jogger" in text:
        return "jogger"
    if "pants" in text:
        return "general_pants"

    return "unknown"


def map_sleeve_length(row):
    article = str(row.get("articleType", "") or "").lower()
    name = str(row.get("productDisplayName", "") or "").lower()
    text = f"{article} {name}"

    if "short sleeve" in text or "half sleeve" in text:
        return "short_sleeve"
    if "sleeveless" in text:
        return "sleeveless"
    if any(word in text for word in ["shirt", "tshirt", "sweater", "sweatshirt", "jacket", "blazer"]):
        return "long_sleeve"

    return "unknown"


def map_pants_length(row):
    article = str(row.get("articleType", "") or "").lower()
    name = str(row.get("productDisplayName", "") or "").lower()
    text = f"{article} {name}"

    if "shorts" in text:
        return "shorts"
    if any(word in text for word in ["jeans", "trousers", "pants"]):
        return "long"

    return "unknown"


def map_kaggle_mood(row):
    usage = str(row.get("usage", "") or "").lower()
    color = str(row.get("baseColour", "") or "").lower()
    article_type = str(row.get("articleType", "") or "").lower()

    if "formal" in usage:
        return "formal"

    if "sports" in usage:
        return "sporty"

    if color in ["black", "white", "grey", "navy blue", "blue"]:
        return "minimal"

    if "shirt" in article_type or "trouser" in article_type:
        return "classic"

    return "casual"


def map_kaggle_fit(row):
    name = str(row.get("productDisplayName", "") or "").lower()
    article_type = str(row.get("articleType", "") or "").lower()

    if "slim" in name:
        return "슬림핏"

    if "regular" in name:
        return "레귤러핏"

    if "loose" in name or "oversized" in name:
        return "오버핏"

    if "jeans" in article_type or "trousers" in article_type:
        return "스트레이트핏"

    return "레귤러핏"



def add_psl_compat_columns(dataframe):
    """
    기존 LF 기반 master_table_step5_image.csv가 가지고 있던 주요 컬럼들을
    Kaggle 변환 데이터에도 기본값으로 맞춰준다.

    styling_engine.py는 여러 점수/상태 컬럼이 있다고 가정하고 동작하므로,
    Kaggle styles.csv에 없는 컬럼은 안전한 기본값으로 생성한다.
    """
    df_compat = dataframe.copy()

    default_values = {
        # 재고/상태
        "has_stock": 1,
        "stock_status": "in_stock",
        "is_soldout": False,
        "available_size_count": 1,
        "size_count": 1,
        "available_sizes": "FREE",
        "size_list": "FREE",
        "is_available": True,
        "in_stock": True,

        # 가격/할인
        "original_price": None,
        "discount_rate": 0,

        # 기존 추천 점수 계열
        "final_score": 0.0,
        "styling_score": 0.0,
        "score": 0.0,
        "total_score": 0.0,
        "popularity_score": 0.0,
        "brand_score": 0.0,
        "color_score": 0.0,
        "mood_score": 0.0,
        "season_score": 0.0,
        "fit_score": 0.0,
        "formality_score": 0.0,
        "role_score": 0.0,
        "category_score": 0.0,
        "age_score": 0.0,
        "trend_score": 0.0,
        "discount_score": 0.0,
        "role_compatibility_score": 0.0,

        # mood vector 컬럼
        "mood_business_casual": 0.0,
        "mood_casual": 0.0,
        "mood_street": 0.0,
        "mood_minimal": 0.0,
        "mood_formal": 0.0,

        # age vector 컬럼
        "age_20s": 0.0,
        "age_30s": 0.0,
        "age_40s_plus": 0.0,

        # 시즌 프로필 컬럼
        "season_warm_weight": 0.0,
        "season_mid_weight": 0.0,
        "season_cold_weight": 0.0,
        "season_temperature_score": 0.5,

        # 기존 속성 컬럼 계열
        "color_group_label": "",
        "color_group_name": "",
        "color_name": "",
        "main_color": "",
        "main_color_group": "",
        "primary_mood": "",
        "secondary_mood": "",
        "display_mood_tag": "",
        "mood": "",
        "style_mood": "",
        "mood_primary": "",
        "style_label": "",
        "fit": "",
        "fit_type": "",
        "fit_group": "",
        "fit_name": "",

        # 사용 상황
        "main_occasion": "",
        "occasion": "",
        "usage_scene": "",

        # subtype/length
        "top_subtype": "unknown",
        "bottom_subtype": "unknown",
        "sleeve_length_type": "unknown",
        "pants_length_type": "unknown",

        # 이미지 여분 컬럼
        "image_url_00": "",
        "image_url_01": "",
        "image_url_02": "",
    }

    for col, default_value in default_values.items():
        if col not in df_compat.columns:
            df_compat[col] = default_value

    # None으로 둔 original_price는 sale_price 기준으로 채움
    if "sale_price" in df_compat.columns:
        df_compat["original_price"] = df_compat["original_price"].fillna(df_compat["sale_price"])

    # 속성 컬럼은 이미 만든 대표 컬럼 기준으로 다시 보정
    if "color_group" in df_compat.columns:
        for col in ["color_group_label", "color_group_name", "color_name", "main_color", "main_color_group"]:
            df_compat[col] = df_compat[col].replace("", pd.NA).fillna(df_compat["color_group"])

    if "mood_label" in df_compat.columns:
        for col in ["primary_mood", "mood", "style_mood", "mood_primary", "style_label"]:
            df_compat[col] = df_compat[col].replace("", pd.NA).fillna(df_compat["mood_label"])

    if "fit_label" in df_compat.columns:
        for col in ["fit", "fit_type", "fit_group", "fit_name"]:
            df_compat[col] = df_compat[col].replace("", pd.NA).fillna(df_compat["fit_label"])

    if "occasion_label" in df_compat.columns:
        for col in ["main_occasion", "occasion", "usage_scene"]:
            df_compat[col] = df_compat[col].replace("", pd.NA).fillna(df_compat["occasion_label"])

    if "image_url" in df_compat.columns:
        df_compat["image_url_00"] = df_compat["image_url_00"].replace("", pd.NA).fillna(df_compat["image_url"])

    # 추천 엔진에서 ranking에 쓰기 쉬운 대표 점수들을 동일하게 맞춤
    if "final_score" in df_compat.columns:
        for col in ["styling_score", "score", "total_score"]:
            df_compat[col] = df_compat[col].replace("", pd.NA).fillna(df_compat["final_score"])

    return df_compat


def load_kaggle_as_psl_table(csv_path):
    """
    Kaggle styles.csv를 기존 PSL 추천 로직이 기대하는 컬럼 구조로 변환해서 반환한다.
    기존 LF 크롤링 CSV 대신 Kaggle 공개 데이터셋을 바로 사용하기 위한 로딩 함수다.
    """
    kaggle_df = pd.read_csv(csv_path, on_bad_lines="skip")

    required_cols = [
        "id",
        "gender",
        "masterCategory",
        "subCategory",
        "articleType",
        "baseColour",
        "season",
        "usage",
        "productDisplayName",
    ]

    missing_cols = [col for col in required_cols if col not in kaggle_df.columns]
    if missing_cols:
        raise ValueError(f"Kaggle styles.csv에 필요한 컬럼이 없습니다: {missing_cols}")

    # 남성/공용 의류만 사용
    kaggle_df = kaggle_df[
        (kaggle_df["gender"].isin(["Men", "Unisex"]))
        & (kaggle_df["masterCategory"] == "Apparel")
    ].copy()

    kaggle_df["product_code"] = kaggle_df["id"].astype(str)
    kaggle_df["product_name"] = kaggle_df["productDisplayName"].fillna("")
    kaggle_df["brand_name"] = kaggle_df["id"].apply(make_virtual_brand)
    kaggle_df["category_name"] = kaggle_df["articleType"].fillna("")
    kaggle_df["item_role"] = kaggle_df.apply(map_kaggle_item_role, axis=1)

    # 기존 추천/개인화 로직에서 쓰는 컬럼명으로 맞춤
    kaggle_df["color_group"] = kaggle_df["baseColour"].fillna("")
    kaggle_df["color_group_label"] = kaggle_df["color_group"]
    kaggle_df["color_group_name"] = kaggle_df["color_group"]
    kaggle_df["color_name"] = kaggle_df["color_group"]

    kaggle_df["season_profile_label"] = kaggle_df["season"].apply(normalize_season)

    kaggle_df["mood_label"] = kaggle_df.apply(map_kaggle_mood, axis=1)
    kaggle_df["mood"] = kaggle_df["mood_label"]
    kaggle_df["primary_mood"] = kaggle_df["mood_label"]
    kaggle_df["style_mood"] = kaggle_df["mood_label"]

    kaggle_df["fit_label"] = kaggle_df.apply(map_kaggle_fit, axis=1)
    kaggle_df["fit"] = kaggle_df["fit_label"]
    kaggle_df["fit_type"] = kaggle_df["fit_label"]
    kaggle_df["fit_group"] = kaggle_df["fit_label"]

    kaggle_df["occasion_label"] = kaggle_df["usage"].fillna("Casual")
    kaggle_df["occasion"] = kaggle_df["occasion_label"]
    kaggle_df["main_occasion"] = kaggle_df["occasion_label"]
    kaggle_df["usage_scene"] = kaggle_df["occasion_label"]

    kaggle_df["sale_price"] = kaggle_df.apply(make_virtual_price, axis=1)
    kaggle_df["original_price"] = kaggle_df["sale_price"]
    kaggle_df["discount_rate"] = 0
    kaggle_df["has_stock"] = 1
    kaggle_df["price_range"] = kaggle_df["sale_price"].apply(make_price_range)

    # 기존 styling_engine이 사용하는 mood/season/subtype 벡터 생성
    mood_vectors = kaggle_df["mood_label"].apply(map_mood_vector).apply(pd.Series)
    for col in mood_vectors.columns:
        kaggle_df[col] = mood_vectors[col]

    season_vectors = kaggle_df["season"].apply(map_season_weights)
    kaggle_df["season_warm_weight"] = season_vectors.apply(lambda x: x[0])
    kaggle_df["season_mid_weight"] = season_vectors.apply(lambda x: x[1])
    kaggle_df["season_cold_weight"] = season_vectors.apply(lambda x: x[2])
    kaggle_df["season_temperature_score"] = season_vectors.apply(lambda x: x[3])

    kaggle_df["top_subtype"] = kaggle_df.apply(map_top_subtype, axis=1)
    kaggle_df["bottom_subtype"] = kaggle_df.apply(map_bottom_subtype, axis=1)
    kaggle_df["sleeve_length_type"] = kaggle_df.apply(map_sleeve_length, axis=1)
    kaggle_df["pants_length_type"] = kaggle_df.apply(map_pants_length, axis=1)
    kaggle_df["display_mood_tag"] = kaggle_df["mood_label"]
    kaggle_df["secondary_mood"] = ""

    kaggle_df["image_url"] = kaggle_df["id"].apply(get_static_image_path)
    kaggle_df["image_url_00"] = kaggle_df["image_url"]
    kaggle_df["image_url_01"] = ""
    kaggle_df["image_url_02"] = ""

    # 추천에 필요한 역할만 남김
    kaggle_df = kaggle_df[kaggle_df["item_role"].isin(["top", "bottom", "outer"])].copy()

    # 기존 LF 기반 추천 엔진이 기대하던 컬럼들을 Kaggle 데이터에도 맞춰준다.
    kaggle_df = add_psl_compat_columns(kaggle_df)

    # 추천 엔진 필터/정렬에서 숫자형으로 비교하는 컬럼 보정
    numeric_cols = [
        "has_stock",
        "available_size_count",
        "final_score",
        "season_warm_weight",
        "season_mid_weight",
        "season_cold_weight",
        "season_temperature_score",
        "mood_business_casual",
        "mood_casual",
        "mood_street",
        "mood_minimal",
        "mood_formal",
        "age_20s",
        "age_30s",
        "age_40s_plus",
    ]

    for col in numeric_cols:
        if col in kaggle_df.columns:
            kaggle_df[col] = pd.to_numeric(kaggle_df[col], errors="coerce").fillna(0)


    return kaggle_df.reset_index(drop=True)


# Kaggle 공개 데이터셋을 기존 PSL 컬럼 구조로 변환해서 사용
df = load_kaggle_as_psl_table(CSV_PATH)


def clean_value(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):
        if math.isnan(float(value)):
            return ""
        return float(value)

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value

    return value


def df_to_records(dataframe: pd.DataFrame):
    if dataframe is None or dataframe.empty:
        return []

    records = []
    for _, row in dataframe.iterrows():
        record = {}
        for col in dataframe.columns:
            record[col] = clean_value(row.get(col, ""))
        records.append(record)

    return records


def series_to_dict(series: pd.Series, cols: list):
    return {col: clean_value(series.get(col, "")) for col in cols}


def get_price_map():
    price_cols = [
        "product_code",
        "sale_price",
        "original_price",
        "discount_rate",
        "price_range",
    ]

    existing_cols = [col for col in price_cols if col in df.columns]
    return df[existing_cols].drop_duplicates(subset=["product_code"]).copy()

def get_product_attribute_map():
    attribute_cols = [
        "product_code",
        "brand_name",
        "sale_price",
        "original_price",
        "discount_rate",
        "price_range",
        "color_group",
        "color_group_label",
        "color_group_name",
        "color_name",
        "fit",
        "fit_type",
        "fit_group",
        "primary_mood",
        "mood",
        "mood_label",
        "style_mood",
        "main_occasion",
        "occasion",
        "usage_scene",
    ]

    existing_cols = [col for col in attribute_cols if col in df.columns]

    return df[existing_cols].drop_duplicates(subset=["product_code"]).copy()

def enrich_candidate_prices(candidate_df: pd.DataFrame) -> pd.DataFrame:
    if candidate_df is None or candidate_df.empty:
        return candidate_df

    price_df = get_price_map()

    candidate_df = candidate_df.drop(
        columns=["sale_price", "original_price", "discount_rate", "price_range"],
        errors="ignore",
    )

    return candidate_df.merge(price_df, on="product_code", how="left")


def safe_number(value):
    try:
        if value is None or pd.isna(value) or value == "":
            return 0
        return float(value)
    except Exception:
        return 0


def enrich_set_prices(set_df: pd.DataFrame) -> pd.DataFrame:
    if set_df is None or set_df.empty:
        return set_df

    result_df = set_df.copy()
    attribute_df = get_product_attribute_map()

    role_map = {
        "top": "top_product_code",
        "bottom": "bottom_product_code",
        "outer": "outer_product_code",
    }

    for role, code_col in role_map.items():
        if code_col not in result_df.columns:
            continue

        rename_map = {
            "product_code": code_col,
            "brand_name": f"{role}_brand_name",
            "sale_price": f"{role}_sale_price",
            "original_price": f"{role}_original_price",
            "discount_rate": f"{role}_discount_rate",
            "price_range": f"{role}_price_range",
            "color_group": f"{role}_color_group",
            "color_group_label": f"{role}_color_group_label",
            "color_group_name": f"{role}_color_group_name",
            "color_name": f"{role}_color_name",
            "fit": f"{role}_fit",
            "fit_type": f"{role}_fit_type",
            "fit_group": f"{role}_fit_group",
            "primary_mood": f"{role}_primary_mood",
            "mood": f"{role}_mood",
            "mood_label": f"{role}_mood_label",
            "style_mood": f"{role}_style_mood",
            "main_occasion": f"{role}_main_occasion",
            "occasion": f"{role}_occasion",
            "usage_scene": f"{role}_usage_scene",
        }

        existing_rename_map = {
            old_col: new_col
            for old_col, new_col in rename_map.items()
            if old_col in attribute_df.columns
        }

        temp_attribute_df = attribute_df.rename(columns=existing_rename_map)

        keep_cols = list(existing_rename_map.values())

        result_df = result_df.drop(
            columns=[
                col for col in keep_cols
                if col != code_col and col in result_df.columns
            ],
            errors="ignore"
        )

        result_df = result_df.merge(
            temp_attribute_df[keep_cols],
            on=code_col,
            how="left"
        )

    result_df["set_total_sale_price"] = result_df.apply(
        lambda row: (
            safe_number(row.get("top_sale_price", 0))
            + safe_number(row.get("bottom_sale_price", 0))
            + safe_number(row.get("outer_sale_price", 0))
        ),
        axis=1,
    )

    result_df["set_total_sale_price"] = result_df["set_total_sale_price"].apply(
        lambda x: x if x > 0 else ""
    )

    return result_df


@app.get("/")
def home():
    return FileResponse(os.path.join(BASE_DIR, "app", "static", "index.html"))


@app.get("/page")
def page():
    return FileResponse(os.path.join(BASE_DIR, "app", "static", "index.html"))


@app.get("/search")
def search_products(
    keyword: str = "",
    brand: str = "",
    role: str = "",
    category: str = "",
    price_range: str = "",
    limit: int = 200,
):
    keyword = keyword.strip()
    brand = brand.strip()
    role = role.strip()
    category = category.strip()
    price_range = price_range.strip()

    search_df = df.copy()

    if keyword:
        search_df = search_df[
            search_df["product_name"].str.contains(keyword, case=False, na=False)
            | search_df["product_code"].str.contains(keyword, case=False, na=False)
            | search_df["brand_name"].str.contains(keyword, case=False, na=False)
        ]

    if brand:
        search_df = search_df[search_df["brand_name"] == brand]

    if role:
        search_df = search_df[search_df["item_role"].str.lower() == role.lower()]

    if category:
        search_df = search_df[
            search_df["category_name"].str.contains(category, case=False, na=False)
            | search_df["product_name"].str.contains(category, case=False, na=False)
        ]

    if price_range and "price_range" in search_df.columns:
        search_df = search_df[search_df["price_range"] == price_range]

    search_df = search_df.head(limit)

    # 검색 결과 카드 UI에 필요한 image_url 추가
    output_cols = [
        "product_code",
        "product_name",
        "brand_name",
        "image_url",
        "image_url_00",
        "image_url_01",
        "image_url_02",
        "item_role",
        "category_name",
        "sale_price",
        "original_price",
        "discount_rate",
        "season_profile_label",
        "price_range",
    ]

    output_cols = [col for col in output_cols if col in search_df.columns]

    return df_to_records(search_df[output_cols])


def get_user_profile_for_recommendation(user_id: int | None):
    if user_id is None:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT preferred_mood,
               preferred_brands,
               preferred_price_range,
               preferred_fit,
               preferred_colors,
               main_occasion
        FROM user_profiles
        WHERE user_id = ?
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "preferred_mood": row["preferred_mood"] or "",
        "preferred_brands": row["preferred_brands"] or "",
        "preferred_price_range": row["preferred_price_range"] or "",
        "preferred_fit": row["preferred_fit"] or "",
        "preferred_colors": row["preferred_colors"] or "",
        "main_occasion": row["main_occasion"] or ""
    }

def split_profile_values(value):
    if value is None:
        return []

    return [
        item.strip()
        for item in str(value).split(",")
        if item.strip()
    ]

def normalize_preference_value(value):
    if value is None:
        return ""

    value = str(value).strip()

    value_map = {
        # 색상
        "그레이": "그레이/차콜",
        "차콜": "그레이/차콜",
        "화이트": "화이트/아이보리",
        "아이보리": "화이트/아이보리",
        "베이지": "베이지/카멜",
        "카멜": "베이지/카멜",
        "카키": "그린/카키",
        "그린": "그린/카키",
        "레드": "레드/버건디",
        "버건디": "레드/버건디",
        "옐로우": "옐로우/오렌지",
        "오렌지": "옐로우/오렌지",

        # 무드
        "minimal": "미니멀",
        "casual": "캐주얼",
        "formal": "포멀",
        "business_casual": "비즈니스캐주얼",
        "street": "스트릿",
        "classic": "클래식",
        "dandy": "댄디",

        # 핏
        "regular": "레귤러",
        "slim": "슬림",
        "oversized": "오버핏",
        "overfit": "오버핏",
        "relaxed": "릴렉스",
        "wide": "와이드",
        "unknown": "",
    }

    return value_map.get(value, value)


def preference_matches(preferred_values, item_value):
    if not preferred_values or not item_value:
        return False

    normalized_item_value = normalize_preference_value(item_value)

    normalized_preferred_values = [
        normalize_preference_value(value)
        for value in preferred_values
    ]

    if normalized_item_value in normalized_preferred_values:
        return True

    # 예: 선호값 "그레이" / 상품값 "그레이/차콜" 같은 경우 보완
    for preferred_value in normalized_preferred_values:
        if preferred_value and normalized_item_value:
            if preferred_value in normalized_item_value or normalized_item_value in preferred_value:
                return True

    return False


def has_profile_value(user_profile):
    if not user_profile:
        return False

    for value in user_profile.values():
        if value and str(value).strip():
            return True

    return False


def first_existing_column(df, candidates):
    for col in candidates:
        if col in df.columns:
            return col
    return None


def calculate_item_preference_score(row, user_profile, prefix=""):
    if not user_profile:
        return 0, ""

    score = 0
    reasons = []

    preferred_moods = split_profile_values(user_profile.get("preferred_mood"))
    preferred_brands = split_profile_values(user_profile.get("preferred_brands"))
    preferred_price_ranges = split_profile_values(user_profile.get("preferred_price_range"))
    preferred_fits = split_profile_values(user_profile.get("preferred_fit"))
    preferred_colors = split_profile_values(user_profile.get("preferred_colors"))
    main_occasions = split_profile_values(user_profile.get("main_occasion"))

    # 후보 컬럼명 후보들
    brand_col_candidates = [
        f"{prefix}brand_name",
        f"{prefix}brand",
        "brand_name",
        "brand"
    ]

    price_col_candidates = [
        f"{prefix}price_range",
        "price_range"
    ]

    color_col_candidates = [
        f"{prefix}color_group",
        f"{prefix}color_group_label",
        f"{prefix}color_group_name",
        f"{prefix}color_name",
        f"{prefix}color",
        f"{prefix}main_color",
        f"{prefix}main_color_group",
        "color_group",
        "color_group_label",
        "color_group_name",
        "color_name",
        "color",
        "main_color",
        "main_color_group"
    ]

    fit_col_candidates = [
        f"{prefix}fit",
        f"{prefix}fit_type",
        f"{prefix}fit_group",
        f"{prefix}fit_name",
        f"{prefix}fit_label",
        "fit",
        "fit_type",
        "fit_group",
        "fit_name",
        "fit_label"
    ]

    mood_col_candidates = [
        f"{prefix}primary_mood",
        f"{prefix}mood",
        f"{prefix}mood_label",
        f"{prefix}style_mood",
        f"{prefix}mood_primary",
        f"{prefix}style_label",
        "primary_mood",
        "mood",
        "mood_label",
        "style_mood",
        "mood_primary",
        "style_label"
    ]

    occasion_col_candidates = [
        f"{prefix}main_occasion",
        f"{prefix}occasion",
        f"{prefix}usage_scene",
        "main_occasion",
        "occasion",
        "usage_scene"
    ]

    # 브랜드
    brand_value = ""
    for col in brand_col_candidates:
        if col in row.index:
            brand_value = str(row.get(col, "") or "")
            break

    if preferred_brands and brand_value in preferred_brands:
        score += 12
        reasons.append("선호 브랜드")

    # 가격대
    price_value = ""
    for col in price_col_candidates:
        if col in row.index:
            price_value = str(row.get(col, "") or "")
            break

    if preferred_price_ranges and price_value in preferred_price_ranges:
        score += 10
        reasons.append("선호 가격대")

    # 색상
    color_value = ""
    for col in color_col_candidates:
        if col in row.index:
            color_value = str(row.get(col, "") or "")
            break

    if preference_matches(preferred_colors, color_value):
        score += 8
        reasons.append("선호 색상")

    # 핏
    fit_value = ""
    for col in fit_col_candidates:
        if col in row.index:
            fit_value = str(row.get(col, "") or "")
            break

    if preference_matches(preferred_fits, fit_value):
        score += 8
        reasons.append("선호 핏")

    # 무드
    mood_value = ""
    for col in mood_col_candidates:
        if col in row.index:
            mood_value = str(row.get(col, "") or "")
            break

    if preference_matches(preferred_moods, mood_value):
        score += 15
        reasons.append("선호 무드")

    # 사용 상황
    occasion_value = ""
    for col in occasion_col_candidates:
        if col in row.index:
            occasion_value = str(row.get(col, "") or "")
            break

    if preference_matches(main_occasions, occasion_value):
        score += 10
        reasons.append("주 사용 상황")

    reason_text = ", ".join(reasons)

    return score, reason_text


def add_personalization_to_candidates(candidate_df, user_profile):
    if candidate_df is None or candidate_df.empty:
        return candidate_df

    df_personalized = candidate_df.copy()

    if not has_profile_value(user_profile):
        df_personalized["user_preference_score"] = 0
        df_personalized["personalized_score"] = df_personalized.get("styling_score", 0)
        df_personalized["personalized_reason"] = ""
        return df_personalized

    scores = []
    reasons = []

    for _, row in df_personalized.iterrows():
        score, reason = calculate_item_preference_score(row, user_profile)
        scores.append(score)
        reasons.append(reason)

    df_personalized["user_preference_score"] = scores

    base_score_col = first_existing_column(
        df_personalized,
        ["styling_score", "score", "total_score", "set_score"]
    )

    if base_score_col:
        df_personalized["personalized_score"] = (
            df_personalized[base_score_col].fillna(0) + df_personalized["user_preference_score"]
        )
    else:
        df_personalized["personalized_score"] = df_personalized["user_preference_score"]

    df_personalized["personalized_reason"] = reasons

    df_personalized = df_personalized.sort_values(
        by="personalized_score",
        ascending=False
    )

    return df_personalized


def add_personalization_to_sets(set_df, user_profile):
    if set_df is None or set_df.empty:
        return set_df

    df_personalized = set_df.copy()

    if not has_profile_value(user_profile):
        df_personalized["user_preference_score"] = 0

        if "set_score" in df_personalized.columns:
            df_personalized["personalized_score"] = df_personalized["set_score"].fillna(0)
        else:
            df_personalized["personalized_score"] = 0

        df_personalized["personalized_reason"] = ""
        return df_personalized

    total_scores = []
    total_reasons = []

    for _, row in df_personalized.iterrows():
        preference_score = 0
        reason_set = set()

        anchor_product_code = str(row.get("anchor_product_code", "") or "")

        for prefix in ["top_", "bottom_", "outer_"]:
            role_product_code = str(row.get(f"{prefix}product_code", "") or "")

            if not role_product_code:
                continue

            # 기준 상품은 사용자가 이미 선택한 상품이므로 세트 개인화 점수에서 제외
            if anchor_product_code and role_product_code == anchor_product_code:
                continue

            item_score, item_reason = calculate_item_preference_score(
                row,
                user_profile,
                prefix=prefix
            )

            preference_score += item_score

            if item_reason:
                for reason in item_reason.split(","):
                    reason = reason.strip()
                    if reason:
                        reason_set.add(reason)

        total_scores.append(preference_score)
        total_reasons.append(", ".join(sorted(reason_set)))

    df_personalized["user_preference_score"] = total_scores

    if "set_score" in df_personalized.columns:
        df_personalized["personalized_score"] = (
            df_personalized["set_score"].fillna(0)
            + df_personalized["user_preference_score"]
        )
    else:
        df_personalized["personalized_score"] = df_personalized["user_preference_score"]

    df_personalized["personalized_reason"] = total_reasons

    df_personalized = df_personalized.sort_values(
        by="personalized_score",
        ascending=False
    )

    return df_personalized

@app.get("/recommend/{product_code}")
def recommend(
    product_code: str,
    brand: str = "",
    category: str = "",
    price_range: str = "",
    same_brand_only: bool = False,
    user_id: int | None = None,
    use_personalization: bool = True
):
    user_profile = get_user_profile_for_recommendation(user_id) if use_personalization else None

    #기존 추천 로직 계속

    try:
        anchor_item = get_anchor_item(df, product_code)

        filtered_df = df.copy()

        if same_brand_only:
            filtered_df = filtered_df[
                filtered_df["brand_name"] == anchor_item.get("brand_name", "")
            ]
        elif brand:
            filtered_df = filtered_df[filtered_df["brand_name"] == brand]

        if category:
            filtered_df = filtered_df[
                filtered_df["category_name"].str.contains(category, case=False, na=False)
                | filtered_df["product_name"].str.contains(category, case=False, na=False)
            ]

        if price_range and "price_range" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["price_range"] == price_range]

        if product_code not in filtered_df["product_code"].values:
            anchor_df = df[df["product_code"] == product_code]
            filtered_df = pd.concat([anchor_df, filtered_df], ignore_index=True)

        result = build_styling_sets(
            df=filtered_df,
            anchor_product_code=product_code,
            top_n_per_role=50,
            top_n_sets=50,
            same_brand_only=False,
        )

        top_candidates = enrich_candidate_prices(result["top_candidates"])
        bottom_candidates = enrich_candidate_prices(result["bottom_candidates"])
        outer_candidates = enrich_candidate_prices(result["outer_candidates"])
        two_piece_sets = enrich_set_prices(result["two_piece_sets"])
        three_piece_sets = enrich_set_prices(result["three_piece_sets"])
        top_candidates = add_personalization_to_candidates(top_candidates, user_profile)
        bottom_candidates = add_personalization_to_candidates(bottom_candidates, user_profile)
        outer_candidates = add_personalization_to_candidates(outer_candidates, user_profile)

        two_piece_sets = add_personalization_to_sets(two_piece_sets, user_profile)
        three_piece_sets = add_personalization_to_sets(three_piece_sets, user_profile)

        # 기준 상품 영역에 image_url 추가
        anchor_cols = [
            "product_code",
            "product_name",
            "brand_name",
            "image_url",
            "image_url_00",
            "image_url_01",
            "image_url_02",
            "item_role",
            "category_name",
            "sale_price",
            "original_price",
            "discount_rate",
            "season_profile_label",
            "price_range",
        ]

        return {
            "anchor": series_to_dict(anchor_item, anchor_cols),
            "user_profile": user_profile,
            "top_candidates": df_to_records(top_candidates),
            "bottom_candidates": df_to_records(bottom_candidates),
            "outer_candidates": df_to_records(outer_candidates),
            "two_piece_sets": df_to_records(two_piece_sets),
            "three_piece_sets": df_to_records(three_piece_sets),
        }

    except ValueError:
        raise HTTPException(status_code=404, detail=f"Product code not found: {product_code}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))