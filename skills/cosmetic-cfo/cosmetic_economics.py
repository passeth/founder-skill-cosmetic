#!/usr/bin/env python3
"""화장품 원가와 BEP (cosmetic-cfo). Standard library only, no network.

Reads one JSON file that describes a cosmetic product launch and reports the
numbers a planner checks before an order goes to the factory: the cost of one
unit, what each bundle (단품, 2개 구성, 세트) leaves per order after VAT, the
channel commission and shipping, the average contribution per unit for the
planned mix, the break-even quantity against the first production run, the
profit if the whole run sells, and what-ifs.

    python3 cosmetic_economics.py cosmetic/<slug>/numbers.json
    python3 cosmetic_economics.py cosmetic/<slug>/numbers.json --out cosmetic/<slug>/cfo.md
    python3 cosmetic_economics.py cosmetic/<slug>/numbers.json --json
    python3 cosmetic_economics.py numbers.json --unit-cost 3300 --commission 0.10 --price-factor 0.9

The model (brand view, the way the planning team calculates it):

    unit cost        content (won per g x grams) + packaging items
                     (container and pump, print or label, carton, filling)
    fixed cost       initial_units x unit cost + one_off (influencers, design...)
                     The first run is paid for up front, so it is a fixed cost.
    per order        net revenue - commission - shipping
                     net revenue = price / (1 + vat_rate) when vat_included,
                     else the price as given. Commission is charged on the price
                     the customer pays (the price field).
    per unit         per order / units_per_order, averaged over the mix
    BEP              ceil(fixed / average contribution per unit)
    sell-through     BEP / initial_units
    full sale        initial_units x average contribution - fixed
    reorder          average contribution - unit cost (each unit after the first
                     run has to buy its own cost)

The input (see example.json in this folder):

    product            name, for the report
    size_ml            volume of one unit in ml, for the price per 100 ml
    unit_cost          {content: {won_per_g, grams}, items: [{label, cost}]}
    vat_included       true if the prices include VAT (Korean retail prices do)
    vat_rate           optional, default 0.10 (Korean VAT)
    commission_rate    channel commission, 0.20 = 20 percent
    shipping_per_order shipping paid by the brand per order (free shipping)
    bundles            [{name, units_per_order, price, unit_share or order_share,
                         shipping_per_order (optional override)}]
                       Shares are by units sold (unit_share) or by orders
                       (order_share), one kind for all bundles, summing to 1.
    initial_units      the first production run (초도 물량)
    one_off            [{label, cost}] one-off spend: influencers, design, molds

Any field may carry a "source" and "as_of" string; they are printed next to the
number. Every number in the report comes from the file. A missing field is an
error, never a guess.
"""

import argparse
import json
import math
import sys

DEFAULT_VAT = 0.10


class NumbersError(Exception):
    pass


def won(v):
    sign = "-" if v < 0 else ""
    return "%s%s원" % (sign, "{:,.0f}".format(abs(round(v))))


def count(v):
    return "{:,.0f}".format(v)


def pct(v):
    return "%.1f%%" % (v * 100)


def _need(d, key, where):
    if not isinstance(d, dict) or key not in d or d[key] in (None, ""):
        raise NumbersError("'%s' is missing%s" % (key, (" in " + where) if where else ""))
    return d[key]


def _num(v, where):
    if isinstance(v, bool):
        raise NumbersError("%s is not a number: %r" % (where, v))
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise NumbersError("%s is not a number: %r" % (where, v))
    if x < 0:
        raise NumbersError("%s cannot be negative: %r" % (where, v))
    return x


def _sum_items(items, field):
    if items is None:
        return 0.0
    if not isinstance(items, list):
        raise NumbersError("'%s' must be a list of {label, cost}" % field)
    total = 0.0
    for i, it in enumerate(items):
        if not isinstance(it, dict) or "cost" not in it:
            raise NumbersError("%s[%d] needs a 'cost'" % (field, i))
        total += _num(it["cost"], "%s[%d].cost" % (field, i))
    return total


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise NumbersError("no such file: %s" % path)
    except json.JSONDecodeError as e:
        raise NumbersError("%s is not valid JSON: %s" % (path, e))


def unit_cost(spec):
    uc = _need(spec, "unit_cost", "")
    content = _need(uc, "content", "unit_cost")
    per_g = _num(_need(content, "won_per_g", "unit_cost.content"), "unit_cost.content.won_per_g")
    grams = _num(_need(content, "grams", "unit_cost.content"), "unit_cost.content.grams")
    if "items" not in uc:
        raise NumbersError("'items' is missing in unit_cost (container, print, carton, filling; [] if none)")
    items = _sum_items(uc["items"], "unit_cost.items")
    return per_g * grams, items


def analyse(spec, unit_cost_override=None, commission=None, price_factor=1.0, shipping=None, initial=None):
    """Every number in the report. Pure function, easy to test."""
    content_cost, items_cost = unit_cost(spec)
    cost = content_cost + items_cost if unit_cost_override is None else float(unit_cost_override)
    size_ml = _num(_need(spec, "size_ml", ""), "size_ml")
    if size_ml <= 0:
        raise NumbersError("size_ml must be above zero")
    if "vat_included" not in spec or not isinstance(spec["vat_included"], bool):
        raise NumbersError("'vat_included' is missing: true if the prices include VAT, false if not")
    vat_rate = _num(spec.get("vat_rate", DEFAULT_VAT), "vat_rate")
    rate = _num(_need(spec, "commission_rate", ""), "commission_rate") if commission is None else float(commission)
    if rate >= 1:
        raise NumbersError("commission_rate is a fraction: 0.20 means 20 percent")
    ship_default = _num(_need(spec, "shipping_per_order", ""), "shipping_per_order") if shipping is None else float(shipping)
    initial_units = _num(_need(spec, "initial_units", ""), "initial_units") if initial is None else float(initial)
    if initial_units <= 0:
        raise NumbersError("initial_units must be above zero")
    one_off = _sum_items(spec.get("one_off", []), "one_off")

    bundles = _need(spec, "bundles", "")
    if not isinstance(bundles, list) or not bundles:
        raise NumbersError("'bundles' needs at least one bundle (단품)")
    kinds = {k for b in bundles for k in ("unit_share", "order_share") if isinstance(b, dict) and k in b}
    if len(kinds) != 1:
        raise NumbersError("give every bundle a 'unit_share' (by units sold) or every bundle an 'order_share'"
                           " (by orders), one kind for all")
    kind = kinds.pop()

    rows = []
    for i, b in enumerate(bundles):
        where = "bundles[%d]" % i
        name = _need(b, "name", where)
        units = _num(_need(b, "units_per_order", where), where + ".units_per_order")
        if units <= 0:
            raise NumbersError("%s.units_per_order must be above zero" % where)
        price = _num(_need(b, "price", where), where + ".price") * price_factor
        if price <= 0:
            raise NumbersError("%s.price must be above zero" % where)
        share = _num(_need(b, kind, where), "%s.%s" % (where, kind))
        ship = ship_default if (shipping is not None or "shipping_per_order" not in b) else _num(
            b["shipping_per_order"], where + ".shipping_per_order")
        net = price / (1 + vat_rate) if spec["vat_included"] else price
        fee = price * rate
        per_order = net - fee - ship
        rows.append({
            "name": name, "units_per_order": units, "price": price, "share": share,
            "net_revenue": net, "vat": price - net, "commission": fee, "shipping": ship,
            "contribution_per_order": per_order, "contribution_per_unit": per_order / units,
            "price_per_100ml": price / (units * size_ml) * 100, "price_per_unit": price / units,
        })
    total_share = sum(r["share"] for r in rows)
    if abs(total_share - 1.0) > 0.001:
        raise NumbersError("the %ss add up to %.3f, not 1" % (kind, total_share))

    if kind == "unit_share":
        unit_mix = [r["share"] for r in rows]
    else:  # convert order shares into unit shares
        units_w = [r["share"] * r["units_per_order"] for r in rows]
        unit_mix = [u / sum(units_w) for u in units_w]
    for r, u in zip(rows, unit_mix):
        r["unit_share"] = u
    avg = sum(r["contribution_per_unit"] * r["unit_share"] for r in rows)

    fixed_stock = initial_units * cost
    fixed = fixed_stock + one_off
    bep = math.inf if avg <= 0 else math.ceil(round(fixed / avg, 6))
    sell_through = math.inf if math.isinf(bep) else bep / initial_units
    full_profit = initial_units * avg - fixed
    reorder = avg - cost

    flags = []
    for r in rows:
        if r["contribution_per_order"] <= 0:
            flags.append("%s: 주문마다 손해예요(수수료와 배송비를 빼면 %s)." % (r["name"], won(r["contribution_per_order"])))
    if avg <= 0:
        flags.append("평균 공헌이익이 0원 이하라 BEP가 없어요.")
    elif bep > initial_units:
        flags.append("BEP %s개가 초도 물량 %s개보다 많아요. 초도를 다 팔아도 고정비를 못 채워요." % (count(bep), count(initial_units)))
    if reorder <= 0:
        flags.append("재발주부터 개당 이익이 %s예요. 팔수록 손해예요." % won(reorder))

    return {
        "product": spec.get("product", ""), "size_ml": size_ml, "vat_included": spec["vat_included"],
        "vat_rate": vat_rate, "commission_rate": rate, "shipping_per_order": ship_default,
        "content_cost": content_cost if unit_cost_override is None else None,
        "items_cost": items_cost if unit_cost_override is None else None,
        "unit_cost": cost, "initial_units": initial_units, "fixed_stock": fixed_stock, "one_off": one_off,
        "fixed": fixed, "mix_basis": kind, "bundles": rows, "avg_contribution_per_unit": avg,
        "bep_units": bep, "sell_through": sell_through, "full_sale_profit": full_profit,
        "reorder_profit_per_unit": reorder, "flags": flags,
    }


def sensitivity(spec):
    base = analyse(spec)
    return [
        ("기본", base),
        ("판매가 -10%", analyse(spec, price_factor=0.9)),
        ("개당 원가 +10%", analyse(spec, unit_cost_override=base["unit_cost"] * 1.1)),
        ("수수료 +5%p", analyse(spec, commission=base["commission_rate"] + 0.05)),
        ("배송비 +500원", analyse(spec, shipping=base["shipping_per_order"] + 500)),
    ]


def _src(d):
    bits = [d.get(k) for k in ("source", "as_of") if isinstance(d, dict) and d.get(k)]
    return (" (%s)" % ", ".join(bits)) if bits else ""


def report(spec, a, what_if=True):
    L = ["# 원가와 BEP: %s" % (a["product"] or "제품"), ""]
    L.append("모든 숫자는 입력 파일에서 나왔어요. 찾아보거나 추측한 숫자는 없어요. 브랜드 기준 계산이에요.")
    L.append("")
    L.append("## 개당 원가")
    L.append("")
    L.append("| 항목 | 개당 |")
    L.append("| --- | ---: |")
    uc = spec["unit_cost"]
    if a["content_cost"] is not None:
        c = uc["content"]
        L.append("| 내용물 (%s원/g x %sg)%s | %s |" % (c["won_per_g"], count(float(c["grams"])), _src(c), won(a["content_cost"])))
        for it in uc.get("items") or []:
            L.append("| %s%s | %s |" % (it.get("label", "부자재"), _src(it), won(float(it["cost"]))))
    else:
        L.append("| (what-if로 바꾼 원가) | %s |" % won(a["unit_cost"]))
    L.append("| **합계** | **%s** |" % won(a["unit_cost"]))
    L.append("")
    L.append("## 구성별 주문당 공헌이익")
    L.append("")
    L.append("판매가는 부가세 %s, 수수료 %s(결제가 기준), 주문당 배송비 %s. 비중은 %s 기준이에요." % (
        "포함" if a["vat_included"] else "별도(부가세를 빼지 않음)", pct(a["commission_rate"]),
        won(a["shipping_per_order"]), "수량" if a["mix_basis"] == "unit_share" else "주문"))
    L.append("")
    L.append("| 구성 | 판매가 | 100ml당 | 부가세 | 수수료 | 배송비 | 주문당 공헌이익 | 개당 | 수량 비중 |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for r in a["bundles"]:
        L.append("| %s (%s개) | %s | %s | -%s | -%s | -%s | %s | %s | %s |" % (
            r["name"], count(r["units_per_order"]), won(r["price"]), won(r["price_per_100ml"]), won(r["vat"]),
            won(r["commission"]), won(r["shipping"]), won(r["contribution_per_order"]),
            won(r["contribution_per_unit"]), pct(r["unit_share"])))
    L.append("")
    L.append("- **개당 평균 공헌이익: %s** (원가를 빼기 전, 고정비를 채우는 돈)" % won(a["avg_contribution_per_unit"]))
    L.append("")
    L.append("## 고정비와 BEP")
    L.append("")
    L.append("- 고정비 **%s** = 초도 %s개 x %s (%s) + 일회성 %s" % (
        won(a["fixed"]), count(a["initial_units"]), won(a["unit_cost"]), won(a["fixed_stock"]), won(a["one_off"])))
    for it in spec.get("one_off") or []:
        L.append("  - %s%s: %s" % (it.get("label", "일회성"), _src(it), won(float(it["cost"]))))
    if math.isinf(a["bep_units"]):
        L.append("- **BEP: 없음** (개당 평균 공헌이익이 0원 이하)")
    else:
        L.append("- **BEP: %s개, 초도 소진율 %s**" % (count(a["bep_units"]), pct(a["sell_through"])))
    L.append("- 초도 %s개 완판 시 이익: **%s**" % (count(a["initial_units"]), won(a["full_sale_profit"])))
    L.append("- 재발주부터 개당 이익: %s (평균 공헌이익 - 개당 원가)" % won(a["reorder_profit_per_unit"]))
    L.append("")
    if what_if:
        L.append("## What-if")
        L.append("")
        L.append("| 시나리오 | 개당 원가 | 개당 평균 공헌이익 | BEP | 소진율 | 완판 시 이익 |")
        L.append("| --- | ---: | ---: | ---: | ---: | ---: |")
        for name, s in sensitivity(spec):
            inf = math.isinf(s["bep_units"])
            L.append("| %s | %s | %s | %s | %s | %s |" % (
                name, won(s["unit_cost"]), won(s["avg_contribution_per_unit"]),
                "없음" if inf else count(s["bep_units"]) + "개", "-" if inf else pct(s["sell_through"]),
                won(s["full_sale_profit"])))
        L.append("")
    if a["flags"]:
        L.append("## 경고")
        L.append("")
        for f in a["flags"]:
            L.append("- %s" % f)
    else:
        L.append("경고 없음. 숫자는 입력만큼만 맞아요: 원가는 견적서로, 수수료는 채널 계약으로 확인하세요.")
    return "\n".join(L) + "\n"


def to_json(a):
    out = json.loads(json.dumps(a, default=str))
    for k in ("bep_units", "sell_through"):
        if isinstance(a[k], float) and math.isinf(a[k]):
            out[k] = None
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("numbers", help="cosmetic/<slug>/numbers.json")
    ap.add_argument("--out", help="write the report here (markdown)")
    ap.add_argument("--json", action="store_true", help="print the numbers as JSON")
    ap.add_argument("--unit-cost", type=float, help="what-if: cost of one unit in won")
    ap.add_argument("--commission", type=float, help="what-if: commission rate, 0.10 = 10 percent")
    ap.add_argument("--price-factor", type=float, default=1.0, help="what-if: multiply every price (0.9 = -10%%)")
    ap.add_argument("--shipping", type=float, help="what-if: shipping per order in won")
    ap.add_argument("--initial", type=float, help="what-if: initial production run in units")
    args = ap.parse_args(argv)
    try:
        spec = load(args.numbers)
        a = analyse(spec, args.unit_cost, args.commission, args.price_factor, args.shipping, args.initial)
        overridden = (args.unit_cost, args.commission, args.shipping, args.initial) != (None,) * 4 or args.price_factor != 1.0
    except NumbersError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(to_json(a), indent=1, ensure_ascii=False))
        return 0
    text = report(spec, a, what_if=not overridden)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote %s" % args.out)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
