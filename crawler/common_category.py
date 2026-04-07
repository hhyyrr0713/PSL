import time
from typing import Dict, Optional

import requests


def fetch_categories_json(
    product_code: str,
    session: requests.Session,
    headers: Optional[dict] = None,
    timeout: int = 15,
    sleep_sec: float = 0.0,
) -> Optional[dict]:
    url = f"https://nxapi.lfmall.co.kr/product/v1/basic/category/{product_code}"

    try:
        response = session.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        if sleep_sec > 0:
            time.sleep(sleep_sec)

        return data
    except Exception as e:
        print(f"[WARN] categories fetch failed - {product_code}: {e}")
        return None


def parse_standard_categories(categories_json: Optional[dict]) -> Dict[str, str]:
    result = {
        "lf_category_l1": "",
        "lf_category_l2": "",
        "lf_category_l3": "",
    }

    if not categories_json:
        return result

    try:
        category_list = (
            categories_json.get("body", {})
            .get("productStandardCategoriesDTOList", [])
        )

        for cat in category_list:
            depth = cat.get("standardCategoryDepth")
            name = str(cat.get("standardCategoryName", "")).strip()

            if depth == 1:
                result["lf_category_l1"] = name
            elif depth == 2:
                result["lf_category_l2"] = name
            elif depth == 3:
                result["lf_category_l3"] = name

    except Exception as e:
        print(f"[WARN] category parse failed: {e}")

    return result


def get_category_info(
    product_code: str,
    session: requests.Session,
    headers: Optional[dict] = None,
    timeout: int = 15,
    sleep_sec: float = 0.0,
) -> Dict[str, str]:
    categories_json = fetch_categories_json(
        product_code=product_code,
        session=session,
        headers=headers,
        timeout=timeout,
        sleep_sec=sleep_sec,
    )
    return parse_standard_categories(categories_json)