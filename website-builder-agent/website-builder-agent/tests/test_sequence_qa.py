from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image, ImageDraw

from utils import sequence_qa


def room(shift=0, tint=(200, 200, 200)):
    image = Image.new("RGB", (768, 432), tint)
    d = ImageDraw.Draw(image)
    d.rectangle((200 + shift, 80, 560 + shift, 360), outline=(20, 20, 20), width=6)
    d.line((0, 432, 200 + shift, 360), fill=(20, 20, 20), width=6)
    d.line((768, 432, 560 + shift, 360), fill=(20, 20, 20), width=6)
    d.rectangle((420 + shift, 250, 480 + shift, 330), outline=(30, 30, 30), width=5)
    return image


class SequenceQaTests(unittest.TestCase):
    def test_same_camera_passes_moved_camera_fails(self):
        same = sequence_qa.alignment([room(tint=(150, 180, 210)), room()])
        moved = sequence_qa.alignment([room(shift=90), room()])
        self.assertGreaterEqual(min(same), sequence_qa.MIN_ALIGNMENT)
        self.assertLess(min(moved), sequence_qa.MIN_ALIGNMENT)

    def test_review_must_be_strict_and_never_raises(self):
        with TemporaryDirectory() as tmp:
            paths = []
            for i in range(2):
                path = Path(tmp) / f"{i}.png"; room().save(path); paths.append(path)
            low = sequence_qa.check(paths, ["A", "B"], ask=lambda *a, **k: {"score": 6, "ok": True})
            self.assertFalse(low["ok"])
            good = sequence_qa.check(paths, ["A", "B"], ask=lambda *a, **k: {"score": 9, "ok": True, "issues": []})
            self.assertTrue(good["ok"])
            def boom(*a, **k):
                raise RuntimeError("429")
            self.assertFalse(sequence_qa.check(paths, ["A", "B"], ask=boom)["ok"])
        self.assertIn("inside the room", sequence_qa.REVIEW_BRIEF)


if __name__ == "__main__":
    unittest.main()
