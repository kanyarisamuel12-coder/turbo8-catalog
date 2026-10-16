#!/usr/bin/env python3
"""Trusted, data-only validation and deterministic publication of community carts."""
import argparse
import base64
import hashlib
import io
import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
import zlib
from pathlib import Path

REPO = 'kanyarisamuel12-coder/turbo8-catalog'
MAX_EXPANDED = 64 * 1024 * 1024
MAX_ZIP = 32 * 1024 * 1024
MAX_FILES = 128
ID = re.compile(r'u[1-9][0-9]{0,19}-[a-f0-9]{32}')
VERSION = re.compile(r'(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})\.(0|[1-9][0-9]{0,5})')
PATH = re.compile(r'[A-Za-z0-9_-]+(?:[./][A-Za-z0-9_-]+)*')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def version(value):
    require(isinstance(value, str) and VERSION.fullmatch(value), 'Version must be MAJOR.MINOR.PATCH')
    return tuple(map(int, value.split('.')))


def safe_path(name):
    return isinstance(name, str) and len(name) <= 160 and PATH.fullmatch(name) and '..' not in name and not name.startswith('.')


def png_size(raw):
    require(len(raw) >= 33 and raw[:8] == b'\x89PNG\r\n\x1a\n' and raw[12:16] == b'IHDR', 'Invalid PNG header')
    offset = 8
    ended = False
    while offset + 12 <= len(raw):
        size = struct.unpack('>I', raw[offset:offset + 4])[0]
        require(offset + size + 12 <= len(raw), 'Truncated PNG chunk')
        chunk = raw[offset + 4:offset + 8 + size]
        crc = struct.unpack('>I', raw[offset + 8 + size:offset + 12 + size])[0]
        require(zlib.crc32(chunk) & 0xffffffff == crc, 'PNG checksum mismatch')
        offset += size + 12
        if chunk[:4] == b'IEND':
            ended = True
            break
    require(ended and offset == len(raw), 'Invalid PNG ending')
    return struct.unpack('>II', raw[16:24])


def validate(files, cart_id, actor=None, previous=None, check_js=True):
    """Never import, source, or execute any submitted file."""
    require(ID.fullmatch(cart_id), 'Invalid cartridge ID')
    require(0 < len(files) <= MAX_FILES and sum(map(len, files.values())) <= MAX_EXPANDED, 'Too many files or expanded bytes')
    require(all(safe_path(p) for p in files), 'Unsafe path')
    require(len({p.casefold() for p in files}) == len(files), 'Case-insensitive path collision')
    require('submission.json' in files and len(files['submission.json']) <= 16384, 'Missing or oversized submission.json')
    meta = json.loads(files['submission.json'])
    require(isinstance(meta, dict) and meta.get('schema') == 1, 'Unsupported submission schema')
    allowed = {'schema', 'id', 'author_id', 'title', 'summary', 'controls', 'version', 'code_license', 'assets_license', 'changes', 'remix_of'}
    require(set(meta) <= allowed, 'Unknown submission field')
    require(meta.get('id') == cart_id, 'ID does not match directory')
    author = meta.get('author_id')
    require(type(author) is int and author > 0 and cart_id.startswith(f'u{author}-'), 'Invalid author ID')
    if actor is not None:
        require(author == actor, 'Only the verified GitHub author may submit this cartridge')
    for key, limit in [('title', 120), ('summary', 2000), ('controls', 1000), ('code_license', 200), ('assets_license', 200), ('changes', 2000)]:
        value = meta.get(key)
        require(isinstance(value, str) and 0 < len(value.strip()) <= limit and '\x00' not in value, f'Missing or invalid {key}')
    version(meta.get('version'))
    remix = meta.get('remix_of', '')
    require(isinstance(remix, str) and (not remix or re.fullmatch(r'[a-z0-9-]{1,100}', remix)), 'Invalid remix source')
    if previous:
        require(previous['author_id'] == author and previous['id'] == cart_id, 'Author and ID are immutable')
        require(version(meta['version']) > version(previous['version']), 'An update must increase the version')
    cartridge = {p[len('cartridge/'):]: v for p, v in files.items() if p.startswith('cartridge/')}
    require(len(cartridge) + 1 == len(files), 'Only submission.json and cartridge/ are allowed')
    require('index.json' in cartridge and len(cartridge['index.json']) <= 65536, 'Missing or oversized cartridge index')
    index = json.loads(cartridge['index.json'])
    require(isinstance(index, dict), 'Invalid cartridge index')
    require(index.get('name') == meta['title'] and index.get('cartridgeVersion') == meta['version'], 'Cartridge title/version must match submission')
    resolution = index.get('resolution', {'width': 256, 'height': 144})
    require(isinstance(resolution, dict), 'Invalid canvas')
    w, h = resolution.get('width'), resolution.get('height')
    require(all(type(n) in (int, float) and 64 <= n <= 512 and int(n) == n for n in [w, h]), 'Invalid canvas dimensions')
    w, h = int(w), int(h)
    require(w * h <= 196608 and max(w/h, h/w) <= 3, 'Canvas exceeds supported limits')
    cover = cartridge.get('cover.png', b'')
    require(len(cover) <= 128 * 1024 and png_size(cover) == (256, 144), 'Cover must be 256 x 144 PNG, at most 128 KiB')
    scripts = index.get('scripts')
    require(isinstance(scripts, list) and 1 <= len(scripts) <= 32, 'Invalid script list')
    require(all(isinstance(s, str) and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_-]{0,63}\.js', s) for s in scripts), 'Invalid script filename')
    require(len(set(scripts)) == len(scripts), 'Duplicate scripts')
    allowed_files = set(scripts) | {'index.json', 'cover.png', 'sprites.png', 'maps.json', 'sfx.json', 'music.json', 'palette.json', 'spriteMeta.json', 'flags.json', 'sprites.json', 'pico8.json', 'postEffects.json', 'virtualControls.json'}
    images = index.get('images', [])
    require(isinstance(images, list) and len(images) <= 64, 'Invalid image list')
    image_bytes = image_pixels = 0
    image_ids = set()
    for entry in images:
        require(isinstance(entry, dict) and isinstance(entry.get('id'), str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', entry['id']), 'Invalid image entry')
        require(entry['id'] not in image_ids, 'Duplicate image ID')
        image_ids.add(entry['id'])
        name = 'images/' + entry['id'] + '.png' 
        require(entry.get('file') == name and name in cartridge, 'Missing embedded image')
        require(len(cartridge[name]) <= 8 * 1024 * 1024, 'Embedded image too large')
        iw, ih = png_size(cartridge[name])
        require(1 <= iw <= 4096 and 1 <= ih <= 4096 and iw * ih <= 4194304, 'Embedded image dimensions too large')
        require(entry.get('width') == iw and entry.get('height') == ih, 'Embedded image dimensions do not match')
        image_bytes += len(cartridge[name])
        image_pixels += iw * ih
        require(image_bytes <= 16 * 1024 * 1024 and image_pixels <= 8388608, 'Total embedded image budget exceeded')
        allowed_files.add(name)
    require(set(cartridge) <= allowed_files, 'Unexpected cartridge file')
    require(all(s in cartridge for s in scripts), 'Missing script')
    palette = json.loads(cartridge.get('palette.json', b'null'))
    require(isinstance(palette, list) and 1 <= len(palette) <= 256 and all(isinstance(c, str) and re.fullmatch(r'#[a-fA-F0-9]{6}', c) for c in palette), 'Invalid or missing palette')
    if 'sprites.json' in cartridge:
        sprites = json.loads(cartridge['sprites.json'])
        require(isinstance(sprites, list) and len(sprites) <= 4096, 'Invalid sprites')
        require(all(isinstance(sprite, list) and len(sprite) <= 64 and all(c is None or isinstance(c, str) and re.fullmatch(r'#[a-fA-F0-9]{6}', c) for c in sprite) for sprite in sprites), 'Invalid sprite pixels')
    else:
        require('sprites.png' in cartridge, 'Missing sprites')
        sw, sh = png_size(cartridge['sprites.png'])
        require(1 <= sw <= 4096 and 1 <= sh <= 4096 and sw * sh <= 4096 * 64, 'Sprite sheet too large')
    for name, limit in [('maps', 64), ('sfx', 256), ('music', 256)]:
        if name + '.json' in cartridge:
            resources = json.loads(cartridge[name + '.json'])
            require(isinstance(resources, list) and len(resources) <= limit and all(isinstance(x, dict) for x in resources), 'Invalid ' + name)
    for name, raw in cartridge.items():
        if name.endswith('.json'):
            json.loads(raw)
        if name.endswith('.js'):
            require(len(raw) <= 2 * 1024 * 1024, 'Script too large')
            raw.decode('utf-8')
            if check_js:
                result = subprocess.run(['node', '--check', '--input-type=commonjs'], input=raw, capture_output=True, timeout=20)
                require(result.returncode == 0, f'JavaScript syntax check failed: {name}')
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, raw in sorted(cartridge.items()):
            info = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw, compresslevel=9)
    raw = out.getvalue()
    require(len(raw) <= MAX_ZIP, 'Packaged cartridge exceeds 32 MiB')
    return meta, raw, cover, {'width': w, 'height': h}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Unexpected redirect from GitHub API')


def api(path, limit=4 * 1024 * 1024):
    require(path.startswith('/repos/' + REPO + '/') or re.fullmatch(r'/repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/git/(trees|blobs)/[a-f0-9]{40}', path), 'Unexpected API path')
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'Turbo8-Catalog', 'Authorization': 'Bearer ' + os.environ['GH_TOKEN']}
    request = urllib.request.Request('https://api.github.com' + path, headers=headers)
    with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
        raw = response.read(limit + 1)
    require(len(raw) <= limit, 'GitHub response exceeds limit')
    return json.loads(raw)


def tree_files(repository, commit, cart_id, metadata_only=False):
    require(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository), 'Invalid repository')
    require(re.fullmatch(r'[a-f0-9]{40}', commit), 'Invalid commit')
    sha = commit
    for component in ['carts', cart_id]:
        tree = api(f'/repos/{repository}/git/trees/{sha}')
        match = next((x for x in tree['tree'] if x['path'] == component), None)
        if not match:
            return {}, ''
        require(match['type'] == 'tree', 'Cartridge directory must be a tree')
        sha = match['sha']
    root_sha = sha
    files = {}
    pending = [('', sha)]
    total = 0
    while pending:
        prefix, sha = pending.pop()
        tree = api(f'/repos/{repository}/git/trees/{sha}')
        require(not tree.get('truncated') and len(tree['tree']) <= MAX_FILES, 'Oversized tree')
        for entry in tree['tree']:
            if metadata_only and (prefix or entry['path'] != 'submission.json'):
                continue
            name = prefix + entry['path']
            require(safe_path(name), 'Unsafe path')
            if entry['type'] == 'tree':
                require(name == 'cartridge' or name == 'cartridge/images', 'Unexpected subdirectory')
                pending.append((name + '/', entry['sha']))
                continue
            require(entry['type'] == 'blob' and entry['mode'] == '100644', 'Symlinks, executables and submodules are not allowed')
            size = entry.get('size', MAX_EXPANDED + 1)
            total += size
            require(total <= MAX_EXPANDED and size <= 16 * 1024 * 1024 and len(files) < MAX_FILES, 'File budget exceeded')
            blob = api(f'/repos/{repository}/git/blobs/{entry["sha"]}', (size * 4 // 3) + 65536)
            require(blob.get('encoding') == 'base64', 'Unexpected blob encoding')
            data = base64.b64decode(blob['content'])
            require(len(data) == size, 'Blob size mismatch')
            files[name] = data
    return files, root_sha


def check_pr(event_path, output):
    event = json.loads(Path(event_path).read_text())
    pr = event['pull_request']
    require(pr['base']['repo']['full_name'] == REPO and pr['base']['ref'] == 'main', 'Unexpected PR target')
    current = api(f'/repos/{REPO}/pulls/{pr["number"]}')
    require(current['head']['sha'] == pr['head']['sha'], 'PR changed; wait for its newer check')
    changed = []
    for page in range(1, 4):
        batch = api(f'/repos/{REPO}/pulls/{pr["number"]}/files?per_page=100&page={page}')
        changed.extend(batch)
        if len(batch) < 100:
            break
    require(len(changed) == current['changed_files'], 'Incomplete PR file list')
    require(0 < len(changed) <= MAX_FILES, 'PR must contain one cartridge and at most 128 changed files')
    ids = set()
    for item in changed:
        for path in [item['filename'], item.get('previous_filename', item['filename'])]:
            parts = path.split('/')
            require(len(parts) >= 3 and parts[0] == 'carts' and ID.fullmatch(parts[1]), 'PR may only change a cartridge directory')
            ids.add(parts[1])
    require(len(ids) == 1, 'Submit one cartridge per PR')
    cart_id = ids.pop()
    files, revision = tree_files(pr['head']['repo']['full_name'], pr['head']['sha'], cart_id)
    trusted_base = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    prior, _ = tree_files(REPO, trusted_base, cart_id, metadata_only=True)
    previous = json.loads(prior['submission.json']) if prior else None
    require(api(f'/repos/{REPO}/pulls/{pr["number"]}')['head']['sha'] == pr['head']['sha'], 'PR changed during validation')
    meta, raw, _, _ = validate(files, cart_id, int(pr['user']['id']), previous)
    output.mkdir(parents=True, exist_ok=True)
    (output / f'{cart_id}.zip').write_bytes(raw)
    (output / 'review.json').write_bytes(json_bytes({'id': cart_id, 'version': meta['version'], 'author_id': meta['author_id'], 'head_sha': pr['head']['sha'], 'submission_revision': revision, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}))
    print('Validated one cartridge; candidate ZIP is available as a workflow artifact.')


def local_files(directory):
    files = {}
    for p in directory.rglob('*'):
        require(not p.is_symlink(), 'Symlinks are not allowed')
        if p.is_file():
            require(p.stat().st_size <= 16 * 1024 * 1024, 'File too large')
            files[p.relative_to(directory).as_posix()] = p.read_bytes()
            require(len(files) <= MAX_FILES and sum(map(len, files.values())) <= MAX_EXPANDED, 'Cartridge exceeds file budget')
    return files


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True).strip()


def release_asset(tag, filename, raw, commit):
    """Existing version assets are immutable; retries verify rather than overwrite."""
    listed = json.loads(gh('api', f'repos/{REPO}/releases?per_page=100'))
    # Fetch a named release directly so older versions remain retryable beyond page one.
    existing = next((r for r in listed if r['tag_name'] == tag), None)
    if existing is None:
        probe = subprocess.run(['gh', 'api', f'repos/{REPO}/releases/tags/{tag}'], text=True, capture_output=True)
        if probe.returncode == 0:
            existing = json.loads(probe.stdout)
        else:
            require('404' in probe.stderr, 'Cannot determine existing Release state')
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / filename
        path.write_bytes(raw)
        if existing is None:
            gh('release', 'create', tag, '--repo', REPO, '--target', commit, '--title', tag, '--notes', 'Reviewed Turbo8 community cartridge.', '--latest=false', '--draft')
            existing = json.loads(gh('api', f'repos/{REPO}/releases/tags/{tag}'))
        asset = next((a for a in existing['assets'] if a['name'] == filename), None)
        if asset:
            downloaded_dir = Path(tmp) / 'downloaded'
            downloaded_dir.mkdir()
            gh('release', 'download', tag, '--repo', REPO, '--pattern', filename, '--dir', str(downloaded_dir))
            downloaded = (downloaded_dir / filename).read_bytes()
            require(downloaded == raw, 'Existing version has different bytes; increase the version')
        else:
            require(existing['draft'], 'Published Release is missing its asset; manual repair required')
            gh('release', 'upload', tag, str(path), '--repo', REPO)
        if existing['draft']:
            gh('release', 'edit', tag, '--repo', REPO, '--draft=false', '--latest=false')
    # Verify public delivery before exposing a catalog entry.
    public = f'https://github.com/{REPO}/releases/download/{tag}/{filename}'
    with urllib.request.urlopen(public, timeout=60) as response:
        downloaded = response.read(MAX_ZIP + 1)
    require(downloaded == raw, 'Public Release download verification failed')


def build(root, output, publish=False):
    require(not output.exists(), 'Output directory must be new')
    shutil.copytree(root / 'docs', output)
    (output / '.nojekyll').touch()
    manifest = json.loads((root / 'docs/catalog-v2.json').read_text())
    require(manifest.get('schema') == 1, 'Unsupported catalog schema')
    entries = {x['id']: x for x in manifest['cartridges']}
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    for directory in sorted((root / 'carts').glob('*')):
        require(directory.is_dir() and not directory.is_symlink(), 'Invalid cartridge directory')
        meta, raw, cover, resolution = validate(local_files(directory), directory.name)
        revision = subprocess.check_output(['git', 'rev-parse', f'{commit}:carts/{directory.name}'], cwd=root, text=True).strip()
        tag = f'cart-{directory.name}-v{meta["version"]}'
        asset = f'{directory.name}-v{meta["version"]}.zip'
        if publish:
            release_asset(tag, asset, raw, commit)
        entries[directory.name] = {'id': directory.name, 'title': meta['title'], 'version': meta['version'], 'tag': tag, 'asset': asset, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'resolution': resolution, 'author_id': meta['author_id'], 'summary': meta['summary'], 'controls': meta['controls'], 'code_license': meta['code_license'], 'assets_license': meta['assets_license'], 'remix_of': meta.get('remix_of', ''), 'submission_revision': revision}
        (output / 'covers').mkdir(exist_ok=True)
        (output / 'covers' / (directory.name + '.png')).write_bytes(cover)
    manifest['cartridges'] = sorted(entries.values(), key=lambda x: x['title'].casefold())
    manifest['source_commit'] = commit
    (output / 'catalog-v2.json').write_bytes(json_bytes(manifest))
    legacy = dict(manifest, cartridges=[x for x in manifest['cartridges'] if x['bytes'] <= 8 * 1024 * 1024])
    (output / 'catalog.json').write_bytes(json_bytes(legacy))
    print(f'Built {len(entries)} catalog entries; preserved curated catalog and covers.')


def verify_pages(expected):
    wanted = json.loads(expected.read_text())
    for attempt in range(12):
        url = f'https://kanyarisamuel12-coder.github.io/turbo8-catalog/catalog-v2.json?revision={wanted["source_commit"]}&attempt={attempt}'
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                actual = json.loads(response.read(1024 * 1024))
            if actual == wanted:
                print('Public catalog matches the deployed artifact.')
                return
        except (OSError, ValueError):
            pass
        time.sleep(10)
    raise ValueError('Public Pages catalog did not reach the expected revision')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    check = commands.add_parser('check-pr')
    check.add_argument('--event', required=True)
    check.add_argument('--output', type=Path, required=True)
    generate = commands.add_parser('build')
    generate.add_argument('--root', type=Path, default=Path('.'))
    generate.add_argument('--output', type=Path, required=True)
    generate.add_argument('--publish', action='store_true')
    verify = commands.add_parser('verify-pages')
    verify.add_argument('--expected', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'check-pr':
        check_pr(args.event, args.output)
    elif args.command == 'build':
        build(args.root.resolve(), args.output.resolve(), args.publish)
    else:
        verify_pages(args.expected)


if __name__ == '__main__':
    main()
