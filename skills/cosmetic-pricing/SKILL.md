---
name: cosmetic-pricing
description: >-
  화장품 가격 구조를 정한다. 정가(표기 가격)·판매가(상시가)·세일가(올영세일, 쿠폰)를
  나누고, 단품·2개 구성·1+1·기획세트를 짜고, 경쟁 제품과 100ml당 가격으로 비교하고,
  부가세 포함가 기준으로 원가·BEP를 돌려 본다. 소비자 패널의 가격 네 질문 답은
  Van Westendorp 도구(van_westendorp.py --currency won)로 허용 가격 범위로 읽는다.
  "가격 정해줘", "가격 구조 짜줘", "얼마에 팔아야 해", "1+1 해도 돼", "기획세트 가격",
  "100ml당 비교", "세일가 얼마까지" 같은 말에 쓴다.
argument-hint: "[프로젝트 슬러그] [후보 판매가]"
---

# cosmetic-pricing

가격은 마진을 가장 빨리 움직이는 손잡이이고 가장 많이 짐작으로 정하는 숫자다. 이 스킬은
확인할 수 있는 세 가지로 정한다: 구매자가 한 말, 경쟁 제품의 100ml당 가격, 제품이 벌어야
하는 돈.

사용자가 `/cosmetic-pricing` 뒤에 쓴 것: `$ARGUMENTS`

## 공통 규칙 (모든 cosmetic-* 스킬)

- 작업 폴더는 `cosmetic/<프로젝트-슬러그>/`다. 어느 프로젝트인지 확인한다.
- 사실이 아닌 것을 만들지 않는다. 추정은 '가설', 모르는 것은 '확인 필요'. 숫자는
  출처와 확인일.
- 경쟁사 문구를 베끼지 않는다. 효능, 1위, 근거 없는 수치를 만들지 않는다.
- beauty-data MCP는 있으면 쓰고 없으면 공개 웹으로 내려간다. MCP 데이터(카피 원문,
  OCR, 처방, 공급사, 가격)는 내부용이고 외부 게시물에 옮기지 않는다.

## 도구

```bash
python3 "${CLAUDE_SKILL_DIR}/../founder-pricing/van_westendorp.py" cosmetic/<슬러그>/panel/answers --price 10900 --currency won --out cosmetic/<슬러그>/pricing-curve.md
python3 "${CLAUDE_SKILL_DIR}/../cosmetic-cfo/cosmetic_economics.py" cosmetic/<슬러그>/numbers.json --price-factor 0.9
```

## Step 1: 구매자가 한 말

`/cosmetic-consumer`가 돌았으면 구매자마다 가격 네 답(너무 싸다, 싸다, 비싸다, 너무
비싸다)이 원 단위로 있다. 위 명령으로 읽는다. 실제 설문 CSV(열 `too_cheap, cheap,
expensive, too_expensive`)가 있으면 그것이 시뮬레이션보다 낫다.

| 점 | 뜻 |
| --- | --- |
| PMC | 이보다 싸면 품질을 의심하는 사람이 너무 많다 |
| OPP | 양쪽 저항이 가장 적은 가격 |
| IPP | 싸다는 사람과 비싸다는 사람이 같아지는 가격 |
| PME | 이보다 비싸면 안 사는 사람이 너무 많다 |

PMC~PME가 허용 범위다. 패널이 안 돌았으면 그렇다고 말하고 `/cosmetic-consumer --quick`을
권한다. 범위를 지어내지 않는다.

## Step 2: 경쟁 제품의 100ml당 가격

`competitors.md`/`competitors.csv`에서 같은 용량 구간과 이웃 구간의 판매가, 100ml당
가격, 프로모션 구성을 가져온다. 없으면 지금 찾는다(MCP `search_products`, 없으면 공개
상품 페이지). 같은 것끼리 비교한다: 1L는 1L끼리, 세트는 개당으로 환산해서. 모든 가격에
출처와 확인일.

## Step 3: 가격 구조

화장품 가격은 한 숫자가 아니다. 표로 정한다(모두 부가세 포함가).

| 층 | 뜻 | 정할 것 |
| --- | --- | --- |
| 정가 | 표기하는 소비자가 | 실제로 그 가격에 팔 계획이 있는지. 할인율 표기 근거가 되므로 RA 확인 필요 |
| 판매가 | 평소에 팔리는 가격 | BEP의 기준 |
| 세일가 | 올영세일, 쿠폰, 브랜드데이 | 얼마까지 내려가도 되는지(아래 Step 4 what-if) |
| 구성 | 단품, 2개, 1+1, 3종 세트, 기획세트(증정) | 구성별 가격, 100ml당, 예상 수량 비중 |

- 1+1과 2개 구성은 배송 1박스인지 확인한다(배송비가 주문당이라 공헌이익이 달라진다).
- 증정(미니어처, 사은품)은 원가로 `numbers.json`에 넣는다. 공짜가 아니다.
- 채널마다 수수료가 다르면(올리브영, 쿠팡, 자사몰) 채널별로 따로 계산한다.

## Step 4: 제품이 벌어야 하는 돈

`numbers.json`(`/cosmetic-cfo`)이 있으면 후보 가격과 구성 믹스로 돌려 본다.

```bash
python3 "${CLAUDE_SKILL_DIR}/../cosmetic-cfo/cosmetic_economics.py" cosmetic/<슬러그>/numbers.json --price-factor 0.85   # 세일가 15% 할인
python3 "${CLAUDE_SKILL_DIR}/../cosmetic-cfo/cosmetic_economics.py" cosmetic/<슬러그>/numbers.json --commission 0.10     # 자사몰 비중이 클 때
```

구성 믹스를 바꿀 때는 `numbers.json`의 `bundles`를 복사한 파일로 돌리고, 원본은 결정 뒤에만
고친다. 없으면 `/cosmetic-cfo`를 먼저 권한다.

## Step 5: 결정

`cosmetic/<슬러그>/pricing.md`:

1. **가격 구조 표:** 구성, 판매가, 100ml당, 경쟁 비교 한 줄.
2. **왜 이 가격인가:** 허용 범위 안의 위치, 경쟁 대비, 도구가 낸 BEP·소진율·완판 이익.
3. **세일 바닥:** 이 아래로 가면 주문마다 손해이거나 BEP가 초도를 넘는 가격.
4. **정가 표기:** 쓸지, 쓴다면 실제 판매 계획과 RA 확인 항목.
5. **테스트할 것:** 범위 안의 두 가격이나 두 구성, 어떻게 시험할지(자사몰 A/B, 사전 예약).
6. 패널의 가격 반대 이유 상위 셋(그들의 말), 마케팅이 답하도록.

## 규칙

- 시뮬레이션 가격 답은 무엇을 시험할지 고르는 데 쓴다. 증거가 아니다.
- **가짜 정가 금지:** 판 적 없고 팔 계획도 없는 "정가"로 할인율을 만들지 않는다.
- "최저가", "역대 최저" 같은 말은 근거(기간, 비교 대상) 없이는 쓰지 않는다. cosmetic-claims로.
- 원가 아래로 파는 구성은 그렇다고 밝히고, 버틸 수 있는 기간을 CFO 숫자로 적는다.

## 출력

`cosmetic/<슬러그>/pricing-curve.md`, `cosmetic/<슬러그>/pricing.md`. 가격·구성이 바뀌면
`numbers.json`을 고치고 `/cosmetic-cfo`를 다시 돌린다.
