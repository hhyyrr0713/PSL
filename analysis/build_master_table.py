import pandas as pd
import numpy as np
from pathlib import Path
import re
import ast

# =========================
# 1. 경로 설정
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

print("BASE_DIR:", BASE_DIR)
print("DATA_DIR:", DATA_DIR)

# =========================
# 2. 원본 csv 파일 목록 지정
# =========================
RAW_CSV_FILES = [
    "allegri_products_enriched_all.csv",
    "daks_men_products_enriched_all.csv",
    "hazzys_men_products_enriched_all.csv",
    "ilcorso_products_enriched_all.csv",
    "jillstuartnewyork_men_products_enriched_all.csv",
    "tngt_men_products_enriched_all.csv",
]

# =========================
# 3. 기본 컬럼 정의
# =========================
BASE_COLUMNS = [
    "product_code",
    "product_name",
    "brand_name",
    "brand_id",
    "brand_group_id",
    "product_sale_type",

    # 기존 season
    "season",

    # ===== seasonName 계열 =====
    "season_name_raw",
    "season_spring",
    "season_summer",
    "season_fall",
    "season_winter",
    "season_all",

    "original_price",
    "sale_price",
    "discount_rate",
    "sale_count",
    "cart_count",
    "review_count",
    "review_score",
    "purchase_count",
    "viewing_count",
    "wish_count",
    "size_total_stock",
    "size_stock_detail",
    "color_total_stock",
    "color_stock_detail",
    "lf_category_l1",
    "lf_category_l2",
    "lf_category_l3",

    # 질스튜어트용 컬럼도 유지
    "display_category_id",
    "soldout",
]

NUMERIC_INT_COLUMNS = [
    "product_sale_type",
    "season_spring",
    "season_summer",
    "season_fall",
    "season_winter",
    "season_all",
    "original_price",
    "sale_price",
    "discount_rate",
    "sale_count",
    "cart_count",
    "review_count",
    "purchase_count",
    "viewing_count",
    "wish_count",
    "size_total_stock",
    "color_total_stock",
]

NUMERIC_FLOAT_COLUMNS = [
    "review_score",
]

# =========================
# 4. 스타일링 규칙 정의
# =========================
MOOD_KEYS = [
    "business_casual",
    "casual",
    "street",
    "minimal",
    "formal",
]

AGE_KEYS = [
    "20s",
    "30s",
    "40s_plus",
]

BRAND_MOOD_PRIORS = {
    "allegri": {
        "business_casual": 6,
        "casual": 1,
        "street": 0,
        "minimal": 1,
        "formal": 2,
    },
    "daks men": {
        "business_casual": 4,
        "casual": 1,
        "street": 0,
        "minimal": 1,
        "formal": 4,
    },
    "hazzys men": {
        "business_casual": 4,
        "casual": 3,
        "street": 0,
        "minimal": 1,
        "formal": 2,
    },
    "ilcorso": {
        "business_casual": 1,
        "casual": 4,
        "street": 1,
        "minimal": 4,
        "formal": 0,
    },
    "jillstuartnewyork men": {
        "business_casual": 3,
        "casual": 2,
        "street": 0,
        "minimal": 4,
        "formal": 1,
    },
    "tngt": {
        "business_casual": 4,
        "casual": 3,
        "street": 1,
        "minimal": 1,
        "formal": 1,
    },
}

BRAND_AGE_PRIORS = {
    "allegri": {"20s": 2, "30s": 4, "40s_plus": 4},
    "daks men": {"20s": 0, "30s": 2, "40s_plus": 8},
    "hazzys men": {"20s": 3, "30s": 4, "40s_plus": 3},
    "ilcorso": {"20s": 5, "30s": 4, "40s_plus": 1},
    "jillstuartnewyork men": {"20s": 3, "30s": 5, "40s_plus": 2},
    "tngt": {"20s": 4, "30s": 4, "40s_plus": 2},
}

CATEGORY_MOOD_PRIORS = {
    "자켓": {
        "business_casual": 5,
        "casual": 1,
        "street": 0,
        "minimal": 2,
        "formal": 2,
    },
    "코트": {
        "business_casual": 4,
        "casual": 1,
        "street": 0,
        "minimal": 3,
        "formal": 2,
    },
    "점퍼": {
        "business_casual": 1,
        "casual": 4,
        "street": 1,
        "minimal": 3,
        "formal": 1,
    },
    "트렌치코트": {
        "business_casual": 4,
        "casual": 1,
        "street": 0,
        "minimal": 2,
        "formal": 3,
    },
    "셔츠": {
        "business_casual": 5,
        "casual": 1,
        "street": 0,
        "minimal": 2,
        "formal": 2,
    },
    "티셔츠": {
        "business_casual": 1,
        "casual": 5,
        "street": 2,
        "minimal": 2,
        "formal": 0,
    },
    "스웨터/맨투맨": {
        "business_casual": 2,
        "casual": 3,
        "street": 1,
        "minimal": 3,
        "formal": 1,
    },
    "베스트": {
        "business_casual": 4,
        "casual": 1,
        "street": 0,
        "minimal": 3,
        "formal": 2,
    },
    "팬츠": {
        "business_casual": 3,
        "casual": 3,
        "street": 1,
        "minimal": 2,
        "formal": 1,
    },
    "수트": {
        "business_casual": 2,
        "casual": 0,
        "street": 0,
        "minimal": 1,
        "formal": 7,
    },
}

KEYWORD_MOOD_ADJUSTMENTS = {
    "블레이저": {"business_casual": 2, "formal": 2},
    "blazer": {"business_casual": 2, "formal": 2},
    "슬랙스": {"business_casual": 2, "formal": 2},
    "slacks": {"business_casual": 2, "formal": 2},
    "테일러드": {"business_casual": 2, "formal": 2},
    "tailored": {"business_casual": 2, "formal": 2},
    "체스터": {"business_casual": 1, "formal": 3},
    "chester": {"business_casual": 1, "formal": 3},
    "더블": {"formal": 2},
    "double": {"formal": 2},
    "드레스": {"formal": 3},
    "dress": {"formal": 3},
    "치노": {"business_casual": 2},
    "chino": {"business_casual": 2},
    "셋업": {"business_casual": 2, "formal": 2},
    "setup": {"business_casual": 2, "formal": 2},
    "set up": {"business_casual": 2, "formal": 2},
    "zegna": {"minimal": 1, "formal": 2},
    "tollegno": {"minimal": 1, "formal": 2},
    "canclini": {"business_casual": 1, "formal": 2},
    "후드": {"casual": 2, "street": 1},
    "hood": {"casual": 2, "street": 1},
    "후디": {"casual": 2, "street": 1},
    "hoodie": {"casual": 2, "street": 1},
    "맨투맨": {"casual": 2},
    "스웨트": {"casual": 2},
    "sweat": {"casual": 2},
    "조거": {"casual": 2, "street": 1},
    "jogger": {"casual": 2, "street": 1},
    "카고": {"street": 2, "casual": 1},
    "cargo": {"street": 2, "casual": 1},
    "그래픽": {"street": 2, "casual": 1},
    "graphic": {"street": 2, "casual": 1},
    "프린트": {"street": 1, "casual": 1},
    "print": {"street": 1, "casual": 1},
    "미니멀": {"minimal": 3},
    "minimal": {"minimal": 3},
    "에센셜": {"minimal": 3},
    "essential": {"minimal": 3},
    "베이직": {"minimal": 1, "casual": 1},
    "basic": {"minimal": 1, "casual": 1},
    "클래식": {"minimal": 2, "business_casual": 1},
    "classic": {"minimal": 2, "business_casual": 1},
    "모던": {"minimal": 2},
    "modern": {"minimal": 2},
    "clean": {"minimal": 2},
    "simple": {"minimal": 2},
    "soft texture": {"minimal": 1},
    "premium basic": {"minimal": 2},
}

FIT_MOOD_ADJUSTMENTS = {
    "slim": {"business_casual": 1, "formal": 1},
    "regular": {"business_casual": 1, "minimal": 1},
    "relaxed": {"casual": 1, "minimal": 1},
    "wide": {"street": 1, "casual": 1, "minimal": 1},
    "oversized": {"street": 2, "casual": 1, "minimal": 1},
    "unknown": {},
}

MATERIAL_LUXURY_MAP = {
    "cashmere": 5,
    "wool": 4,
    "leather": 4,
    "knit": 3,
    "cotton": 3,
    "denim": 2,
    "synthetic": 2,
    "unknown": 2,
}

MATERIAL_TEXTURE_MAP = {
    "cashmere": "soft",
    "wool": "soft",
    "leather": "structured",
    "knit": "soft",
    "cotton": "balanced",
    "denim": "rugged",
    "synthetic": "technical",
    "unknown": "unknown",
}

CATEGORY_TO_ITEM_ROLE = {
    "코트": "outer",
    "자켓": "outer",
    "점퍼": "outer",
    "트렌치코트": "outer",
    "셔츠": "top",
    "티셔츠": "top",
    "스웨터/맨투맨": "top",
    "베스트": "top",
    "팬츠": "bottom",
    "수트": "set",
    "가방": "accessory",
    "벨트": "accessory",
    "장갑": "accessory",
    "모자": "accessory",
    "머플러": "accessory",
    "넥타이": "accessory",
    "슬리퍼": "accessory",
    "양말": "accessory",
    "펫의류": "other",
}

FIT_KEYWORDS = {
    "oversized": ["오버핏", "oversized", "overfit", "세미오버", "오버"],
    "wide": ["와이드", "wide", "루즈핏", "loose fit", "loose", "루즈"],
    "relaxed": ["릴렉스", "relaxed", "여유핏", "comfort", "컴포트", "relax fit"],
    "slim": ["슬림", "slim", "스키니", "skinny", "테이퍼드", "tapered", "슬림 핏", "slim fit"],
    "regular": [
        "레귤러", "regular", "basic", "standard", "스탠다드",
        "클래식핏", "regular fit", "new regular fit", "레귤러 핏", "스탠다드 핏"
    ],
}

MATERIAL_KEYWORDS = {
    "cashmere": ["캐시미어", "cashmere"],
    "wool": ["울", "wool"],
    "leather": ["레더", "leather", "가죽"],
    "knit": ["니트", "knit"],
    "cotton": ["코튼", "cotton"],
    "denim": ["데님", "denim", "jean", "진"],
    "synthetic": ["폴리", "poly", "나일론", "nylon", "synthetic"],
}

PATTERN_KEYWORDS = {
    "stripe": ["스트라이프", "stripe"],
    "check": ["체크", "check", "checkered", "plaid"],
    "graphic": ["그래픽", "graphic", "로고", "logo"],
    "print": ["프린트", "print"],
}

# =========================
# 5. 유틸 함수
# =========================
def safe_str(value, default: str = "") -> str:
    if pd.isna(value):
        return default
    return str(value).strip()

def to_int_series(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("원", "", regex=False)
        .str.replace("%", "", regex=False)
        .replace({"None": np.nan, "nan": np.nan, "": np.nan, "<NA>": np.nan})
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
        .astype(int)
    )

def to_float_series(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .replace({"None": np.nan, "nan": np.nan, "": np.nan, "<NA>": np.nan})
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0.0)
        .astype(float)
    )

def normalize_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower().strip()
    text = text.replace("_", " ")
    text = text.replace("-", " ")
    text = text.replace("/", " ")
    text = re.sub(r"\s+", " ", text)
    return text

def normalize_brand_name(brand_name):
    brand = normalize_text(brand_name)
    mapping = {
        "알레그리": "allegri",
        "allegri": "allegri",
        "알레그리 남성": "allegri",
        "닥스 men": "daks men",
        "daks men": "daks men",
        "daksmen": "daks men",
        "헤지스 men": "hazzys men",
        "hazzys men": "hazzys men",
        "hazzysmen": "hazzys men",
        "일꼬르소": "ilcorso",
        "ilcorso": "ilcorso",
        "질스튜어트뉴욕 men": "jillstuartnewyork men",
        "jillstuartnewyork men": "jillstuartnewyork men",
        "jill stuart new york men": "jillstuartnewyork men",
        "jillstuart new york men": "jillstuartnewyork men",
        "tngt": "tngt",
    }
    return mapping.get(brand, brand)

def contains_any(text, keywords):
    return any(keyword in text for keyword in keywords)

def init_score_dict(keys):
    return {k: 0 for k in keys}

def add_scores(base_dict, add_dict, weight=1.0):
    for k, v in add_dict.items():
        if k in base_dict:
            base_dict[k] += v * weight
    return base_dict

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [col.strip() for col in df.columns]

    existing_cols = [col for col in BASE_COLUMNS if col in df.columns]
    missing_cols = [col for col in BASE_COLUMNS if col not in df.columns]

    print("\n[현재 존재하는 컬럼]")
    print(existing_cols)

    print("\n[없는 컬럼]")
    print(missing_cols)

    keep_cols = existing_cols.copy()
    if "source_file" in df.columns:
        keep_cols.append("source_file")

    return df[keep_cols].copy()

def preprocess_string_id_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "product_code" in df.columns:
        df["product_code"] = df["product_code"].astype(str).str.strip()

    if "brand_id" in df.columns:
        df["brand_id"] = df["brand_id"].astype(str).str.strip()

    if "brand_group_id" in df.columns:
        df["brand_group_id"] = df["brand_group_id"].astype(str).str.strip()

    for col in [
        "brand_name", "season", "season_name_raw",
        "size_stock_detail", "color_stock_detail",
        "lf_category_l1", "lf_category_l2", "lf_category_l3",
        "display_category_id", "soldout"
    ]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    return df

def preprocess_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in NUMERIC_INT_COLUMNS:
        if col in df.columns:
            df[col] = to_int_series(df[col])

    for col in NUMERIC_FLOAT_COLUMNS:
        if col in df.columns:
            df[col] = to_float_series(df[col])

    return df

def add_code_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["product_code"] = df["product_code"].astype(str).str.strip()
    df["category_code"] = df["product_code"].str[2:4]
    df["color_code"] = df["product_code"].str[-2:]
    return df

def normalize_season_name(text) -> str:
    if pd.isna(text):
        return ""
    text = str(text).strip()
    if not text:
        return ""
    text = text.replace("/", ",")
    text = text.replace("·", ",")
    text = text.replace("|", ",")
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def recompute_season_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "season_name_raw" not in df.columns:
        df["season_name_raw"] = ""

    df["season_name_raw"] = df["season_name_raw"].fillna("").apply(normalize_season_name)
    text_series = df["season_name_raw"].astype(str)
    lower_series = text_series.str.lower()

    season_all = (
        text_series.str.contains("사계절", na=False)
        | text_series.str.contains("4계절", na=False)
        | text_series.str.contains("올시즌", na=False)
        | lower_series.str.contains("all season", na=False)
        | (lower_series == "all")
    )

    spring = text_series.str.contains("봄", na=False)
    summer = text_series.str.contains("여름", na=False)
    fall = text_series.str.contains("가을", na=False)
    winter = text_series.str.contains("겨울", na=False)

    first_half = text_series.str.contains("상반기", na=False)
    second_half = text_series.str.contains("하반기", na=False)

    df["season_all"] = season_all.astype(int)
    df["season_spring"] = (spring | first_half | season_all).astype(int)
    df["season_summer"] = (summer | first_half | season_all).astype(int)
    df["season_fall"] = (fall | second_half | season_all).astype(int)
    df["season_winter"] = (winter | second_half | season_all).astype(int)

    return df

def normalize_triplet(warm: float, mid: float, cold: float):
    total = warm + mid + cold
    if total <= 0:
        return 0.0, 0.0, 0.0
    return warm / total, mid / total, cold / total

def build_season_profile_from_flags(row: pd.Series) -> pd.Series:
    spring = int(row.get("season_spring", 0))
    summer = int(row.get("season_summer", 0))
    fall = int(row.get("season_fall", 0))
    winter = int(row.get("season_winter", 0))
    season_all = int(row.get("season_all", 0))

    flags = (spring, summer, fall, winter)

    if season_all == 1 or flags == (1, 1, 1, 1):
        warm, mid, cold = 0.33, 0.34, 0.33
        label = "all_season"

    elif sum(flags) == 0:
        warm, mid, cold = 0.0, 0.0, 0.0
        label = "unknown"

    elif flags == (1, 0, 0, 0):   # spring
        warm, mid, cold = 0.0, 1.0, 0.0
        label = "spring"
    elif flags == (0, 1, 0, 0):   # summer
        warm, mid, cold = 1.0, 0.0, 0.0
        label = "summer"
    elif flags == (0, 0, 1, 0):   # fall
        warm, mid, cold = 0.0, 1.0, 0.0
        label = "fall"
    elif flags == (0, 0, 0, 1):   # winter
        warm, mid, cold = 0.0, 0.0, 1.0
        label = "winter"

    elif flags == (1, 1, 0, 0):   # spring + summer
        warm, mid, cold = 0.75, 0.25, 0.0
        label = "spring_summer"
    elif flags == (0, 1, 1, 0):   # summer + fall
        warm, mid, cold = 0.75, 0.25, 0.0
        label = "summer_fall"
    elif flags == (0, 0, 1, 1):   # fall + winter
        warm, mid, cold = 0.0, 0.25, 0.75
        label = "fall_winter"
    elif flags == (1, 0, 0, 1):   # winter + spring
        warm, mid, cold = 0.0, 0.25, 0.75
        label = "winter_spring"
    elif flags == (1, 0, 1, 0):   # spring + fall
        warm, mid, cold = 0.0, 1.0, 0.0
        label = "spring_fall"
    elif flags == (0, 1, 0, 1):   # summer + winter (드문 케이스)
        warm, mid, cold = 0.5, 0.0, 0.5
        label = "summer_winter"

    elif flags == (1, 1, 1, 0):   # spring + summer + fall
        warm, mid, cold = 0.34, 0.66, 0.0
        label = "spring_summer_fall"
    elif flags == (1, 0, 1, 1):   # spring + fall + winter
        warm, mid, cold = 0.0, 0.66, 0.34
        label = "spring_fall_winter"
    elif flags == (1, 1, 0, 1):   # spring + summer + winter
        warm, mid, cold = 0.40, 0.20, 0.40
        label = "spring_summer_winter"
    elif flags == (0, 1, 1, 1):   # summer + fall + winter
        warm, mid, cold = 0.40, 0.20, 0.40
        label = "summer_fall_winter"

    else:
        warm = float(summer)
        mid = float(spring + fall)
        cold = float(winter)
        warm, mid, cold = normalize_triplet(warm, mid, cold)
        label = "fallback"

    if warm + mid + cold <= 0:
        temp_score = np.nan
    else:
        temp_score = warm * 0.0 + mid * 0.5 + cold * 1.0

    return pd.Series({
        "season_warm_weight": round(warm, 4),
        "season_mid_weight": round(mid, 4),
        "season_cold_weight": round(cold, 4),
        "season_temperature_score": round(temp_score, 4) if not pd.isna(temp_score) else np.nan,
        "season_profile_label": label,
    })

def add_season_profile_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    season_profile_df = df.apply(build_season_profile_from_flags, axis=1)
    df = pd.concat([df, season_profile_df], axis=1)
    return df

def basic_check(df: pd.DataFrame) -> None:
    print("\n===== df shape =====")
    print(df.shape)

    print("\n===== null count =====")
    print(df.isnull().sum())

    print("\n===== duplicated product_code =====")
    if "product_code" in df.columns:
        print(df["product_code"].duplicated().sum())

def show_unique_codes(df: pd.DataFrame) -> None:
    print("\n===== category_code unique =====")
    print(sorted(df["category_code"].dropna().unique().tolist()))
    print("개수:", df["category_code"].nunique())

    print("\n===== color_code unique =====")
    print(sorted(df["color_code"].dropna().unique().tolist()))
    print("개수:", df["color_code"].nunique())

def make_price_range(price: int) -> str:
    if price <= 100000:
        return "10만원 이하"
    elif price <= 500000:
        return "10만~50만원"
    elif price <= 1000000:
        return "50만~100만원"
    else:
        return "100만원 이상"

def get_size_type(category_name: str) -> str:
    top_categories = [
        "셔츠", "티셔츠", "스웨터/맨투맨", "자켓",
        "점퍼", "코트", "트렌치코트", "베스트", "수트"
    ]
    bottom_categories = ["팬츠"]

    if category_name in top_categories:
        return "top"
    elif category_name in bottom_categories:
        return "bottom"
    else:
        return "free"

def normalize_size_value(size_val: str, size_type: str) -> str:
    if pd.isna(size_val):
        return ""

    size_val = str(size_val).strip().upper()
    size_val = size_val.replace("사이즈", "").replace("SIZE", "")
    size_val = re.sub(r"\s+", "", size_val)

    if size_val == "":
        return ""

    free_alias = {
        "FREE": "FREE",
        "F": "FREE",
        "ONE": "FREE",
        "ONESIZE": "FREE",
        "ONE SIZE": "FREE",
        "XXX": "XXX",
    }

    if size_val in free_alias:
        return free_alias[size_val]

    top_alpha_map = {
        "S": "95", "M": "100", "L": "105", "XL": "110", "XXL": "115", "2XL": "115",
        "0S": "95", "00S": "95", "0M": "100", "00M": "100", "0L": "105", "00L": "105",
        "0XL": "110", "00XL": "110", "0XXL": "115", "00XXL": "115",
    }

    if size_val in top_alpha_map:
        return top_alpha_map[size_val]

    if size_type == "top":
        top_numeric_map = {
            "46": "90", "046": "90", "48": "95", "048": "95", "50": "100", "050": "100",
            "52": "105", "052": "105", "54": "110", "054": "110", "56": "115", "056": "115",
        }
        if size_val in top_numeric_map:
            return top_numeric_map[size_val]

    if size_type == "bottom":
        bottom_code_map = {
            "78": "30", "078": "30", "82": "32", "082": "32", "86": "34", "086": "34",
            "88": "35", "088": "35", "90": "36", "090": "36", "94": "38", "094": "38",
            "96": "39", "096": "39", "98": "40", "098": "40",
        }
        if size_val in bottom_code_map:
            return bottom_code_map[size_val]

    if size_val.isdigit():
        return str(int(size_val))

    return size_val

def size_sort_key(x):
    x = str(x).strip()
    if x == "FREE":
        return (2, x)
    if x == "XXX":
        return (3, x)
    if x.isdigit():
        return (0, int(x))
    return (1, x)

def extract_available_sizes_from_row(row) -> list:
    size_detail = row["size_stock_detail"]
    size_type = row["size_type"]

    if pd.isna(size_detail):
        return []

    text = str(size_detail).strip()

    if text == "" or text.lower() in ["nan", "none", "null", "[]", "{}"]:
        return []

    result = []

    pattern_with_paren = re.findall(
        r"([A-Za-z0-9]+)\s*\(\s*([A-Za-z0-9]+)\s*\)\s*:\s*(\d+)",
        text
    )

    if pattern_with_paren:
        for outer_size, inner_size, stock in pattern_with_paren:
            if int(stock) > 0:
                norm_size = normalize_size_value(inner_size, size_type)
                if norm_size:
                    result.append(norm_size)
        return sorted(list(set(result)), key=size_sort_key)

    pattern_basic = re.findall(r"([A-Za-z0-9]+)\s*:\s*(\d+)", text)

    if pattern_basic:
        for size_val, stock in pattern_basic:
            if int(stock) > 0:
                norm_size = normalize_size_value(size_val, size_type)
                if norm_size:
                    result.append(norm_size)
        return sorted(list(set(result)), key=size_sort_key)

    try:
        parsed = ast.literal_eval(text)

        if isinstance(parsed, dict):
            for k, v in parsed.items():
                try:
                    stock = float(v)
                except Exception:
                    stock = 0

                if stock > 0:
                    norm_size = normalize_size_value(k, size_type)
                    if norm_size:
                        result.append(norm_size)

            return sorted(list(set(result)), key=size_sort_key)

        elif isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict):
                    size_val = None
                    stock_val = 0

                    for key, value in item.items():
                        key_lower = str(key).lower()
                        if key_lower in ["size", "option", "name", "label"]:
                            size_val = normalize_size_value(value, size_type)
                        if key_lower in ["stock", "qty", "quantity", "count"]:
                            try:
                                stock_val = float(value)
                            except Exception:
                                stock_val = 0

                    if size_val and stock_val > 0:
                        result.append(size_val)

                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    size_val = normalize_size_value(item[0], size_type)
                    try:
                        stock_val = float(item[1])
                    except Exception:
                        stock_val = 0
                    if size_val and stock_val > 0:
                        result.append(size_val)

                else:
                    size_val = normalize_size_value(item, size_type)
                    if size_val:
                        result.append(size_val)

            return sorted(list(set(result)), key=size_sort_key)

    except Exception:
        pass

    candidates = re.split(r"[,/|]+", text)
    candidates = [normalize_size_value(x, size_type) for x in candidates]
    candidates = [x for x in candidates if x]

    if 0 < len(candidates) <= 20:
        return sorted(list(set(candidates)), key=size_sort_key)

    return []

def size_list_to_string(size_list: list) -> str:
    if not isinstance(size_list, list):
        return ""
    sorted_list = sorted(list(set(size_list)), key=size_sort_key)
    return ",".join(sorted_list)

# =========================
# 6. 스타일링용 파생 함수
# =========================
def derive_item_role(category_name):
    return CATEGORY_TO_ITEM_ROLE.get(category_name, "other")

def derive_fit_type(product_name):
    name = normalize_text(product_name)
    priority_order = ["oversized", "wide", "relaxed", "slim", "regular"]

    for fit_type in priority_order:
        keywords = FIT_KEYWORDS.get(fit_type, [])
        normalized_keywords = [normalize_text(k) for k in keywords]
        if contains_any(name, normalized_keywords):
            return fit_type
    return "unknown"

def derive_material_type(product_name):
    name = normalize_text(product_name)

    for material, keywords in MATERIAL_KEYWORDS.items():
        normalized_keywords = [normalize_text(k) for k in keywords]
        if contains_any(name, normalized_keywords):
            return material
    return "unknown"

def derive_pattern_type(product_name):
    name = normalize_text(product_name)

    for pattern_type, keywords in PATTERN_KEYWORDS.items():
        normalized_keywords = [normalize_text(k) for k in keywords]
        if contains_any(name, normalized_keywords):
            return pattern_type
    return "solid"

def derive_luxury_level(material_type):
    return MATERIAL_LUXURY_MAP.get(material_type, 2)

def derive_texture_class(material_type):
    return MATERIAL_TEXTURE_MAP.get(material_type, "unknown")

def get_keyword_mood_adjustments(product_name):
    name = normalize_text(product_name)
    score_dict = init_score_dict(MOOD_KEYS)

    for keyword, adjustment in KEYWORD_MOOD_ADJUSTMENTS.items():
        if normalize_text(keyword) in name:
            add_scores(score_dict, adjustment)

    return score_dict

def normalize_mood_scores_to_10(score_dict):
    total = sum(score_dict.values())

    if total <= 0:
        return {
            "business_casual": 2,
            "casual": 4,
            "street": 1,
            "minimal": 2,
            "formal": 1,
        }

    raw_scaled = {k: (v / total) * 10 for k, v in score_dict.items()}
    floor_scores = {k: int(raw_scaled[k]) for k in raw_scaled}
    remainder = 10 - sum(floor_scores.values())

    decimal_order = sorted(
        raw_scaled.keys(),
        key=lambda k: raw_scaled[k] - floor_scores[k],
        reverse=True
    )

    normalized = floor_scores.copy()
    for i in range(remainder):
        normalized[decimal_order[i]] += 1

    return normalized

def get_primary_secondary_mood(mood_scores):
    sorted_items = sorted(mood_scores.items(), key=lambda x: x[1], reverse=True)
    primary = sorted_items[0][0]
    secondary = sorted_items[1][0] if len(sorted_items) > 1 else primary
    return primary, secondary

def build_display_mood_tag(mood_scores):
    sorted_items = sorted(mood_scores.items(), key=lambda x: x[1], reverse=True)
    first_mood, first_score = sorted_items[0]
    second_mood, second_score = sorted_items[1]
    gap = first_score - second_score

    if gap <= 1:
        return f"{first_mood}+{second_mood}", gap
    return first_mood, gap

def build_mood_scores(brand_name, category_name, product_name, fit_type):
    scores = init_score_dict(MOOD_KEYS)

    norm_brand = normalize_brand_name(brand_name)
    brand_prior = BRAND_MOOD_PRIORS.get(norm_brand, {})
    add_scores(scores, brand_prior, weight=1.0)

    category_prior = CATEGORY_MOOD_PRIORS.get(category_name, {})
    add_scores(scores, category_prior, weight=1.2)

    keyword_adj = get_keyword_mood_adjustments(product_name)
    add_scores(scores, keyword_adj, weight=1.3)

    fit_adj = FIT_MOOD_ADJUSTMENTS.get(fit_type, {})
    add_scores(scores, fit_adj, weight=1.0)

    for k in scores:
        if scores[k] < 0:
            scores[k] = 0

    normalized_scores = normalize_mood_scores_to_10(scores)
    primary_mood, secondary_mood = get_primary_secondary_mood(normalized_scores)
    display_mood_tag, mood_gap_1_2 = build_display_mood_tag(normalized_scores)

    return normalized_scores, primary_mood, secondary_mood, display_mood_tag, mood_gap_1_2

def build_age_scores(brand_name):
    norm_brand = normalize_brand_name(brand_name)
    return BRAND_AGE_PRIORS.get(norm_brand, {"20s": 3, "30s": 4, "40s_plus": 3})

# ===== subtype 파생 =====
def derive_sleeve_length_type(row) -> str:
    l2 = safe_str(row.get("lf_category_l2", ""))
    l3 = safe_str(row.get("lf_category_l3", ""))
    product_name = safe_str(row.get("product_name", "")).lower()

    text = f"{l2} {l3} {product_name}"

    if "반팔" in text or "숏 슬리브" in text or "short sleeve" in text:
        return "short_sleeve"
    if "긴팔" in text or "롱 슬리브" in text or "long sleeve" in text:
        return "long_sleeve"
    if "민소매" in text or "슬리브리스" in text or "sleeveless" in text:
        return "sleeveless"

    return "unknown"

def derive_pants_length_type(row) -> str:
    l2 = safe_str(row.get("lf_category_l2", ""))
    l3 = safe_str(row.get("lf_category_l3", ""))
    product_name = safe_str(row.get("product_name", "")).lower()

    text = f"{l2} {l3} {product_name}"

    if (
        "숏" in text
        or "쇼츠" in text
        or "shorts" in text
        or "반바지" in text
        or "버뮤다" in text
        or "bermuda" in text
        or "하프팬츠" in text
        or "하프 팬츠" in text
        or "half pants" in text
        or "5부" in text
        or "6부" in text
        or "7부" in text
    ):
        return "shorts"

    if "롱팬츠" in text or "긴바지" in text or "팬츠" in text or "trousers" in text:
        return "long"

    return "unknown"

def derive_top_subtype(row) -> str:
    l2 = safe_str(row.get("lf_category_l2", ""))
    l3 = safe_str(row.get("lf_category_l3", ""))
    product_name = safe_str(row.get("product_name", "")).lower()
    item_role = safe_str(row.get("item_role", "")).lower()

    text = f"{l2} {l3} {product_name}"

    if item_role not in {"top", "outer"}:
        return "unknown"

    if "후드" in text or "hoodie" in text or "hood" in text:
        return "hoodie"
    if "스웻" in text or "맨투맨" in text or "sweatshirt" in text or "sweat shirt" in text:
        return "sweatshirt"
    if "반집업" in text or "하프 집업" in text or "half zip" in text or "half-zip" in text:
        return "half_zip"

    if "티셔츠" in text:
        sleeve_type = derive_sleeve_length_type(row)
        if sleeve_type == "short_sleeve":
            return "short_sleeve_tshirt"
        if sleeve_type == "long_sleeve":
            return "long_sleeve_tshirt"
        return "tshirt"

    if "셔츠" in text:
        return "shirt"
    if "니트" in text or "sweater" in text or "터틀넥" in text or "turtleneck" in text:
        return "knit"
    if "가디건" in text or "cardigan" in text:
        return "cardigan"
    if "베스트" in text or "vest" in text:
        return "vest"
    if "바람막이" in text or "windbreaker" in text:
        return "windbreaker"
    if "점퍼" in text or "jumper" in text or "블루종" in text or "blouson" in text:
        return "jumper"
    if "자켓" in text or "jacket" in text or "블레이저" in text or "blazer" in text:
        return "jacket"
    if "코트" in text or "coat" in text or "트렌치" in text or "trench" in text:
        return "coat"

    return "unknown"

def derive_bottom_subtype(row) -> str:
    l2 = safe_str(row.get("lf_category_l2", ""))
    l3 = safe_str(row.get("lf_category_l3", ""))
    product_name = safe_str(row.get("product_name", "")).lower()
    item_role = safe_str(row.get("item_role", "")).lower()

    text = f"{l2} {l3} {product_name}"

    if item_role != "bottom":
        return "unknown"

    is_shorts = derive_pants_length_type(row) == "shorts"

    if "슬랙스" in text or "slacks" in text:
        return "slacks_shorts" if is_shorts else "slacks"
    if "데님팬츠" in text or "데님" in text or "jean" in text or "jeans" in text:
        return "denim_shorts" if is_shorts else "denim"
    if "치노" in text or "chino" in text:
        return "chino_shorts" if is_shorts else "chino"
    if "카고" in text or "cargo" in text:
        return "cargo_shorts" if is_shorts else "cargo"
    if "조거" in text or "jogger" in text or "트레이닝" in text or "sweatpants" in text:
        return "jogger_shorts" if is_shorts else "jogger"
    if "팬츠" in text or "trousers" in text:
        return "shorts" if is_shorts else "general_pants"
    if is_shorts:
        return "shorts"

    return "unknown"

# =========================
# 7. 파일 목록 확인
# =========================
print("\n[data 폴더 안 전체 파일 목록]")
all_files = list(DATA_DIR.glob("*"))
for file in all_files:
    print(file.name)

csv_files = [DATA_DIR / file_name for file_name in RAW_CSV_FILES]

print("\n[읽을 원본 csv 파일 목록]")
for file in csv_files:
    print(file.name)

missing_raw_files = [file.name for file in csv_files if not file.exists()]
if missing_raw_files:
    raise FileNotFoundError(f"다음 원본 csv 파일이 없습니다: {missing_raw_files}")

# =========================
# 8. csv 파일 읽기
# =========================
df_list = []

for file in csv_files:
    temp_df = pd.read_csv(file)
    temp_df["source_file"] = file.name
    df_list.append(temp_df)

df = pd.concat(df_list, ignore_index=True)

print("\n[합친 직후 데이터 크기]")
print(df.shape)

# =========================
# 9. 컬럼 정리 + 전처리 + 코드 추출
# =========================
df = standardize_columns(df)
df = preprocess_string_id_columns(df)
df = preprocess_numeric_columns(df)
df = recompute_season_flags(df)
df = add_season_profile_columns(df)
df = add_code_columns(df)

# =========================
# 9-1. season_temperature_score null 확인
# =========================
print("\n===== season_temperature_score null rows =====")
season_null_df = df[df["season_temperature_score"].isna()].copy()

print("null 개수:", len(season_null_df))

if not season_null_df.empty:
    print(
        season_null_df[
            [
                "product_code",
                "product_name",
                "brand_name",
                "season",
                "season_name_raw",
                "season_spring",
                "season_summer",
                "season_fall",
                "season_winter",
                "season_all",
                "season_warm_weight",
                "season_mid_weight",
                "season_cold_weight",
                "season_temperature_score",
                "season_profile_label",
                "source_file",
            ]
        ]
        .head(50)
        .to_string(index=False)
    )
else:
    print("null 없음")

season_null_output = DATA_DIR / "season_temperature_null_rows.csv"
season_null_df.to_csv(season_null_output, index=False, encoding="utf-8-sig")

print("\n[season_temperature_score null rows 저장 완료]")
print(season_null_output)

# =========================
# 10. product_code 기준 중복 확인 + 저장
# =========================
dup_df_before_drop = df[df["product_code"].duplicated(keep=False)].copy()

print("\n===== duplicated product_code rows before drop =====")
print(dup_df_before_drop.sort_values(["product_code", "source_file"]).head(50))

dup_output_path = DATA_DIR / "duplicated_product_codes.csv"
dup_df_before_drop.to_csv(dup_output_path, index=False, encoding="utf-8-sig")

print("\n[중복 product_code 저장 완료]")
print(dup_output_path)

print("\n[중복 제거 전 행 수]")
print(len(df))

df = df.drop_duplicates(subset=["product_code"], keep="first").copy()

print("\n[중복 제거 후 행 수]")
print(len(df))

# =========================
# 11. 결과 확인
# =========================
basic_check(df)
show_unique_codes(df)

print("\n===== season_name_raw 분포 상위 30 =====")
print(df["season_name_raw"].fillna("(null)").value_counts(dropna=False).head(30))

print("\n===== 시즌 플래그 합계 =====")
print(
    df[[
        "season_spring",
        "season_summer",
        "season_fall",
        "season_winter",
        "season_all",
    ]].sum()
)

print("\n===== season_profile_label 분포 =====")
print(df["season_profile_label"].value_counts(dropna=False).head(30))

print("\n===== season profile sample 30 =====")
print(
    df[
        [
            "product_code",
            "product_name",
            "season_name_raw",
            "season_spring",
            "season_summer",
            "season_fall",
            "season_winter",
            "season_all",
            "season_warm_weight",
            "season_mid_weight",
            "season_cold_weight",
            "season_temperature_score",
            "season_profile_label",
        ]
    ]
    .head(30)
    .to_string(index=False)
)

# =========================
# 12. master_table_step1 저장
# =========================
output_path = DATA_DIR / "master_table_step1.csv"
df.to_csv(output_path, index=False, encoding="utf-8-sig")

print("\n[저장 완료 - master_table_step1]")
print(output_path)

# =========================
# 13. category_code 샘플 확인용 파일 저장
# =========================
category_sample = (
    df[["category_code", "product_code", "product_name", "brand_name", "source_file"]]
    .sort_values(["category_code", "product_code"])
    .drop_duplicates(subset=["category_code", "product_code"])
)

category_sample_output = DATA_DIR / "category_code_samples.csv"
category_sample.to_csv(category_sample_output, index=False, encoding="utf-8-sig")

print("\n[category_code 샘플 저장 완료]")
print(category_sample_output)

# =========================
# 14. color_code 샘플 확인용 파일 저장
# =========================
color_sample = (
    df[["color_code", "product_code", "product_name", "brand_name", "source_file"]]
    .sort_values(["color_code", "product_code"])
    .drop_duplicates(subset=["color_code", "product_code"])
)

color_sample_output = DATA_DIR / "color_code_samples.csv"
color_sample.to_csv(color_sample_output, index=False, encoding="utf-8-sig")

print("\n[color_code 샘플 저장 완료]")
print(color_sample_output)

# =========================
# 15. category_code -> category_name 매핑
# =========================
category_map = {
    "BA": "가방",
    "BE": "벨트",
    "CO": "코트",
    "GV": "장갑",
    "HE": "모자",
    "JA": "자켓",
    "JU": "점퍼",
    "LG": "펫의류",
    "MU": "머플러",
    "NE": "넥타이",
    "PA": "팬츠",
    "SH": "셔츠",
    "SO": "슬리퍼",
    "SS": "양말",
    "ST": "수트",
    "SW": "스웨터/맨투맨",
    "TR": "트렌치코트",
    "TS": "티셔츠",
    "VE": "베스트",
}

df["category_name"] = df["category_code"].map(category_map)
df["size_type"] = df["category_name"].apply(get_size_type)

print("\n===== category_name null count =====")
print(df["category_name"].isnull().sum())

print("\n===== category_name unique =====")
print(sorted(df["category_name"].dropna().unique().tolist()))

print("\n===== size_type value counts =====")
print(df["size_type"].value_counts(dropna=False))

category_mapped_output = DATA_DIR / "master_table_step2_category.csv"
df.to_csv(category_mapped_output, index=False, encoding="utf-8-sig")

print("\n[저장 완료 - master_table_step2_category]")
print(category_mapped_output)

# =========================
# 16. color_code -> color_name / color_group 매핑
# =========================
color_name_map = {
    "B1": "블루", "B2": "블루", "B3": "블루", "B4": "블루", "B5": "블루",
    "BA": "블랙", "BB": "블랙", "BK": "블랙",
    "C1": "코랄", "C2": "코랄", "C3": "코랄",
    "CG": "차콜",
    "G1": "그레이", "G2": "그레이", "G3": "그레이",
    "CM": "카멜",
    "CR": "크림",
    "I1": "베이지", "I2": "베이지", "I3": "베이지", "I4": "베이지",
    "IV": "아이보리",
    "OW": "오프화이트",
    "WT": "화이트",
    "D1": "와인/버건디", "D2": "와인/버건디", "D3": "와인/버건디",
    "E1": "그린", "E2": "그린", "E3": "그린", "E5": "그린",
    "K1": "카키", "K2": "카키", "K3": "카키", "K4": "카키", "K5": "카키",
    "L1": "그린", "L2": "그린",
    "MU": "멀티컬러",
    "N1": "네이비", "N2": "네이비", "N3": "네이비", "N5": "네이비",
    "O1": "오렌지", "O2": "오렌지", "O3": "오렌지",
    "P1": "핑크", "P2": "핑크", "P3": "핑크", "P4": "핑크",
    "R1": "레드", "R2": "레드", "R3": "레드",
    "S1": "브라운", "S2": "브라운", "S3": "브라운",
    "W1": "브라운", "W2": "브라운", "W3": "브라운",
    "SV": "실버",
    "T1": "청록", "T2": "청록", "T3": "청록",
    "U1": "퍼플", "U2": "퍼플", "U3": "퍼플",
    "V1": "바이올렛", "V2": "바이올렛", "V3": "바이올렛",
    "Y1": "옐로우", "Y2": "옐로우", "Y3": "옐로우",
}

color_group_map = {
    "BA": "블랙", "BB": "블랙", "BK": "블랙",
    "CR": "화이트/아이보리", "IV": "화이트/아이보리", "OW": "화이트/아이보리", "WT": "화이트/아이보리",
    "CG": "그레이/차콜", "G1": "그레이/차콜", "G2": "그레이/차콜", "G3": "그레이/차콜",
    "B1": "블루", "B2": "블루", "B3": "블루", "B4": "블루", "B5": "블루",
    "T1": "블루", "T2": "블루", "T3": "블루",
    "N1": "네이비", "N2": "네이비", "N3": "네이비", "N5": "네이비",
    "CM": "베이지/카멜", "I1": "베이지/카멜", "I2": "베이지/카멜", "I3": "베이지/카멜", "I4": "베이지/카멜",
    "S1": "브라운", "S2": "브라운", "S3": "브라운", "W1": "브라운", "W2": "브라운", "W3": "브라운",
    "E1": "그린/카키", "E2": "그린/카키", "E3": "그린/카키", "E5": "그린/카키",
    "K1": "그린/카키", "K2": "그린/카키", "K3": "그린/카키", "K4": "그린/카키", "K5": "그린/카키",
    "L1": "그린/카키", "L2": "그린/카키",
    "D1": "레드/버건디", "D2": "레드/버건디", "D3": "레드/버건디",
    "R1": "레드/버건디", "R2": "레드/버건디", "R3": "레드/버건디",
    "P1": "핑크", "P2": "핑크", "P3": "핑크", "P4": "핑크",
    "O1": "옐로우/오렌지", "O2": "옐로우/오렌지", "O3": "옐로우/오렌지",
    "Y1": "옐로우/오렌지", "Y2": "옐로우/오렌지", "Y3": "옐로우/오렌지",
    "U1": "퍼플", "U2": "퍼플", "U3": "퍼플",
    "V1": "퍼플", "V2": "퍼플", "V3": "퍼플",
    "SV": "실버",
    "MU": "멀티컬러",
    "C1": "코랄", "C2": "코랄", "C3": "코랄",
}

df["color_name"] = df["color_code"].map(color_name_map)
df["color_group"] = df["color_code"].map(color_group_map)

print("\n===== color_name null count =====")
print(df["color_name"].isnull().sum())

print("\n===== color_group null count =====")
print(df["color_group"].isnull().sum())

print("\n===== color_name unique =====")
print(sorted(df["color_name"].dropna().unique().tolist()))

print("\n===== color_group unique =====")
print(sorted(df["color_group"].dropna().unique().tolist()))

print("\n===== unmapped color_code =====")
print(sorted(df.loc[df["color_group"].isna(), "color_code"].dropna().unique().tolist()))

# =========================
# 17. price_range 생성
# =========================
df["price_range"] = df["sale_price"].apply(make_price_range)

print("\n===== price_range 분포 =====")
print(df["price_range"].value_counts(dropna=False))

# =========================
# 18. size_stock_detail 파싱
# =========================
df["available_size_list"] = df.apply(extract_available_sizes_from_row, axis=1)
df["available_size_count"] = df["available_size_list"].apply(len)
df["available_size_text"] = df["available_size_list"].apply(size_list_to_string)

df["has_stock"] = np.where(
    (df["size_total_stock"] > 0) | (df["available_size_count"] > 0),
    1,
    0
)

print("\n===== available_size_list sample 20 =====")
print(
    df[
        [
            "product_code", "product_name", "category_name", "size_type",
            "size_stock_detail", "size_total_stock", "available_size_list",
            "available_size_count", "available_size_text", "has_stock",
        ]
    ]
    .head(20)
    .to_string(index=False)
)

print("\n===== available_size_count 분포 =====")
print(df["available_size_count"].value_counts(dropna=False).sort_index())

print("\n===== has_stock 분포 =====")
print(df["has_stock"].value_counts(dropna=False))

print("\n===== bottom size normalization sample =====")
print(
    df.loc[
        df["category_name"] == "팬츠",
        ["product_code", "product_name", "size_stock_detail", "available_size_text"]
    ]
    .head(30)
    .to_string(index=False)
)

print("\n===== top size normalization sample =====")
print(
    df.loc[
        df["size_type"] == "top",
        ["product_code", "product_name", "category_name", "size_stock_detail", "available_size_text"]
    ]
    .head(30)
    .to_string(index=False)
)

# =========================
# 19. 점수 컬럼 생성
# =========================
df["purchase_part"] = np.minimum(df["purchase_count"], 600) * 5
df["wish_part"] = np.minimum(df["wish_count"], 200) * 3.5
df["view_part"] = np.minimum(df["viewing_count"], 100) * 3
df["review_count_part"] = np.minimum(df["review_count"], 100) * 5
df["review_score_part"] = np.minimum(df["review_score"], 5.0) * 60

df["newproductscore"] = np.select(
    [df["product_sale_type"] == 1, df["product_sale_type"] == 2],
    [500, 200],
    default=0
)

df["final_score"] = (
    df["purchase_part"]
    + df["wish_part"]
    + df["view_part"]
    + df["review_count_part"]
    + df["review_score_part"]
    + df["newproductscore"]
)

print("\n===== score summary =====")
print(
    df[
        [
            "purchase_part", "wish_part", "view_part", "review_count_part",
            "review_score_part", "newproductscore", "final_score",
        ]
    ].describe()
)

top20 = (
    df[
        [
            "product_code", "product_name", "brand_name", "brand_id", "brand_group_id",
            "category_name", "size_type", "color_name", "color_group", "price_range",
            "sale_price", "purchase_count", "wish_count", "viewing_count",
            "review_count", "review_score", "product_sale_type",
            "available_size_text", "final_score",
        ]
    ]
    .sort_values("final_score", ascending=False)
    .head(20)
    .copy()
)

print("\n===== final_score top 20 =====")
print(top20.to_string(index=False))

# =========================
# 20. 스타일링용 컬럼 생성
# =========================
df["item_role"] = df["category_name"].apply(derive_item_role)
df["fit_type"] = df["product_name"].apply(derive_fit_type)
df["material_type"] = df["product_name"].apply(derive_material_type)
df["pattern_type"] = df["product_name"].apply(derive_pattern_type)

df["sleeve_length_type"] = df.apply(derive_sleeve_length_type, axis=1)
df["pants_length_type"] = df.apply(derive_pants_length_type, axis=1)
df["top_subtype"] = df.apply(derive_top_subtype, axis=1)
df["bottom_subtype"] = df.apply(derive_bottom_subtype, axis=1)

mood_results = df.apply(
    lambda row: build_mood_scores(
        brand_name=row["brand_name"],
        category_name=row["category_name"],
        product_name=row["product_name"],
        fit_type=row["fit_type"],
    ),
    axis=1
)

df["mood_score_dict"] = mood_results.apply(lambda x: x[0])
df["primary_mood"] = mood_results.apply(lambda x: x[1])
df["secondary_mood"] = mood_results.apply(lambda x: x[2])
df["display_mood_tag"] = mood_results.apply(lambda x: x[3])
df["mood_gap_1_2"] = mood_results.apply(lambda x: x[4])

for mood_key in MOOD_KEYS:
    df[f"mood_{mood_key}"] = df["mood_score_dict"].apply(lambda d: d.get(mood_key, 0))

age_results = df["brand_name"].apply(build_age_scores)
df["age_score_dict"] = age_results

for age_key in AGE_KEYS:
    df[f"age_{age_key}"] = df["age_score_dict"].apply(lambda d: d.get(age_key, 0))

df["luxury_level"] = df["material_type"].apply(derive_luxury_level)
df["texture_class"] = df["material_type"].apply(derive_texture_class)

print("\n===== sleeve_length_type 분포 =====")
print(df["sleeve_length_type"].value_counts(dropna=False))

print("\n===== pants_length_type 분포 =====")
print(df["pants_length_type"].value_counts(dropna=False))

print("\n===== top_subtype 분포 상위 30 =====")
print(df["top_subtype"].value_counts(dropna=False).head(30))

print("\n===== bottom_subtype 분포 상위 30 =====")
print(df["bottom_subtype"].value_counts(dropna=False).head(30))

print("\n===== styling columns sample 20 =====")
print(
    df[
        [
            "brand_name", "category_name", "product_name", "lf_category_l2", "lf_category_l3",
            "item_role", "sleeve_length_type", "pants_length_type",
            "top_subtype", "bottom_subtype",
            "fit_type", "material_type", "pattern_type",
            "primary_mood", "secondary_mood", "display_mood_tag", "mood_gap_1_2",
            "mood_business_casual", "mood_casual", "mood_street", "mood_minimal", "mood_formal",
            "age_20s", "age_30s", "age_40s_plus",
            "luxury_level", "texture_class",
            "season_warm_weight", "season_mid_weight", "season_cold_weight",
            "season_temperature_score", "season_profile_label",
        ]
    ]
    .head(20)
    .to_string(index=False)
)

print("\n===== primary_mood 분포 =====")
print(df["primary_mood"].value_counts(dropna=False))

print("\n===== secondary_mood 분포 =====")
print(df["secondary_mood"].value_counts(dropna=False))

print("\n===== display_mood_tag 분포 상위 30 =====")
print(df["display_mood_tag"].value_counts(dropna=False).head(30))

print("\n===== fit_type 분포 =====")
print(df["fit_type"].value_counts(dropna=False))

print("\n===== material_type 분포 =====")
print(df["material_type"].value_counts(dropna=False))

print("\n===== item_role 분포 =====")
print(df["item_role"].value_counts(dropna=False))

print("\n===== role-aware 정리 직전 outer의 top_subtype 분포 =====")
print(
    df[df["item_role"] == "outer"]["top_subtype"]
    .value_counts(dropna=False)
    .head(30)
)

print("\n===== role-aware 정리 직전 outer sample =====")
print(
    df.loc[
        df["item_role"] == "outer",
        ["product_code", "product_name", "category_name", "item_role", "top_subtype"]
    ]
    .head(30)
    .to_string(index=False)
)

# =========================
# role-aware unknown 정리
# =========================
for col in ["item_role", "sleeve_length_type", "pants_length_type", "top_subtype", "bottom_subtype"]:
    if col in df.columns:
        df[col] = df[col].fillna("").astype(str).str.strip()

for col in ["sleeve_length_type", "pants_length_type", "top_subtype", "bottom_subtype"]:
    if col in df.columns:
        df[col] = df[col].replace({
            "": "unknown",
            "nan": "unknown",
            "None": "unknown",
        })

if "item_role" in df.columns and "sleeve_length_type" in df.columns:
    df.loc[df["item_role"] != "top", "sleeve_length_type"] = "not_applicable"

if "item_role" in df.columns and "pants_length_type" in df.columns:
    df.loc[df["item_role"] != "bottom", "pants_length_type"] = "not_applicable"

if "item_role" in df.columns and "top_subtype" in df.columns:
    df.loc[~df["item_role"].isin(["top", "outer"]), "top_subtype"] = "not_applicable"

if "item_role" in df.columns and "bottom_subtype" in df.columns:
    df.loc[df["item_role"] != "bottom", "bottom_subtype"] = "not_applicable"

# =========================
# 확인 출력
# =========================
print("\n===== role-aware 정리 후 분포 =====")

print("\n===== sleeve_length_type 분포 =====")
print(df["sleeve_length_type"].value_counts(dropna=False))

print("\n===== pants_length_type 분포 =====")
print(df["pants_length_type"].value_counts(dropna=False))

print("\n===== top_subtype 분포 상위 30 =====")
print(df["top_subtype"].value_counts(dropna=False).head(30))

print("\n===== bottom_subtype 분포 상위 30 =====")
print(df["bottom_subtype"].value_counts(dropna=False).head(30))

print("\n===== top만 필터한 sleeve_length_type 분포 =====")
print(df[df["item_role"] == "top"]["sleeve_length_type"].value_counts(dropna=False))

print("\n===== bottom만 필터한 pants_length_type 분포 =====")
print(df[df["item_role"] == "bottom"]["pants_length_type"].value_counts(dropna=False))

print("\n===== top만 필터한 top_subtype 분포 =====")
print(df[df["item_role"] == "top"]["top_subtype"].value_counts(dropna=False).head(30))

print("\n===== bottom만 필터한 bottom_subtype 분포 =====")
print(df[df["item_role"] == "bottom"]["bottom_subtype"].value_counts(dropna=False).head(30))

print("\n===== outer만 필터한 top_subtype 분포 =====")
print(
    df[df["item_role"] == "outer"]["top_subtype"]
    .value_counts(dropna=False)
    .head(30)
)

print("\n===== role-aware 정리 후 outer sample =====")
print(
    df.loc[
        df["item_role"] == "outer",
        ["product_code", "product_name", "category_name", "item_role", "top_subtype"]
    ]
    .head(30)
    .to_string(index=False)
)

# =========================
# 21. 최종 저장
# =========================
final_output_path = DATA_DIR / "master_table_step4_styling.csv"
df.to_csv(final_output_path, index=False, encoding="utf-8-sig")

print("\n[저장 완료 - master_table_step4_styling]")
print(final_output_path)