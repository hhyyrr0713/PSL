import time
import requests
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

INPUT_PATH = DATA_DIR / "master_table_step4_styling.csv"
OUTPUT_IMAGE_PATH = DATA_DIR / "product_image_urls.csv"
OUTPUT_MASTER_PATH = DATA_DIR / "master_table_step5_image.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Origin": "https://www.lfmall.co.kr",
    "Referer": "https://www.lfmall.co.kr/",
}


def find_image_by_suffix(image_list, product_code, suffix):
    """
    suffix 예시: "00", "01", "02"
    URL 안에 상품코드_00, 상품코드_01, 상품코드_02가 들어간 이미지를 찾는다.
    """
    target = f"{product_code}_{suffix}"

    for img in image_list:
        image_url = img.get("imageUrl", "")
        if target in image_url:
            return image_url

    return ""


def get_product_image_urls(product_code):
    url = f"https://nxapi.lfmall.co.kr/product/v1/contents/{product_code}"

    result = {
        "image_url": "",
        "image_url_00": "",
        "image_url_01": "",
        "image_url_02": "",
    }

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)

        if res.status_code != 200:
            print(f"[실패] {product_code} status={res.status_code}")
            return result

        data = res.json()

        image_list = (
            data.get("body", {})
            .get("productContentsDTO", {})
            .get("productImageDTOList", [])
        )

        if not image_list:
            print(f"[이미지 없음] {product_code}")
            return result

        # DETAIL은 상세 설명 이미지라 제외하고, 카드에서 보여줄 MAIN + SUB 이미지만 사용
        display_images = [
            img for img in image_list
            if img.get("imageType") in {"MAIN", "SUB"} and img.get("imageUrl")
        ]

        # 혹시 MAIN/SUB가 비어 있으면 전체 이미지에서 찾기
        target_images = display_images if display_images else image_list

        image_url_00 = find_image_by_suffix(target_images, product_code, "00")
        image_url_01 = find_image_by_suffix(target_images, product_code, "01")
        image_url_02 = find_image_by_suffix(target_images, product_code, "02")

        result["image_url_00"] = image_url_00
        result["image_url_01"] = image_url_01
        result["image_url_02"] = image_url_02

        # 기본 대표 이미지는 00 → 01 → 02 → MAIN/SUB 첫 번째 순서
        # 실제 화면에서는 00/01/02를 화살표로 넘겨볼 예정
        if image_url_00:
            result["image_url"] = image_url_00
        elif image_url_01:
            result["image_url"] = image_url_01
        elif image_url_02:
            result["image_url"] = image_url_02
        elif target_images:
            result["image_url"] = target_images[0].get("imageUrl", "")
        else:
            result["image_url"] = image_list[0].get("imageUrl", "")

        return result

    except Exception as e:
        print(f"[에러] {product_code}: {e}")
        return result


def main():
    df = pd.read_csv(INPUT_PATH, low_memory=False)

    df["product_code"] = df["product_code"].astype(str)
    product_codes = df["product_code"].dropna().unique().tolist()

    print(f"전체 상품 수: {len(product_codes)}")

    results = []

    for idx, product_code in enumerate(product_codes, start=1):
        image_result = get_product_image_urls(product_code)

        results.append({
            "product_code": product_code,
            "image_url": image_result["image_url"],
            "image_url_00": image_result["image_url_00"],
            "image_url_01": image_result["image_url_01"],
            "image_url_02": image_result["image_url_02"],
        })

        if idx % 100 == 0:
            print(f"{idx}/{len(product_codes)} 완료")

        time.sleep(0.03)

    image_df = pd.DataFrame(results)

    image_df.to_csv(OUTPUT_IMAGE_PATH, index=False, encoding="utf-8-sig")

    # 기존 step5 파일이 있더라도 step4 기준으로 새로 merge해서 재생성
    merged = df.merge(image_df, on="product_code", how="left")
    merged.to_csv(OUTPUT_MASTER_PATH, index=False, encoding="utf-8-sig")

    print("이미지 URL 수집 완료")
    print(f"이미지 URL 목록 저장: {OUTPUT_IMAGE_PATH}")
    print(f"이미지 포함 마스터 저장: {OUTPUT_MASTER_PATH}")

    print("image_url null 개수:", merged["image_url"].isna().sum())
    print(
        "image_url_00 null/빈값 개수:",
        (merged["image_url_00"].isna() | (merged["image_url_00"] == "")).sum()
    )
    print(
        "image_url_01 null/빈값 개수:",
        (merged["image_url_01"].isna() | (merged["image_url_01"] == "")).sum()
    )
    print(
        "image_url_02 null/빈값 개수:",
        (merged["image_url_02"].isna() | (merged["image_url_02"] == "")).sum()
    )


if __name__ == "__main__":
    main()