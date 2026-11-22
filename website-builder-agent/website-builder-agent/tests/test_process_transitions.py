from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image, ImageDraw

from utils.depth_scene_runtime import SCRIPT
from utils.scroll_scrub import TRANSITIONS, change_mask


class ProcessTransitionTests(unittest.TestCase):
    def test_change_mask_marks_only_the_changed_work(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            before = Image.new("RGB", (768, 432), (120, 120, 120))
            after = before.copy()
            ImageDraw.Draw(after).rectangle((0, 216, 768, 432), fill=(200, 196, 190))  # tiled lower half
            before.save(root / "a.png"); after.save(root / "b.png")
            mask = Image.open(change_mask(root / "a.png", root / "b.png", root / "m.webp")).convert("L")
            top, bottom = mask.crop((0, 0, 384, 80)), mask.crop((0, 150, 384, 216))
            self.assertLess(max(top.getdata()), 40)
            self.assertGreater(sum(bottom.getdata()) / (384 * 66), 180)

    def test_runtime_knows_every_process_move(self):
        self.assertEqual(TRANSITIONS, ("depth", "coat", "tiles", "rise", "build"))
        for name in ("coat: 1", "tiles: 2", "rise: 3", "build: 4", "stageReveal", "uniform1f(U('style')"):
            self.assertIn(name, SCRIPT)


if __name__ == "__main__":
    unittest.main()
