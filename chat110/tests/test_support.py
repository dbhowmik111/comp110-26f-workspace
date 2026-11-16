"""Check inspection contracts without downloading or loading model weights."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from chat110.support import next_token_logits


class InspectionTests(unittest.TestCase):
    def test_ranked_subset_preserves_raw_logits_and_breaks_ties_by_id(self):
        import torch

        tokenizer = Mock(return_value={"input_ids": torch.tensor([[2, 818]])})
        model = Mock()
        model.config.max_position_embeddings = 8
        model.return_value = SimpleNamespace(logits=torch.tensor([[[-4.0, 2.0, 2.0, -1.0]]]))
        with (
            patch("chat110.support._get_tokenizer", return_value=tokenizer),
            patch("chat110.support._get_model", return_value=model),
        ):
            result = next_token_logits("The", top_k=3)
            self.assertEqual(list(result.items()), [(1, 2.0), (2, 2.0), (3, -1.0)])
            tokenizer.assert_called_with("The", add_special_tokens=True, return_tensors="pt")
            # Asking for more entries than exist still returns the actual vocabulary.
            self.assertEqual(len(next_token_logits("The", top_k=10)), 4)

    def test_invalid_requests_do_not_load_model_or_tokenizer(self):
        with (
            patch("chat110.support._get_tokenizer") as tokenizer,
            patch("chat110.support._get_model") as model,
        ):
            for prompt, top_k in (("", 5), ("  ", 5), ("The", 0), ("The", -1)):
                with self.subTest(prompt=prompt, top_k=top_k), self.assertRaises(ValueError):
                    next_token_logits(prompt, top_k=top_k)
            tokenizer.assert_not_called()
            model.assert_not_called()

    def test_prompt_must_leave_room_for_a_continuation(self):
        import torch

        tokenizer = Mock(return_value={"input_ids": torch.tensor([[2, 818]])})
        model = Mock()
        model.config.max_position_embeddings = 2
        with (
            patch("chat110.support._get_tokenizer", return_value=tokenizer),
            patch("chat110.support._get_model", return_value=model),
            self.assertRaisesRegex(ValueError, "too long"),
        ):
            next_token_logits("The")
        model.assert_not_called()


if __name__ == "__main__":
    unittest.main()
