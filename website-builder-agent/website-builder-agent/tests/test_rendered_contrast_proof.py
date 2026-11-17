"""Pixel-contrast verification must fail closed on all unsupported images."""
from io import BytesIO
from PIL import Image
import unittest

from utils.rendered_contrast_proof import rendered_background_contrast


def shot(colors):
    pixels = Image.new("RGB", (len(colors), 2))
    for x, rgb in enumerate(colors):
        pixels.putpixel((x, 0), rgb)
        pixels.putpixel((x, 1), rgb)
    output = BytesIO()
    pixels.save(output, format="PNG")
    return output.getvalue()


class RealPixelContrastTests(unittest.TestCase):
    def test_white_text_over_every_dark_photo_pixel_is_proved(self):
        value = rendered_background_contrast(
            shot([(4, 12, 22), (18, 30, 44), (30, 44, 58)]),
            [255, 255, 255], 4.5)
        self.assertGreaterEqual(value, 4.5)

    def test_white_text_cannot_pass_photograph_with_one_bright_pixel(self):
        self.assertIsNone(rendered_background_contrast(
            shot([(3, 5, 8), (250, 250, 250), (12, 20, 30)]),
            [255, 255, 255], 4.5))

    def test_white_text_cannot_pass_ambiguous_midrange_pixel(self):
        self.assertIsNone(rendered_background_contrast(
            shot([(18, 18, 18), (160, 160, 160)]),
            [255, 255, 255], 4.5))

    def test_transparent_capture_and_corrupted_png_are_not_proof(self):
        image = Image.new("RGBA", (3, 2), (0, 0, 0, 0))
        data = BytesIO()
        image.save(data, format="PNG")
        self.assertIsNone(rendered_background_contrast(
            data.getvalue(), [255, 255, 255], 4.5))
        self.assertIsNone(rendered_background_contrast(
            b"\x89PNG\r\n\x1a\ninvalid", [255, 255, 255], 4.5))

    def test_non_strict_unsafe_threshold_and_dimensions_are_rejected(self):
        self.assertIsNone(rendered_background_contrast(
            shot([(0, 0, 0)]), [255, 255, 255], 2))
        self.assertIsNone(rendered_background_contrast(
            shot([(0, 0, 0)]), [255, 255, 255], 4.5, max_pixels=1))


if __name__ == "__main__":
    unittest.main()
