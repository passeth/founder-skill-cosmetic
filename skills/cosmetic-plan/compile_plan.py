#!/usr/bin/env python3
"""상품기획서와 개발 의뢰서 컴파일 (cosmetic-plan). Standard library only, no network.

Reads what the other cosmetic-* skills wrote into one project folder
(cosmetic/<slug>/) and writes two documents:

    product-plan.md   상품기획서: verdict, key numbers, concept, evidence,
                      ingredient research, formula plan, USP, price and BEP,
                      claims check, brand, marketing, next steps
    dev-request.md    개발 의뢰서 for the lab: product, size, target costs,
                      formula plan, ingredients, claims limits, package brief

The verdict is computed, never written by hand:

    추진 가능   every check that has data passes
    아직       at least one check fails (each failure is listed with its number)
    미완성     there is no numbers.json yet (run cosmetic-cfo first)

The checks:
    1. every bundle earns money per order after VAT, commission and shipping
    2. the break-even quantity fits inside the first run (x --max-sell-through, default 1.0)
    3. each unit after the first run earns money (reorder profit per unit > 0)
    4. enough of the buyer panel buys (panel/results.json, --min-buy-rate, default 25%)
    5. no expression in claims.csv is still marked 근거 없음

    python3 compile_plan.py --dir cosmetic/<slug>
    python3 compile_plan.py --dir cosmetic/<slug> --check
    python3 compile_plan.py --dir cosmetic/<slug> --min-buy-rate 0.3 --max-sell-through 0.9
"""

import argparse
import csv
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

PLAN_SECTIONS = [  # (file in the project folder, heading, which skill writes it)
    ("summary.md", "요약", "cosmetic-plan"),
    ("concept.md", "1. 제품 컨셉", "cosmetic-plan"),
    ("competitors.md", "2. 개발 근거: 경쟁 제품", "cosmetic-competitors"),
    ("panel/results.md", "2. 개발 근거: 구매자 패널", "cosmetic-consumer"),
    ("ingredients.md", "3. 성분 리서치", "cosmetic-formula"),
    ("formula.md", "4. 제형 기획", "cosmetic-formula"),
    ("usp.md", "5. USP", "cosmetic-plan"),
    ("pricing.md", "6. 가격", "cosmetic-pricing"),
    ("cfo.md", "6. 원가와 BEP", "cosmetic-cfo"),
    ("claims.md", "7. 표시·광고 점검", "cosmetic-claims"),
    ("brand.md", "8. 브랜드와 패키지", "cosmetic-brand"),
    ("marketing.md", "9. 마케팅", "cosmetic-marketing"),
    ("next-steps.md", "10. 다음 단계", "cosmetic-plan"),
    ("brief.md", "부록: 출발 메모", "cosmetic-intake"),
]
REQUEST_SECTIONS = [
    ("formula.md", "제형 기획", "cosmetic-formula"),
    ("ingredients.md", "컨셉 원료와 성분", "cosmetic-formula"),
    ("claims.md", "표시·광고 제한", "cosmetic-claims"),
    ("design-brief.md", "패키지 디자인 브리프", "cosmetic-brand"),
]
OPEN_CLAIM = "근거 없음"
PENDING_CLAIM = "RA 확인 필요"


def _load_economics():
    path = os.path.join(HERE, "..", "cosmetic-cfo", "cosmetic_economics.py")
    spec = importlib.util.spec_from_file_location("cosmetic_economics", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ce = _load_economics()


def _read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    except FileNotFoundError:
        return None


def _strip_h1(text):
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(("#" + l) if l.startswith("#") else l for l in lines).strip()


def claims_status(d):
    """Counts of claims.csv rows by status, or None if there is no claims.csv."""
    path = os.path.join(d, "claims.csv")
    if not os.path.exists(path):
        return None
    counts = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            st = (row.get("status") or "").strip() or "(빈칸)"
            counts[st] = counts.get(st, 0) + 1
    return counts


def verdict(d, min_buy_rate=0.25, max_sell_through=1.0):
    """Return (verdict, checks, numbers, panel, claims). checks = [(ok, text)]."""
    checks = []
    numbers = panel = None
    raw = _read(os.path.join(d, "numbers.json"))
    if raw:
        numbers = ce.analyse(json.loads(raw))
        losing = [b for b in numbers["bundles"] if b["contribution_per_order"] <= 0]
        if losing:
            checks.append((False, "주문마다 손해인 구성: %s." % ", ".join(
                "%s %s" % (b["name"], ce.won(b["contribution_per_order"])) for b in losing)))
        else:
            checks.append((True, "모든 구성이 주문마다 남아요 (%s)." % ", ".join(
                "%s %s" % (b["name"], ce.won(b["contribution_per_order"])) for b in numbers["bundles"])))
        bep, st = numbers["bep_units"], numbers["sell_through"]
        if math.isinf(bep):
            checks.append((False, "BEP가 없어요: 개당 평균 공헌이익이 %s예요." % ce.won(numbers["avg_contribution_per_unit"])))
        else:
            checks.append((st <= max_sell_through, "BEP %s개, 초도 %s개의 %s (기준 %s 이하)." % (
                ce.count(bep), ce.count(numbers["initial_units"]), ce.pct(st), ce.pct(max_sell_through))))
        r = numbers["reorder_profit_per_unit"]
        checks.append((r > 0, "재발주부터 개당 이익 %s." % ce.won(r)))
    raw = _read(os.path.join(d, "panel", "results.json"))
    if raw:
        panel = json.loads(raw)
        rate = panel["buy_rate"]
        checks.append((rate >= min_buy_rate, "시뮬레이션 구매자 %d명 중 %d명 구매 (%.0f%%, 기준 %.0f%%)." % (
            panel["answered"], panel["buys"], rate * 100, min_buy_rate * 100)))
    claims = claims_status(d)
    if claims is not None:
        bad = claims.get(OPEN_CLAIM, 0)
        checks.append((bad == 0, "표시·광고: 근거 없이 남은 표현 %d건, RA 확인 대기 %d건." % (bad, claims.get(PENDING_CLAIM, 0))))
    if numbers is None:
        v = "미완성"
    elif all(ok for ok, _ in checks):
        v = "추진 가능"
    else:
        v = "아직"
    return v, checks, numbers, panel, claims


def _title(d, numbers):
    brief = _read(os.path.join(d, "brief.md"))
    if brief:
        first = brief.splitlines()[0]
        if first.startswith("# "):
            return first[2:].strip()
    if numbers and numbers.get("product"):
        return numbers["product"]
    return "신제품"


def _key_numbers(numbers, panel):
    L = ["| 핵심 숫자 | |", "| --- | ---: |", "| 개당 원가 | %s |" % ce.won(numbers["unit_cost"])]
    for b in numbers["bundles"]:
        L.append("| %s 판매가 (100ml당) | %s (%s) |" % (b["name"], ce.won(b["price"]), ce.won(b["price_per_100ml"])))
    bep = numbers["bep_units"]
    L += ["| 개당 평균 공헌이익 | %s |" % ce.won(numbers["avg_contribution_per_unit"]),
          "| 고정비 (초도 원가 + 일회성) | %s |" % ce.won(numbers["fixed"]),
          "| BEP (초도 소진율) | %s |" % ("없음" if math.isinf(bep) else "%s개 (%s)" % (ce.count(bep), ce.pct(numbers["sell_through"]))),
          "| 초도 %s개 완판 시 이익 | %s |" % (ce.count(numbers["initial_units"]), ce.won(numbers["full_sale_profit"])),
          "| 재발주부터 개당 이익 | %s |" % ce.won(numbers["reorder_profit_per_unit"])]
    if panel:
        L.append("| 구매자 패널 | %d명 구매 · %d명 안 삼 |" % (panel["buys"], panel["passes"]))
    return L


def _sections(d, sections):
    L, missing = [], []
    for fname, heading, skill in sections:
        text = _read(os.path.join(d, fname))
        if text:
            L += ["## %s" % heading, "", _strip_h1(text), ""]
        else:
            missing.append((heading, skill))
    return L, missing


def compile_plan(d, min_buy_rate=0.25, max_sell_through=1.0):
    v, checks, numbers, panel, claims = verdict(d, min_buy_rate, max_sell_through)
    title = _title(d, numbers)
    L = ["# %s · 상품기획서" % title, "", "> 내부용. 추정은 '가설', 모르는 것은 '확인 필요'. 숫자는 출처와 확인일이 있는 것만.", ""]
    L += ["**판정: %s**" % v, ""]
    L += ["- %s %s" % ("✓" if ok else "✗", text) for ok, text in checks]
    if v == "미완성":
        L.append("- 숫자가 아직 없어요. /cosmetic-cfo를 먼저 돌리고 다시 컴파일하세요.")
    L.append("")
    if numbers:
        L += _key_numbers(numbers, panel) + [""]
    body, missing = _sections(d, PLAN_SECTIONS)
    L += body
    if missing:
        L += ["## 아직 없는 것", ""]
        L += ["- %s: /%s" % m for m in missing]
        L.append("")
    L.append("_구매자 패널은 시뮬레이션이고 숫자는 입력값에서 나온 예측이에요. 실제 견적, 실제 판매, 랩 시험, RA 확인으로"
             " 굳히세요. 법률·세무 자문이 아니에요._")
    return v, "\n".join(L) + "\n"


def compile_request(d):
    raw = _read(os.path.join(d, "numbers.json"))
    numbers = ce.analyse(json.loads(raw)) if raw else None
    spec = json.loads(raw) if raw else None
    title = _title(d, numbers)
    L = ["# %s · 개발 의뢰서" % title, "",
         "> 내부용. 처방 %·공급사·원가는 밖으로 내보내지 않아요. 처방·규제 판단은 랩 확인 필요, RA 확인 필요로 남겨요.", ""]
    if numbers:
        content = spec["unit_cost"]["content"]
        L += ["| 항목 | 값 |", "| --- | --- |",
              "| 용량 | %sml |" % ce.count(numbers["size_ml"]),
              "| 내용물 목표 원가 | %s원/g (개당 %s) |" % (content["won_per_g"], ce.won(numbers["content_cost"])),
              "| 개당 목표 원가 합계 | %s |" % ce.won(numbers["unit_cost"]),
              "| 초도 물량 | %s개 |" % ce.count(numbers["initial_units"])]
        for it in spec["unit_cost"].get("items") or []:
            L.append("| %s | %s |" % (it.get("label", "부자재"), ce.won(float(it["cost"]))))
        L.append("")
    else:
        L += ["- 목표 원가가 아직 없어요: /cosmetic-cfo", ""]
    body, missing = _sections(d, REQUEST_SECTIONS)
    L += body
    if missing:
        L += ["## 아직 없는 것", ""]
        L += ["- %s: /%s" % m for m in missing]
        L.append("")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dir", required=True, help="the project folder, cosmetic/<slug>")
    ap.add_argument("--min-buy-rate", type=float, default=0.25)
    ap.add_argument("--max-sell-through", type=float, default=1.0)
    ap.add_argument("--check", action="store_true", help="print the verdict only; exit 0 if 추진 가능")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.dir):
        print("error: no %s/ folder. Run /cosmetic-intake first." % a.dir, file=sys.stderr)
        return 2
    try:
        v, plan = compile_plan(a.dir, a.min_buy_rate, a.max_sell_through)
        request = compile_request(a.dir)
        _, checks, _, _, _ = verdict(a.dir, a.min_buy_rate, a.max_sell_through)
    except ce.NumbersError as e:
        print("error: numbers.json: %s" % e, file=sys.stderr)
        return 2
    if a.check:
        print("판정: %s" % v)
        for ok, t in checks:
            print("  %s %s" % ("✓" if ok else "✗", t))
        return 0 if v == "추진 가능" else 1
    for name, text in (("product-plan.md", plan), ("dev-request.md", request)):
        with open(os.path.join(a.dir, name), "w", encoding="utf-8") as fh:
            fh.write(text)
    print("판정: %s. Wrote %s and %s" % (v, os.path.join(a.dir, "product-plan.md"), os.path.join(a.dir, "dev-request.md")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
