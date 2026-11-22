import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image

from utils import build_film
from utils.film_hero import hero_html


class BuildFilmTests(unittest.TestCase):
    def test_film_only_for_reviewed_trade_folders(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertIsNone(build_film.film_for("Kylpyhuoneremontit", root))
            frames = root / "kylpyhuone" / "frames"
            frames.mkdir(parents=True)
            for i in range(30):
                Image.new("RGB", (32, 18)).save(frames / f"f{i + 1:03d}.webp")
            self.assertIsNone(build_film.film_for("Kylpyhuoneremontit", root))  # no film.json = not reviewed
            (root / "kylpyhuone" / "film.json").write_text(json.dumps({"labels": ["Purku", "Valmis"]}))
            film = build_film.film_for("Laatoitus ja kylpyhuoneet", root)
            self.assertEqual(len(film["frames"]), 30)
            self.assertEqual(film["labels"], ["Purku", "Valmis"])
            self.assertIn("tekoälyllä luotu", film["note"])
            self.assertIsNone(build_film.film_for("Kattoremontit", root))

    def test_script_skips_demolition_without_before_keyframe(self):
        calls = []
        with TemporaryDirectory() as tmp:
            keys = Path(tmp) / "kylpyhuone" / "keys"
            keys.mkdir(parents=True)
            for i in range(2, 6):
                Image.new("RGB", (32, 18)).save(keys / f"k{i}.webp")
            original = build_film.animate_pair
            build_film.animate_pair = lambda a, b, prompt, target, **k: calls.append(prompt) or None
            try:
                build_film.make_film("kylpyhuone", Path(tmp), Path(tmp) / "out", limit=1)
            finally:
                build_film.animate_pair = original
        self.assertEqual(len(calls), 1)
        self.assertIn("waterproofing", calls[0])

    def test_hero_is_labelled_and_has_still_fallback(self):
        page = hero_html(prefix="assets/film/", count=120, labels=["Purku", "Valmis"], headline_html="<h1>X</h1>",
                         body_html="", note="Havainnevideo, tekoälyllä luotu", alt="Havainnevideo")
        self.assertIn('class="film__poster" src="assets/film/f120.webp"', page)
        self.assertIn("Havainnevideo, tekoälyllä luotu", page)
        self.assertIn('data-count="120"', page)


if __name__ == "__main__":
    unittest.main()
