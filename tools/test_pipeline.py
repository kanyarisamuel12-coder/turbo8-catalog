#!/usr/bin/env python3
import copy
import importlib.util
import json
import struct
import unittest
from unittest.mock import patch
import io
import zlib
from pathlib import Path

spec = importlib.util.spec_from_file_location('pipeline', Path(__file__).with_name('catalog_pipeline.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
CART = 'u123-' + 'a' * 32


def png(w, h):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress((b'\0' + b'\0' * w * 3) * h)) + chunk(b'IEND', b'')


def fixture():
    meta = {'schema': 1, 'id': CART, 'author_id': 123, 'title': 'Review fixture', 'summary': 'A test', 'controls': 'Arrows', 'version': '1.0.0', 'code_license': 'MIT', 'assets_license': 'CC0-1.0', 'changes': 'Initial submission', 'remix_of': ''}
    index = {'name': meta['title'], 'cartridgeVersion': meta['version'], 'scripts': ['main.js'], 'resolution': {'width': 256, 'height': 144}}
    return {'submission.json': p.json_bytes(meta), 'cartridge/index.json': p.json_bytes(index), 'cartridge/main.js': b'function _draw() { cls(0); }\n', 'cartridge/cover.png': png(256, 144), 'cartridge/palette.json': b'["#000000","#ffffff"]', 'cartridge/sprites.json': b'[]'}


class ValidationTests(unittest.TestCase):
    def test_deterministic_zip(self):
        one = p.validate(fixture(), CART)
        two = p.validate(dict(reversed(list(fixture().items()))), CART)
        self.assertEqual(one[1], two[1])

    def test_author_cannot_be_forged(self):
        with self.assertRaisesRegex(ValueError, 'verified GitHub author'):
            p.validate(fixture(), CART, actor=456)

    def test_version_must_increase(self):
        f = fixture()
        previous = json.loads(f['submission.json'])
        with self.assertRaisesRegex(ValueError, 'increase'):
            p.validate(f, CART, previous=previous)

    def test_unsafe_files(self):
        for name in ['../escape', '.github/workflows/test.yml', 'cartridge/../../escape', 'cartridge/main.js/../extra', 'cartridge/Main.js', 'cartridge/secret.txt']:
            f = fixture(); f[name] = b'x'
            with self.subTest(name=name), self.assertRaises(ValueError):
                p.validate(f, CART)

    def test_metadata_must_match_package(self):
        f = fixture(); index = json.loads(f['cartridge/index.json']); index['name'] = 'Forged'; f['cartridge/index.json'] = p.json_bytes(index)
        with self.assertRaisesRegex(ValueError, 'match'):
            p.validate(f, CART)

    def test_reject_malformed_png(self):
        f = fixture(); f['cartridge/cover.png'] = f['cartridge/cover.png'][:-5]
        with self.assertRaises(ValueError): p.validate(f, CART)

    def test_reject_bad_js_without_executing(self):
        f = fixture(); f['cartridge/main.js'] = b'function broken( {'
        with self.assertRaisesRegex(ValueError, 'syntax'): p.validate(f, CART)
        f['cartridge/main.js'] = b'throw new Error("must never execute");'
        p.validate(f, CART)

    def test_godot_integral_float_canvas(self):
        f = fixture(); index = json.loads(f['cartridge/index.json']); index['resolution'] = {'width': 256.0, 'height': 144.0}; f['cartridge/index.json'] = p.json_bytes(index)
        self.assertEqual(p.validate(f, CART)[3], {'width': 256, 'height': 144})

    def test_canvas_and_duplicate_scripts(self):
        for change in [{'resolution': {'width': 512, 'height': 512}}, {'scripts': ['main.js', 'main.js']}, {'images': {}}]:
            f = fixture(); index = json.loads(f['cartridge/index.json']); index.update(change); f['cartridge/index.json'] = p.json_bytes(index)
            with self.assertRaises(ValueError): p.validate(f, CART)

    def test_expanded_budget(self):
        f = fixture(); f['cartridge/main.js'] = b' ' * (p.MAX_EXPANDED + 1)
        with self.assertRaisesRegex(ValueError, 'expanded'): p.validate(f, CART)

    def test_public_api_is_fixed(self):
        with self.assertRaisesRegex(ValueError, 'Unexpected API path'): p.api('https://example.com/token')


class PublicationTests(unittest.TestCase):
    def release_stub(self, existing_bytes=None, draft=True):
        state = {'tag_name': 'test-tag', 'draft': draft, 'assets': [] if existing_bytes is None else [{'name': 'fixture.zip'}]}
        calls = []
        def fake_gh(*args):
            calls.append(args)
            if args[0] == 'api': return json.dumps([state])
            if args[:2] == ('release', 'download'):
                directory = Path(args[args.index('--dir') + 1]); (directory / 'fixture.zip').write_bytes(existing_bytes)
            if args[:2] == ('release', 'upload'): state['assets'] = [{'name': 'fixture.zip'}]
            if args[:2] == ('release', 'edit'): state['draft'] = False
            return ''
        return state, calls, fake_gh

    def test_resume_draft_release(self):
        state, calls, fake = self.release_stub()
        with patch.object(p, 'gh', fake), patch.object(p.urllib.request, 'urlopen', return_value=io.BytesIO(b'zip')):
            p.release_asset('test-tag', 'fixture.zip', b'zip', 'a' * 40)
        self.assertFalse(state['draft'])
        self.assertEqual(sum(c[:2] == ('release', 'upload') for c in calls), 1)

    def test_retry_preserves_existing_asset(self):
        state, calls, fake = self.release_stub(b'zip', draft=False)
        with patch.object(p, 'gh', fake), patch.object(p.urllib.request, 'urlopen', return_value=io.BytesIO(b'zip')):
            p.release_asset('test-tag', 'fixture.zip', b'zip', 'a' * 40)
        self.assertFalse(any(c[:2] in [('release', 'upload'), ('release', 'edit')] for c in calls))

    def test_version_collision_fails_without_overwrite(self):
        state, calls, fake = self.release_stub(b'old', draft=False)
        with patch.object(p, 'gh', fake), self.assertRaisesRegex(ValueError, 'different bytes'):
            p.release_asset('test-tag', 'fixture.zip', b'new', 'a' * 40)
        self.assertFalse(any(c[:2] == ('release', 'upload') for c in calls))

    def test_bad_public_download_blocks_catalog(self):
        state, calls, fake = self.release_stub(b'zip', draft=False)
        with patch.object(p, 'gh', fake), patch.object(p.urllib.request, 'urlopen', return_value=io.BytesIO(b'corrupt')), self.assertRaisesRegex(ValueError, 'Public Release'):
            p.release_asset('test-tag', 'fixture.zip', b'zip', 'a' * 40)


if __name__ == '__main__': unittest.main()
