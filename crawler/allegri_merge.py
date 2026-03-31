import requests
import pandas as pd
import time

COMMON_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://www.lfmall.co.kr",
    "Referer": "https://www.lfmall.co.kr/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
    "DEVICE-TYPE": "2",
    "BUILD-VERSION": "20260316@8810db5",
    "X-REQUEST-TOKEN": "i8b0/FkpFTQbzQj0x/x4PkbFA1T9p0uVDAIfXjuIxYk=",
    "X-XSRF-TOKEN": "1db9b2f5-acd0-48fb-af72-710613a7a249",
}

COMMON_COOKIES = {
    "XSRF-TOKEN": "1db9b2f5-acd0-48fb-af72-710613a7a249",
    "JSESSIONID": "fc1c8108-adec-4a31-a9ca-2d1c042c3176",
}

LIST_URL = "https://nxapi.lfmall.co.kr/exhibition/search/v1/brandGroup/1897"

CSV_PATH = "../data/allegri_products_enriched_all.csv"
SAVE_PATH = "../data/allegri_products_enriched_all_fixed.csv"


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


def collect_product_sale_type() -> pd.DataFrame:
    print("첫 페이지 요청 중...")
    first_data = get_list_page(1)

    total_count = first_data["body"]["results"]["total"]
    total_page = first_data["body"]["results"]["totalPage"]

    print("총 상품 수:", total_count)
    print("총 페이지 수:", total_page)

    all_rows = []

    for page in range(1, total_page + 1):
        print(f"{page}/{total_page} 페이지 수집 중...")

        try:
            data = get_list_page(page)
        except Exception as e:
            print(f"{page}페이지 요청 실패:", e)
            continue

        products = data["body"]["results"]["products"]

        for p in products:
            product_code = str(p.get("id")).strip()
            product_sale_type = p.get("productSaleType")

            all_rows.append({
                "product_code": product_code,
                "product_sale_type": product_sale_type,
            })

        time.sleep(0.2)

    sale_type_df = pd.DataFrame(all_rows)
    sale_type_df["product_code"] = sale_type_df["product_code"].astype(str).str.strip()
    sale_type_df = sale_type_df.drop_duplicates(subset=["product_code"])

    print("\nsale_type 수집 완료")
    print(sale_type_df.head())
    print("sale_type row 수:", len(sale_type_df))
    print("sale_type 빈값 개수:", sale_type_df["product_sale_type"].isna().sum())
    print("sale_type 값 분포:")
    print(sale_type_df["product_sale_type"].value_counts(dropna=False).sort_index())

    return sale_type_df


def main():
    print("기존 CSV 불러오는 중...")
    origin_df = pd.read_csv(CSV_PATH)

    origin_df["product_code"] = origin_df["product_code"].astype(str).str.strip()

    print("기존 CSV row 수:", len(origin_df))
    print(origin_df[["product_code"]].head())

    sale_type_df = collect_product_sale_type()

    # 기존 컬럼 제거
    origin_df = origin_df.drop(columns=["product_sale_type"], errors="ignore")

    # merge
    merged_df = origin_df.merge(
        sale_type_df,
        on="product_code",
        how="left"
    )

    print("\nmerge 완료")
    print(merged_df[["product_code", "product_sale_type"]].head())
    print("최종 row 수:", len(merged_df))
    print("product_sale_type 빈값 개수:", merged_df["product_sale_type"].isna().sum())
    print("product_sale_type 값 분포:")
    print(merged_df["product_sale_type"].value_counts(dropna=False).sort_index())

    merged_df.to_csv(SAVE_PATH, index=False, encoding="utf-8-sig")
    print(f"저장 완료: {SAVE_PATH}")


if __name__ == "__main__":
    main()