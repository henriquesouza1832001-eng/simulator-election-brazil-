"""Offline evaluation tests for the reviewed-label interpreter candidate."""
from __future__ import annotations

import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from app.ai.local_interpreter import evaluate_field, fit_naive_bayes, predict, tokenize
from app.ai.trainer import train


class LocalInterpreterTests(unittest.TestCase):
    def test_tokenizer_normalizes_portuguese_and_adds_word_pairs(self) -> None:
        tokens = tokenize("Ampliar a saúde pública com novas unidades.")
        self.assertIn("saude", tokens)
        self.assertIn("saude__publica", tokens)
        self.assertNotIn("com", tokens)

    def test_naive_bayes_uses_reviewed_text_features(self) -> None:
        model = fit_naive_bayes([
            {"text": "construir ferrovia para transporte de cargas", "label": "public_investment"},
            {"text": "reduzir contratos e auditar compras públicas", "label": "fiscal_efficiency"},
        ])
        result = predict(model, "ampliar ferrovia e transporte de cargas")
        self.assertEqual(result["label"], "public_investment")
        self.assertGreaterEqual(result["confidence"], 0.5)

    def test_holdout_evaluation_qualifies_clear_classes(self) -> None:
        samples = []
        for index in range(10):
            samples.append({"text": f"ferrovia carga transporte publico obra {index}",
                            "labels": {"category": "public_investment"}})
            samples.append({"text": f"auditoria contrato despesa fiscal controle {index}",
                            "labels": {"category": "fiscal_efficiency"}})
        result = evaluate_field(samples, "category")
        self.assertTrue(result["ready"])
        self.assertEqual(result["accuracy"], 1.0)
        self.assertIsNotNone(result["model"])

    def test_insufficient_class_examples_do_not_create_a_model(self) -> None:
        samples = [
            {"text": f"proposta categoria public {index}", "labels": {"category": "public_investment"}}
            for index in range(4)
        ] + [
            {"text": f"proposta categoria fiscal {index}", "labels": {"category": "fiscal_efficiency"}}
            for index in range(4)
        ]
        result = evaluate_field(samples, "category")
        self.assertFalse(result["ready"])
        self.assertIsNone(result["model"])

    def test_trainer_writes_validated_per_player_candidate_without_activating_it(self) -> None:
        samples = []
        for index in range(10):
            samples.append({"text": f"ferrovia carga transporte obra {index}",
                            "labels": {"category": "public_investment"}})
            samples.append({"text": f"auditoria contrato despesa fiscal {index}",
                            "labels": {"category": "fiscal_efficiency"}})
        with tempfile.TemporaryDirectory() as folder:
            with patch("app.ai.trainer.load_reviewed_examples", return_value={"player-one": samples}):
                report = train(Path(folder))
            artifact_path = Path(report["reports"][0]["fields"]["category"]["artifact"])
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))

        self.assertEqual(report["status"], "completed")
        self.assertFalse(report["live_interpreter_changed"])
        self.assertTrue(artifact_path.name.endswith(".category.candidate.json"))
        self.assertEqual(artifact["activation"], "offline_candidate_only")
        self.assertEqual(artifact["validation"]["accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
