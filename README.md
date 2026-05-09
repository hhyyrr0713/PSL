# PSL: Personal Styling Lab

LF Mall 남성 패션 상품 데이터를 기반으로, 사용자가 선택한 아이템과 어울리는 상의/하의/아우터 및 2피스·3피스 코디를 추천하는 규칙 기반 스타일링 추천 웹 서비스입니다.

PSL은 단순 상품 추천이 아니라, 실제 패션 스타일링 관점에서 아이템 역할, 색상, 무드, 핏, 계절감, 가격대, 상품 이미지 등을 함께 반영하여 사용자가 쇼핑몰처럼 탐색할 수 있는 추천 화면을 구현하는 것을 목표로 했습니다.

> 본 프로젝트는 개인 포트폴리오 및 학습 목적으로 제작되었으며, LF 및 LFmall의 공식 서비스가 아닙니다.

<img width="2785" height="1129" alt="image" src="https://github.com/user-attachments/assets/b892e0a3-545b-4ccb-bf68-5a28259ebb2c" />

---

## 1. 프로젝트 개요

PSL은 LF Mall의 남성 패션 브랜드 상품 데이터를 수집하고, 이를 기반으로 스타일링 추천 엔진과 웹 기반 추천 앱을 구현한 개인 프로젝트입니다.

사용자는 웹 화면에서 상품을 검색한 뒤 기준 상품을 선택하고, 원하는 추천 조건을 설정하여 다음과 같은 결과를 받을 수 있습니다.

- 상의 추천
- 하의 추천
- 아우터 추천
- 2피스 추천
- 3피스 추천

1차 MVP에서는 추천 엔진이 웹에서 동작하는 것을 목표로 했고, 2차 MVP에서는 상품 이미지와 카드형 UI를 적용하여 실제 쇼핑 서비스처럼 탐색할 수 있는 화면으로 개선했습니다.

---

## 2. 사용 브랜드

현재 데이터 수집 및 추천 대상은 LF Mall 남성 패션 브랜드 중심으로 구성했습니다.

- ALLEGRI
- DAKS MEN
- HAZZYS MEN
- ILCORSO
- JILLSTUART NEWYORK MEN
- TNGT

---

## 3. 주요 기능

### 상품 검색

사용자는 상품명, 브랜드명, 상품코드를 기준으로 상품을 검색할 수 있습니다.

검색 필터는 다음 조건을 지원합니다.

- 브랜드
- 역할: 상의 / 하의 / 아우터
- 카테고리
- 가격대

검색 결과는 카드 UI와 페이지네이션 방식으로 표시됩니다.

### 기준 상품 선택

검색 결과에서 상품 카드를 클릭하면 해당 상품이 추천의 기준 아이템으로 선택됩니다.

선택된 기준 상품은 이미지, 상품명, 가격, 브랜드, 역할, 카테고리, 시즌 정보와 함께 표시됩니다.

### 추천 조건 설정

추천 시 다음 조건을 설정할 수 있습니다.

- 추천 방식
  - 전체 보기
  - 상의 후보
  - 하의 후보
  - 아우터 후보
  - 2피스 추천
  - 3피스 추천
- 추천 브랜드
- 추천 카테고리
- 추천 가격대
- 동일 브랜드만 추천

### 추천 결과 표시

추천 결과는 상품 카드 형태로 표시됩니다.

각 상품 카드에는 다음 정보가 포함됩니다.

- 상품 이미지
- 상품명
- 브랜드
- 판매가
- 역할
- 카테고리
- 시즌 정보
- 가격대

### 이미지 슬라이더

LF Mall 상품 이미지 API에서 가져온 상품별 이미지 후보를 카드 안에서 화살표로 넘겨볼 수 있도록 구현했습니다.

수집한 이미지 컬럼은 다음과 같습니다.

- `image_url`
- `image_url_00`
- `image_url_01`
- `image_url_02`

상품마다 이미지 개수가 다르기 때문에, 프론트엔드에서는 존재하는 이미지 URL만 배열로 구성하여 슬라이더에 표시합니다.

### 2피스/3피스 코디 카드

2피스/3피스 추천 결과는 단순 표가 아니라 하나의 코디 카드처럼 표시됩니다.

코디 카드에는 다음 정보가 포함됩니다.

- 상의 이미지 / 상품명 / 가격
- 하의 이미지 / 상품명 / 가격
- 아우터 이미지 / 상품명 / 가격
- 세트 총 가격
- 추천 조합 설명

---

## 4. 데이터 수집 및 전처리

LF Mall API를 기반으로 상품 데이터를 수집했습니다.

수집 및 통합한 주요 데이터는 다음과 같습니다.

- 상품 코드
- 상품명
- 브랜드
- 가격
- 할인율
- 리뷰 수
- 리뷰 평점
- 구매 수
- 조회 수
- 위시 수
- 색상
- 사이즈 재고
- 카테고리
- 시즌 정보
- 상품 이미지 URL

브랜드별 CSV를 통합하여 마스터 테이블을 구성했습니다.

1차 MVP 기준 마스터 테이블:

```text
data/master_table_step4_styling.csv
```

2차 MVP 기준 이미지 포함 마스터 테이블:

```text
data/master_table_step5_image.csv
```

이미지 URL만 별도로 저장한 파일:

```text
data/product_image_urls.csv
```

---

## 5. 상품 이미지 URL 수집

2차 MVP에서는 상품 검색 결과와 추천 결과를 쇼핑몰 카드처럼 보여주기 위해 LF Mall 상품 이미지 API를 추가로 연동했습니다.

사용한 API 형식은 다음과 같습니다.

```text
https://nxapi.lfmall.co.kr/product/v1/contents/{product_code}
```

응답 내 `productImageDTOList`에서 상품 이미지 URL을 추출했습니다.

이미지 타입은 다음과 같이 구분됩니다.

- `MAIN`
- `SUB`
- `DETAIL`

이 중 카드 UI에 적합한 `MAIN`, `SUB` 이미지를 중심으로 사용하고, 상세 설명 이미지인 `DETAIL`은 제외했습니다.

이미지 수집 결과, 모든 상품에 `image_url_00`이 존재했고, 일부 상품은 `image_url_01`, `image_url_02`까지 존재했습니다. 상품마다 제공되는 이미지 수가 다르기 때문에 프론트엔드에서는 빈 URL을 제외하고 존재하는 이미지만 슬라이더에 표시하도록 구현했습니다.

---

## 6. Feature Engineering

추천 품질을 높이기 위해 상품별 스타일링 관련 파생 변수를 생성했습니다.

주요 파생 변수는 다음과 같습니다.

- `item_role`
  - top
  - bottom
  - outer
- `fit_type`
- `material_type`
- `pattern_type`
- `top_subtype`
- `bottom_subtype`
- `sleeve_length_type`
- `pants_length_type`
- `primary_mood`
- `secondary_mood`
- `display_mood_tag`
- `mood_*`
- `age_*`
- `luxury_level`
- `texture_class`
- `color_group`
- `price_range`
- `has_stock`

또한 가격대 구간, 색상 그룹, 사이즈 재고 여부 등을 정리하여 검색 및 추천 필터에 활용했습니다.

---

## 7. 시즌 프로필 개선

초기에는 단순히 SS/FW 또는 계절 flag의 겹침 여부만 기준으로 계절감을 판단했습니다.

하지만 이 방식은 다음과 같은 문제가 있었습니다.

예를 들어, 여름+가을 아이템과 가을+겨울 아이템은 둘 다 “가을”이 겹치기 때문에 궁합이 좋다고 판단될 수 있습니다. 그러나 실제 체감 계절감은 여름축과 겨울축이 섞여 어색할 수 있습니다.

이를 개선하기 위해 시즌 정보를 다음 세 축으로 재해석했습니다.

- `season_warm_weight`
- `season_mid_weight`
- `season_cold_weight`
- `season_temperature_score`
- `season_profile_label`

즉 단순히 “계절이 겹치는가”가 아니라, 아이템의 체감 온도감이 얼마나 가까운지를 기준으로 계절 궁합을 판단하도록 개선했습니다.

3피스 추천에서는 상의, 하의, 아우터 전체 조합의 계절감 차이가 지나치게 벌어지지 않도록 coherence penalty를 추가했습니다.

---

## 8. 스타일링 추천 로직

추천 엔진은 규칙 기반 방식으로 구현했습니다.

사용 점수 요소는 다음과 같습니다.

- 무드 조화 점수
- 색상 조화 점수
- 포멀도 유사도
- 핏 조화 점수
- 브랜드 통일감
- 연령대 적합도
- 기존 상품 인기도 점수
- 역할 궁합 점수
- 시즌 궁합 점수

추천 방식은 크게 세 가지입니다.

### Pair 추천

기준 아이템과 다른 역할의 아이템 간 1:1 궁합을 계산합니다.

예시:

- 셔츠 기준 → 하의 추천
- 팬츠 기준 → 상의/아우터 추천
- 아우터 기준 → 상의/하의 추천

### 2피스 추천

기준 아이템을 포함하여 2개 아이템으로 구성된 조합을 추천합니다.

예시:

- 상의 + 하의
- 아우터 + 상의
- 하의 + 상의

### 3피스 추천

상의, 하의, 아우터를 포함한 3피스 코디 조합을 추천합니다.

3피스 추천에서는 pairwise 점수뿐 아니라 전체 조합의 계절감 coherence도 함께 고려합니다.

---

## 9. 웹 앱 구현

추천 엔진을 FastAPI 백엔드와 HTML/CSS/JavaScript 프론트엔드로 연결하여 웹에서 사용할 수 있도록 구현했습니다.

### 백엔드

```text
app/main.py
```

FastAPI를 사용하여 다음 API를 제공합니다.

- `/search`
  - 상품 검색 API
- `/recommend/{product_code}`
  - 기준 상품 기반 추천 API
- `/page`
  - 웹 페이지 접근 경로
- `/docs`
  - FastAPI 자동 문서

### 프론트엔드

```text
app/static/index.html
```

HTML, CSS, JavaScript로 구현했습니다.

주요 기능:

- PSL 브랜딩 적용
- 상품 검색
- 검색 결과 카드 UI
- 상품 이미지 슬라이더
- 검색 결과 페이지네이션
- 기준 상품 선택
- 추천 방식 선택
- 추천 필터 설정
- 추천 결과 카드 UI
- 2피스/3피스 코디 카드 UI
- 가격 및 세트 총 가격 표시
- 추천 결과 페이지네이션

---

## 10. 프로젝트 구조

```text
PSL/
├─ app/
│  ├─ main.py
│  └─ static/
│     └─ index.html
│
├─ crawler/
│  ├─ collect_image_urls.py
│  ├─ product_list_Allegri.py
│  ├─ product_list_DaksMen.py
│  ├─ product_list_HazzysMen.py
│  ├─ product_list_Ilcoroso.py
│  ├─ product_list_JillstuartNewYorkMen.py
│  ├─ product_list_TngtMen.py
│  └─ common_category.py
│
├─ analysis/
│  ├─ build_master_table.py
│  ├─ recommend_runner.py
│  ├─ recommend_system.py
│  └─ recommend_protfolio_export.py
│
├─ styling/
│  ├─ styling_engine.py
│  ├─ styling_rules.py
│  ├─ styling_from_item.py
│  ├─ styling_from_theme.py
│  └─ rule_registry.csv
│
├─ data/
│  ├─ master_table_step4_styling.csv
│  ├─ product_image_urls.csv
│  ├─ master_table_step5_image.csv
│  └─ portfolio_results/
│
├─ output/
│  └─ recommendations/
│
├─ requirements.txt
└─ README.md
```

---

## 11. 실행 방법

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 이미지 URL 수집

이미지 URL을 새로 수집하거나 갱신하려면 다음 파일을 실행합니다.

```bash
python crawler/collect_image_urls.py
```

실행 결과 다음 파일이 생성됩니다.

```text
data/product_image_urls.csv
data/master_table_step5_image.csv
```

### 3. FastAPI 서버 실행

프로젝트 루트 폴더에서 실행합니다.

```bash
uvicorn app.main:app --reload
```

### 4. 웹 페이지 접속

```text
http://127.0.0.1:8000/static/index.html
```

또는

```text
http://127.0.0.1:8000/page
```

### 5. API 문서 확인

```text
http://127.0.0.1:8000/docs
```

---

## 12. 현재 구현 상태

현재 2차 MVP 구현이 완료된 상태입니다.

### 1차 MVP 완료 내용

- LF Mall 상품 데이터 수집
- 브랜드별 상품 데이터 통합
- 마스터 테이블 구축
- 스타일링용 feature engineering
- 규칙 기반 추천 엔진 구현
- 시즌 프로필 기반 계절감 개선
- 2피스/3피스 추천 구현
- FastAPI 백엔드 구현
- 기본 웹 프론트엔드 구현
- 검색/추천 필터 구현
- 가격 및 세트 총 가격 표시
- 추천 결과 페이지네이션 구현

### 2차 MVP 완료 내용

- 프로젝트명 PSL(Personal Styling Lab) 적용
- 상품 이미지 URL 수집
- `image_url_00`, `image_url_01`, `image_url_02` 컬럼 구축
- 이미지 포함 마스터 테이블 생성
- 검색 결과 카드 UI 적용
- 기준 상품 카드 UI 적용
- 추천 결과 카드 UI 적용
- 2피스/3피스 코디 카드 UI 적용
- 상품 이미지 슬라이더 구현
- 추천 API 응답에 이미지 URL 포함
- 프론트엔드에서 존재하는 이미지만 슬라이더로 표시
- 전체 UI를 쇼핑몰 탐색 흐름에 가깝게 개선

---

## 13. 기술 스택

### Backend

- Python
- FastAPI
- Pandas
- NumPy

### Frontend

- HTML
- CSS
- JavaScript

### Data

- LF Mall API
- CSV 기반 마스터 테이블
- 상품 이미지 URL 수집

### Tools

- VS Code
- Git / GitHub
- PowerShell

---

## 14. 프로젝트 의의

이 프로젝트는 단순히 추천 모델을 적용하는 것보다, 실제 쇼핑몰 데이터를 기반으로 추천 시스템이 동작하기 위해 필요한 전 과정을 직접 설계한 데 의미가 있습니다.

특히 다음 과정을 중점적으로 수행했습니다.

- 실제 커머스 데이터 수집
- 상품 데이터 정제 및 통합
- 패션 도메인 기반 feature engineering
- 규칙 기반 추천 로직 설계
- 계절감 문제 개선
- 상품 이미지 API 연동
- 카드형 UI 및 이미지 슬라이더 구현
- 웹 기반 추천 서비스 구현

이를 통해 데이터 수집부터 추천 로직, API 서버, 프론트엔드 UI까지 이어지는 end-to-end 추천 시스템의 2차 MVP를 완성했습니다.

---

## 15. 향후 개선 방향

향후 개선할 수 있는 방향은 다음과 같습니다.

### 추천 설명 개선

현재 추천 이유와 점수는 내부적으로 계산되며 일부 조합 설명에 활용됩니다.  
향후에는 사용자가 이해하기 쉬운 문장형 추천 설명을 더 정교하게 제공할 수 있습니다.

### 테마 기반 추천

비즈니스 캐주얼, 데일리, 미니멀, 포멀 등 사용자가 원하는 스타일 테마를 선택하면 해당 테마에 맞는 코디를 추천하도록 확장할 수 있습니다.

### 이미지 기반 코디 시각화

현재는 상품 이미지를 카드 형태로 나란히 보여주는 방식입니다.  
향후에는 상품 이미지를 조합하여 마네킹 스타일의 코디 시각화로 확장할 수 있습니다.

### DB 연동

현재는 CSV 파일 기반으로 데이터를 로드합니다.  
향후 PostgreSQL, MySQL 등의 DB를 연결하여 데이터 관리와 검색 성능을 개선할 수 있습니다.

### 배포

현재 앱은 로컬 환경에서 실행됩니다.  
향후 Render, Railway, AWS 등을 활용하여 외부 접속 가능한 형태로 배포할 수 있습니다.

---

## 16. 1차 MVP 구현 화면

<img width="2872" height="1469" alt="image" src="https://github.com/user-attachments/assets/d7f71956-176b-4d46-a5bb-9725a7ba47a9" />

<img width="2800" height="1190" alt="image" src="https://github.com/user-attachments/assets/e2e8020e-0e74-4aef-9f0a-e6b36605c1cd" />

<img width="2684" height="1307" alt="image" src="https://github.com/user-attachments/assets/1a4d0391-21a3-4276-94f0-2f133db2459e" />

<img width="2694" height="1412" alt="image" src="https://github.com/user-attachments/assets/c9a8c02f-39a1-429f-b2fd-c6c16b8ca1db" />

<img width="2691" height="1080" alt="image" src="https://github.com/user-attachments/assets/82e44520-0f21-4dca-bc27-fdeb00cade3b" />

---

## 17. 2차 MVP 구현 화면

<img width="2734" height="1438" alt="image" src="https://github.com/user-attachments/assets/e143f569-bd5d-44bd-bc93-549212b0bfa0" />

<img width="2695" height="1318" alt="image" src="https://github.com/user-attachments/assets/2e6fae76-3106-4cde-bffe-2a736c894c71" />

<img width="2728" height="1332" alt="image" src="https://github.com/user-attachments/assets/43a04c90-b3cd-48d1-b629-f35c711a495f" />

<img width="2750" height="997" alt="image" src="https://github.com/user-attachments/assets/e99f365c-a5ed-4706-a1e2-da061934615a" />

<img width="2761" height="888" alt="image" src="https://github.com/user-attachments/assets/79a8480f-ed53-4f83-9047-5427687c08a7" />
