from pathlib import Path
import random

import pandas as pd


# 1. Kaggle 원본 데이터 위치
# 현재 네 구조 기준:
# PSL/archive/styles.csv
# PSL/archive/images/
DATASET_PATH = Path("archive")
STYLES_PATH = DATASET_PATH / "styles.csv"
IMAGES_PATH = DATASET_PATH / "images"

# 2. 변환 결과 저장 위치
OUTPUT_PATH = Path("data/psl_products_kaggle.csv")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)


def map_item_role(row):
    """
    Kaggle의 subCategory / articleType을 PSL의 역할(top, bottom, outer)로 변환
    """
    sub_category = str(row.get("subCategory", "")).lower()
    article_type = str(row.get("articleType", "")).lower()

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


def make_brand(product_id):
    """
    Kaggle 데이터에는 실제 브랜드 컬럼이 부족하므로
    PSL 테스트용 가상 브랜드 생성
    """
    brands = [
        "MONO STUDIO",
        "URBAN LINE",
        "CLASSIC WORKS",
        "SOFT STANDARD",
        "MODERN ARCHIVE",
        "DAILY FORM",
    ]

    return brands[int(product_id) % len(brands)]


def make_price(row):
    """
    Kaggle 데이터에는 가격 컬럼이 없으므로
    카테고리/역할 기준으로 테스트용 가격 생성
    """
    article_type = str(row.get("articleType", "")).lower()
    role = row.get("item_role", "")

    if role == "outer":
        return random.randint(120000, 320000)

    if role == "bottom":
        return random.randint(59000, 180000)

    if "shirts" in article_type:
        return random.randint(49000, 160000)

    if "tshirts" in article_type:
        return random.randint(29000, 90000)

    return random.randint(39000, 200000)


def make_price_range(price):
    if price <= 100000:
        return "10만원 이하"

    if price <= 500000:
        return "10만~50만원"

    if price <= 1000000:
        return "50만~100만원"

    return "100만원 이상"


def map_mood(row):
    """
    usage / color / articleType 기반으로 PSL용 mood 생성
    """
    usage = str(row.get("usage", "")).lower()
    color = str(row.get("baseColour", "")).lower()
    article_type = str(row.get("articleType", "")).lower()

    if "formal" in usage:
        return "formal"

    if "sports" in usage:
        return "sporty"

    if color in ["black", "white", "grey", "navy blue", "blue"]:
        return "minimal"

    if "shirt" in article_type or "trouser" in article_type:
        return "classic"

    return "casual"


def map_fit(row):
    """
    Kaggle 데이터에는 fit 정보가 없으므로
    상품명/카테고리 기반으로 테스트용 fit 생성
    """
    name = str(row.get("productDisplayName", "")).lower()
    article_type = str(row.get("articleType", "")).lower()

    if "slim" in name:
        return "슬림핏"

    if "regular" in name:
        return "레귤러핏"

    if "loose" in name or "oversized" in name:
        return "오버핏"

    if "jeans" in article_type or "trousers" in article_type:
        return "스트레이트핏"

    return "레귤러핏"


def normalize_season(value):
    value = str(value)

    if value in ["Spring", "Summer", "Fall", "Winter"]:
        return value

    return "All Season"


def main():
    print("Kaggle styles.csv 읽는 중...")

    df = pd.read_csv(STYLES_PATH, on_bad_lines="skip")

    print("원본 행 수:", len(df))

    # 남성/공용 의류만 사용
    df = df[
        (df["gender"].isin(["Men", "Unisex"]))
        & (df["masterCategory"] == "Apparel")
    ].copy()

    print("남성/공용 의류 필터링 후:", len(df))

    # 이미지 파일 존재 여부 확인
    df["local_image_path"] = df["id"].apply(lambda x: str(IMAGES_PATH / f"{x}.jpg"))
    df = df[df["local_image_path"].apply(lambda p: Path(p).exists())].copy()

    print("이미지 파일 존재 상품 수:", len(df))

    # 기본 컬럼 변환
    df["product_code"] = df["id"].astype(str)
    df["product_name"] = df["productDisplayName"].fillna("")
    df["brand_name"] = df["id"].apply(make_brand)
    df["category_name"] = df["articleType"].fillna("")
    df["item_role"] = df.apply(map_item_role, axis=1)
    df["color_group"] = df["baseColour"].fillna("")
    df["season_profile_label"] = df["season"].apply(normalize_season)
    df["occasion_label"] = df["usage"].fillna("Casual")
    df["mood_label"] = df.apply(map_mood, axis=1)
    df["fit_label"] = df.apply(map_fit, axis=1)

    # 가격 생성
    df["sale_price"] = df.apply(make_price, axis=1)
    df["price_range"] = df["sale_price"].apply(make_price_range)

    # 브라우저에서 접근 가능한 이미지 경로
    # 이 경로가 작동하려면 이미지 파일이 app/static/kaggle_images/ 안에 있어야 함
    df["image_url"] = df["id"].apply(lambda x: f"/static/kaggle_images/{x}.jpg")
    df["image_url_00"] = df["image_url"]
    df["image_url_01"] = ""
    df["image_url_02"] = ""

    # 추천에 필요한 top/bottom/outer만 사용
    df = df[df["item_role"].isin(["top", "bottom", "outer"])].copy()

    print("top/bottom/outer 필터링 후:", len(df))
    print(df["item_role"].value_counts())

    columns = [
        "product_code",
        "product_name",
        "brand_name",
        "sale_price",
        "price_range",
        "category_name",
        "item_role",
        "color_group",
        "season_profile_label",
        "mood_label",
        "fit_label",
        "occasion_label",
        "image_url",
        "image_url_00",
        "image_url_01",
        "image_url_02",
    ]

    df = df[columns].copy()

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("변환 완료")
    print("저장 위치:", OUTPUT_PATH)
    print("최종 상품 수:", len(df))
    print(df.head())


if __name__ == "__main__":
    main()