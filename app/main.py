import os
import sys
import math

import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
STYLING_DIR = os.path.join(BASE_DIR, "styling")
CSV_PATH = os.path.join(DATA_DIR, "master_table_step4_styling.csv")

sys.path.append(STYLING_DIR)

from styling_engine import build_styling_sets, get_anchor_item, load_master_table


app = FastAPI(title="LF Styling Recommendation API")

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

df = load_master_table(CSV_PATH)


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
    price_df = get_price_map()

    role_map = {
        "top": "top_product_code",
        "bottom": "bottom_product_code",
        "outer": "outer_product_code",
    }

    for role, code_col in role_map.items():
        if code_col not in result_df.columns:
            continue

        temp_price_df = price_df.rename(
            columns={
                "product_code": code_col,
                "sale_price": f"{role}_sale_price",
                "original_price": f"{role}_original_price",
                "discount_rate": f"{role}_discount_rate",
                "price_range": f"{role}_price_range",
            }
        )

        result_df = result_df.merge(temp_price_df, on=code_col, how="left")

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

    output_cols = [
        "product_code",
        "product_name",
        "brand_name",
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


@app.get("/recommend/{product_code}")
def recommend(
    product_code: str,
    brand: str = "",
    category: str = "",
    price_range: str = "",
    same_brand_only: bool = False,
):
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

        anchor_cols = [
            "product_code",
            "product_name",
            "brand_name",
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