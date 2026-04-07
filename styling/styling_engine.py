import os
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


# =========================
# 기본 설정
# =========================
MOOD_COLS = [
    "mood_business_casual",
    "mood_casual",
    "mood_street",
    "mood_minimal",
    "mood_formal",
]

AGE_COLS = [
    "age_20s",
    "age_30s",
    "age_40s_plus",
]

SEASON_COLS = [
    "season_spring",
    "season_summer",
    "season_fall",
    "season_winter",
]

NEUTRAL_COLOR_GROUPS = {
    "블랙",
    "화이트/아이보리",
    "그레이/차콜",
    "네이비",
    "베이지/카멜",
    "브라운",
}

SIMILAR_COLOR_GROUPS = {
    ("블랙", "그레이/차콜"),
    ("화이트/아이보리", "베이지/카멜"),
    ("네이비", "블루"),
    ("브라운", "베이지/카멜"),
    ("그린/카키", "베이지/카멜"),
    ("레드/버건디", "브라운"),
}

GOOD_COLOR_PAIRS = {
    ("네이비", "화이트/아이보리"),
    ("네이비", "베이지/카멜"),
    ("블랙", "화이트/아이보리"),
    ("블랙", "그레이/차콜"),
    ("블루", "화이트/아이보리"),
    ("브라운", "화이트/아이보리"),
    ("그린/카키", "화이트/아이보리"),
}

BAD_COLOR_PAIRS = {
    ("레드/버건디", "옐로우/오렌지"),
    ("핑크", "옐로우/오렌지"),
    ("퍼플", "그린/카키"),
}

INVALID_SUBTYPE_VALUES = {"", "unknown", "not_applicable", "not applicable", "na", "none", "null"}

WINTER_HEAVY_KEYWORDS = {
    "패딩", "다운", "down", "puffer", "플리스", "fleece",
    "기모", "코지 웜", "cosy warm", "cosy_warm", "cosywarm",
    "헤비다운", "heavy down"
}

SUMMER_LIGHT_KEYWORDS = {
    "반팔", "short sleeve", "short-sleeve", "sleeveless",
    "민소매", "리넨", "linen", "쿨", "cool", "나일론", "nylon"
}


# =========================
# 유틸
# =========================
def safe_float(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def safe_str(value, default: str = "") -> str:
    if pd.isna(value):
        return default
    return str(value).strip()


def normalize_score(value: float, min_value: float, max_value: float) -> float:
    if max_value <= min_value:
        return 0.0
    value = max(min_value, min(value, max_value))
    return (value - min_value) / (max_value - min_value)


def get_mood_vector(item: pd.Series) -> np.ndarray:
    vec = np.array([safe_float(item.get(col, 0.0)) for col in MOOD_COLS], dtype=float)
    total = vec.sum()
    if total <= 0:
        return np.zeros(len(MOOD_COLS), dtype=float)
    return vec / total


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def pair_key(a: str, b: str) -> tuple:
    return tuple(sorted([str(a), str(b)]))


def has_keyword(text: str, keywords: set) -> bool:
    text = safe_str(text).lower()
    return any(keyword.lower() in text for keyword in keywords)


# =========================
# 시즌 유틸
# =========================
def get_season_vector(item: pd.Series) -> np.ndarray:
    return np.array([safe_float(item.get(col, 0.0)) for col in SEASON_COLS], dtype=float)


def season_info_missing(item: pd.Series) -> bool:
    return get_season_vector(item).sum() <= 0


def season_overlap_count(item_a: pd.Series, item_b: pd.Series) -> int:
    vec_a = get_season_vector(item_a)
    vec_b = get_season_vector(item_b)
    return int(np.sum((vec_a > 0) & (vec_b > 0)))


def season_overlap_score(item_a: pd.Series, item_b: pd.Series) -> float:
    if season_info_missing(item_a) or season_info_missing(item_b):
        return 50.0

    overlap = season_overlap_count(item_a, item_b)

    if overlap >= 2:
        return 100.0
    elif overlap == 1:
        return 75.0
    else:
        return 20.0


def build_season_reason(item_a: pd.Series, item_b: pd.Series, label: str = "top-outer") -> str:
    if season_info_missing(item_a) or season_info_missing(item_b):
        return f"{label} 시즌 정보 부족"

    overlap = season_overlap_count(item_a, item_b)

    if overlap >= 2:
        return f"{label} 시즌 궁합이 좋음"
    elif overlap == 1:
        return f"{label} 시즌 일부 겹침"
    else:
        return f"{label} 시즌 불일치"


def is_winter_heavy_item(item: pd.Series) -> bool:
    name = safe_str(item.get("product_name", "")).lower()
    category = safe_str(item.get("category_name", "")).lower()
    season_raw = safe_str(item.get("season_name_raw", "")).lower()

    text = f"{name} {category} {season_raw}"

    if has_keyword(text, WINTER_HEAVY_KEYWORDS):
        return True

    season_winter = safe_float(item.get("season_winter", 0))
    season_summer = safe_float(item.get("season_summer", 0))

    if season_winter > 0 and season_summer <= 0:
        return True

    return False


def is_explicit_summer_item(item: pd.Series) -> bool:
    name = safe_str(item.get("product_name", "")).lower()
    category = safe_str(item.get("category_name", "")).lower()
    season_raw = safe_str(item.get("season_name_raw", "")).lower()

    text = f"{name} {category} {season_raw}"

    if has_keyword(text, SUMMER_LIGHT_KEYWORDS):
        return True

    season_summer = safe_float(item.get("season_summer", 0))
    season_winter = safe_float(item.get("season_winter", 0))

    if season_summer > 0 and season_winter <= 0:
        return True

    return False


def should_block_by_season_conflict(
    anchor_item: pd.Series,
    candidate_item: pd.Series,
) -> bool:
    anchor_is_summer = is_explicit_summer_item(anchor_item)
    candidate_is_winter_heavy = is_winter_heavy_item(candidate_item)

    if anchor_is_summer and candidate_is_winter_heavy:
        return True

    return False


def apply_strict_season_filter(
    anchor_item: pd.Series,
    candidates_df: pd.DataFrame,
) -> pd.DataFrame:
    if candidates_df.empty:
        return candidates_df.copy()

    filtered_rows = []

    for _, row in candidates_df.iterrows():
        if should_block_by_season_conflict(anchor_item, row):
            continue
        filtered_rows.append(row)

    if not filtered_rows:
        return pd.DataFrame(columns=candidates_df.columns)

    return pd.DataFrame(filtered_rows).reset_index(drop=True)


# =========================
# 데이터 로드
# =========================
def load_master_table(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    required_defaults = {
        "product_code": "",
        "product_name": "",
        "brand_name": "",
        "category_name": "",
        "item_role": "unknown",
        "color_group": "",
        "fit_type": "unknown",
        "primary_mood": "",
        "secondary_mood": "",
        "display_mood_tag": "",
        "final_score": 0.0,
        "has_stock": 0,
        "available_size_count": 0,
        "top_subtype": "unknown",
        "bottom_subtype": "unknown",
        "sleeve_length_type": "unknown",
        "pants_length_type": "unknown",
        "season_name_raw": "",
        "season_spring": 0,
        "season_summer": 0,
        "season_fall": 0,
        "season_winter": 0,
        "season_all": 0,
    }

    for col, default_value in required_defaults.items():
        if col not in df.columns:
            df[col] = default_value

    for col in MOOD_COLS + AGE_COLS + SEASON_COLS + ["season_all"]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["final_score"] = pd.to_numeric(df["final_score"], errors="coerce").fillna(0.0)
    df["has_stock"] = pd.to_numeric(df["has_stock"], errors="coerce").fillna(0).astype(int)
    df["available_size_count"] = pd.to_numeric(df["available_size_count"], errors="coerce").fillna(0).astype(int)

    text_cols = [
        "product_code",
        "product_name",
        "brand_name",
        "category_name",
        "item_role",
        "color_group",
        "fit_type",
        "primary_mood",
        "secondary_mood",
        "display_mood_tag",
        "top_subtype",
        "bottom_subtype",
        "sleeve_length_type",
        "pants_length_type",
        "season_name_raw",
    ]

    for col in text_cols:
        df[col] = df[col].fillna("").astype(str).str.strip()

    return df


# =========================
# Anchor 조회
# =========================
def get_anchor_item(df: pd.DataFrame, product_code: str) -> pd.Series:
    target = df[df["product_code"] == product_code]
    if target.empty:
        raise ValueError(f"Anchor product_code not found: {product_code}")
    return target.iloc[0]


# =========================
# 역할 매핑
# =========================
def determine_target_roles(anchor_role: str) -> List[str]:
    anchor_role = safe_str(anchor_role).lower()

    role_map = {
        "outer": ["top", "bottom"],
        "top": ["outer", "bottom"],
        "bottom": ["top", "outer"],
        "set": ["top"],
        "onepiece": ["outer"],
        "unknown": ["top", "bottom", "outer"],
    }

    return role_map.get(anchor_role, ["top", "bottom", "outer"])


def resolve_target_roles(
    anchor_role: str,
    recommendation_mode: str = "all",
) -> List[str]:
    natural_roles = determine_target_roles(anchor_role)

    mode_map = {
        "all": ["top", "bottom", "outer"],
        "top_only": ["top"],
        "bottom_only": ["bottom"],
        "outer_only": ["outer"],
        "top_bottom": ["top", "bottom"],
        "top_outer": ["top", "outer"],
        "bottom_outer": ["bottom", "outer"],
    }

    requested_roles = mode_map.get(recommendation_mode, ["top", "bottom", "outer"])
    final_roles = [role for role in requested_roles if role in natural_roles]

    return final_roles


# =========================
# 후보 필터링
# =========================
def filter_candidates(
    df: pd.DataFrame,
    anchor_item: pd.Series,
    target_roles: List[str],
    allowed_brands: Optional[List[str]] = None,
    same_brand_only: bool = False,
) -> pd.DataFrame:
    candidates = df.copy()

    candidates = candidates[candidates["product_code"] != anchor_item["product_code"]]
    candidates = candidates[candidates["has_stock"] == 1]
    candidates = candidates[candidates["item_role"].str.lower().isin([r.lower() for r in target_roles])]

    if same_brand_only:
        candidates = candidates[candidates["brand_name"] == anchor_item["brand_name"]]

    if allowed_brands:
        candidates = candidates[candidates["brand_name"].isin(allowed_brands)]

    candidates = candidates.reset_index(drop=True)
    return candidates


# =========================
# 점수 계산 - 세부 항목
# =========================
def calculate_mood_score(anchor_item: pd.Series, candidate_item: pd.Series) -> float:
    anchor_vec = get_mood_vector(anchor_item)
    cand_vec = get_mood_vector(candidate_item)

    sim = cosine_similarity(anchor_vec, cand_vec)
    sim_score = sim * 100

    anchor_primary = safe_str(anchor_item.get("primary_mood"))
    anchor_secondary = safe_str(anchor_item.get("secondary_mood"))
    cand_primary = safe_str(candidate_item.get("primary_mood"))
    cand_secondary = safe_str(candidate_item.get("secondary_mood"))

    bonus = 0.0
    if anchor_primary and cand_primary and anchor_primary == cand_primary:
        bonus += 8.0
    if anchor_primary and cand_secondary and anchor_primary == cand_secondary:
        bonus += 4.0
    if anchor_secondary and cand_primary and anchor_secondary == cand_primary:
        bonus += 4.0

    return min(100.0, sim_score + bonus)


def calculate_color_score(anchor_item: pd.Series, candidate_item: pd.Series) -> float:
    color_a = safe_str(anchor_item.get("color_group"))
    color_b = safe_str(candidate_item.get("color_group"))

    if not color_a or not color_b:
        return 50.0

    if color_a == color_b:
        return 82.0

    key = pair_key(color_a, color_b)

    if key in BAD_COLOR_PAIRS:
        return 28.0

    if key in GOOD_COLOR_PAIRS:
        return 90.0

    if key in SIMILAR_COLOR_GROUPS:
        return 78.0

    if color_a in NEUTRAL_COLOR_GROUPS or color_b in NEUTRAL_COLOR_GROUPS:
        return 75.0

    return 58.0


def get_formality_level(item: pd.Series) -> float:
    mood_scores = {
        "business_casual": safe_float(item.get("mood_business_casual", 0.0)),
        "casual": safe_float(item.get("mood_casual", 0.0)),
        "street": safe_float(item.get("mood_street", 0.0)),
        "minimal": safe_float(item.get("mood_minimal", 0.0)),
        "formal": safe_float(item.get("mood_formal", 0.0)),
    }

    weights = {
        "street": 1.0,
        "casual": 2.0,
        "minimal": 3.0,
        "business_casual": 4.0,
        "formal": 5.0,
    }

    total_mood = sum(mood_scores.values())
    if total_mood <= 0:
        return 3.0

    weighted_sum = sum(mood_scores[k] * weights[k] for k in mood_scores)
    return weighted_sum / total_mood


def calculate_formality_score(anchor_item: pd.Series, candidate_item: pd.Series) -> float:
    level_a = get_formality_level(anchor_item)
    level_b = get_formality_level(candidate_item)
    gap = abs(level_a - level_b)

    score = max(20.0, 100.0 - gap * 20.0)
    return score


def calculate_fit_score(anchor_item: pd.Series, candidate_item: pd.Series) -> float:
    fit_a = safe_str(anchor_item.get("fit_type", "unknown")).lower()
    fit_b = safe_str(candidate_item.get("fit_type", "unknown")).lower()

    role_a = safe_str(anchor_item.get("item_role", "unknown")).lower()
    role_b = safe_str(candidate_item.get("item_role", "unknown")).lower()

    if fit_a == "unknown" or fit_b == "unknown":
        return 60.0

    if fit_a == fit_b:
        return 78.0

    loose_keywords = {"oversized", "wide", "relaxed", "loose"}
    slim_keywords = {"slim", "skinny", "tight"}

    a_loose = fit_a in loose_keywords
    b_loose = fit_b in loose_keywords
    a_slim = fit_a in slim_keywords
    b_slim = fit_b in slim_keywords

    if role_a != role_b:
        if a_loose and b_loose:
            return 62.0
        if a_slim and b_slim:
            return 75.0
        if (a_loose and b_slim) or (a_slim and b_loose):
            return 70.0

    return 65.0


def calculate_brand_score(anchor_item: pd.Series, candidate_item: pd.Series) -> float:
    brand_a = safe_str(anchor_item.get("brand_name"))
    brand_b = safe_str(candidate_item.get("brand_name"))

    if not brand_a or not brand_b:
        return 50.0

    if brand_a == brand_b:
        return 85.0

    return 65.0


def calculate_popularity_score(candidate_item: pd.Series, max_final_score: float) -> float:
    final_score = safe_float(candidate_item.get("final_score", 0.0))
    if max_final_score <= 0:
        return 50.0
    return normalize_score(final_score, 0.0, max_final_score) * 100.0


def calculate_age_score(anchor_item: pd.Series, candidate_item: pd.Series) -> float:
    vec_a = np.array([safe_float(anchor_item.get(col, 0.0)) for col in AGE_COLS], dtype=float)
    vec_b = np.array([safe_float(candidate_item.get(col, 0.0)) for col in AGE_COLS], dtype=float)

    if vec_a.sum() <= 0 or vec_b.sum() <= 0:
        return 50.0

    vec_a = vec_a / vec_a.sum()
    vec_b = vec_b / vec_b.sum()

    sim = cosine_similarity(vec_a, vec_b)
    return sim * 100.0


# =========================
# subtype/length 우선 사용
# =========================
def infer_bottom_subtype_fallback(item: pd.Series) -> str:
    name = safe_str(item.get("product_name")).lower()
    category = safe_str(item.get("category_name", "")).lower()
    mood_tag = safe_str(item.get("display_mood_tag", "")).lower()

    text = f"{name} {category} {mood_tag}"

    if any(keyword in text for keyword in ["슬랙스", "slacks", "trouser", "trousers"]):
        return "slacks"
    if any(keyword in text for keyword in ["데님", "jean", "jeans", "청바지"]):
        return "denim"
    if any(keyword in text for keyword in ["치노", "chino"]):
        return "chino"
    if any(keyword in text for keyword in ["조거", "jogger", "sweat pants", "sweatpants", "트레이닝"]):
        return "jogger"
    if any(keyword in text for keyword in ["카고", "cargo"]):
        return "cargo"
    if any(keyword in text for keyword in ["숏", "쇼츠", "shorts", "반바지"]):
        return "shorts"
    if any(keyword in text for keyword in ["팬츠", "pants", "trousers"]):
        return "general_pants"

    return "unknown"


def infer_top_outer_subtype_fallback(item: pd.Series) -> str:
    name = safe_str(item.get("product_name")).lower()
    category = safe_str(item.get("category_name", "")).lower()
    mood_tag = safe_str(item.get("display_mood_tag", "")).lower()

    text = f"{name} {category} {mood_tag}"

    if any(keyword in text for keyword in ["후드", "hood", "hoodie"]):
        return "hoodie"
    if any(keyword in text for keyword in ["스웻", "맨투맨", "sweatshirt", "sweat shirt"]):
        return "sweatshirt"
    if any(keyword in text for keyword in ["반집업", "하프 집업", "half zip", "half-zip"]):
        return "half_zip"
    if any(keyword in text for keyword in ["가디건", "cardigan"]):
        return "cardigan"
    if any(keyword in text for keyword in ["베스트", "vest"]):
        return "vest"
    if any(keyword in text for keyword in ["니트", "knit", "sweater", "터틀넥", "turtle-neck", "turtleneck"]):
        return "knit"
    if any(keyword in text for keyword in ["셔츠", "shirt"]):
        return "shirt"
    if any(keyword in text for keyword in ["바람막이", "windbreaker"]):
        return "windbreaker"
    if any(keyword in text for keyword in ["워크자켓", "워크 자켓", "자켓", "jacket", "블레이저", "blazer"]):
        return "jacket"
    if any(keyword in text for keyword in ["점퍼", "jumper", "블루종", "blouson", "ma-1", "ma1"]):
        return "jumper"
    if any(keyword in text for keyword in ["코트", "coat", "트렌치", "trench"]):
        return "coat"
    if any(keyword in text for keyword in ["티셔츠", "t-shirt", "tee", "반팔", "긴팔", "집업티", "폴로"]):
        return "tshirt"

    return "unknown"


def get_effective_bottom_subtype(item: pd.Series) -> str:
    subtype = safe_str(item.get("bottom_subtype", "unknown")).lower()
    if subtype not in INVALID_SUBTYPE_VALUES:
        return subtype
    return infer_bottom_subtype_fallback(item)


def get_effective_top_outer_subtype(item: pd.Series) -> str:
    subtype = safe_str(item.get("top_subtype", "unknown")).lower()
    if subtype not in INVALID_SUBTYPE_VALUES:
        return subtype
    return infer_top_outer_subtype_fallback(item)


def get_effective_pants_length_type(item: pd.Series) -> str:
    length_type = safe_str(item.get("pants_length_type", "unknown")).lower()
    if length_type not in INVALID_SUBTYPE_VALUES:
        return length_type

    bottom_subtype = get_effective_bottom_subtype(item)
    if "shorts" in bottom_subtype or bottom_subtype == "shorts":
        return "shorts"
    if bottom_subtype in {"slacks", "denim", "chino", "cargo", "jogger", "general_pants"}:
        return "long"

    name = safe_str(item.get("product_name", "")).lower()
    if any(k in name for k in ["숏", "쇼츠", "shorts", "반바지"]):
        return "shorts"
    if any(k in name for k in ["팬츠", "슬랙스", "데님", "치노", "trousers", "pants"]):
        return "long"

    return "unknown"


def get_effective_sleeve_length_type(item: pd.Series) -> str:
    sleeve_type = safe_str(item.get("sleeve_length_type", "unknown")).lower()
    if sleeve_type not in INVALID_SUBTYPE_VALUES:
        return sleeve_type

    name = safe_str(item.get("product_name", "")).lower()
    if any(k in name for k in ["반팔", "숏 슬리브", "short sleeve"]):
        return "short_sleeve"
    if any(k in name for k in ["긴팔", "롱 슬리브", "long sleeve"]):
        return "long_sleeve"
    if any(k in name for k in ["민소매", "슬리브리스", "sleeveless"]):
        return "sleeveless"

    return "unknown"


def get_style_axis_scores(item: pd.Series) -> Dict[str, float]:
    return {
        "business": safe_float(item.get("mood_business_casual", 0.0)) + safe_float(item.get("mood_formal", 0.0)),
        "casual": safe_float(item.get("mood_casual", 0.0)),
        "street": safe_float(item.get("mood_street", 0.0)),
        "minimal": safe_float(item.get("mood_minimal", 0.0)),
    }


# =========================
# 역할 궁합 점수
# =========================
def calculate_role_compatibility_score(anchor_item: pd.Series, candidate_item: pd.Series) -> float:
    anchor_role = safe_str(anchor_item.get("item_role", "unknown")).lower()
    candidate_role = safe_str(candidate_item.get("item_role", "unknown")).lower()

    anchor_axes = get_style_axis_scores(anchor_item)
    score = 65.0

    if anchor_role in {"top", "outer"} and candidate_role == "bottom":
        anchor_subtype = get_effective_top_outer_subtype(anchor_item)
        bottom_subtype = get_effective_bottom_subtype(candidate_item)
        pants_length_type = get_effective_pants_length_type(candidate_item)

        business_like = anchor_axes["business"] + anchor_axes["minimal"] * 0.5
        casual_like = anchor_axes["casual"] + anchor_axes["street"]

        if pants_length_type == "shorts":
            if anchor_subtype in {"jacket", "coat", "shirt", "vest", "cardigan", "knit"}:
                score -= 18.0
            elif anchor_subtype in {"half_zip", "hoodie", "sweatshirt"}:
                score -= 12.0
            elif anchor_subtype == "jumper":
                score -= 10.0
            elif anchor_subtype == "windbreaker":
                score -= 4.0
            elif anchor_subtype in {"tshirt", "short_sleeve_tshirt", "long_sleeve_tshirt"}:
                score += 6.0

        if bottom_subtype in {"slacks", "slacks_shorts"}:
            if casual_like >= business_like + 10:
                score -= 18.0
            elif casual_like > business_like:
                score -= 10.0
            else:
                score += 8.0

        if bottom_subtype in {
            "denim", "denim_shorts",
            "cargo", "cargo_shorts",
            "jogger", "jogger_shorts"
        }:
            if casual_like > business_like:
                score += 14.0
            else:
                score -= 4.0

        if bottom_subtype in {"chino", "chino_shorts"}:
            if business_like >= casual_like:
                score += 10.0
            else:
                score += 2.0

        if anchor_subtype == "shirt":
            if bottom_subtype in {"slacks", "chino"}:
                score += 10.0
            if bottom_subtype == "general_pants":
                score += 3.0
            if bottom_subtype == "denim":
                score += 2.0
            if bottom_subtype in {"cargo", "jogger"}:
                score -= 8.0
            if bottom_subtype in {"shorts", "denim_shorts", "cargo_shorts", "chino_shorts", "jogger_shorts"}:
                score -= 12.0

        if anchor_subtype == "knit":
            if bottom_subtype in {"slacks", "chino"}:
                score += 10.0
            if bottom_subtype == "denim":
                score += 14.0
            if bottom_subtype == "general_pants":
                score += 4.0
            if bottom_subtype in {"cargo", "jogger"}:
                score -= 8.0
            if bottom_subtype in {"shorts", "denim_shorts", "cargo_shorts", "chino_shorts", "jogger_shorts"}:
                score -= 10.0

        if anchor_subtype == "cardigan":
            if bottom_subtype in {"slacks", "chino"}:
                score += 10.0
            if bottom_subtype == "denim":
                score += 13.0
            if bottom_subtype == "general_pants":
                score += 4.0
            if bottom_subtype in {"cargo", "jogger"}:
                score -= 8.0
            if bottom_subtype in {"shorts", "denim_shorts", "cargo_shorts", "chino_shorts", "jogger_shorts"}:
                score -= 12.0

        if anchor_subtype == "half_zip":
            if bottom_subtype in {"slacks", "chino"}:
                score += 6.0
            if bottom_subtype == "denim":
                score += 10.0
            if bottom_subtype == "general_pants":
                score += 5.0
            if bottom_subtype in {"cargo", "jogger"}:
                score += 1.0
            if bottom_subtype in {"shorts", "denim_shorts", "cargo_shorts", "chino_shorts", "jogger_shorts"}:
                score -= 8.0

        if anchor_subtype == "sweatshirt":
            if bottom_subtype in {"slacks", "slacks_shorts"}:
                score -= 12.0
            if bottom_subtype == "denim":
                score += 14.0
            if bottom_subtype in {"cargo", "jogger"}:
                score += 8.0
            if bottom_subtype in {"denim_shorts", "cargo_shorts", "jogger_shorts"}:
                score += 4.0
            if bottom_subtype in {"chino", "general_pants"}:
                score += 1.0

        if anchor_subtype == "hoodie":
            if bottom_subtype in {"slacks", "slacks_shorts"}:
                score -= 14.0
            if bottom_subtype == "denim":
                score += 12.0
            if bottom_subtype in {"cargo", "jogger"}:
                score += 12.0
            if bottom_subtype in {"denim_shorts", "cargo_shorts", "jogger_shorts"}:
                score += 6.0
            if bottom_subtype in {"chino", "general_pants"}:
                score += 3.0

        if anchor_subtype in {"tshirt", "short_sleeve_tshirt", "long_sleeve_tshirt"}:
            if bottom_subtype in {"denim", "cargo", "jogger", "shorts", "denim_shorts", "cargo_shorts", "jogger_shorts"}:
                score += 10.0
            if bottom_subtype in {"general_pants"}:
                score += 5.0
            if bottom_subtype in {"slacks"}:
                score -= 2.0
            if bottom_subtype in {"chino"}:
                score += 2.0

        if anchor_subtype == "jumper":
            if casual_like > business_like:
                if bottom_subtype in {"slacks", "slacks_shorts"}:
                    score -= 12.0
                if bottom_subtype in {"denim", "cargo", "general_pants"}:
                    score += 8.0
                if bottom_subtype in {"chino"}:
                    score += 3.0
            else:
                if bottom_subtype in {"slacks", "chino"}:
                    score += 8.0
                if bottom_subtype == "denim":
                    score += 5.0

        if anchor_subtype == "windbreaker":
            if pants_length_type == "shorts":
                score -= 2.0
            if bottom_subtype in {"denim", "cargo", "jogger"}:
                score += 10.0
            if bottom_subtype in {"shorts", "denim_shorts", "cargo_shorts", "jogger_shorts"}:
                score += 2.0
            if bottom_subtype in {"slacks"}:
                score -= 6.0
            if bottom_subtype in {"chino", "general_pants"}:
                score += 2.0

        if anchor_subtype in {"jacket", "coat"}:
            if bottom_subtype in {"slacks", "chino"}:
                score += 10.0
            if bottom_subtype == "general_pants":
                score += 3.0
            if bottom_subtype == "denim":
                score += 1.0
            if bottom_subtype in {"cargo", "jogger"}:
                score -= 10.0
            if bottom_subtype in {"shorts", "denim_shorts", "cargo_shorts", "chino_shorts", "jogger_shorts"}:
                score -= 14.0

        if anchor_subtype == "vest":
            if bottom_subtype in {"slacks", "chino", "general_pants"}:
                score += 12.0
            if bottom_subtype in {"general_pants"}:
                score += 6.0
            if bottom_subtype == "denim":
                score -= 2.0
            if bottom_subtype in {"cargo", "jogger", "denim_shorts", "cargo_shorts", "jogger_shorts", "shorts"}:
                score -= 10.0

    elif anchor_role == "bottom" and candidate_role in {"top", "outer"}:
        bottom_subtype = get_effective_bottom_subtype(anchor_item)
        pants_length_type = get_effective_pants_length_type(anchor_item)
        candidate_subtype = get_effective_top_outer_subtype(candidate_item)

        business_like = anchor_axes["business"] + anchor_axes["minimal"] * 0.5
        casual_like = anchor_axes["casual"] + anchor_axes["street"]

        if bottom_subtype in {"slacks", "slacks_shorts"}:
            if candidate_subtype in {"jacket", "coat", "shirt", "knit", "cardigan"}:
                score += 12.0
            if candidate_subtype in {"hoodie", "sweatshirt"}:
                score -= 10.0

        if bottom_subtype in {"denim", "denim_shorts", "cargo", "cargo_shorts", "jogger", "jogger_shorts"}:
            if candidate_subtype in {"hoodie", "sweatshirt", "jumper", "tshirt", "short_sleeve_tshirt", "long_sleeve_tshirt", "windbreaker"}:
                score += 12.0
            if candidate_subtype in {"jacket", "coat"} and casual_like > business_like:
                score -= 8.0

        if bottom_subtype in {"chino", "chino_shorts"}:
            if candidate_subtype in {"shirt", "knit", "jacket", "cardigan"}:
                score += 10.0

        if candidate_subtype == "vest":
            if bottom_subtype in {"slacks", "chino", "general_pants"}:
                score += 4.0
            elif bottom_subtype in {"denim", "cargo", "jogger", "shorts", "denim_shorts", "cargo_shorts", "jogger_shorts"}:
                score -= 8.0

        is_shorts_anchor = (
            pants_length_type == "shorts"
            or bottom_subtype in {"shorts", "denim_shorts", "cargo_shorts", "chino_shorts", "jogger_shorts"}
        )

        if is_shorts_anchor:
            if candidate_subtype in {"jacket", "coat"}:
                score -= 20.0

            if candidate_subtype in {"shirt", "vest", "cardigan", "knit"}:
                score -= 16.0

            if candidate_subtype in {"windbreaker", "tshirt", "short_sleeve_tshirt", "long_sleeve_tshirt"}:
                score += 10.0

            if candidate_subtype in {"sweatshirt", "hoodie"}:
                score += 5.0

            if candidate_subtype in {"jumper"}:
                score += 2.0

    return max(20.0, min(100.0, score))


# =========================
# 최종 쌍 점수 계산
# =========================
def calculate_pair_score(
    anchor_item: pd.Series,
    candidate_item: pd.Series,
    max_final_score: float,
) -> Dict[str, float]:
    mood_score = calculate_mood_score(anchor_item, candidate_item)
    color_score = calculate_color_score(anchor_item, candidate_item)
    formality_score = calculate_formality_score(anchor_item, candidate_item)
    fit_score = calculate_fit_score(anchor_item, candidate_item)
    brand_score = calculate_brand_score(anchor_item, candidate_item)
    age_score = calculate_age_score(anchor_item, candidate_item)
    popularity_score = calculate_popularity_score(candidate_item, max_final_score)
    role_compatibility_score = calculate_role_compatibility_score(anchor_item, candidate_item)

    total_score = (
        mood_score * 0.24
        + color_score * 0.18
        + formality_score * 0.12
        + fit_score * 0.08
        + brand_score * 0.05
        + age_score * 0.03
        + popularity_score * 0.12
        + role_compatibility_score * 0.18
    )

    return {
        "styling_score": round(total_score, 4),
        "mood_score": round(mood_score, 4),
        "color_score": round(color_score, 4),
        "formality_score": round(formality_score, 4),
        "fit_score": round(fit_score, 4),
        "brand_score": round(brand_score, 4),
        "age_score": round(age_score, 4),
        "popularity_score": round(popularity_score, 4),
        "role_compatibility_score": round(role_compatibility_score, 4),
    }


# =========================
# 후보 정렬
# =========================
def rank_candidates(
    anchor_item: pd.Series,
    candidates_df: pd.DataFrame,
) -> pd.DataFrame:
    if candidates_df.empty:
        return candidates_df.copy()

    max_final_score = candidates_df["final_score"].max()
    scored_rows = []

    for _, row in candidates_df.iterrows():
        score_dict = calculate_pair_score(
            anchor_item=anchor_item,
            candidate_item=row,
            max_final_score=max_final_score,
        )

        row_dict = row.to_dict()
        row_dict.update(score_dict)
        scored_rows.append(row_dict)

    ranked_df = pd.DataFrame(scored_rows)
    ranked_df = ranked_df.sort_values(
        by=["styling_score", "final_score", "available_size_count"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    return ranked_df


# =========================
# 추천 이유 생성
# =========================
def build_reason_text(anchor_item: pd.Series, candidate_item: pd.Series, score_row: pd.Series) -> str:
    reasons = []

    if safe_float(score_row.get("mood_score", 0)) >= 80:
        reasons.append("무드 조화가 좋음")

    if safe_float(score_row.get("color_score", 0)) >= 80:
        reasons.append("색 조합이 안정적임")

    if safe_float(score_row.get("formality_score", 0)) >= 80:
        reasons.append("포멀도 차이가 크지 않음")

    if safe_float(score_row.get("role_compatibility_score", 0)) >= 78:
        reasons.append("아이템 성격상 궁합이 좋음")

    if safe_float(score_row.get("brand_score", 0)) >= 80:
        reasons.append("동일 브랜드 조합으로 통일감이 있음")

    if safe_float(score_row.get("popularity_score", 0)) >= 75:
        reasons.append("기존 추천 점수도 높은 편")

    candidate_subtype = get_effective_top_outer_subtype(candidate_item)
    if candidate_subtype == "vest":
        reasons.append("레이어드 활용도가 높은 베스트 아이템")

    if not reasons:
        reasons.append("전체 밸런스가 무난한 조합")

    return ", ".join(reasons)


# =========================
# 메인 엔진
# =========================
def build_styling_recommendations(
    df: pd.DataFrame,
    anchor_product_code: str,
    top_n: int = 10,
    allowed_brands: Optional[List[str]] = None,
    same_brand_only: bool = False,
    recommendation_mode: str = "all",
) -> pd.DataFrame:
    anchor_item = get_anchor_item(df, anchor_product_code)

    target_roles = resolve_target_roles(
        anchor_role=anchor_item["item_role"],
        recommendation_mode=recommendation_mode,
    )

    if not target_roles:
        return pd.DataFrame()

    candidates = filter_candidates(
        df=df,
        anchor_item=anchor_item,
        target_roles=target_roles,
        allowed_brands=allowed_brands,
        same_brand_only=same_brand_only,
    )

    # 명확한 여름-겨울 충돌은 보정이 아니라 제거
    candidates = apply_strict_season_filter(anchor_item, candidates)

    anchor_bottom_subtype = get_effective_bottom_subtype(anchor_item)
    anchor_pants_length_type = get_effective_pants_length_type(anchor_item)

    is_shorts_anchor = (
        anchor_pants_length_type == "shorts"
        or anchor_bottom_subtype in {"shorts", "denim_shorts", "cargo_shorts", "chino_shorts", "jogger_shorts"}
    )

    if is_shorts_anchor:
        def allow_for_shorts(row: pd.Series) -> bool:
            subtype = get_effective_top_outer_subtype(row)
            sleeve = get_effective_sleeve_length_type(row)
            name = safe_str(row.get("product_name", "")).lower()

            if subtype == "windbreaker":
                return True

            if "후드 집업" in name or "후드집업" in name or "hooded zip-up" in name or "zip-up hoodie" in name:
                return True

            if subtype in {"tshirt", "short_sleeve_tshirt"}:
                return sleeve == "short_sleeve" or "반팔" in name

            if subtype == "shirt":
                return sleeve == "short_sleeve" or "반팔" in name

            if subtype == "knit":
                return sleeve == "short_sleeve" or "반팔" in name

            return False

        candidates = candidates[candidates.apply(allow_for_shorts, axis=1)].reset_index(drop=True)

    ranked = rank_candidates(anchor_item, candidates)

    if ranked.empty:
        return ranked

    ranked = ranked.head(top_n).copy()

    ranked["reason_text"] = ranked.apply(
        lambda row: build_reason_text(anchor_item, row, row),
        axis=1,
    )

    output_cols = [
        "product_code",
        "product_name",
        "brand_name",
        "item_role",
        "category_name",
        "color_group",
        "fit_type",
        "top_subtype",
        "bottom_subtype",
        "sleeve_length_type",
        "pants_length_type",
        "display_mood_tag",
        "final_score",
        "styling_score",
        "mood_score",
        "color_score",
        "formality_score",
        "fit_score",
        "brand_score",
        "age_score",
        "popularity_score",
        "role_compatibility_score",
        "season_name_raw",
        "season_spring",
        "season_summer",
        "season_fall",
        "season_winter",
        "reason_text",
    ]

    output_cols = [col for col in output_cols if col in ranked.columns]
    return ranked[output_cols]


def split_recommendations_by_role(ranked_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    if ranked_df.empty or "item_role" not in ranked_df.columns:
        empty_df = pd.DataFrame(columns=ranked_df.columns if not ranked_df.empty else [])
        return {
            "top": empty_df.copy(),
            "bottom": empty_df.copy(),
            "outer": empty_df.copy(),
        }

    grouped = {}
    for role in ["top", "bottom", "outer"]:
        role_df = ranked_df[ranked_df["item_role"].str.lower() == role].copy()
        role_df = role_df.reset_index(drop=True)
        grouped[role] = role_df

    return grouped


def build_styling_recommendations_by_role(
    df: pd.DataFrame,
    anchor_product_code: str,
    top_n_per_role: int = 10,
    allowed_brands: Optional[List[str]] = None,
    same_brand_only: bool = False,
    recommendation_mode: str = "all",
) -> Dict[str, pd.DataFrame]:
    ranked_df = build_styling_recommendations(
        df=df,
        anchor_product_code=anchor_product_code,
        top_n=300,
        allowed_brands=allowed_brands,
        same_brand_only=same_brand_only,
        recommendation_mode=recommendation_mode,
    )

    grouped = split_recommendations_by_role(ranked_df)

    for role in grouped:
        grouped[role] = (
            grouped[role]
            .drop_duplicates(subset=["product_code"])
            .head(top_n_per_role)
            .reset_index(drop=True)
        )

    return grouped


# =========================
# 세트 추천 유틸
# =========================
def calculate_top_outer_pair_score(
    top_row: pd.Series,
    outer_row: pd.Series,
) -> Dict[str, float]:
    max_final_score = max(
        safe_float(top_row.get("final_score", 0.0)),
        safe_float(outer_row.get("final_score", 0.0)),
        1.0,
    )

    score_dict = calculate_pair_score(
        anchor_item=top_row,
        candidate_item=outer_row,
        max_final_score=max_final_score,
    )

    top_outer_base_score = float(score_dict["styling_score"])
    top_outer_season_score = season_overlap_score(top_row, outer_row)

    adjusted_top_outer_score = round(
        top_outer_base_score * 0.8 + top_outer_season_score * 0.2,
        4,
    )

    return {
        "top_outer_base_score": round(top_outer_base_score, 4),
        "top_outer_season_score": round(top_outer_season_score, 4),
        "top_outer_score": adjusted_top_outer_score,
        "top_outer_season_overlap_count": season_overlap_count(top_row, outer_row),
        "top_outer_season_reason": build_season_reason(top_row, outer_row, label="top-outer"),
    }


# =========================
# bottom anchor 세트
# =========================
def build_two_piece_sets_for_bottom_anchor(
    grouped_result: Dict[str, pd.DataFrame],
    anchor_item: pd.Series,
    top_n_sets: int = 10,
) -> pd.DataFrame:
    top_df = grouped_result.get("top", pd.DataFrame())

    if top_df.empty:
        return pd.DataFrame()

    rows = []

    for _, top_row in top_df.iterrows():
        bt_score = round(float(top_row.get("styling_score", 0.0)), 4)

        rows.append({
            "set_type": "2piece",
            "anchor_product_code": anchor_item.get("product_code", ""),
            "anchor_product_name": anchor_item.get("product_name", ""),
            "anchor_role": anchor_item.get("item_role", ""),
            "bottom_product_code": anchor_item.get("product_code", ""),
            "bottom_product_name": anchor_item.get("product_name", ""),
            "top_product_code": top_row.get("product_code", ""),
            "top_product_name": top_row.get("product_name", ""),
            "outer_product_code": "",
            "outer_product_name": "",
            "bottom_top_score": bt_score,
            "bottom_outer_score": 0.0,
            "top_outer_base_score": 0.0,
            "top_outer_season_score": 0.0,
            "top_outer_score": 0.0,
            "top_outer_season_overlap_count": 0,
            "top_outer_season_reason": "",
            "set_score": bt_score,
            "top_reason_text": top_row.get("reason_text", ""),
            "outer_reason_text": "",
            "set_reason": f"{top_row.get('product_name', '')} 상의와의 2피스 조합",
        })

    set_df = pd.DataFrame(rows)
    set_df = set_df.sort_values(
        by=["set_score", "bottom_top_score"],
        ascending=[False, False],
    ).reset_index(drop=True)

    return set_df.head(top_n_sets)


def build_three_piece_sets_for_bottom_anchor(
    grouped_result: Dict[str, pd.DataFrame],
    anchor_item: pd.Series,
    top_n_sets: int = 10,
) -> pd.DataFrame:
    top_df = grouped_result.get("top", pd.DataFrame())
    outer_df = grouped_result.get("outer", pd.DataFrame())

    if top_df.empty or outer_df.empty:
        return pd.DataFrame()

    rows = []

    for _, top_row in top_df.iterrows():
        for _, outer_row in outer_df.iterrows():
            if safe_str(top_row.get("product_code")) == safe_str(outer_row.get("product_code")):
                continue

            if should_block_by_season_conflict(top_row, outer_row):
                continue

            bt_score = round(float(top_row.get("styling_score", 0.0)), 4)
            bo_score = round(float(outer_row.get("styling_score", 0.0)), 4)

            to_score_dict = calculate_top_outer_pair_score(top_row, outer_row)
            to_base_score = to_score_dict["top_outer_base_score"]
            to_season_score = to_score_dict["top_outer_season_score"]
            to_score = to_score_dict["top_outer_score"]
            to_overlap_count = to_score_dict["top_outer_season_overlap_count"]
            to_season_reason = to_score_dict["top_outer_season_reason"]

            set_score = round((bt_score + bo_score + to_score) / 3, 4)

            rows.append({
                "set_type": "3piece",
                "anchor_product_code": anchor_item.get("product_code", ""),
                "anchor_product_name": anchor_item.get("product_name", ""),
                "anchor_role": anchor_item.get("item_role", ""),
                "bottom_product_code": anchor_item.get("product_code", ""),
                "bottom_product_name": anchor_item.get("product_name", ""),
                "top_product_code": top_row.get("product_code", ""),
                "top_product_name": top_row.get("product_name", ""),
                "outer_product_code": outer_row.get("product_code", ""),
                "outer_product_name": outer_row.get("product_name", ""),
                "bottom_top_score": bt_score,
                "bottom_outer_score": bo_score,
                "top_outer_base_score": to_base_score,
                "top_outer_season_score": to_season_score,
                "top_outer_score": to_score,
                "top_outer_season_overlap_count": to_overlap_count,
                "top_outer_season_reason": to_season_reason,
                "set_score": set_score,
                "top_reason_text": top_row.get("reason_text", ""),
                "outer_reason_text": outer_row.get("reason_text", ""),
                "set_reason": (
                    f"{top_row.get('product_name', '')} + "
                    f"{outer_row.get('product_name', '')} 3피스 조합 / "
                    f"{to_season_reason}"
                ),
            })

    if not rows:
        return pd.DataFrame()

    set_df = pd.DataFrame(rows)
    set_df = set_df.sort_values(
        by=["set_score", "bottom_top_score", "bottom_outer_score", "top_outer_score"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)

    return set_df.head(top_n_sets)


# =========================
# top anchor 세트
# =========================
def build_two_piece_sets_for_top_anchor(
    grouped_result: Dict[str, pd.DataFrame],
    anchor_item: pd.Series,
    top_n_sets: int = 10,
) -> pd.DataFrame:
    bottom_df = grouped_result.get("bottom", pd.DataFrame())

    if bottom_df.empty:
        return pd.DataFrame()

    rows = []

    for _, bottom_row in bottom_df.iterrows():
        tb_score = round(float(bottom_row.get("styling_score", 0.0)), 4)

        rows.append({
            "set_type": "2piece",
            "anchor_product_code": anchor_item.get("product_code", ""),
            "anchor_product_name": anchor_item.get("product_name", ""),
            "anchor_role": anchor_item.get("item_role", ""),
            "bottom_product_code": bottom_row.get("product_code", ""),
            "bottom_product_name": bottom_row.get("product_name", ""),
            "top_product_code": anchor_item.get("product_code", ""),
            "top_product_name": anchor_item.get("product_name", ""),
            "outer_product_code": "",
            "outer_product_name": "",
            "bottom_top_score": tb_score,
            "bottom_outer_score": 0.0,
            "top_outer_base_score": 0.0,
            "top_outer_season_score": 0.0,
            "top_outer_score": 0.0,
            "top_outer_season_overlap_count": 0,
            "top_outer_season_reason": "",
            "set_score": tb_score,
            "top_reason_text": "",
            "outer_reason_text": "",
            "set_reason": f"{bottom_row.get('product_name', '')} 하의와의 2피스 조합",
        })

    set_df = pd.DataFrame(rows)
    set_df = set_df.sort_values(
        by=["set_score", "bottom_top_score"],
        ascending=[False, False],
    ).reset_index(drop=True)

    return set_df.head(top_n_sets)


def build_three_piece_sets_for_top_anchor(
    grouped_result: Dict[str, pd.DataFrame],
    anchor_item: pd.Series,
    top_n_sets: int = 10,
) -> pd.DataFrame:
    bottom_df = grouped_result.get("bottom", pd.DataFrame())
    outer_df = grouped_result.get("outer", pd.DataFrame())

    if bottom_df.empty or outer_df.empty:
        return pd.DataFrame()

    rows = []

    for _, bottom_row in bottom_df.iterrows():
        for _, outer_row in outer_df.iterrows():
            if safe_str(bottom_row.get("product_code")) == safe_str(outer_row.get("product_code")):
                continue

            if should_block_by_season_conflict(anchor_item, outer_row):
                continue

            bt_score = round(float(bottom_row.get("styling_score", 0.0)), 4)

            to_score_dict = calculate_top_outer_pair_score(anchor_item, outer_row)
            to_base_score = to_score_dict["top_outer_base_score"]
            to_season_score = to_score_dict["top_outer_season_score"]
            to_score = to_score_dict["top_outer_score"]
            to_overlap_count = to_score_dict["top_outer_season_overlap_count"]
            to_season_reason = to_score_dict["top_outer_season_reason"]

            max_final_score = max(
                safe_float(bottom_row.get("final_score", 0.0)),
                safe_float(outer_row.get("final_score", 0.0)),
                1.0,
            )
            bo_score_dict = calculate_pair_score(bottom_row, outer_row, max_final_score)
            bo_score = round(float(bo_score_dict["styling_score"]), 4)

            set_score = round((bt_score + bo_score + to_score) / 3, 4)

            rows.append({
                "set_type": "3piece",
                "anchor_product_code": anchor_item.get("product_code", ""),
                "anchor_product_name": anchor_item.get("product_name", ""),
                "anchor_role": anchor_item.get("item_role", ""),
                "bottom_product_code": bottom_row.get("product_code", ""),
                "bottom_product_name": bottom_row.get("product_name", ""),
                "top_product_code": anchor_item.get("product_code", ""),
                "top_product_name": anchor_item.get("product_name", ""),
                "outer_product_code": outer_row.get("product_code", ""),
                "outer_product_name": outer_row.get("product_name", ""),
                "bottom_top_score": bt_score,
                "bottom_outer_score": bo_score,
                "top_outer_base_score": to_base_score,
                "top_outer_season_score": to_season_score,
                "top_outer_score": to_score,
                "top_outer_season_overlap_count": to_overlap_count,
                "top_outer_season_reason": to_season_reason,
                "set_score": set_score,
                "top_reason_text": "",
                "outer_reason_text": outer_row.get("reason_text", ""),
                "set_reason": (
                    f"{bottom_row.get('product_name', '')} + "
                    f"{outer_row.get('product_name', '')} 3피스 조합 / "
                    f"{to_season_reason}"
                ),
            })

    if not rows:
        return pd.DataFrame()

    set_df = pd.DataFrame(rows)
    set_df = set_df.sort_values(
        by=["set_score", "bottom_top_score", "bottom_outer_score", "top_outer_score"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)

    return set_df.head(top_n_sets)


# =========================
# outer anchor 세트
# =========================
def build_two_piece_sets_for_outer_anchor(
    grouped_result: Dict[str, pd.DataFrame],
    anchor_item: pd.Series,
    top_n_sets: int = 10,
) -> pd.DataFrame:
    top_df = grouped_result.get("top", pd.DataFrame())

    if top_df.empty:
        return pd.DataFrame()

    rows = []

    for _, top_row in top_df.iterrows():
        if should_block_by_season_conflict(top_row, anchor_item):
            continue

        ot_score_dict = calculate_top_outer_pair_score(top_row, anchor_item)
        ot_score = round(float(ot_score_dict["top_outer_score"]), 4)

        rows.append({
            "set_type": "2piece",
            "anchor_product_code": anchor_item.get("product_code", ""),
            "anchor_product_name": anchor_item.get("product_name", ""),
            "anchor_role": anchor_item.get("item_role", ""),
            "bottom_product_code": "",
            "bottom_product_name": "",
            "top_product_code": top_row.get("product_code", ""),
            "top_product_name": top_row.get("product_name", ""),
            "outer_product_code": anchor_item.get("product_code", ""),
            "outer_product_name": anchor_item.get("product_name", ""),
            "bottom_top_score": 0.0,
            "bottom_outer_score": 0.0,
            "top_outer_base_score": ot_score_dict["top_outer_base_score"],
            "top_outer_season_score": ot_score_dict["top_outer_season_score"],
            "top_outer_score": ot_score,
            "top_outer_season_overlap_count": ot_score_dict["top_outer_season_overlap_count"],
            "top_outer_season_reason": ot_score_dict["top_outer_season_reason"],
            "set_score": ot_score,
            "top_reason_text": top_row.get("reason_text", ""),
            "outer_reason_text": "",
            "set_reason": f"{top_row.get('product_name', '')} 상의와의 2피스 조합",
        })

    if not rows:
        return pd.DataFrame()

    set_df = pd.DataFrame(rows)
    set_df = set_df.sort_values(
        by=["set_score", "top_outer_score"],
        ascending=[False, False],
    ).reset_index(drop=True)

    return set_df.head(top_n_sets)


def build_three_piece_sets_for_outer_anchor(
    grouped_result: Dict[str, pd.DataFrame],
    anchor_item: pd.Series,
    top_n_sets: int = 10,
) -> pd.DataFrame:
    top_df = grouped_result.get("top", pd.DataFrame())
    bottom_df = grouped_result.get("bottom", pd.DataFrame())

    if top_df.empty or bottom_df.empty:
        return pd.DataFrame()

    rows = []

    for _, top_row in top_df.iterrows():
        for _, bottom_row in bottom_df.iterrows():
            if safe_str(top_row.get("product_code")) == safe_str(bottom_row.get("product_code")):
                continue

            if should_block_by_season_conflict(top_row, anchor_item):
                continue

            bt_score = round(float(bottom_row.get("styling_score", 0.0)), 4)

            max_final_score = max(
                safe_float(bottom_row.get("final_score", 0.0)),
                safe_float(anchor_item.get("final_score", 0.0)),
                1.0,
            )
            bo_score_dict = calculate_pair_score(bottom_row, anchor_item, max_final_score)
            bo_score = round(float(bo_score_dict["styling_score"]), 4)

            to_score_dict = calculate_top_outer_pair_score(top_row, anchor_item)
            to_base_score = to_score_dict["top_outer_base_score"]
            to_season_score = to_score_dict["top_outer_season_score"]
            to_score = to_score_dict["top_outer_score"]
            to_overlap_count = to_score_dict["top_outer_season_overlap_count"]
            to_season_reason = to_score_dict["top_outer_season_reason"]

            set_score = round((bt_score + bo_score + to_score) / 3, 4)

            rows.append({
                "set_type": "3piece",
                "anchor_product_code": anchor_item.get("product_code", ""),
                "anchor_product_name": anchor_item.get("product_name", ""),
                "anchor_role": anchor_item.get("item_role", ""),
                "bottom_product_code": bottom_row.get("product_code", ""),
                "bottom_product_name": bottom_row.get("product_name", ""),
                "top_product_code": top_row.get("product_code", ""),
                "top_product_name": top_row.get("product_name", ""),
                "outer_product_code": anchor_item.get("product_code", ""),
                "outer_product_name": anchor_item.get("product_name", ""),
                "bottom_top_score": bt_score,
                "bottom_outer_score": bo_score,
                "top_outer_base_score": to_base_score,
                "top_outer_season_score": to_season_score,
                "top_outer_score": to_score,
                "top_outer_season_overlap_count": to_overlap_count,
                "top_outer_season_reason": to_season_reason,
                "set_score": set_score,
                "top_reason_text": top_row.get("reason_text", ""),
                "outer_reason_text": "",
                "set_reason": (
                    f"{top_row.get('product_name', '')} + "
                    f"{bottom_row.get('product_name', '')} 3피스 조합 / "
                    f"{to_season_reason}"
                ),
            })

    if not rows:
        return pd.DataFrame()

    set_df = pd.DataFrame(rows)
    set_df = set_df.sort_values(
        by=["set_score", "bottom_top_score", "bottom_outer_score", "top_outer_score"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)

    return set_df.head(top_n_sets)


# =========================
# 공통 세트 엔진
# =========================
def build_styling_sets(
    df: pd.DataFrame,
    anchor_product_code: str,
    top_n_per_role: int = 5,
    top_n_sets: int = 10,
    allowed_brands: Optional[List[str]] = None,
    same_brand_only: bool = False,
) -> Dict[str, pd.DataFrame]:
    anchor_item = get_anchor_item(df, anchor_product_code)
    anchor_role = safe_str(anchor_item.get("item_role", "")).lower()

    grouped_result = build_styling_recommendations_by_role(
        df=df,
        anchor_product_code=anchor_product_code,
        top_n_per_role=top_n_per_role,
        allowed_brands=allowed_brands,
        same_brand_only=same_brand_only,
        recommendation_mode="all",
    )

    empty_df = pd.DataFrame()

    if anchor_role == "bottom":
        two_piece_sets = build_two_piece_sets_for_bottom_anchor(
            grouped_result=grouped_result,
            anchor_item=anchor_item,
            top_n_sets=top_n_sets,
        )
        three_piece_sets = build_three_piece_sets_for_bottom_anchor(
            grouped_result=grouped_result,
            anchor_item=anchor_item,
            top_n_sets=top_n_sets,
        )
    elif anchor_role == "top":
        two_piece_sets = build_two_piece_sets_for_top_anchor(
            grouped_result=grouped_result,
            anchor_item=anchor_item,
            top_n_sets=top_n_sets,
        )
        three_piece_sets = build_three_piece_sets_for_top_anchor(
            grouped_result=grouped_result,
            anchor_item=anchor_item,
            top_n_sets=top_n_sets,
        )
    elif anchor_role == "outer":
        two_piece_sets = build_two_piece_sets_for_outer_anchor(
            grouped_result=grouped_result,
            anchor_item=anchor_item,
            top_n_sets=top_n_sets,
        )
        three_piece_sets = build_three_piece_sets_for_outer_anchor(
            grouped_result=grouped_result,
            anchor_item=anchor_item,
            top_n_sets=top_n_sets,
        )
    else:
        two_piece_sets = empty_df.copy()
        three_piece_sets = empty_df.copy()

    return {
        "top_candidates": grouped_result.get("top", empty_df.copy()),
        "bottom_candidates": grouped_result.get("bottom", empty_df.copy()),
        "outer_candidates": grouped_result.get("outer", empty_df.copy()),
        "two_piece_sets": two_piece_sets,
        "three_piece_sets": three_piece_sets,
    }


# =========================
# 실행 예시
# =========================
if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    CSV_PATH = os.path.join(DATA_DIR, "master_table_step4_styling.csv")

    df = load_master_table(CSV_PATH)

    test_product_code = "JNTS5B201WT"   # top
    # test_product_code = "IEPA5E408BK"  # bottom
    # test_product_code = "TNJU6E107BK"  # outer

    try:
        result = build_styling_sets(
            df=df,
            anchor_product_code=test_product_code,
            top_n_per_role=5,
            top_n_sets=10,
            same_brand_only=False,
        )

        print("\n===== TOP 후보 =====")
        if result["top_candidates"].empty:
            print("추천 결과 없음")
        else:
            print(
                result["top_candidates"][
                    ["product_code", "product_name", "brand_name", "styling_score", "reason_text"]
                ].to_string(index=False)
            )

        print("\n===== BOTTOM 후보 =====")
        if result["bottom_candidates"].empty:
            print("추천 결과 없음")
        else:
            print(
                result["bottom_candidates"][
                    ["product_code", "product_name", "brand_name", "styling_score", "reason_text"]
                ].to_string(index=False)
            )

        print("\n===== OUTER 후보 =====")
        if result["outer_candidates"].empty:
            print("추천 결과 없음")
        else:
            print(
                result["outer_candidates"][
                    ["product_code", "product_name", "brand_name", "styling_score", "reason_text"]
                ].to_string(index=False)
            )

        print("\n===== 2피스 세트 추천 =====")
        if result["two_piece_sets"].empty:
            print("추천 결과 없음")
        else:
            print(
                result["two_piece_sets"][
                    [
                        "bottom_product_code",
                        "bottom_product_name",
                        "top_product_code",
                        "top_product_name",
                        "outer_product_code",
                        "outer_product_name",
                        "bottom_top_score",
                        "top_outer_score",
                        "set_score",
                        "set_reason",
                    ]
                ].to_string(index=False)
            )

        print("\n===== 3피스 세트 추천 =====")
        if result["three_piece_sets"].empty:
            print("추천 결과 없음")
        else:
            print(
                result["three_piece_sets"][
                    [
                        "bottom_product_code",
                        "bottom_product_name",
                        "top_product_code",
                        "top_product_name",
                        "outer_product_code",
                        "outer_product_name",
                        "bottom_top_score",
                        "bottom_outer_score",
                        "top_outer_base_score",
                        "top_outer_season_score",
                        "top_outer_score",
                        "top_outer_season_overlap_count",
                        "top_outer_season_reason",
                        "set_score",
                        "set_reason",
                    ]
                ].to_string(index=False)
            )

    except Exception as e:
        print(f"[ERROR] {e}")