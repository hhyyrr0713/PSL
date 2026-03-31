import requests
import pandas as pd
import time
import re

COMMON_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://www.lfmall.co.kr",
    "Referer": "https://www.lfmall.co.kr/",
    "User-Agent": "Mozilla/5.0",
    "DEVICE-TYPE": "2",
    "BUILD-VERSION": "20260316@8810db5",
}

COMMON_COOKIES = {}

LIST_URL = "https://nxapi.lfmall.co.kr/exhibition/search/v1/brandGroup/1004"
SAVE_PATH = "../data/tngt_men_products_enriched_all.csv"


# ---------------- banner ----------------
def get_banner_info(product_code: str) -> tuple[int, int]:
    url = f"https://nxapi.lfmall.co.kr/product/detail/v1/banner/{product_code}"

    params = {
        "brandCode": "B000",
        "productSaleType": 1,
        "targetPlatform": "PC",
    }

    response = requests.get(url, headers=COMMON_HEADERS, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    purchase_count = 0
    viewing_count = 0

    banner_list = data.get("body", {}).get("productDetailBandBannerDTOList", [])

    for banner in banner_list:
        text = banner.get("bannerText", "")
        nums = re.findall(r"\d+", text)

        if not nums:
            continue

        value = int(nums[0])

        if "구매" in text:
            purchase_count = value
        elif "보고있어요" in text or "보고 있어요" in text:
            viewing_count = value

    return purchase_count, viewing_count


# ---------------- wish ----------------
def get_wish_count(product_code: str) -> int:
    url = f"https://nxapi.lfmall.co.kr/product/detail/v1/product-wish/{product_code}/count"

    response = requests.get(url, headers=COMMON_HEADERS, timeout=10)
    response.raise_for_status()
    data = response.json()

    wish_info = data.get("body", {}).get("productWishInformation", {})
    wish_count = wish_info.get("productWishCount", 0)

    if wish_count is None:
        wish_count = 0

    return wish_count


# ---------------- size ----------------
def get_size_stock_info(product_code: str) -> tuple[int, str]:
    url = f"https://nxapi.lfmall.co.kr/product/detail/v1/options/{product_code}"

    params = {"stockCheckYn": "N"}

    response = requests.get(url, headers=COMMON_HEADERS, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    option_data = data.get("body", {}).get("productOptionDTO", {})
    size_list = option_data.get("productOptionSizeDTOList", [])

    size_total_stock = 0
    size_stock_items = []

    for item in size_list:
        size_value = item.get("sizeValue")
        stock_qty = item.get("currentStockQuantity", 0) or 0

        size_total_stock += stock_qty

        if size_value is not None:
            size_stock_items.append(f"{size_value}:{stock_qty}")

    return size_total_stock, ", ".join(size_stock_items)


# ---------------- color ----------------
def get_color_stock_info(product_code: str) -> tuple[int, str]:
    url = f"https://nxapi.lfmall.co.kr/product/detail/v1/color-chips/{product_code}"

    response = requests.get(url, headers=COMMON_HEADERS, timeout=10)
    response.raise_for_status()
    data = response.json()

    color_list = data.get("body", {}).get("colorChipDTOList", [])

    color_total_stock = 0
    color_stock_items = []

    for item in color_list:
        color_name = item.get("colorName")
        stock_qty = item.get("currentStockQuantity", 0) or 0

        color_total_stock += stock_qty

        if color_name is not None:
            color_stock_items.append(f"{color_name}:{stock_qty}")

    return color_total_stock, ", ".join(color_stock_items)


# ---------------- list ----------------
def get_list_page(page: int) -> dict:
    payload = {
        "brandGroupPageWithFixedTid": False,
        "defaultSearchYn": "N",
        "sendLogYN": "N",
        "page": page,
        "size": 20,
        "saleType": [1, 2],
        "tid": ["110219"],
        "categoryIds": ["110219"],
        "order": "popular",
        "aggs": [
            "saleType", "colors", "season", "styleYear", "brandGroup",
            "gender", "searchCategory", "price", "prop1", "prop2",
            "size1", "size2", "benefit", "review",
            "atcrIsseYn", "eventMasters", "categories"
        ],
    }

    response = requests.post(LIST_URL, headers=COMMON_HEADERS, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


# ---------------- main ----------------
def main():
    first_data = get_list_page(1)

    total_page = first_data["body"]["results"]["totalPage"]
    all_rows = []

    for page in range(1, total_page + 1):
        print(f"{page}/{total_page}")

        data = get_list_page(page)
        products = data["body"]["results"]["products"]

        for p in products:
            product_code = p.get("id")

            try:
                purchase_count, viewing_count = get_banner_info(product_code)
            except:
                purchase_count, viewing_count = 0, 0

            try:
                wish_count = get_wish_count(product_code)
            except:
                wish_count = 0

            try:
                size_total_stock, size_stock_detail = get_size_stock_info(product_code)
            except:
                size_total_stock, size_stock_detail = 0, ""

            try:
                color_total_stock, color_stock_detail = get_color_stock_info(product_code)
            except:
                color_total_stock, color_stock_detail = 0, ""

            row = {
                "product_code": p.get("id"),
                "product_name": p.get("name"),
                "brand_name": p.get("brandName"),
                "brand_id": p.get("brandId"),
                "brand_group_id": p.get("brandGroupId"),

                # ⭐ 핵심 위치 (질스튜어트랑 동일)
                "product_sale_type": p.get("productSaleType"),
                "season": p.get("season"),

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
            }

            all_rows.append(row)
            time.sleep(0.05)

    df = pd.DataFrame(all_rows)

    df = df[[
        "product_code", "product_name", "brand_name",
        "brand_id", "brand_group_id",
        "product_sale_type", "season",
        "original_price", "sale_price", "discount_rate",
        "sale_count", "cart_count",
        "review_count", "review_score",
        "purchase_count", "viewing_count", "wish_count",
        "size_total_stock", "size_stock_detail",
        "color_total_stock", "color_stock_detail"
    ]]

    df.to_csv(SAVE_PATH, index=False, encoding="utf-8-sig")
    print("완료")


if __name__ == "__main__":
    main()