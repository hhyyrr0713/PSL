import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

FILE_LIST = [
    "allegri_products_enriched_all.csv",
    "daks_men_products_enriched_all.csv",
    "hazzys_men_products_enriched_all.csv",
    "ilcorso_products_enriched_all.csv",
    "jillstuartnewyork_men_products_enriched_all.csv",
    "tngt_men_products_enriched_all.csv",
]

SAVE_PATH = os.path.join(DATA_DIR, "master_table_step_season.csv")


def normalize_season_name(text) -> str:
    if pd.isna(text):
        return ""

    text = str(text).strip()
    if not text:
        return ""

    text = text.replace("/", ",")
    text = text.replace("·", ",")
    text = text.replace("|", ",")
    text = " ".join(text.split())

    return text


def recompute_season_flags(df: pd.DataFrame) -> pd.DataFrame:
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

    # 후처리용 임시 규칙
    first_half = text_series.str.contains("상반기", na=False)
    second_half = text_series.str.contains("하반기", na=False)

    df["season_all"] = season_all.astype(int)
    df["season_spring"] = (spring | first_half | season_all).astype(int)
    df["season_summer"] = (summer | first_half | season_all).astype(int)
    df["season_fall"] = (fall | second_half | season_all).astype(int)
    df["season_winter"] = (winter | second_half | season_all).astype(int)

    return df


def main():
    dfs = []

    required_columns = [
        "product_code",
        "product_name",
        "brand_name",
        "brand_id",
        "brand_group_id",
        "product_sale_type",
        "season",
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
        "display_category_id",
        "soldout",
    ]

    for file_name in FILE_LIST:
        file_path = os.path.join(DATA_DIR, file_name)

        print(f"\n불러오는 중: {file_name}")
        df = pd.read_csv(file_path, dtype={"product_code": "string", "brand_id": "string"})

        df["product_code"] = df["product_code"].astype(str).str.strip()

        for col in required_columns:
            if col not in df.columns:
                df[col] = pd.NA

        df = df[required_columns]

        print(f"row 수: {len(df)}")
        dfs.append(df)

    master_df = pd.concat(dfs, ignore_index=True)

    print("\nconcat 완료")
    print("concat row 수:", len(master_df))

    before_dedup = len(master_df)
    master_df = master_df.drop_duplicates(subset=["product_code"], keep="first")
    after_dedup = len(master_df)

    print("중복 제거 전:", before_dedup)
    print("중복 제거 후:", after_dedup)
    print("중복 제거 수:", before_dedup - after_dedup)

    master_df = recompute_season_flags(master_df)

    print("\nseason_name_raw 분포 상위 30개")
    print(master_df["season_name_raw"].fillna("(null)").value_counts(dropna=False).head(30))

    print("\n시즌 플래그 합계")
    print(
        master_df[
            [
                "season_spring",
                "season_summer",
                "season_fall",
                "season_winter",
                "season_all",
            ]
        ].sum()
    )

    print("\n카테고리 샘플")
    print(
        master_df[
            ["product_code", "product_name", "brand_name", "lf_category_l1", "lf_category_l2", "lf_category_l3"]
        ].head(10)
    )

    master_df.to_csv(SAVE_PATH, index=False, encoding="utf-8-sig")
    print(f"\n저장 완료: {SAVE_PATH}")


if __name__ == "__main__":
    main()