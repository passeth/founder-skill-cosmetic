import json
import os
import shutil
import tempfile
import unittest

from _load import load, example

cp = load("cosmetic-consumer", "cosmetic_panel")
vw = load("founder-pricing", "van_westendorp")


def customer():
    with open(example("cosmetic-consumer", "customer.example.json"), encoding="utf-8") as fh:
        return json.load(fh)


class Deal(unittest.TestCase):
    def test_same_seed_same_cards(self):
        self.assertEqual(cp.deal(customer(), 100, 7), cp.deal(customer(), 100, 7))
        self.assertNotEqual(cp.deal(customer(), 100, 7), cp.deal(customer(), 100, 8))

    def test_cosmetic_fields_are_dealt_by_share(self):
        cards = cp.deal(customer(), 100, 3)
        skin, channel = {}, {}
        for c in cards:
            skin[c["skin_type"]] = skin.get(c["skin_type"], 0) + 1
            channel[c["channel"]] = channel.get(c["channel"], 0) + 1
            for k in ("concern", "sale_waiting"):
                self.assertTrue(c[k])
        self.assertEqual(skin, {"건성": 25, "지성": 25, "복합성": 35, "민감성": 15})
        self.assertEqual(channel, {"올리브영": 40, "쿠팡": 35, "자사몰·스마트스토어": 15, "인스타 공구": 10})
        self.assertEqual(len({c["name"] for c in cards}), 100)

    def test_profile_without_cosmetic_fields_is_refused(self):
        c = customer()
        del c["skin_types"]
        with self.assertRaises(cp.PanelError):
            cp.deal(c)


class Flow(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        cp.init(self.d, example("cosmetic-consumer", "customer.example.json"),
                example("cosmetic-consumer", "pitch.example.md"), n=20, seed=5)

    def tearDown(self):
        shutil.rmtree(self.d)

    def answer(self, pid, buys, code="price", **extra):
        a = {"id": pid, "buys": buys, "reason_code": code, "reason": "이유 %s" % pid,
             "purchases_first_month": 1 if buys else 0, "would_change_my_mind": "" if buys else "1+1",
             "where_buy": "쿠팡" if buys else "", "wait_for_sale": buys and pid < "P005",
             "price_too_cheap": 4000, "price_cheap": 7000, "price_expensive": 13000, "price_too_expensive": 18000}
        a.update(extra)
        with open(os.path.join(self.d, "answers", pid + ".json"), "w", encoding="utf-8") as fh:
            json.dump(a, fh, ensure_ascii=False)

    def test_briefs_are_korean_and_carry_the_card(self):
        waves = cp.write_briefs(self.d, wave=10)
        self.assertEqual([len(w) for w in waves], [10, 10])
        with open(waves[0][0][1], encoding="utf-8") as fh:
            brief = fh.read()
        self.assertIn("10,900원", brief)
        self.assertIn('"id": "P001"', brief)
        self.assertIn("피부:", brief)
        self.assertIn("맞춰 주지 마세요", brief)
        self.assertIn("만원", brief)

    def test_check_tally_and_pricing_reads_the_answers(self):
        for i in range(1, 21):
            pid = "P%03d" % i
            self.answer(pid, i <= 8, "scent" if i <= 8 else ("price" if i <= 15 else "volume"))
        self.answer("P020", False, "vibes")
        self.assertEqual([p for p, _ in cp.check(self.d)], ["P020"])
        res = cp.tally(self.d)
        self.assertEqual((res["buys"], res["passes"], res["answered"]), (8, 11, 19))
        self.assertEqual(res["why_not"][0][:2], ("price", 7))
        self.assertEqual(res["wait_for_sale"], 4)
        self.assertEqual(res["where_buy"], [("쿠팡", 8)])
        self.assertTrue(res["by_skin_type"])
        text = cp.results_md(res)
        self.assertIn("**8명 구매 · 11명 안 삼**", text)
        self.assertIn("후기·추천사로 쓰지 않아요", text)
        rows, dropped = vw.read(os.path.join(self.d, "answers"))
        self.assertEqual(len(rows), 20)
        self.assertIn("원", vw.report(vw.analyse(rows), dropped, price=10900, currency="won"))

    def test_save_refuses_junk(self):
        cp.save(self.d, "P002", '답: {"id": "P002", "buys": false, "reason_code": "texture", "reason": "끈적할 듯"}')
        self.assertNotIn("P002", dict(cp.check(self.d)))
        with self.assertRaises(cp.PanelError):
            cp.save(self.d, "P003", '{"id": "P003", "buys": "글쎄", "reason_code": "price", "reason": "x"}')
        with self.assertRaises(cp.PanelError):
            cp.save(self.d, "P999", '{"id": "P999"}')

    def test_tally_with_no_answers_refuses(self):
        with self.assertRaises(cp.PanelError):
            cp.tally(self.d)


if __name__ == "__main__":
    unittest.main()
