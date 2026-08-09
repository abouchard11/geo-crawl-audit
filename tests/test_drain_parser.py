import importlib.util
import ipaddress
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("drain_parser", ROOT / "scripts" / "drain_parser.py")
drain_parser = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(drain_parser)


class RegistryTests(unittest.TestCase):
    def test_current_vendor_registry(self):
        registry = json.loads((ROOT / "scripts" / "bots.json").read_text())
        by_token = {bot["token"]: bot for bot in registry["bots"]}
        self.assertIn("GPTBot/1.4", by_token["GPTBot"]["ua"])
        self.assertIn("OAI-SearchBot/1.4", by_token["OAI-SearchBot"]["ua"])
        self.assertEqual(
            by_token["PerplexityBot"]["ip_ranges"],
            "https://www.perplexity.com/perplexitybot.json",
        )
        self.assertEqual(by_token["ClaudeBot"]["ip_cidrs"], ["160.79.104.0/21"])

    def test_static_anthropic_network_is_verifiable(self):
        networks = drain_parser.verification_networks(
            {"ip_cidrs": ["160.79.104.0/21"], "ip_ranges": None}
        )
        self.assertIn(ipaddress.ip_address("160.79.104.1"), networks[0])


class InputTests(unittest.TestCase):
    def test_malformed_ndjson_line_is_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "logs.ndjson"
            path.write_text(
                '{"proxy":{"userAgent":"GPTBot/1.4","path":"/","statusCode":200}}\n'
                'not-json\n'
            )
            rows = list(drain_parser.iter_records([str(path)], "vercel"))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], 200)


if __name__ == "__main__":
    unittest.main()
