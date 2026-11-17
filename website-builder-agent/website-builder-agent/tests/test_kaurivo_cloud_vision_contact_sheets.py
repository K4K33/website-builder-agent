"""QA-only screenshots remain complete even with an 8-image free provider cap."""
import base64
import hashlib
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image
from utils.kaurivo_cloud_vision_packet import (
    compact_concept_review_user_content, compact_vision_user_content,
)


class AllConceptVisionTests(unittest.TestCase):
    def build_images(self, root, count):
        paths = []
        for index in range(count):
            path = root / ("view-" + str(index + 1) + ".png")
            image = Image.new("RGB", (300, 420),
                              (15 + index * 11, 31 + index * 7, 50 + index * 6))
            image.save(path)
            paths.append(str(path))
        return paths

    def test_all_twelve_concept_views_plus_two_original_views_are_covered(self):
        with TemporaryDirectory() as tmp:
            paths = self.build_images(Path(tmp), 14)
            hashes = [hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths]
            message = compact_concept_review_user_content(
                '{"views_in_image_order":[]}', paths)
            self.assertEqual(len(message), 8)
            self.assertIn("VIEW 01", message[0]["text"])
            self.assertIn("VIEW 12", message[0]["text"])
            self.assertIn("VIEW 13", message[0]["text"])
            self.assertIn("VIEW 14", message[0]["text"])
            for pair in message[1:]:
                self.assertEqual(pair["type"], "image_url")
                url = pair["image_url"]["url"]
                self.assertTrue(url.startswith("data:image/jpeg;base64,"))
                encoded = url.split(",", 1)[1]
                with Image.open(BytesIO(base64.b64decode(encoded))) as sheet:
                    self.assertEqual(sheet.size, (1940, 2160))
            self.assertEqual(
                hashes,
                [hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths])
            self.assertLess(sum(len(p["image_url"]["url"]) for p in message[1:]),
                            4_000_000)

    def test_source_absent_still_reviews_all_twelve_concept_viewports(self):
        with TemporaryDirectory() as tmp:
            paths = self.build_images(Path(tmp), 12)
            message = compact_concept_review_user_content("review all 12", paths)
            self.assertEqual(len(message), 7)

    def test_never_silently_drop_a_concept_screenshot_to_fit_free_limits(self):
        with TemporaryDirectory() as tmp:
            paths = self.build_images(Path(tmp), 11)
            with self.assertRaisesRegex(RuntimeError, "all 12 or 14"):
                compact_concept_review_user_content("private", paths)
            with self.assertRaisesRegex(RuntimeError, "image count"):
                compact_vision_user_content("private", paths)
            with self.assertRaisesRegex(RuntimeError, "source screenshot unavailable"):
                compact_concept_review_user_content("private", paths + [
                    str(Path(tmp) / "missing.png")
                ])


if __name__ == "__main__":
    unittest.main()
