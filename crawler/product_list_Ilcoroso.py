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
    "X-REQUEST-TOKEN": "srJLwOLQ7Ttuq9AX0cb5xmntmPnUZ63UlXV3c4Zx9nM=",
    "X-XSRF-TOKEN": "1db9b2f5-acd0-48fb-af72-710613a7a249",
}

COMMON_COOKIES = {
    "XSRF-TOKEN": "1db9b2f5-acd0-48fb-af72-710613a7a249",
    "JSESSIONID": "4bb3b6f9-cdcd-46e2-9736-f364d510ad06",
}

LIST_URL = "https://nxapi.lfmall.co.kr/exhibition/search/v1/brandGroup/2751"
SAVE_PATH = "../data/ilcorso_products_enriched_all.csv"


def get_banner_info(product_code: str) -> tuple[int, int]:
    url = f"https://nxapi.lfmall.co.kr/product/detail/v1/banner/{product_code}"

    params = {
        "brandCode": "IE",
        "productSaleType": 1,
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

    wish_info = data.get("body", {}).get("productWishInformation", {})
    wish_count = wish_info.get("productWishCount", 0)

    if wish_count is None:
        wish_count = 0

    return wish_count


def get_size_stock_info(product_code: str) -> tuple[int, str]:
    url = f"https://nxapi.lfmall.co.kr/product/detail/v1/options/{product_code}"

    params = {
        "stockCheckYn": "N"
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

    option_data = data.get("body", {}).get("productOptionDTO", {})
    size_list = option_data.get("productOptionSizeDTOList", [])

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

    color_list = data.get("body", {}).get("colorChipDTOList", [])

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

            print(f"[{page}페이지 {idx}/{len(products)}] {product_code} | {product_name}")

            try:
                purchase_count, viewing_count = get_banner_info(product_code)
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

            row = {
                "product_code": product_code,
                "product_name": product_name,
                "brand_name": p.get("brandName"),
                "brand_id": p.get("brandId"),
                "brand_group_id": p.get("brandGroupId"),
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
    ]

    df = df[column_order]

    print("\n===== 수집 완료 =====")
    print(df.head())
    print("최종 수집 상품 수:", len(df))

    df.to_csv(SAVE_PATH, index=False, encoding="utf-8-sig")
    print(f"CSV 저장 완료: {SAVE_PATH}")


if __name__ == "__main__":
    main()