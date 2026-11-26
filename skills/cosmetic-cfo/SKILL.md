---
name: cosmetic-cfo
description: >-
  화장품 원가와 BEP. 내용물(원/g × 용량), 용기·펌프, 인쇄·라벨, 단상자, 충진·제조비로
  개당 원가를 내고, 부가세 포함 판매가에서 채널 수수료와 주문당 배송비를 뺀 구성별
  (단품, 2개, 세트) 공헌이익, 구성 믹스의 개당 평균 공헌이익, 초도 물량 원가와 마케팅비를
  고정비로 본 BEP 수량과 초도 소진율, 완판 시 이익, 재발주부터 개당 이익, what-if를
  계산한다. 모든 숫자는 입력 파일에서 나오고 빠진 값은 오류로 알린다. "원가 BEP 계산",
  "손익 봐줘", "원가 계산해줘", "BEP 몇 개야", "초도 몇 개 팔아야 해", "마진 나와",
  "수수료 바뀌면 어떻게 돼" 같은 말에 쓴다.
argument-hint: "[프로젝트 슬러그 또는 numbers.json 경로]"
---

# cosmetic-cfo

"그거 얼마 드는데?"를 묻는 사람. 좋은 기획이 제품이 되는지는 마진이 정한다. 이 스킬은
그 숫자를 찾고, 모든 숫자를 확인할 수 있는 입력까지 거슬러 올라가게 한다.

사용자가 `/cosmetic-cfo` 뒤에 쓴 것: `$ARGUMENTS`

## 공통 규칙 (모든 cosmetic-* 스킬)

- 작업 폴더는 `cosmetic/<프로젝트-슬러그>/`다. 어느 프로젝트인지 확인한다.
- 사실이 아닌 것을 만들지 않는다. 추정은 '가설', 모르는 것은 '확인 필요'. 숫자는
  출처와 확인일.
- 경쟁사 문구를 베끼지 않는다. 효능, 1위, 근거 없는 수치를 만들지 않는다.
- beauty-data MCP는 있으면 쓰고 없으면 공개 웹으로 내려간다. MCP 데이터(카피 원문,
  OCR, 처방, 공급사, 가격)는 내부용이고 외부 게시물에 옮기지 않는다.

## 도구

```bash
python3 "${CLAUDE_SKILL_DIR}/cosmetic_economics.py" cosmetic/<슬러그>/numbers.json --out cosmetic/<슬러그>/cfo.md
```

## Step 1: 입력 모으기

`cosmetic/<슬러그>/numbers.json`을 쓴다. 모양은 이 폴더의 `example.json`(가상 예시: 솔트브리즈
1L 퍼퓸 바디워시)과 `example.aggressive.json`(같은 제품의 공격안: 단상자
생략, 3향 세트 추가).

| 필드 | 넣을 것 |
| --- | --- |
| `product` | 제품명 |
| `size_ml` | 한 개 용량(ml). 100ml당 가격에 쓴다 |
| `unit_cost.content` | `won_per_g`(내용물 원/g), `grams`(충진량 g) |
| `unit_cost.items` | `[{label, cost}]`: 용기+펌프, 인쇄/라벨, 단상자, 충진·제조. 없는 항목은 0으로 적어 없다는 걸 남긴다 |
| `vat_included` | 판매가가 부가세 포함이면 `true`(국내 소비자가는 보통 포함) |
| `vat_rate` | 선택, 기본 0.10 |
| `commission_rate` | 채널 수수료, 0.20 = 20%. 결제가(판매가) 기준 |
| `shipping_per_order` | 브랜드가 내는 주문당 배송비(무료배송) |
| `bundles` | `[{name, units_per_order, price, unit_share}]`. 비중은 수량 기준 `unit_share` 또는 주문 기준 `order_share` 중 한 가지로, 합이 1 |
| `initial_units` | 초도 물량(예: 3종 × 10,000개 = 30,000) |
| `one_off` | `[{label, cost}]`: 인플루언서, 디자인, 금형, 촬영 같은 일회성 비용 |

항목마다 `source`, `as_of`를 붙일 수 있고 보고서에 함께 찍힌다. 숫자를 가져올 순서:

1. 사용자의 견적서, 단가표, 계약서(부자재 견적, 랩 내용물 견적, 채널 수수료 계약).
2. 내부 시스템의 기준가(beauty-data MCP의 `riselab_supplier` ERP 단가 등). **내부용**이다.
3. 추정. `cfo-sources.md`에 '추정'이라고 쓰고 이유를 적는다. 추정을 사실처럼 쓰지 않는다.

내용물 원/g은 `/cosmetic-formula`의 목표 원가와 같아야 한다. 다르면 어느 쪽이 최신인지
사용자에게 묻는다.

## Step 2: 돌리기

```bash
python3 "${CLAUDE_SKILL_DIR}/cosmetic_economics.py" cosmetic/<슬러그>/numbers.json --out cosmetic/<슬러그>/cfo.md
```

계산 방식(브랜드 기준):

- 개당 원가 = 내용물(원/g × g) + 부자재·충진 항목.
- 고정비 = 초도 물량 × 개당 원가 + 일회성 비용. 초도는 먼저 돈을 내고 만들기 때문이다.
- 주문당 공헌이익 = 부가세를 뺀 매출 − 수수료(결제가 기준) − 배송비. 원가는 고정비에
  들어 있으므로 여기서 빼지 않는다.
- 개당 평균 공헌이익 = 구성별 개당 공헌이익을 수량 비중으로 평균.
- BEP = 고정비 ÷ 개당 평균 공헌이익(올림). 초도 소진율 = BEP ÷ 초도 물량.
- 완판 시 이익 = 초도 × 개당 평균 공헌이익 − 고정비.
- 재발주부터 개당 이익 = 개당 평균 공헌이익 − 개당 원가.

예시 값(테스트로 고정): `example.json`은 고정비 120,500,000원, BEP 24,171개(80.6%), 완판
시 이익 29,063,636원. `example.aggressive.json`은 104,000,000원, 21,393개(71.3%),
41,843,636원.

파일을 고치지 않는 what-if:

```bash
python3 "${CLAUDE_SKILL_DIR}/cosmetic_economics.py" cosmetic/<슬러그>/numbers.json --unit-cost 3300
python3 "${CLAUDE_SKILL_DIR}/cosmetic_economics.py" cosmetic/<슬러그>/numbers.json --commission 0.10
python3 "${CLAUDE_SKILL_DIR}/cosmetic_economics.py" cosmetic/<슬러그>/numbers.json --price-factor 0.9 --initial 20000
```

보고서의 what-if 표: 판매가 −10%, 개당 원가 +10%, 수수료 +5%p, 배송비 +500원. 경고:
주문마다 손해인 구성, BEP 없음, BEP가 초도보다 큼, 재발주부터 손해.

## Step 3: CFO 메모

`cfo.md` 맨 위에 짧게, 쉬운 말로:

- **마진:** BEP와 소진율, 완판 시 이익, 재발주부터 개당 이익.
- **가장 민감한 줄:** 결과를 가장 크게 움직이는 가정(보통 수수료, 배송비, 구성 믹스),
  그걸 보여 주는 what-if.
- **마진을 올릴 방법 세 가지:** 각각 바꾸는 숫자와 결과(what-if를 돌려서, 짐작 말고).
- **확인할 견적:** 아직 추정인 줄과 누구에게 받을지.

## 규칙

- 메모의 모든 숫자는 도구 출력이나 이름 붙일 수 있는 입력에서 온다.
- **공식 숫자는 브랜드 기준만** 쓴다. 충진·제조비가 사내 제조 매출이 되더라도 BEP에는
  원가로 넣고, 공장 가동·제조 매출 효과는 "마진이 얇아도 추진하는 이유"로 따로 적는다.
- 실제 원가, 견적, 공급사, 수수료 계약은 내부용이다. 공개 저장소나 외부 문서에 넣지 않는다.
- 세무·회계 자문이 아니다. 부가세 처리와 채널 정산은 회계 담당이 확인한다고 한 번 말한다.

## 출력

`cosmetic/<슬러그>/numbers.json`, `cfo.md`, `cfo-sources.md`. 다음: `/cosmetic-plan`이
판정에 이 숫자를 쓴다. 마진이 얇으면 `/cosmetic-pricing`이나 `/cosmetic-formula`(목표 원가).
