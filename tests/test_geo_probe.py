import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("geo_probe", ROOT / "scripts" / "geo_probe.py")
geo_probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(geo_probe)


class RobotsTests(unittest.TestCase):
    def test_wildcard_and_end_anchor(self):
        self.assertTrue(geo_probe.robots_path_matches("/*.pdf$", "/guide.pdf"))
        self.assertFalse(geo_probe.robots_path_matches("/*.pdf$", "/guide.pdf?download=1"))

    def test_allow_wins_equal_length_tie(self):
        groups = {"*": [("disallow", "/"), ("allow", "/")]}
        self.assertEqual(geo_probe.robots_verdict(groups, "ExampleBot"), (True, False))


class ScoringTests(unittest.TestCase):
    def test_failed_baseline_withholds_score(self):
        out = {
            "domain": "example.com",
            "baseline": {"status": 403},
            "flags": [],
        }
        geo_probe.score_and_flag(out, [])
        self.assertIsNone(out["score"])
        self.assertFalse(out["conclusive"])
        self.assertEqual(out["flags"][0]["code"], "BASELINE_ANOMALY")

    def test_thin_html_claim_is_scoped_to_baseline_response(self):
        out = {
            "domain": "example.com",
            "baseline": {"status": 200, "cold_ttfb": 0.1, "repeat_ttfb": 0.1},
            "bot_ttfb_median": 0.1,
            "content": {"classification": "CSR_SHELL", "visible_words": 10},
            "robots": {"verdicts": {}, "sitemaps": []},
            "flags": [],
        }
        geo_probe.score_and_flag(out, [])
        finding = next(flag for flag in out["flags"] if flag["code"] == "CSR_SHELL")
        self.assertIn("baseline raw HTML", finding["detail"])
        self.assertIn("may miss", finding["detail"])
        self.assertNotIn("invisible", finding["detail"])


if __name__ == "__main__":
    unittest.main()
