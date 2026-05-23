import os
import unittest


class SecurityContractTests(unittest.TestCase):
    def test_chat_endpoint_does_not_trust_body_user_id_by_default(self):
        path = os.path.join(os.getcwd(), "ml", "api", "main.py")
        with open(path, encoding="utf-8") as f:
            content = f.read()

        self.assertIn("ALLOW_UNVERIFIED_CHAT_USER_ID", content)
        self.assertIn("X-ML-User-Id", content)
        self.assertIn("Ignoring unverified body user_id", content)

    def test_bm25_uses_safe_websearch_query_parser(self):
        path = os.path.join(os.getcwd(), "ml", "nlp", "retrieval", "bm25_search.py")
        with open(path, encoding="utf-8") as f:
            content = f.read()

        self.assertIn("websearch_to_tsquery", content)
        self.assertNotIn('" & ".join', content)

    def test_backend_accepts_dbscan_noise_segment(self):
        path = os.path.join(os.getcwd(), "backend", "src", "controllers", "ml.controller.ts")
        with open(path, encoding="utf-8") as f:
            content = f.read()

        self.assertIn("segment_id: z.number().int().min(-1)", content)


if __name__ == "__main__":
    unittest.main()
