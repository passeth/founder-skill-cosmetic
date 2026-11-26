#!/usr/bin/env python3
"""화장품 구매자 패널 (cosmetic-consumer). Standard library only, no network.

Built on founder-consumer's panel.py (same dealing, same seed rule, same answer
files, so van_westendorp.py reads them unchanged). It adds what a cosmetics buyer
card needs: skin type, skin concern, the channel they buy from (Olive Young,
Coupang, brand mall...) and how they wait for sales. Briefs are in Korean and
the pitch is the first screen of a product detail page.

    python3 cosmetic_panel.py --dir cosmetic/<slug>/panel init --customer cosmetic/<slug>/customer.json --pitch cosmetic/<slug>/pitch.md [--n 100] [--seed 7]
    python3 cosmetic_panel.py --dir cosmetic/<slug>/panel prompts [--wave 10]
    python3 cosmetic_panel.py --dir cosmetic/<slug>/panel check
    python3 cosmetic_panel.py --dir cosmetic/<slug>/panel save P003 < reply.txt
    python3 cosmetic_panel.py --dir cosmetic/<slug>/panel tally
    python3 cosmetic_panel.py --dir cosmetic/<slug>/panel status

--dir is required: there can be several projects. The tool never answers for a
buyer. Simulated buyers are not customers, and their answers are never reviews.
"""

import argparse
import importlib.util
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_base():
    path = os.path.join(HERE, "..", "founder-consumer", "panel.py")
    spec = importlib.util.spec_from_file_location("founder_panel_base", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


base = _load_base()
PanelError = base.PanelError

NAMES = [
    "서연", "지민", "하은", "민준", "수아", "도윤", "지우", "예린", "서준", "유나", "채원", "현우", "다은", "지호", "소윤",
    "은서", "시우", "가은", "준서", "윤아", "하린", "건우", "나연", "주원", "서영", "민서", "예준", "지아", "수빈", "태윤",
    "혜원", "승민", "다인", "우진", "아린", "지환", "보람", "연우", "세아", "동현", "소희", "재윤", "하율", "정민", "유진",
    "선우", "미정", "은우", "수진", "영훈", "초아", "민재", "예나", "성민", "지유", "태민", "해나", "규리", "도현", "라희",
    "진영", "서우", "슬기", "한결", "윤서", "시은", "재희", "나윤", "현서", "보은", "주아", "형준", "다희", "이안", "새봄",
    "은지", "승우", "하람", "채은", "민혁", "소율", "재민", "가윤", "지성", "예서", "윤호", "다현", "유리", "로운", "아영",
    "경민", "서하", "준영", "미소", "인서", "한나", "도경", "수안", "지후", "봄이",
]
REASONS = ["price", "habit", "need", "trust", "quality", "convenience", "timing", "values",
           "scent", "texture", "skin_fit", "ingredients", "design", "volume", "other"]
REASON_KO = {"price": "가격", "habit": "쓰던 것", "need": "필요 없음/필요함", "trust": "신뢰", "quality": "품질",
             "convenience": "편의", "timing": "시기", "values": "가치관", "scent": "향", "texture": "사용감",
             "skin_fit": "피부에 맞나", "ingredients": "성분", "design": "디자인", "volume": "용량", "other": "기타"}
EXTRA = ("skin_types", "concerns", "channels", "sale_waiting")


def validate_customer(c):
    base.validate_customer(c)
    for k in EXTRA:
        items = c.get(k)
        if not items:
            raise PanelError("customer.json needs '%s' (a list of {name, share})" % k)
        for it in items:
            if not isinstance(it, dict) or "name" not in it:
                raise PanelError("every item in '%s' needs a name" % k)


def deal(customer, n=100, seed=7):
    """founder-consumer's cards plus skin type, concern, channel and sale habit. Same inputs, same cards."""
    validate_customer(customer)
    cards = base.deal(customer, n, seed)
    rng = random.Random("%s-cosmetic" % seed)
    columns = {}
    for k in EXTRA:
        col = []
        for it, cnt in zip(customer[k], base._quota(customer[k], n)):
            col += [it] * cnt
        rng.shuffle(col)
        columns[k] = col
    names = NAMES[:]
    rng.shuffle(names)
    while len(names) < n:
        names += ["%s%d" % (x, len(names) // len(NAMES) + 1) for x in NAMES]
    for i, c in enumerate(cards):
        c["name"] = names[i]
        c["skin_type"] = columns["skin_types"][i]["name"]
        c["concern"] = columns["concerns"][i]["name"]
        c["channel"] = columns["channels"][i]["name"]
        c["channel_how"] = columns["channels"][i].get("how", "")
        c["sale_waiting"] = columns["sale_waiting"][i]["name"]
    return cards


def init(d, customer_path, pitch_path, n=100, seed=None):
    try:
        customer = base._read_json(customer_path)
    except FileNotFoundError:
        raise PanelError("no such file: %s" % customer_path)
    try:
        with open(pitch_path, encoding="utf-8") as fh:
            pitch = fh.read().strip()
    except FileNotFoundError:
        raise PanelError("no such file: %s (상세페이지 첫 화면을 먼저 쓰세요)" % pitch_path)
    if not pitch:
        raise PanelError("the pitch is empty")
    if seed is None:
        seed = random.SystemRandom().randrange(1, 10 ** 6)
    cards = deal(customer, n, seed)
    base._write_json(os.path.join(d, "panel.json"), {"n": n, "seed": seed, "customer": customer, "pitch": pitch,
                                                     "kind": "cosmetic"})
    base._write_json(os.path.join(d, "personas.json"), cards)
    os.makedirs(os.path.join(d, "briefs"), exist_ok=True)
    os.makedirs(os.path.join(d, "answers"), exist_ok=True)
    return cards


BRIEF = """당신은 소비자 패널의 시뮬레이션 구매자예요. 화장품 기획팀이 돈을 쓰기 전에, 당신 같은 사람이 이 제품을 살지 알고 싶어 해요. 정직해야 쓸모가 있어요. 사람들은 대부분 대부분의 물건을 사지 않아요. 예의상 "살게요"보다 분명한 "안 사요"가 더 쓸모 있어요.

=== 당신은 ===
{name}, {age}세. {segment}. 연소득 약 {income_man:,}만원.
피부: {skin_type}. 요즘 가장 신경 쓰는 고민: {concern}.
주로 사는 곳: {channel}. {channel_how}
세일: {sale_waiting}.
사는 방식: {behaviour}. {behaviour_how}
{habit_line}이런 제품을 보면 먼저 드는 생각: "{objection}"
당신은 이런 사람들 중 하나예요: {target}.
=== 끝 ===

=== 처음 보는 상세페이지 첫 화면 (스크롤하다 멈춘 그 화면) ===
{pitch}
=== 끝 ===

{name}의 돈, 피부, 습관, 의심으로 평범한 한 주에 결정하세요. 맞춰 주지 마세요. 위에 적힌 것 말고 제품에 대한 사실(효능, 성분, 후기, 순위)을 지어내지 마세요.

파일 쓰기 도구로 {out} 파일을 만드세요(답을 말로만 하지 마세요). 내용은 아래 JSON만, 마크다운 펜스 없이:
{{
  "id": "{id}",
  "buys": true 또는 false,
  "purchases_first_month": 첫 달에 몇 번 살지 (안 사면 0),
  "reason_code": {reasons} 중 하나,
  "reason": "왜인지, 한두 문장, 당신 말투로",
  "objection": "가장 걸리는 점, 당신 말로",
  "would_change_my_mind": "답을 바꿀 한 가지, 없으면 빈 문자열",
  "where_buy": "산다면 어디서 살지 (올리브영, 쿠팡, 자사몰 등), 안 사면 빈 문자열",
  "wait_for_sale": true 또는 false (세일까지 기다렸다 살지),
  "price_too_cheap": 너무 싸서 품질이 의심되는 가격 (원, 숫자),
  "price_cheap": 싸다고 느끼는 가격 (원, 숫자),
  "price_expensive": 비싸다고 느끼지만 살 수도 있는 가격 (원, 숫자),
  "price_too_expensive": 절대 안 사는 가격 (원, 숫자)
}}
"""


def write_briefs(d, wave=base.WAVE):
    state, cards = base.load_state(d)
    target = state["customer"]["target"]
    todo = []
    for c in cards:
        out = os.path.join(d, "answers", c["id"] + ".json")
        if answer_ok(out, c["id"]) is None:
            continue
        brief = BRIEF.format(pitch=state["pitch"], target=target, out=os.path.abspath(out),
                             habit_line=("일상: %s.\n" % c["habit"]) if c.get("habit") else "",
                             income_man=int(round(c["income"] / 10000.0)),
                             reasons=" / ".join(REASONS), **c)
        bp = os.path.join(d, "briefs", c["id"] + ".md")
        with open(bp, "w", encoding="utf-8") as fh:
            fh.write(brief)
        todo.append((c["id"], os.path.abspath(bp)))
    return [todo[i:i + wave] for i in range(0, len(todo), wave)]


def answer_ok(path, pid):
    """None if the answer file is good, else a short problem string."""
    if not os.path.exists(path):
        return "missing"
    try:
        a = base._read_json(path)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return "not valid JSON"
    if not isinstance(a, dict):
        return "not a JSON object"
    missing = base.ANSWER_FIELDS - set(a)
    if missing:
        return "missing " + ", ".join(sorted(missing))
    if a.get("id") != pid:
        return "id is %r, expected %s" % (a.get("id"), pid)
    if not isinstance(a.get("buys"), bool):
        return "'buys' must be true or false"
    if a.get("reason_code") not in REASONS:
        return "reason_code %r is not one of %s" % (a.get("reason_code"), ", ".join(REASONS))
    return None


def check(d):
    _, cards = base.load_state(d)
    probs = []
    for c in cards:
        p = answer_ok(os.path.join(d, "answers", c["id"] + ".json"), c["id"])
        if p:
            probs.append((c["id"], p))
    return probs


def save(d, pid, text):
    """File a buyer's OWN answer that it printed instead of writing. Never used to answer for a buyer."""
    _, cards = base.load_state(d)
    if pid not in {c["id"] for c in cards}:
        raise PanelError("no buyer %s on this panel" % pid)
    start = text.find("{")
    if start < 0:
        raise PanelError("no JSON object in the reply")
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError as e:
        raise PanelError("the reply's JSON does not parse: %s" % e)
    path = os.path.join(d, "answers", pid + ".json")
    base._write_json(path, obj)
    prob = answer_ok(path, pid)
    if prob:
        os.remove(path)
        raise PanelError("%s's answer is not valid (%s); re-run its brief instead" % (pid, prob))
    return path


def tally(d):
    state, cards = base.load_state(d)
    rows, skipped = [], []
    for c in cards:
        path = os.path.join(d, "answers", c["id"] + ".json")
        p = answer_ok(path, c["id"])
        if p:
            skipped.append((c["id"], p))
            continue
        a = base._read_json(path)
        rows.append(dict(c, **{k: v for k, v in a.items() if k != "id"}, id=c["id"]))
    if not rows:
        raise PanelError("no valid answers yet: run the briefs first (cosmetic_panel.py prompts)")

    def rate(rs):
        return sum(1 for r in rs if r["buys"]) / float(len(rs)) if rs else 0.0

    def group(key):
        out = {}
        for r in rows:
            out.setdefault(r.get(key) or "(none)", []).append(r)
        return sorted(((k, len(v), rate(v)) for k, v in out.items()), key=lambda t: (-t[2], -t[1], t[0]))

    def reasons(rs):
        out = {}
        for r in rs:
            out.setdefault(r["reason_code"], []).append(r)
        ranked = sorted(out.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        return [(k, len(v), [x["reason"] for x in v[:2]], [x["id"] for x in v[:2]]) for k, v in ranked]

    yes = [r for r in rows if r["buys"]]
    no = [r for r in rows if not r["buys"]]
    waits = [r for r in yes if r.get("wait_for_sale") is True]
    where = {}
    for r in yes:
        w = (r.get("where_buy") or "").strip()
        if w:
            where[w] = where.get(w, 0) + 1
    firsts = [base._num(r.get("purchases_first_month")) for r in yes]
    firsts = [v for v in firsts if v is not None]
    return {
        "business": state["customer"]["business"], "seed": state["seed"], "dealt": len(cards),
        "answered": len(rows), "skipped": skipped, "buys": len(yes), "passes": len(no),
        "buy_rate": len(yes) / float(len(rows)),
        "by_segment": group("segment"), "by_skin_type": group("skin_type"), "by_concern": group("concern"),
        "by_channel": group("channel"), "by_sale_waiting": group("sale_waiting"), "by_behaviour": group("behaviour"),
        "why_not": reasons(no), "why_yes": reasons(yes),
        "flip": [r["would_change_my_mind"] for r in no if (r.get("would_change_my_mind") or "").strip()],
        "wait_for_sale": len(waits), "where_buy": sorted(where.items(), key=lambda kv: (-kv[1], kv[0])),
        "purchases_first_month_per_buyer": (sum(firsts) / len(firsts)) if firsts else None,
        "price_answers": sum(1 for r in rows if all(base._num(r.get(k)) is not None for k in
                                                     ("price_too_cheap", "price_cheap", "price_expensive", "price_too_expensive"))),
    }


def results_md(res):
    pct = lambda v: "%.0f%%" % (v * 100)
    L = ["# 구매자 패널: %s" % res["business"], ""]
    L.append("**%d명 구매 · %d명 안 삼** (구매율 %s), 응답 %d명. 시드 %s라 같은 카드를 다시 뽑을 수 있어요."
             % (res["buys"], res["passes"], pct(res["buy_rate"]), res["answered"], res["seed"]))
    if res["skipped"]:
        L += ["", "유효한 답이 없는 %d명(전체 %d명)은 빠졌어요: %s." % (
            len(res["skipped"]), res["dealt"], ", ".join("%s (%s)" % s for s in res["skipped"][:10]))]
    L += ["", "시뮬레이션 구매자이지 고객이 아니에요. 구매율은 상한으로 읽고, 반대 이유와 말을 찾는 데 쓰세요."
              " 패널 답은 후기·추천사로 쓰지 않아요."]
    for title, key in (("세그먼트별", "by_segment"), ("피부 타입별", "by_skin_type"), ("피부 고민별", "by_concern"),
                       ("구매 채널별", "by_channel"), ("세일 성향별", "by_sale_waiting"), ("구매 방식별", "by_behaviour")):
        L += ["", "## %s" % title, "", "| 그룹 | 인원 | 구매율 |", "| --- | ---: | ---: |"]
        for k, n, r in res[key]:
            L.append("| %s | %d | %s%s |" % (k, n, pct(r), "  (표본 적음)" if n < 8 else ""))
    for title, key in (("안 사는 이유", "why_not"), ("사는 이유", "why_yes")):
        L += ["", "## %s" % title, "", "| 이유 | 인원 | 그들의 말 |", "| --- | ---: | --- |"]
        for k, n, quotes, ids in res[key]:
            L.append("| %s | %d | %s |" % (REASON_KO.get(k, k), n, " · ".join(
                '"%s" (%s)' % (q.replace("|", "/"), i) for q, i in zip(quotes, ids))))
    if res["flip"]:
        L += ["", "## 안 산다를 바꿀 것", ""]
        L += ["- %s" % f for f in res["flip"][:12]]
    if res["buys"]:
        L += ["", "산다고 한 %d명 중 %d명은 세일까지 기다린다고 했어요." % (res["buys"], res["wait_for_sale"])]
    if res["where_buy"]:
        L += ["", "살 곳: %s." % ", ".join("%s %d명" % kv for kv in res["where_buy"][:6])]
    if res["purchases_first_month_per_buyer"] is not None:
        L += ["", "산다고 한 사람은 첫 달에 평균 **%.1f번** 산다고 했어요." % res["purchases_first_month_per_buyer"]]
    if res["price_answers"]:
        L += ["", "%d명이 가격 질문 네 개에 모두 답했어요. cosmetic-pricing에서 van_westendorp.py로 읽으세요." % res["price_answers"]]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dir", required=True, help="cosmetic/<slug>/panel")
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init")
    i.add_argument("--customer", required=True)
    i.add_argument("--pitch", required=True)
    i.add_argument("--n", type=int, default=100)
    i.add_argument("--seed", type=int)
    p = sub.add_parser("prompts")
    p.add_argument("--wave", type=int, default=base.WAVE)
    sub.add_parser("check")
    sv = sub.add_parser("save")
    sv.add_argument("id")
    t = sub.add_parser("tally")
    t.add_argument("--out")
    sub.add_parser("status")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "init":
            cards = init(a.dir, a.customer, a.pitch, a.n, a.seed)
            st, _ = base.load_state(a.dir)
            print("dealt %d buyers (seed %s) into %s. Next: cosmetic_panel.py --dir %s prompts" % (len(cards), st["seed"], a.dir, a.dir))
        elif a.cmd == "prompts":
            waves = write_briefs(a.dir, a.wave)
            n = sum(len(w) for w in waves)
            if not n:
                print("every buyer has a valid answer. Next: cosmetic_panel.py --dir %s tally" % a.dir)
            else:
                print("%d briefs in %d waves of up to %d. Launch one wave at a time:" % (n, len(waves), a.wave))
                for k, w in enumerate(waves, 1):
                    print("wave %d: %s" % (k, " ".join("%s=%s" % job for job in w)))
        elif a.cmd == "check":
            probs = check(a.dir)
            if not probs:
                print("all answers present and valid")
            for pid, prob in probs:
                print("%s: %s" % (pid, prob))
            return 1 if probs else 0
        elif a.cmd == "save":
            print("saved %s" % save(a.dir, a.id, sys.stdin.read()))
        elif a.cmd == "tally":
            res = tally(a.dir)
            out = a.out or os.path.join(a.dir, "results.md")
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(results_md(res))
            base._write_json(os.path.join(a.dir, "results.json"), res)
            print("%d buy · %d pass (%.0f%%). Wrote %s" % (res["buys"], res["passes"], res["buy_rate"] * 100, out))
        elif a.cmd == "status":
            st, cards = base.load_state(a.dir)
            probs = check(a.dir)
            print("%d buyers dealt (seed %s), %d answered, %d to go" % (len(cards), st["seed"], len(cards) - len(probs), len(probs)))
    except PanelError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
