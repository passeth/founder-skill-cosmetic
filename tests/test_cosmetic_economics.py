import json
import math
import unittest

from _load import load, example

ce = load("cosmetic-cfo", "cosmetic_economics")


def spec(name="example.json"):
    with open(example("cosmetic-cfo", name), encoding="utf-8") as fh:
        return json.load(fh)


class CosmeticEconomics(unittest.TestCase):
    def test_current_case_matches_the_plan(self):
        # 솔트브리즈 1L 퍼퓸 바디워시 (가상 예시): 원가 3,850원, 단품 10,900 · 2개 16,900 반반, 부가세 포함가
        a = ce.analyse(spec())
        self.assertEqual(a["unit_cost"], 3850)
        self.assertEqual(a["fixed"], 120500000)
        self.assertEqual(a["bep_units"], 24171)
        self.assertEqual(round(a["sell_through"] * 100, 1), 80.6)
        self.assertEqual(round(a["full_sale_profit"]), 29063636)
        single, double = a["bundles"]
        self.assertAlmostEqual(single["contribution_per_order"], 10900 / 1.1 - 2180 - 2500, places=6)
        self.assertAlmostEqual(double["contribution_per_unit"], (16900 / 1.1 - 3380 - 2500) / 2, places=6)
        self.assertEqual(round(single["price_per_100ml"]), 1090)
        self.assertEqual(round(double["price_per_100ml"]), 845)
        self.assertEqual(round(a["reorder_profit_per_unit"]), 1135)
        self.assertEqual(a["flags"], [])

    def test_aggressive_case_matches_the_plan(self):
        # 원가 3,300원 (용기 650, 단상자 0), 단품 20% · 2개 50% · 3향 세트 23,900원 30%
        a = ce.analyse(spec("example.aggressive.json"))
        self.assertEqual(a["unit_cost"], 3300)
        self.assertEqual(a["fixed"], 104000000)
        self.assertEqual(a["bep_units"], 21393)
        self.assertEqual(round(a["sell_through"] * 100, 1), 71.3)
        self.assertEqual(round(a["full_sale_profit"]), 41843636)

    def test_same_case_built_from_the_first_example(self):
        s = spec()
        s["unit_cost"]["items"][0]["cost"] = 650
        s["unit_cost"]["items"][2]["cost"] = 0
        s["bundles"] = [
            {"name": "단품", "units_per_order": 1, "price": 10900, "unit_share": 0.2},
            {"name": "2개", "units_per_order": 2, "price": 16900, "unit_share": 0.5},
            {"name": "3향 세트", "units_per_order": 3, "price": 23900, "unit_share": 0.3},
        ]
        a = ce.analyse(s)
        self.assertEqual((a["fixed"], a["bep_units"], round(a["full_sale_profit"])), (104000000, 21393, 41843636))

    def test_vat_excluded_prices_are_not_divided(self):
        s = spec()
        s["vat_included"] = False
        a = ce.analyse(s)
        self.assertAlmostEqual(a["avg_contribution_per_unit"], 5865, places=6)
        self.assertEqual(a["bep_units"], 20546)
        self.assertEqual(round(a["full_sale_profit"]), 55450000)

    def test_order_shares_convert_to_unit_shares(self):
        s = spec()
        # half the orders are single, half are 2-packs: a third of units are singles
        for b in s["bundles"]:
            del b["unit_share"]
            b["order_share"] = 0.5
        a = ce.analyse(s)
        self.assertAlmostEqual(a["bundles"][0]["unit_share"], 1 / 3.0, places=9)
        self.assertAlmostEqual(a["bundles"][1]["unit_share"], 2 / 3.0, places=9)

    def test_what_ifs_move_the_right_way(self):
        rows = dict(ce.sensitivity(spec()))
        base = rows["기본"]
        for name in ("판매가 -10%", "개당 원가 +10%", "수수료 +5%p", "배송비 +500원"):
            self.assertGreater(rows[name]["bep_units"], base["bep_units"], name)
            self.assertLess(rows[name]["full_sale_profit"], base["full_sale_profit"], name)
        cheaper = ce.analyse(spec(), commission=0.10)
        self.assertLess(cheaper["bep_units"], base["bep_units"])
        self.assertEqual(ce.analyse(spec(), unit_cost_override=3300)["fixed"], 104000000)

    def test_bep_above_the_first_run_is_flagged(self):
        a = ce.analyse(spec(), price_factor=0.8)
        self.assertGreater(a["bep_units"], a["initial_units"])
        self.assertTrue(any("초도 물량" in f for f in a["flags"]))

    def test_losing_bundle_and_no_bep(self):
        s = spec()
        for b in s["bundles"]:
            b["price"] = 3000
        a = ce.analyse(s)
        self.assertTrue(math.isinf(a["bep_units"]))
        self.assertTrue(any("주문마다 손해" in f for f in a["flags"]))
        self.assertIn("BEP: 없음", ce.report(s, a))
        self.assertIsNone(ce.to_json(a)["bep_units"])

    def test_missing_fields_are_errors_not_guesses(self):
        for path in (("vat_included",), ("commission_rate",), ("shipping_per_order",), ("initial_units",),
                     ("size_ml",), ("unit_cost", "content", "won_per_g"), ("unit_cost", "items")):
            s = spec()
            target = s
            for k in path[:-1]:
                target = target[k]
            del target[path[-1]]
            with self.assertRaises(ce.NumbersError, msg=path):
                ce.analyse(s)
        s = spec()
        s["bundles"][0]["unit_share"] = 0.6
        with self.assertRaises(ce.NumbersError):
            ce.analyse(s)
        s = spec()
        del s["bundles"][1]["unit_share"]
        s["bundles"][1]["order_share"] = 0.5
        with self.assertRaises(ce.NumbersError):
            ce.analyse(s)
        s = spec()
        s["unit_cost"]["items"][0]["cost"] = "많이"
        with self.assertRaises(ce.NumbersError):
            ce.analyse(s)
        s = spec()
        s["commission_rate"] = 20
        with self.assertRaises(ce.NumbersError):
            ce.analyse(s)

    def test_report_carries_the_key_numbers(self):
        s = spec()
        text = ce.report(s, ce.analyse(s))
        for needle in ("3,850원", "120,500,000원", "24,171개", "80.6%", "29,063,636원", "1,090원", "845원"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
