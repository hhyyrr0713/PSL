# styling/styling_rules.py

MOOD_KEYS = [
    "business_casual",
    "casual",
    "street",
    "minimal",
    "formal",
]

AGE_KEYS = [
    "20s",
    "30s",
    "40s_plus",
]


# --------------------------------------------------
# 1. 브랜드별 무드 prior
# 합계 10 기준
# --------------------------------------------------
BRAND_MOOD_PRIORS = {
    "allegri": {
        "business_casual": 6,
        "casual": 1,
        "street": 0,
        "minimal": 1,
        "formal": 2,
    },
    "daks men": {
        "business_casual": 4,
        "casual": 1,
        "street": 0,
        "minimal": 1,
        "formal": 4,
    },
    "hazzys men": {
        "business_casual": 4,
        "casual": 3,
        "street": 0,
        "minimal": 1,
        "formal": 2,
    },
    "ilcorso": {
        "business_casual": 1,
        "casual": 4,
        "street": 1,
        "minimal": 4,
        "formal": 0,
    },
    "jillstuartnewyork men": {
        "business_casual": 3,
        "casual": 2,
        "street": 0,
        "minimal": 4,
        "formal": 1,
    },
    "tngt": {
        "business_casual": 4,
        "casual": 3,
        "street": 1,
        "minimal": 1,
        "formal": 1,
    },
}


# --------------------------------------------------
# 2. 브랜드별 연령 prior
# 합계 10 기준
# age는 약한 보정용
# --------------------------------------------------
BRAND_AGE_PRIORS = {
    "allegri": {"20s": 2, "30s": 4, "40s_plus": 4},
    "daks men": {"20s": 0, "30s": 2, "40s_plus": 8},
    "hazzys men": {"20s": 3, "30s": 4, "40s_plus": 3},
    "ilcorso": {"20s": 5, "30s": 4, "40s_plus": 1},
    "jillstuartnewyork men": {"20s": 3, "30s": 5, "40s_plus": 2},
    "tngt": {"20s": 4, "30s": 4, "40s_plus": 2},
}


# --------------------------------------------------
# 3. 카테고리별 무드 prior
# 합계 10 기준
# --------------------------------------------------
CATEGORY_MOOD_PRIORS = {
    "자켓": {
        "business_casual": 5,
        "casual": 1,
        "street": 0,
        "minimal": 2,
        "formal": 2,
    },
    "코트": {
        "business_casual": 4,
        "casual": 1,
        "street": 0,
        "minimal": 3,
        "formal": 2,
    },
    "점퍼": {
        "business_casual": 1,
        "casual": 5,
        "street": 2,
        "minimal": 1,
        "formal": 1,
    },
    "트렌치코트": {
        "business_casual": 4,
        "casual": 1,
        "street": 0,
        "minimal": 2,
        "formal": 3,
    },
    "셔츠": {
        "business_casual": 5,
        "casual": 1,
        "street": 0,
        "minimal": 2,
        "formal": 2,
    },
    "티셔츠": {
        "business_casual": 1,
        "casual": 5,
        "street": 2,
        "minimal": 2,
        "formal": 0,
    },
    "스웨터/맨투맨": {
        "business_casual": 2,
        "casual": 4,
        "street": 1,
        "minimal": 2,
        "formal": 1,
    },
    "베스트": {
        "business_casual": 4,
        "casual": 1,
        "street": 0,
        "minimal": 3,
        "formal": 2,
    },
    "팬츠": {
        "business_casual": 2,
        "casual": 4,
        "street": 2,
        "minimal": 1,
        "formal": 1,
    },
    "수트": {
        "business_casual": 2,
        "casual": 0,
        "street": 0,
        "minimal": 1,
        "formal": 7,
    },
}


# --------------------------------------------------
# 4. 상품명 키워드 보정
# 합계 제한 없음
# 발견되는 키워드마다 누적 보정
# --------------------------------------------------
KEYWORD_MOOD_ADJUSTMENTS = {
    # business_casual / formal
    "블레이저": {"business_casual": 2, "formal": 1},
    "blazer": {"business_casual": 2, "formal": 1},
    "슬랙스": {"business_casual": 2, "formal": 1},
    "slacks": {"business_casual": 2, "formal": 1},
    "테일러드": {"business_casual": 2, "formal": 1},
    "tailored": {"business_casual": 2, "formal": 1},
    "체스터": {"business_casual": 1, "formal": 2},
    "chester": {"business_casual": 1, "formal": 2},
    "더블": {"formal": 2},
    "double": {"formal": 2},
    "드레스": {"formal": 2},
    "dress": {"formal": 2},
    "치노": {"business_casual": 2},
    "chino": {"business_casual": 2},

    # casual / street
    "후드": {"casual": 2, "street": 1},
    "hood": {"casual": 2, "street": 1},
    "후디": {"casual": 2, "street": 1},
    "hoodie": {"casual": 2, "street": 1},
    "맨투맨": {"casual": 2},
    "스웨트": {"casual": 2},
    "sweat": {"casual": 2},
    "조거": {"casual": 2, "street": 1},
    "jogger": {"casual": 2, "street": 1},
    "카고": {"street": 2, "casual": 1},
    "cargo": {"street": 2, "casual": 1},
    "그래픽": {"street": 2, "casual": 1},
    "graphic": {"street": 2, "casual": 1},
    "프린트": {"street": 1, "casual": 1},
    "print": {"street": 1, "casual": 1},

    # minimal
    "미니멀": {"minimal": 2},
    "minimal": {"minimal": 2},
    "에센셜": {"minimal": 2},
    "essential": {"minimal": 2},
    "베이직": {"minimal": 1, "casual": 1},
    "basic": {"minimal": 1, "casual": 1},
    "클래식": {"minimal": 1, "business_casual": 1},
    "classic": {"minimal": 1, "business_casual": 1},
}


# --------------------------------------------------
# 5. fit 보정
# --------------------------------------------------
FIT_MOOD_ADJUSTMENTS = {
    "slim": {"business_casual": 1, "formal": 1},
    "regular": {"business_casual": 1, "minimal": 1},
    "relaxed": {"casual": 1, "minimal": 1},
    "wide": {"street": 1, "casual": 1, "minimal": 1},
    "oversized": {"street": 2, "casual": 1, "minimal": 1},
    "unknown": {},
}


# --------------------------------------------------
# 6. 소재 관련
# 소재는 무드가 아니라 고급감/질감용
# --------------------------------------------------
MATERIAL_LUXURY_MAP = {
    "cashmere": 5,
    "wool": 4,
    "leather": 4,
    "knit": 3,
    "cotton": 3,
    "denim": 2,
    "synthetic": 2,
    "unknown": 2,
}

MATERIAL_TEXTURE_MAP = {
    "cashmere": "soft",
    "wool": "soft",
    "leather": "structured",
    "knit": "soft",
    "cotton": "balanced",
    "denim": "rugged",
    "synthetic": "technical",
    "unknown": "unknown",
}


# --------------------------------------------------
# 7. 카테고리 -> item_role
# --------------------------------------------------
CATEGORY_TO_ITEM_ROLE = {
    "코트": "outer",
    "자켓": "outer",
    "점퍼": "outer",
    "트렌치코트": "outer",

    "셔츠": "top",
    "티셔츠": "top",
    "스웨터/맨투맨": "top",
    "베스트": "top",

    "팬츠": "bottom",

    "수트": "set",

    "가방": "accessory",
    "벨트": "accessory",
    "장갑": "accessory",
    "모자": "accessory",
    "머플러": "accessory",
    "넥타이": "accessory",
    "슬리퍼": "accessory",
    "양말": "accessory",

    "펫의류": "other",
}


# --------------------------------------------------
# 8. fit 키워드
# --------------------------------------------------
FIT_KEYWORDS = {
    "oversized": ["오버핏", "oversized", "overfit"],
    "wide": ["와이드", "wide", "루즈핏", "loose fit", "loose"],
    "relaxed": ["릴렉스", "relaxed", "여유핏", "comfort", "컴포트"],
    "slim": ["슬림", "slim", "스키니", "skinny", "테이퍼드", "tapered"],
    "regular": ["레귤러", "regular", "basic", "standard", "스탠다드", "클래식핏"],
}


# --------------------------------------------------
# 9. 소재 키워드
# --------------------------------------------------
MATERIAL_KEYWORDS = {
    "cashmere": ["캐시미어", "cashmere"],
    "wool": ["울", "wool"],
    "leather": ["레더", "leather", "가죽"],
    "knit": ["니트", "knit"],
    "cotton": ["코튼", "cotton"],
    "denim": ["데님", "denim", "jean", "진"],
    "synthetic": ["폴리", "poly", "나일론", "nylon", "synthetic"],
}


# --------------------------------------------------
# 10. 패턴 키워드
# --------------------------------------------------
PATTERN_KEYWORDS = {
    "stripe": ["스트라이프", "stripe"],
    "check": ["체크", "check", "checkered", "plaid"],
    "graphic": ["그래픽", "graphic", "로고", "logo"],
    "print": ["프린트", "print"],
}


# --------------------------------------------------
# 11. 추후 스타일링 템플릿용 기본 틀
# 지금은 비워두거나 간단히만 둬도 됨
# --------------------------------------------------
STYLE_TEMPLATES = {
    "business_casual": {
        "preferred_moods": ["business_casual", "formal", "minimal"],
        "forbidden_high_moods": ["street"],
    },
    "casual": {
        "preferred_moods": ["casual", "minimal"],
        "forbidden_high_moods": [],
    },
    "street": {
        "preferred_moods": ["street", "casual"],
        "forbidden_high_moods": ["formal"],
    },
    "minimal": {
        "preferred_moods": ["minimal", "business_casual"],
        "forbidden_high_moods": [],
    },
}