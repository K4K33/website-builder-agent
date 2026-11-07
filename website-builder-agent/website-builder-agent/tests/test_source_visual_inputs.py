"""Actual input bytes and mocked browser capture; no live browser/API calls."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from hashlib import sha256
from unittest.mock import Mock, patch
from tests.test_visual_asset_continuity import fixture
from utils.visual_asset_continuity import source_visual_image_inputs
from utils.original_experience_probe import probe_original_site_experience

class SourcePixelTests(unittest.TestCase):
    def test_target_bytes_are_supplied_and_tampering_stops_before_model(self):
        r,_=fixture()
        with TemporaryDirectory() as directory:
            file=Path(directory)/'source.png';file.write_bytes(b'\x89PNG\r\n\x1a\nsynthetic-not-a-real-source-review')
            profile={'visual_capture_complete':True,'visual_captures':[{'source_url':'https://company.example/shop',
                'path':str(file),'sha256':sha256(file.read_bytes()).hexdigest()}]}
            images,labels=source_visual_image_inputs(r,profile,allowed_root=directory)
            self.assertEqual(images,[str(file)]);self.assertEqual(labels[0]['source_url'],'https://company.example/shop')
            file.write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError,'before model/search'):
                source_visual_image_inputs(r,profile,allowed_root=directory)

    def test_no_capture_or_wrong_source_never_becomes_alt_only_analysis(self):
        r,_=fixture()
        with TemporaryDirectory() as directory:
            with self.assertRaises(RuntimeError):source_visual_image_inputs(r,{'visual_captures':[]},allowed_root=directory)
            file=Path(directory)/'other.png';file.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
            row={'source_url':'https://reference.example/','path':str(file),'sha256':sha256(file.read_bytes()).hexdigest()}
            with self.assertRaises(RuntimeError):source_visual_image_inputs(r,{'visual_capture_complete':True,'visual_captures':[row]},allowed_root=directory)

    def test_source_probe_reuses_visit_and_saves_full_page_capture(self):
        r,_=fixture();page=Mock();page.evaluate.return_value={};pw=Mock()
        browser=pw.chromium.launch.return_value;context=browser.new_context.return_value;context.new_page.return_value=page
        page.screenshot.side_effect=lambda **kw: Path(kw['path']).write_bytes(b'\x89PNG\r\n\x1a\nsynthetic')
        manager=Mock();manager.__enter__=Mock(return_value=pw);manager.__exit__=Mock(return_value=False)
        with TemporaryDirectory() as directory,patch('playwright.sync_api.sync_playwright',return_value=manager):
            profile=probe_original_site_experience(r['source_inventory'],capture_directory=directory)
            self.assertTrue(profile['visual_capture_complete']);page.goto.assert_called_once();page.screenshot.assert_called_once()
            self.assertTrue(page.screenshot.call_args.kwargs['full_page'])
            self.assertEqual(profile['visual_captures'][0]['asset_ids'],[])

if __name__=='__main__':unittest.main()
