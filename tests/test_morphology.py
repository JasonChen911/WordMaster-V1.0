"""Morphology layer contract tests (rule-based lemmatization + lookup chain)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from morphology import normalize, lemmatize, variants_for, lookup_chain  # noqa: E402


class MorphologyTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize("  Student  "), "student")
        self.assertEqual(normalize("STUDENTS!"), "students")
        self.assertEqual(normalize("well-known"), "well-known")
        self.assertEqual(normalize("it's"), "it's")
        self.assertEqual(normalize(""), "")

    def test_regular_plurals(self):
        self.assertIn("student", lemmatize("students"))
        self.assertIn("cat", lemmatize("cats"))
        self.assertIn("read", lemmatize("reads"))

    def test_es_plurals(self):
        self.assertIn("box", lemmatize("boxes"))
        self.assertIn("class", lemmatize("classes"))
        self.assertIn("bus", lemmatize("buses"))

    def test_y_to_ies(self):
        self.assertIn("study", lemmatize("studies"))

    def test_verb_forms(self):
        self.assertIn("study", lemmatize("studied"))
        self.assertIn("study", lemmatize("studying"))
        self.assertIn("play", lemmatize("played"))
        self.assertIn("love", lemmatize("loved"))
        self.assertIn("stop", lemmatize("stopped"))
        self.assertIn("run", lemmatize("running"))
        self.assertIn("make", lemmatize("making"))

    def test_irregulars(self):
        self.assertEqual(lemmatize("went"), ["go"])
        self.assertIn("child", lemmatize("children"))
        self.assertIn("man", lemmatize("men"))
        self.assertIn("take", lemmatize("took"))

    def test_never_reduce_protected_words(self):
        # These must not be wrongly de-inflected into nonsense.
        self.assertEqual(lemmatize("bus"), [])
        self.assertEqual(lemmatize("news"), [])
        self.assertEqual(lemmatize("class"), [])
        self.assertEqual(lemmatize("status"), [])

    def test_variants_for_chain(self):
        v = variants_for("STUDENTS")
        self.assertEqual(v[0], "students")   # normalized exact first
        self.assertIn("student", v)          # then lemma

    def test_lookup_chain_exact_wins(self):
        # A finder that "has" student/students: exact match must win before lemma.
        db = {"students": "plural", "student": "singular"}
        result, matched, strategy = lookup_chain("students", lambda w: db.get(w))
        self.assertEqual(result, "plural")
        self.assertEqual(matched, "students")
        self.assertEqual(strategy, "exact")

    def test_lookup_chain_lemma_fallback(self):
        db = {"student": "singular"}
        result, matched, strategy = lookup_chain("students", lambda w: db.get(w))
        self.assertEqual(result, "singular")
        self.assertEqual(matched, "student")
        self.assertEqual(strategy, "lemma")

    def test_lookup_chain_no_match(self):
        result, matched, strategy = lookup_chain("zzzzz", lambda w: None)
        self.assertIsNone(result)
        self.assertIsNone(strategy)


if __name__ == "__main__":
    unittest.main()
