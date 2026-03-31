import pandas as pd
import ast
from pathlib import Path

# =========================
# 1. 출력 옵션
# =========================
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 220)
pd.set_option("display.max_colwidth", 80)

# =========================
# 2. 경로 설정
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

file_path = DATA_DIR / "master_table_step3_scored.csv"

print("BASE_DIR:", BASE_DIR)
print("DATA_DIR:", DATA_DIR)
print("READ FILE:", file_path)

# =========================
# 3. csv 읽기
# =========================
df = pd.read_csv(file_path)

print("\n===== loaded df shape =====")
print(df.shape)

# 문자열 공백 정리
string_cols = [
    "brand_name",
    "category_name",
    "color_group",
    "price_range",
    "available_size_text",
    "size_type",
]

for col in string_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

# =========================
# 4. available_size_list 복원
# =========================
def parse_size_list(x):
    if pd.isna(x):
        return []

    x = str(x).strip()

    if x == "":
        return []

    if x.startswith("[") and x.endswith("]"):
        try:
            parsed = ast.literal_eval(x)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed]
        except:
            pass

    return [v.strip() for v in x.split(",") if v.strip()]

df["available_size_list"] = df["available_size_list"].apply(parse_size_list)

# =========================
# 5. 공통 정리 함수
# =========================
def normalize_list_input(values):
    if values is None:
        return None

    if isinstance(values, str):
        values = [values]

    cleaned = []
    for v in values:
        if pd.isna(v):
            continue
        v = str(v).strip()
        if v != "":
            cleaned.append(v)

    return cleaned if cleaned else None

# =========================
# 6. 카테고리 다양성 보정 함수
# =========================
def apply_category_diversity(
    rec_df: pd.DataFrame,
    category_names,
    top_n: int = 30,
    diversity_pool: int = 20,
) -> pd.DataFrame:
    if rec_df.empty:
        return rec_df

    category_names = normalize_list_input(category_names)

    # 카테고리 선택이 없거나 1개면 기존 점수순 유지
    if not category_names or len(category_names) <= 1:
        return rec_df.head(top_n).copy()

    selected_categories = [c for c in category_names if c in rec_df["category_name"].unique()]
    if len(selected_categories) <= 1:
        return rec_df.head(top_n).copy()

    quota = int(diversity_pool / len(selected_categories))
    quota = max(1, quota)

    selected_parts = []
    selected_codes = set()

    # 카테고리별 quota 우선 확보
    for category in selected_categories:
        cat_df = rec_df[rec_df["category_name"] == category].copy()
        cat_top = cat_df.head(quota).copy()

        if not cat_top.empty:
            selected_parts.append(cat_top)
            selected_codes.update(cat_top["product_code"].tolist())

    if selected_parts:
        priority_df = pd.concat(selected_parts, ignore_index=False)
    else:
        priority_df = pd.DataFrame(columns=rec_df.columns)

    # 남은 자리는 전체 점수순으로 채우기
    remain_n = top_n - len(priority_df)

    if remain_n > 0:
        remain_df = rec_df[~rec_df["product_code"].isin(selected_codes)].copy()
        remain_top = remain_df.head(remain_n).copy()
        final_df = pd.concat([priority_df, remain_top], ignore_index=False)
    else:
        final_df = priority_df.copy()

    # 최종 중복 제거 + 점수순 재정렬
    final_df = (
        final_df
        .drop_duplicates(subset=["product_code"], keep="first")
        .sort_values(
            ["final_score", "review_score", "purchase_count"],
            ascending=[False, False, False]
        )
        .head(top_n)
        .copy()
    )

    return final_df

# =========================
# 7. size_type별 사이즈 필터 함수
# =========================
def apply_size_filter(
    rec_df: pd.DataFrame,
    selected_top_sizes=None,
    selected_bottom_sizes=None,
) -> pd.DataFrame:
    selected_top_sizes = normalize_list_input(selected_top_sizes)
    selected_bottom_sizes = normalize_list_input(selected_bottom_sizes)

    if rec_df.empty:
        return rec_df

    def row_matches(row):
        size_type = row.get("size_type", "")
        size_list = row.get("available_size_list", [])

        if not isinstance(size_list, list):
            return False

        # 상의/아우터류
        if size_type == "top":
            if selected_top_sizes:
                return any(size in size_list for size in selected_top_sizes)
            return True

        # 하의류
        if size_type == "bottom":
            if selected_bottom_sizes:
                return any(size in size_list for size in selected_bottom_sizes)
            return True

        # 기타/free 카테고리
        return True

    return rec_df[rec_df.apply(row_matches, axis=1)].copy()

# =========================
# 8. 추천 함수
# =========================
def recommend_products(
    df: pd.DataFrame,
    brand_names=None,
    category_names=None,
    color_groups=None,
    price_ranges=None,
    selected_top_sizes=None,
    selected_bottom_sizes=None,
    top_n: int = 30,
    use_category_diversity: bool = True,
    diversity_pool: int = 20,
) -> pd.DataFrame:
    rec_df = df.copy()

    brand_names = normalize_list_input(brand_names)
    category_names = normalize_list_input(category_names)
    color_groups = normalize_list_input(color_groups)
    price_ranges = normalize_list_input(price_ranges)
    selected_top_sizes = normalize_list_input(selected_top_sizes)
    selected_bottom_sizes = normalize_list_input(selected_bottom_sizes)

    # 기본 필터
    rec_df = rec_df[rec_df["has_stock"] == 1]

    if brand_names:
        rec_df = rec_df[rec_df["brand_name"].isin(brand_names)]

    if category_names:
        rec_df = rec_df[rec_df["category_name"].isin(category_names)]

    if color_groups:
        rec_df = rec_df[rec_df["color_group"].isin(color_groups)]

    if price_ranges:
        rec_df = rec_df[rec_df["price_range"].isin(price_ranges)]

    # 상의/하의 분리 사이즈 필터
    rec_df = apply_size_filter(
        rec_df=rec_df,
        selected_top_sizes=selected_top_sizes,
        selected_bottom_sizes=selected_bottom_sizes,
    )

    # 점수순 정렬
    rec_df = rec_df.sort_values(
        ["final_score", "review_score", "purchase_count"],
        ascending=[False, False, False]
    ).copy()

    # 카테고리 다양성 보정
    if use_category_diversity:
        rec_df = apply_category_diversity(
            rec_df=rec_df,
            category_names=category_names,
            top_n=top_n,
            diversity_pool=diversity_pool,
        )
    else:
        rec_df = rec_df.head(top_n).copy()

    return rec_df

# =========================
# 9. 결과 출력 함수
# =========================
def print_recommendation_result(title: str, rec_df: pd.DataFrame) -> None:
    print(f"\n===== {title} =====")

    if rec_df.empty:
        print("조건에 맞는 상품이 없습니다.")
        return

    output_cols = [
        "product_code",
        "product_name",
        "brand_name",
        "category_name",
        "size_type",
        "color_group",
        "price_range",
        "sale_price",
        "available_size_text",
        "final_score",
    ]

    display_df = rec_df[output_cols].reset_index(drop=True)
    print(display_df.to_string(index=False))

    print("\n===== category distribution =====")
    print(display_df["category_name"].value_counts())

    print("\n===== size_type distribution =====")
    print(display_df["size_type"].value_counts())

# =========================
# 10. 사용자 입력 영역
# 이 부분만 바꿔서 사용
# =========================
USER_BRANDS = ["티엔지티", "알레그리", "질스튜어트뉴욕 맨"]
USER_CATEGORIES = ["팬츠", "자켓"]
USER_COLORS = ["블랙", "네이비"]
USER_PRICES = ["10만원 이하", "10만~50만원"]

# 상의 / 하의 사이즈 분리
USER_TOP_SIZES = ["100", "105"]
USER_BOTTOM_SIZES = ["32", "34"]

TOP_N = 30
USE_CATEGORY_DIVERSITY = True
DIVERSITY_POOL = 20

# =========================
# 11. 추천 실행
# =========================
rec_result = recommend_products(
    df=df,
    brand_names=USER_BRANDS,
    category_names=USER_CATEGORIES,
    color_groups=USER_COLORS,
    price_ranges=USER_PRICES,
    selected_top_sizes=USER_TOP_SIZES,
    selected_bottom_sizes=USER_BOTTOM_SIZES,
    top_n=TOP_N,
    use_category_diversity=USE_CATEGORY_DIVERSITY,
    diversity_pool=DIVERSITY_POOL,
)

print_recommendation_result("recommendation result", rec_result)