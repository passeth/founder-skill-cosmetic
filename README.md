# 화장품 기획용 cosmetic-* 스킬

이 포크는 원본 Founder skill(아래, 영문) 11개를 그대로 두고, 화장품 상품기획용 스킬 10개를
`skills/cosmetic-*`로 더한 것이다. 쓰는 사람은 화장품 OEM·ODM과 자체 브랜드를 함께 하는
회사의 내부 상품기획 팀과 그 팀의 Claude 에이전트다. 고객용이 아니다.

## 흐름

```
intake -> competitors -> consumer -> pricing -> cfo -> formula -> claims -> brand -> marketing -> plan
```

각 스킬은 프로젝트 폴더 `cosmetic/<프로젝트-슬러그>/`에 결과를 쓰고 서로 읽는다. 프로젝트가
여럿이어도 된다. 어느 스킬이든 단독으로 돌릴 수 있다. 앞 파일이 없으면 없다고 말하고, 빈칸을
짐작으로 채우지 않는다.

| 명령 | 하는 일 | 쓰는 파일 |
| --- | --- | --- |
| `/cosmetic-intake` | 전시장·매장 메모, 사진, 전성분, 명함을 기획 시작 파일로. 읽은 것과 추측을 구분 | `brief.md` |
| `/cosmetic-competitors` | 용량 구간별 경쟁 제품, 100ml당 가격, USP 지도, 카피 패턴, 빈자리. 숫자마다 source·as_of | `competitors.csv`, `competitors.md` |
| `/cosmetic-consumer` | 피부 타입·고민·구매 채널·세일 성향이 들어간 구매자 카드로 시뮬레이션 패널. 피치는 상세페이지 첫 화면 | `customer.json`, `pitch.md`, `panel/` |
| `/cosmetic-pricing` | 정가·판매가·세일가, 단품·2개·1+1·기획세트, 100ml당 비교, 부가세 포함가 기준 | `pricing.md`, `pricing-curve.md` |
| `/cosmetic-cfo` | 내용물 원/g, 용기·펌프, 인쇄, 단상자, 충진으로 개당 원가. 구성별 공헌이익, BEP와 초도 소진율, 완판 시 이익, what-if | `numbers.json`, `cfo.md` |
| `/cosmetic-formula` | 출발 처방, 사내 보유 원료, 컨셉 원료, 목표 내용물 원가, 사용감·안정성 시험 항목. 처방 판단은 '랩 확인 필요' | `formula.md`, `ingredients.md` |
| `/cosmetic-claims` | 기능성, 효능 단정, 「N시간」「1위」「피부과 테스트」 같은 표현의 근거 체크리스트. 법률 판단 아님, RA로 넘김 | `claims.csv`, `claims.md` |
| `/cosmetic-brand` | 시리즈명·제품명·향명, 라인업 세계관, 카피 방향, KIPRIS 3류 상표 검색 안내, 패키지 디자인 브리프 | `brand.md`, `design-brief.md` |
| `/cosmetic-marketing` | 포지셔닝 한 줄, 올리브영·쿠팡·자사몰·인스타 시딩 채널, 훅 열 개. 점검을 통과한 표현만 | `marketing.md` |
| `/cosmetic-plan` | 상품기획서(컨셉, 개발 근거, 성분 리서치, 제형 기획, USP, 다음 단계)와 개발 의뢰서. 판정은 숫자로 계산: 추진 가능, 아직, 미완성 | `product-plan.md`, `dev-request.md` |

원본의 운영(ops), 출시(launch), 오퍼(offer), 보드(board)는 화장품판을 만들지 않았다.

## 공통 규칙

- 사실이 아닌 것을 만들지 않는다. 추정은 '가설', 모르는 것은 '확인 필요'. 숫자는 출처와 확인일.
- 경쟁사 문구를 베끼지 않는다. 효능, 1위, 근거 없는 수치를 만들지 않는다.
- 시뮬레이션 구매자의 답은 후기가 아니다. 가짜 후기·가짜 할인(판 적 없는 정가)은 없다.
- 처방·규제 판단은 추측하지 않고 '랩 확인 필요', 'RA 확인 필요'로 남긴다.
- 기획서, 의뢰서, `numbers.json`은 내부 문서다. 실제 원가·처방·공급사가 들어가므로 공개 저장소에
  커밋하지 않는다.

## beauty-data MCP가 있을 때와 없을 때

| | MCP 있음 | MCP 없음 |
| --- | --- | --- |
| 경쟁 제품 | 올리브영 랭킹(`rank_lists`, `rank_series`, `rank_movers`), 가격·전성분(`search_products`, `get_product`), 카피 집계와 원문(`copy_patterns`, `oy_copy`, `search_oy_copy`, `oy_ingredient_claims`), 성분 시장(`market_summary`) | 올리브영·쿠팡·자사몰 상품 페이지를 사람이 읽듯 읽고 링크와 확인일을 단다 |
| 전성분 | `analyze_inci_list`로 INCI·국문명, 기능성 고시 성분, 알러젠 플래그 | 공개 성분사전(CosIng, 대한화장품협회)에서 명칭 확인, 나머지는 RA 확인 |
| 제형 | `riselab_search_products`, `riselab_get_product_knowledge`, `riselab_base_formulas`로 출발 처방, `riselab_materials`로 보유 원료 | 랩에 출발 처방 추천 요청 |
| 원가 | 내부 기준가 참고(내부용) | 견적서와 단가표, 없으면 '추정' 표시 |

MCP 데이터(카피 원문, OCR, 처방, 공급사, 가격)는 내부용이다. 상세페이지, 광고, SNS, 보도자료에
옮기지 않는다. 스킬은 MCP가 없어도 끝까지 돈다.

## 설치

플러그인으로(Claude Code):

```
/plugin marketplace add passeth/founder-skill-cosmetic
/plugin install founder-skill@founder-skill
```

플러그인으로 설치하면 `/founder-skill:cosmetic-cfo`처럼 이름이 붙는다. 그냥 `/cosmetic-cfo`로
쓰려면 폴더를 복사한다. cosmetic 도구가 원본 도구 두 개(`founder-consumer/panel.py`,
`founder-pricing/van_westendorp.py`)를 불러 쓰므로 그 둘도 같이 복사한다.

```bash
git clone https://github.com/passeth/founder-skill-cosmetic.git
cp -r founder-skill-cosmetic/skills/cosmetic-* founder-skill-cosmetic/skills/founder-consumer founder-skill-cosmetic/skills/founder-pricing ~/.claude/skills/
```

## 도구

모두 표준 라이브러리 파이썬이고 네트워크를 쓰지 않는다.

```bash
python3 skills/cosmetic-cfo/cosmetic_economics.py cosmetic/<슬러그>/numbers.json --out cosmetic/<슬러그>/cfo.md
python3 skills/cosmetic-consumer/cosmetic_panel.py --dir cosmetic/<슬러그>/panel init --customer cosmetic/<슬러그>/customer.json --pitch cosmetic/<슬러그>/pitch.md
python3 skills/founder-pricing/van_westendorp.py cosmetic/<슬러그>/panel/answers --price 10900 --currency won
python3 skills/cosmetic-plan/compile_plan.py --dir cosmetic/<슬러그>
```

예시 `skills/cosmetic-cfo/example.json`(가상 예시 솔트브리즈 1L 퍼퓸 바디워시, 원가 3,850원,
단품 10,900원·2개 16,900원 반반, 수수료 20%, 배송비 2,500원, 초도 30,000개, 인플루언서
5,000,000원)은 고정비 120,500,000원, BEP 24,171개(초도 소진율 80.6%), 완판 시 이익 29,063,636원을
낸다. `example.aggressive.json`(원가 3,300원, 단품 20%·2개 50%·3향 세트 23,900원 30%)은
104,000,000원, 21,393개(71.3%), 41,843,636원. 두 결과는 테스트로 고정돼 있다.

---

# The Founder skill

Eleven Claude skills that test a business before you launch it. Free, MIT, no
signup, no API key, nothing to connect.

`skills/founder-board` `skills/founder-marketing` `skills/founder-cfo`
`skills/founder-consumer` `skills/founder-launch` `skills/founder-pricing`
`skills/founder-offer` `skills/founder-competitors` `skills/founder-brand`
`skills/founder-ops` `skills/founder-plan`

One of them is your board of directors, trained on the frameworks of Alex
Hormozi, Peter Thiel and Steve Jobs. One is your marketing director. One is your
CFO and finds your real profit margins. And one is the consumer panel: it spins
up 100 buyer agents trained on your target customer and runs your business
through 100 buyer scenarios.

So you know how to launch, how to market and how to actually make money, before
you spend thousands of dollars finding out the hard way.

## Install

Paste this repo link into Claude and say `install skill`:

```
https://github.com/Jakeschincariol/founder-skill

install skill
```

Or as a plugin, in Claude Code:

```
/plugin marketplace add Jakeschincariol/founder-skill
/plugin install founder-skill@founder-skill
```

Claude Code namespaces plugin skills, so installed as a plugin they show up as
`/founder-skill:founder-board` and so on. Copy the folders instead if you want
plain `/founder-board`:

```bash
git clone https://github.com/Jakeschincariol/founder-skill.git
cp -r founder-skill/skills/founder-* ~/.claude/skills/
```

Project-local instead of global: copy the same folders into your repo's
`.claude/skills/`. No Claude Code at all? Paste any single `SKILL.md` at the top
of a chat and it runs as a mode. You lose the sub-agents and the Python tools,
but the method works.

The tools need Python 3.8 or newer. Nothing to pip install.

## The eleven

| command | job | what it does |
| --- | --- | --- |
| `/founder-board` | Board of Directors | Three board members, each a sub-agent applying one published framework (Offers, from *$100M Offers*; Monopoly, from *Zero to One*; Product, from Isaacson's *Steve Jobs*), score the idea, name what would kill it and vote. |
| `/founder-competitors` | Competitor Scout | Maps direct competitors, indirect ones and substitutes from public sources, with prices, positioning and what their customers complain about, every fact linked. |
| `/founder-consumer` | Consumer Panel | Spins up a swarm of buyer agents (100 by default) from your target customer, each with its own income, habits and objection, and tallies who buys, who doesn't and why. |
| `/founder-pricing` | Pricing Strategist | Turns the panel's price answers into an acceptable price range, sets it against competitors and your margin, and picks what to test. |
| `/founder-offer` | Offer Architect | Builds the offer stack (bonuses, guarantee, real urgency, a name) that answers the panel's objections, then re-tests it on the panel. |
| `/founder-cfo` | CFO | Unit economics: contribution per sale, the real profit margin, break-even per day, year 1 month by month, cash needed, payback, what-ifs. |
| `/founder-marketing` | Marketing Director | Positioning, the channels your buyers use, a dated 30-day launch campaign, ten hooks and the most you can pay for a customer. |
| `/founder-brand` | Brand Designer | Name candidates with the trademark, domain and handle checks to run, a voice, a promise and a brief for the look. |
| `/founder-ops` | Operations Manager | Suppliers, staffing, day-one routines, tools, the permits to check and a risk register, feeding real costs back to the CFO. |
| `/founder-launch` | Launch Lead | A cheap real-world test first, then a dated countdown, the launch-day run sheet and the first 30 days. |
| `/founder-plan` | Business Planner | Compiles everything into one business plan with a verdict computed from the numbers: Profitable, Not yet or Incomplete. |

## How to use it

Run them in this order. Each one reads what the others wrote, in a `founder/`
folder in your project.

```
board -> competitors -> consumer -> pricing -> offer -> cfo -> marketing -> brand -> ops -> launch -> plan
```

An example: a matcha café in Toronto, iced matcha lattes at $6.50 a cup. (Every
input is in the example files in this repo, so you can run the tools on it.)

1. **`/founder-board`** writes `founder/idea.md` from what you told it and puts it
   in front of three board members. Each scores it, lists the risks and votes:
   fund, fund if, or pass. The conditions become a checklist for the rest.
2. **`/founder-competitors`** maps the matcha bars and coffee shops within walking
   distance, what they charge for a latte and what their reviews complain about.
3. **`/founder-consumer`** builds the target customer (urban professionals, 24 to
   38, who buy coffee most days), deals 100 buyer cards across income, habits and
   objections, and runs one sub-agent per buyer. Back comes who buys, who passes,
   the reasons in their words ("my coffee place is closer", "$6.50 is steep for a
   drink") and what would flip a no.
4. **`/founder-pricing`** reads the panel's four price answers per buyer into a
   price range and checks $6.50 against it and against the competitors.
5. **`/founder-offer`** answers the top objections with the offer (a launch-week
   price, a loyalty card) and re-runs a quick panel to see if the buy rate moves.
6. **`/founder-cfo`** runs the unit economics. With the example numbers: each cup
   leaves $4.76 after its own costs, break-even is 186 cups a day, the profit
   margin at the planned 383 cups a day is 38%, year 1 makes $93,926 on operations
   after a slow ramp, the $25,280 startup spend is earned back in month 8, and the
   founder needs $34,092 in cash before it pays for itself.
7. **`/founder-marketing`**, **`/founder-brand`**, **`/founder-ops`** and
   **`/founder-launch`** turn it into a 30-day campaign, a name and a look, the
   suppliers and routines, and a dated launch that starts with a pop-up to test
   real buyers.
8. **`/founder-plan`** compiles `founder/business-plan.md`. Its verdict is
   computed, not written: Profitable only if every unit earns money, year 1 makes
   a profit, break-even fits capacity and enough of the panel buys.

You can also run any one on its own. `/founder-consumer --quick` on an idea you
are only thinking about is a good way to find out if you should.

## The tools

Four of them, all standard-library Python. None touch the network.

```bash
python3 skills/founder-cfo/unit_economics.py founder/numbers.json --out founder/cfo.md   # margins, break-even, year 1
python3 skills/founder-consumer/panel.py init --customer founder/customer.json --pitch founder/pitch.md
python3 skills/founder-pricing/van_westendorp.py founder/panel/answers --price 6.50       # the acceptable price range
python3 skills/founder-plan/compile.py --dir founder                                     # the plan and its verdict
```

**`unit_economics.py`** reads one JSON (example: `skills/founder-cfo/example.json`)
and reports contribution, break-even, the margin at plan, year 1 by month, cash
needed, payback and three what-ifs. Every number traces to an input; a missing
field is an error, never a guess.

**`panel.py`** deals persona cards from your target customer (same seed, same
cards), writes one brief per buyer, checks the answers and tallies them. It never
answers for a buyer.

**`van_westendorp.py`** reads four price answers per buyer (from the panel, or a
CSV from a real survey) and finds the points of marginal cheapness and
expensiveness, the optimal and the indifference price.

**`compile.py`** assembles the plan and computes the verdict.

```bash
python3 -m unittest discover -s tests -v
```

## Fine print

**The board applies published frameworks. It is not those people.** The three
lenses are short summaries, in our words, of ideas from *$100M Offers* by Alex
Hormozi, *Zero to One* by Peter Thiel with Blake Masters, and Walter Isaacson's
biography of Steve Jobs. The board never speaks as them, quotes them or claims
they endorse anything. This project is not affiliated with any of them.

**The consumer panel is simulated buyers, not customers.** It is a fast, cheap way
to find objections, segments and wording before you spend. It is not a forecast:
language models lean agreeable, so read the buy rate as an upper bound, and
confirm the big calls with real people. `/founder-launch` starts with exactly that
test. Panel answers are research; never use them as testimonials.

**The numbers are only as good as the inputs.** The CFO marks every estimate as an
estimate and asks for real quotes. Check costs with suppliers and the structure,
payroll and tax with an accountant.

**Research uses public sources, with links.** No invented competitors, prices,
reviews or quotes. No scraping against a site's terms.

**Not financial, legal or tax advice.** Permits, trademarks and claims depend on
where you are. The skills tell you what to check and where; a professional
confirms it.

## Files

```
skills/founder-board/        SKILL.md, lenses.md
skills/founder-competitors/  SKILL.md
skills/founder-consumer/     SKILL.md, panel.py, customer.example.json, pitch.example.md
skills/founder-pricing/      SKILL.md, van_westendorp.py
skills/founder-offer/        SKILL.md
skills/founder-cfo/          SKILL.md, unit_economics.py, example.json
skills/founder-marketing/    SKILL.md
skills/founder-brand/        SKILL.md
skills/founder-ops/          SKILL.md
skills/founder-launch/       SKILL.md
skills/founder-plan/         SKILL.md, compile.py
skills/cosmetic-intake/      SKILL.md
skills/cosmetic-competitors/ SKILL.md
skills/cosmetic-consumer/    SKILL.md, cosmetic_panel.py, customer.example.json, pitch.example.md
skills/cosmetic-pricing/     SKILL.md
skills/cosmetic-cfo/         SKILL.md, cosmetic_economics.py, example.json, example.aggressive.json
skills/cosmetic-formula/     SKILL.md
skills/cosmetic-claims/      SKILL.md
skills/cosmetic-brand/       SKILL.md
skills/cosmetic-marketing/   SKILL.md
skills/cosmetic-plan/        SKILL.md, compile_plan.py
tests/                       the tests for every tool
```

Your own files live in `founder/` in your project. The skills read each other's.

## Credit

Made by Jake Schincariol, [opusjake.ai](https://opusjake.ai). Siblings:
[Arena](https://github.com/Jakeschincariol/arena-skill),
[Replica](https://github.com/Jakeschincariol/replica-skill),
[X](https://github.com/Jakeschincariol/x-agent-skill),
[LinkedIn](https://github.com/Jakeschincariol/linkedin-agent-skill),
[Instagram](https://github.com/Jakeschincariol/instagram-agent-skill).

## License

MIT. Take it, change it, ship it.
