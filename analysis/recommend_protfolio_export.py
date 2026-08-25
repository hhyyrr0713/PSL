import pandas as pd
import ast
from pathlib import Path

# =========================
# 1. 경로 설정
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "portfolio_results"

OUTPUT_DIR.mkdir(exist_ok=True)

file_path = DATA_DIR / "master_table_step3_scored.csv"

print("READ FILE:", file_path)
print("OUTPUT DIR:", OUTPUT_DIR)

# =========================
# 2. csv 읽기
# =========================
df = pd.read_csv(file_path)

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
# 3. available_size_list 복원
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
# 4. 공통 정리 함수
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
# 5. 카테고리 다양성 보정 함수
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

    if not category_names or len(category_names) <= 1:
        return rec_df.head(top_n).copy()

    selected_categories = [c for c in category_names if c in rec_df["category_name"].unique()]
    if len(selected_categories) <= 1:
        return rec_df.head(top_n).copy()

    quota = int(diversity_pool / len(selected_categories))
    quota = max(1, quota)

    selected_parts = []
    selected_codes = set()

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

    remain_n = top_n - len(priority_df)

    if remain_n > 0:
        remain_df = rec_df[~rec_df["product_code"].isin(selected_codes)].copy()
        remain_top = remain_df.head(remain_n).copy()
        final_df = pd.concat([priority_df, remain_top], ignore_index=False)
    else:
        final_df = priority_df.copy()

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
# 6. size_type별 사이즈 필터 함수
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

        if size_type == "top":
            if selected_top_sizes:
                return any(size in size_list for size in selected_top_sizes)
            return True

        if size_type == "bottom":
            if selected_bottom_sizes:
                return any(size in size_list for size in selected_bottom_sizes)
            return True

        return True

    return rec_df[rec_df.apply(row_matches, axis=1)].copy()

# =========================
# 7. 추천 함수
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

    rec_df = rec_df[rec_df["has_stock"] == 1]

    if brand_names:
        rec_df = rec_df[rec_df["brand_name"].isin(brand_names)]

    if category_names:
        rec_df = rec_df[rec_df["category_name"].isin(category_names)]

    if color_groups:
        rec_df = rec_df[rec_df["color_group"].isin(color_groups)]

    if price_ranges:
        rec_df = rec_df[rec_df["price_range"].isin(price_ranges)]

    rec_df = apply_size_filter(
        rec_df=rec_df,
        selected_top_sizes=selected_top_sizes,
        selected_bottom_sizes=selected_bottom_sizes,
    )

    rec_df = rec_df.sort_values(
        ["final_score", "review_score", "purchase_count"],
        ascending=[False, False, False]
    ).copy()

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
# 8. 포트폴리오 시나리오 정의
# =========================
portfolio_cases = [
    {
        "case_name": "case1_pants_jacket_mixed_portfolio",
        "brand_names": ["티엔지티", "알레그리", "질스튜어트뉴욕 맨"],
        "category_names": ["팬츠", "자켓"],
        "color_groups": ["블랙", "네이비"],
        "price_ranges": ["10만원 이하", "10만~50만원"],
        "selected_top_sizes": ["100", "105"],
        "selected_bottom_sizes": ["32", "34"],
        "top_n": 30,
        "use_category_diversity": True,
        "diversity_pool": 20,
    },
    {
        "case_name": "case2_top_only_multi_categories_portfolio",
        "brand_names": ["헤지스 남성", "닥스 남성"],
        "category_names": ["티셔츠", "셔츠"],
        "color_groups": ["화이트/아이보리", "블루"],
        "price_ranges": ["10만원 이하", "10만~50만원"],
        "selected_top_sizes": ["95", "100"],
        "selected_bottom_sizes": None,
        "top_n": 30,
        "use_category_diversity": True,
        "diversity_pool": 20,
    },
    {
        "case_name": "case3_bottom_only_single_category_portfolio",
        "brand_names": ["티엔지티", "헤지스 남성"],
        "category_names": ["팬츠"],
        "color_groups": ["블랙", "네이비", "그레이/차콜"],
        "price_ranges": ["10만원 이하", "10만~50만원"],
        "selected_top_sizes": None,
        "selected_bottom_sizes": ["30", "32", "34"],
        "top_n": 30,
        "use_category_diversity": True,
        "diversity_pool": 20,
    },
    {
        "case_name": "case4_outer_multi_categories_portfolio",
        "brand_names": None,
        "category_names": ["자켓", "점퍼", "코트"],
        "color_groups": ["블랙", "네이비", "그레이/차콜"],
        "price_ranges": ["10만~50만원", "50만~100만원"],
        "selected_top_sizes": ["100", "105"],
        "selected_bottom_sizes": None,
        "top_n": 30,
        "use_category_diversity": True,
        "diversity_pool": 20,
    },
    {
        "case_name": "case5_shirt_pants_jacket_mixed_portfolio",
        "brand_names": None,
        "category_names": ["팬츠", "자켓", "셔츠"],
        "color_groups": ["블랙", "네이비", "화이트/아이보리"],
        "price_ranges": ["10만원 이하", "10만~50만원"],
        "selected_top_sizes": ["100", "105"],
        "selected_bottom_sizes": ["32", "34"],
        "top_n": 30,
        "use_category_diversity": True,
        "diversity_pool": 20,
    },
]

# =========================
# 9. 실행 및 저장
# =========================
for case in portfolio_cases:
    rec_df = recommend_products(
        df=df,
        brand_names=case["brand_names"],
        category_names=case["category_names"],
        color_groups=case["color_groups"],
        price_ranges=case["price_ranges"],
        selected_top_sizes=case["selected_top_sizes"],
        selected_bottom_sizes=case["selected_bottom_sizes"],
        top_n=case["top_n"],
        use_category_diversity=case["use_category_diversity"],
        diversity_pool=case["diversity_pool"],
    ).copy()

    if rec_df.empty:
        print(f"\n[{case['case_name']}] 조건에 맞는 상품이 없습니다.")
        continue

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

    rec_df = rec_df[output_cols].reset_index(drop=True)

    save_path = OUTPUT_DIR / f"{case['case_name']}.csv"
    rec_df.to_csv(save_path, index=False, encoding="utf-8-sig")

    print(f"\n[{case['case_name']}] 저장 완료")
    print(save_path)