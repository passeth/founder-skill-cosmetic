import json
import os
import shutil
import tempfile
import unittest

from _load import load, example

plan = load("cosmetic-plan", "compile_plan")


class CompilePlan(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        with open(os.path.join(self.d, "brief.md"), "w", encoding="utf-8") as fh:
            fh.write("# 솔트브리즈 1L 바디워시\n\n전시장 메모에서 시작.\n")

    def tearDown(self):
        shutil.rmtree(self.d)

    def numbers(self, **change):
        with open(example("cosmetic-cfo", "example.json"), encoding="utf-8") as fh:
            s = json.load(fh)
        s.update(change)
        with open(os.path.join(self.d, "numbers.json"), "w", encoding="utf-8") as fh:
            json.dump(s, fh, ensure_ascii=False)

    def panel(self, buys, n=100):
        os.makedirs(os.path.join(self.d, "panel"), exist_ok=True)
        with open(os.path.join(self.d, "panel", "results.json"), "w") as fh:
            json.dump({"buys": buys, "passes": n - buys, "answered": n, "buy_rate": buys / float(n)}, fh)

    def claims(self, *statuses):
        with open(os.path.join(self.d, "claims.csv"), "w", encoding="utf-8") as fh:
            fh.write("expression,where,type,evidence,status,note\n")
            for i, st in enumerate(statuses):
                fh.write("표현%d,상세,효능,,%s,\n" % (i, st))

    def test_no_numbers_is_incomplete(self):
        v, text = plan.compile_plan(self.d)
        self.assertEqual(v, "미완성")
        self.assertIn("/cosmetic-cfo", text)

    def test_example_numbers_and_panel_pass(self):
        self.numbers()
        self.panel(40)
        self.claims("통과", "수정", "RA 확인 필요")
        v, text = plan.compile_plan(self.d)
        self.assertEqual(v, "추진 가능")
        self.assertTrue(text.startswith("# 솔트브리즈 1L 바디워시 · 상품기획서"))
        self.assertIn("24,171개 (80.6%)", text)
        self.assertIn("29,063,636원", text)
        self.assertIn("RA 확인 대기 1건", text)
        self.assertIn("4. 제형 기획: /cosmetic-formula", text)
        request = plan.compile_request(self.d)
        self.assertIn("1.8원/g", request)
        self.assertIn("개발 의뢰서", request)

    def test_tight_sell_through_bar_means_not_yet(self):
        self.numbers()
        v, text = plan.compile_plan(self.d, max_sell_through=0.7)
        self.assertEqual(v, "아직")
        self.assertIn("✗ BEP 24,171개", text)

    def test_unsupported_claim_or_weak_panel_means_not_yet(self):
        self.numbers()
        self.claims("통과", "근거 없음")
        self.assertEqual(plan.compile_plan(self.d)[0], "아직")
        os.remove(os.path.join(self.d, "claims.csv"))
        self.panel(10)
        self.assertEqual(plan.compile_plan(self.d)[0], "아직")

    def test_losing_price_means_not_yet(self):
        self.numbers(bundles=[{"name": "단품", "units_per_order": 1, "price": 3000, "unit_share": 1}])
        v, text = plan.compile_plan(self.d)
        self.assertEqual(v, "아직")
        self.assertIn("주문마다 손해", text)


if __name__ == "__main__":
    unittest.main()
