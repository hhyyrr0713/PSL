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

    # "[95, 100, 105]" 같은 문자열
    if x.startswith("[") and x.endswith("]"):
        try:
            parsed = ast.literal_eval(x)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed]
        except:
            pass

    # "95,100,105" 같은 문자열
    return [v.strip() for v in x.split(",") if v.strip()]

df["available_size_list"] = df["available_size_list"].apply(parse_size_list)

print("\n===== available_size_list sample 10 =====")
print(
    df[["product_code", "product_name", "available_size_list", "available_size_text"]]
    .head(10)
    .to_string(index=False)
)

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
# 6. 복수 선택형 추천 함수
# =========================
def recommend_products(
    df: pd.DataFrame,
    brand_names=None,
    category_names=None,
    color_groups=None,
    price_ranges=None,
    selected_sizes=None,
    top_n: int = 10,
) -> pd.DataFrame:
    rec_df = df.copy()

    # 전부 리스트 형태로 정리
    brand_names = normalize_list_input(brand_names)
    category_names = normalize_list_input(category_names)
    color_groups = normalize_list_input(color_groups)
    price_ranges = normalize_list_input(price_ranges)
    selected_sizes = normalize_list_input(selected_sizes)

    # 재고 있는 상품만
    rec_df = rec_df[rec_df["has_stock"] == 1]

    # 브랜드 복수 선택
    if brand_names:
        rec_df = rec_df[rec_df["brand_name"].isin(brand_names)]

    # 카테고리 복수 선택
    if category_names:
        rec_df = rec_df[rec_df["category_name"].isin(category_names)]

    # 색상 복수 선택
    if color_groups:
        rec_df = rec_df[rec_df["color_group"].isin(color_groups)]

    # 가격대 복수 선택
    if price_ranges:
        rec_df = rec_df[rec_df["price_range"].isin(price_ranges)]

    # 사이즈 복수 선택
    if selected_sizes:
        rec_df = rec_df[
            rec_df["available_size_list"].apply(
                lambda size_list: any(size in size_list for size in selected_sizes)
                if isinstance(size_list, list) else False
            )
        ]

    # 점수순 정렬
    rec_df = rec_df.sort_values(
        ["final_score", "review_score", "purchase_count"],
        ascending=[False, False, False]
    )

    return rec_df.head(top_n)

# =========================
# 7. 결과 출력 함수
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
        "color_group",
        "price_range",
        "sale_price",
        "available_size_text",
        "final_score",
    ]

    display_df = rec_df[output_cols].reset_index(drop=True)
    print(display_df.to_string(index=False))

# =========================
# 8. 복수 선택 테스트 1
# =========================
rec_1 = recommend_products(
    df=df,
    brand_names=["티엔지티", "알레그리", "질스튜어트뉴욕 맨"],
    category_names=["팬츠", "자켓"],
    color_groups=["블랙", "네이비"],
    price_ranges=["10만원 이하", "10만~50만원"],
    selected_sizes=["100", "105"],
    top_n=10,
)

print_recommendation_result("multi recommendation test 1", rec_1)

# =========================
# 9. 복수 선택 테스트 2
# =========================
rec_2 = recommend_products(
    df=df,
    brand_names=["헤지스 남성", "닥스 남성"],
    category_names=["티셔츠", "스웨터/맨투맨"],
    color_groups=["그레이/차콜", "네이비", "블랙"],
    price_ranges=["10만~50만원"],
    selected_sizes=["95", "100"],
    top_n=10,
)

print_recommendation_result("multi recommendation test 2", rec_2)

# =========================
# 10. 복수 선택 테스트 3
# =========================
rec_3 = recommend_products(
    df=df,
    brand_names=None,  # 전체 브랜드 허용
    category_names=["셔츠", "티셔츠"],
    color_groups=["블루", "화이트/아이보리"],
    price_ranges=["10만원 이하", "10만~50만원"],
    selected_sizes=["95", "100", "105"],
    top_n=10,
)

print_recommendation_result("multi recommendation test 3", rec_3)