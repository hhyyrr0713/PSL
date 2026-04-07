import os
import requests
import pandas as pd
import time
import re

from common_category import get_category_info


COMMON_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://www.lfmall.co.kr",
    "Referer": "https://www.lfmall.co.kr/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
    "DEVICE-TYPE": "2",
    "BUILD-VERSION": "20260316@8810db5",
    "X-REQUEST-TOKEN": "XSAsKCElkx/GpomuOnAd4APUj1qB3SZJUJj8x0osYEA=",
    "X-XSRF-TOKEN": "1db9b2f5-acd0-48fb-af72-710613a7a249",
}

COMMON_COOKIES = {
    "XSRF-TOKEN": "1db9b2f5-acd0-48fb-af72-710613a7a249",
    "JSESSIONID": "6d4c2847-126a-4d26-aadf-f4b79a4f98ef",
}

LIST_URL = "https://nxapi.lfmall.co.kr/exhibition/search/v1/brandGroup/1001"
BANNER_BRAND_CODE = "DM"
LIST_BRAND_ID = "DM"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
SAVE_PATH = os.path.join(DATA_DIR, "daks_men_products_enriched_all.csv")


def normalize_season_name(text) -> str:
    if text is None:
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


def parse_season_flags(season_name_raw: str) -> dict:
    text = normalize_season_name(season_name_raw)

    lowered = text.lower()
    season_all = int(
        ("사계절" in text)
        or ("4계절" in text)
        or ("올시즌" in text)
        or ("all season" in lowered)
        or (lowered == "all")
    )

    season_spring = int(("봄" in text) or season_all == 1)
    season_summer = int(("여름" in text) or season_all == 1)
    season_fall = int(("가을" in text) or season_all == 1)
    season_winter = int(("겨울" in text) or season_all == 1)

    return {
        "season_name_raw": text,
        "season_spring": season_spring,
        "season_summer": season_summer,
        "season_fall": season_fall,
        "season_winter": season_winter,
        "season_all": season_all,
    }


def deep_find_key(obj, target_key):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == target_key:
                return v
            found = deep_find_key(v, target_key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = deep_find_key(item, target_key)
            if found is not None:
                return found
    return None


def get_season_name(product_code: str) -> str:
    url = f"https://nxapi.lfmall.co.kr/product/v1/descriptions/{product_code}"

    params = {
        "targetPlatForm": "PC"
    }

    response = requests.get(
        url,
        headers=COMMON_HEADERS,
        cookies=COMMON_COOKIES,
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    candidate_paths = [
        ["body", "seasonName"],
        ["body", "product", "seasonName"],
        ["body", "description", "seasonName"],
        ["body", "productDescription", "seasonName"],
    ]

    for path in candidate_paths:
        cur = data
        ok = True
        for key in path:
            if isinstance(cur, dict) and key in cur:
                cur = cur[key]
            else:
                ok = False
                break

        if ok and cur not in (None, "", []):
            return normalize_season_name(cur)

    season_name = deep_find_key(data, "seasonName")
    return normalize_season_name(season_name)


def get_banner_info(product_code: str, product_sale_type: int | None) -> tuple[int, int]:
    url = f"https://nxapi.lfmall.co.kr/product/detail/v1/banner/{product_code}"

    if product_sale_type is None:
        product_sale_type = 1

    params = {
        "brandCode": BANNER_BRAND_CODE,
        "productSaleType": product_sale_type,
        "targetPlatform": "PC",
    }

    response = requests.get(
        url,
        headers=COMMON_HEADERS,
        cookies=COMMON_COOKIES,
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    purchase_count = 0
    viewing_count = 0

    banner_list = data.get("body", {}).get("productDetailBandBannerDTOList") or []

    for banner in banner_list:
        text = banner.get("bannerText", "") or ""
        nums = re.findall(r"\d+", text)

        if not nums:
            continue

        value = int(nums[0])

        if "구매" in text:
            purchase_count = value
        elif "보고있어요" in text or "보고 있어요" in text:
            viewing_count = value

    return purchase_count, viewing_count


def get_wish_count(product_code: str) -> int:
    url = f"https://nxapi.lfmall.co.kr/product/detail/v1/product-wish/{product_code}/count"

    response = requests.get(
        url,
        headers=COMMON_HEADERS,
        cookies=COMMON_COOKIES,
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    wish_info = data.get("body", {}).get("productWishInformation", {}) or {}
    wish_count = wish_info.get("productWishCount", 0)

    if wish_count is None:
        wish_count = 0

    return wish_count


def get_size_stock_info(product_code: str) -> tuple[int, str]:
    url = f"https://nxapi.lfmall.co.kr/product/detail/v1/options/{product_code}"

    params = {"stockCheckYn": "N"}

    response = requests.get(
        url,
        headers=COMMON_HEADERS,
        cookies=COMMON_COOKIES,
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    option_data = data.get("body", {}).get("productOptionDTO", {}) or {}
    size_list = option_data.get("productOptionSizeDTOList", []) or []

    size_total_stock = 0
    size_stock_items = []

    for item in size_list:
        size_value = item.get("sizeValue")
        stock_qty = item.get("currentStockQuantity", 0)

        if stock_qty is None:
            stock_qty = 0

        size_total_stock += stock_qty

        if size_value is not None:
            size_stock_items.append(f"{size_value}:{stock_qty}")

    size_stock_detail = ", ".join(size_stock_items)

    return size_total_stock, size_stock_detail


def get_color_stock_info(product_code: str) -> tuple[int, str]:
    url = f"https://nxapi.lfmall.co.kr/product/detail/v1/color-chips/{product_code}"

    response = requests.get(
        url,
        headers=COMMON_HEADERS,
        cookies=COMMON_COOKIES,
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    color_list = data.get("body", {}).get("colorChipDTOList", []) or []

    color_total_stock = 0
    color_stock_items = []

    for item in color_list:
        color_name = item.get("colorName")
        stock_qty = item.get("currentStockQuantity", 0)

        if stock_qty is None:
            stock_qty = 0

        color_total_stock += stock_qty

        if color_name is not None:
            color_stock_items.append(f"{color_name}:{stock_qty}")

    color_stock_detail = ", ".join(color_stock_items)

    return color_total_stock, color_stock_detail


def get_list_page(page: int) -> dict:
    payload = {
        "brandGroupPageWithFixedTid": False,
        "defaultSearchYn": "N",
        "sendLogYN": "N",
        "page": page,
        "size": 20,
        "saleType": [1, 2],
        "brandId": [LIST_BRAND_ID],
        "order": "popular",
        "aggs": [
            "saleType",
            "colors",
            "season",
            "styleYear",
            "brandGroup",
            "gender",
            "searchCategory",
            "price",
            "prop1",
            "prop2",
            "size1",
            "size2",
            "benefit",
            "review",
            "atcrIsseYn",
            "eventMasters",
            "categories",
        ],
    }

    response = requests.post(
        LIST_URL,
        headers=COMMON_HEADERS,
        cookies=COMMON_COOKIES,
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    session = requests.Session()
    session.headers.update(COMMON_HEADERS)
    session.cookies.update(COMMON_COOKIES)

    print("첫 페이지 요청 중...")
    first_data = get_list_page(1)

    total_count = first_data["body"]["results"]["total"]
    total_page = first_data["body"]["results"]["totalPage"]

    print("총 상품 수:", total_count)
    print("총 페이지 수:", total_page)

    all_rows = []

    for page in range(1, total_page + 1):
        print(f"\n===== {page}/{total_page} 페이지 시작 =====")

        try:
            data = get_list_page(page)
        except Exception as e:
            print(f"{page}페이지 리스트 요청 실패:", e)
            continue

        products = data["body"]["results"]["products"]
        print(f"{page}페이지 상품 수: {len(products)}")

        for idx, p in enumerate(products, start=1):
            product_code = p.get("id")
            product_name = p.get("name")
            product_sale_type = p.get("productSaleType")

            print(f"[{page}페이지 {idx}/{len(products)}] {product_code} | {product_name}")

            try:
                season_name_raw = get_season_name(product_code)
                season_flags = parse_season_flags(season_name_raw)
            except Exception as e:
                print("seasonName 에러:", product_code, e)
                season_flags = {
                    "season_name_raw": "",
                    "season_spring": 0,
                    "season_summer": 0,
                    "season_fall": 0,
                    "season_winter": 0,
                    "season_all": 0,
                }

            try:
                purchase_count, viewing_count = get_banner_info(product_code, product_sale_type)
            except Exception as e:
                print("banner 에러:", product_code, e)
                purchase_count, viewing_count = 0, 0

            try:
                wish_count = get_wish_count(product_code)
            except Exception as e:
                print("wish 에러:", product_code, e)
                wish_count = 0

            try:
                size_total_stock, size_stock_detail = get_size_stock_info(product_code)
            except Exception as e:
                print("size stock 에러:", product_code, e)
                size_total_stock, size_stock_detail = 0, ""

            try:
                color_total_stock, color_stock_detail = get_color_stock_info(product_code)
            except Exception as e:
                print("color stock 에러:", product_code, e)
                color_total_stock, color_stock_detail = 0, ""

            try:
                category_info = get_category_info(
                    product_code=product_code,
                    session=session,
                    headers=COMMON_HEADERS,
                    timeout=15,
                    sleep_sec=0.0,
                )
            except Exception as e:
                print("category 에러:", product_code, e)
                category_info = {
                    "lf_category_l1": "",
                    "lf_category_l2": "",
                    "lf_category_l3": "",
                }

            row = {
                "product_code": product_code,
                "product_name": product_name,
                "brand_name": p.get("brandName"),
                "brand_id": p.get("brandId"),
                "brand_group_id": p.get("brandGroupId"),
                "product_sale_type": p.get("productSaleType"),
                "season": p.get("season"),
                "season_name_raw": season_flags["season_name_raw"],
                "season_spring": season_flags["season_spring"],
                "season_summer": season_flags["season_summer"],
                "season_fall": season_flags["season_fall"],
                "season_winter": season_flags["season_winter"],
                "season_all": season_flags["season_all"],
                "original_price": p.get("originalPrice"),
                "sale_price": p.get("salePrice"),
                "discount_rate": p.get("discountRate"),
                "sale_count": p.get("saleCount"),
                "cart_count": p.get("cartCount"),
                "review_count": p.get("reviewCount"),
                "review_score": p.get("reviewScore"),
                "purchase_count": purchase_count,
                "viewing_count": viewing_count,
                "wish_count": wish_count,
                "size_total_stock": size_total_stock,
                "size_stock_detail": size_stock_detail,
                "color_total_stock": color_total_stock,
                "color_stock_detail": color_stock_detail,
                "lf_category_l1": category_info["lf_category_l1"],
                "lf_category_l2": category_info["lf_category_l2"],
                "lf_category_l3": category_info["lf_category_l3"],
            }

            all_rows.append(row)
            time.sleep(0.05)

        time.sleep(0.1)

    df = pd.DataFrame(all_rows)

    column_order = [
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
    ]

    df = df[column_order]

    print("\n===== 수집 완료 =====")
    print(df.head())
    print("최종 수집 상품 수:", len(df))

    print("\n===== season_name_raw 분포 확인 =====")
    print(df["season_name_raw"].fillna("(null)").value_counts(dropna=False).head(20))

    print("\n===== 시즌 플래그 합계 =====")
    print(
        df[[
            "season_spring",
            "season_summer",
            "season_fall",
            "season_winter",
            "season_all"
        ]].sum()
    )

    print("\n===== category 샘플 확인 =====")
    print(df[["product_code", "product_name", "lf_category_l1", "lf_category_l2", "lf_category_l3"]].head(10))

    df.to_csv(SAVE_PATH, index=False, encoding="utf-8-sig")
    print(f"CSV 저장 완료: {SAVE_PATH}")


if __name__ == "__main__":
    main()