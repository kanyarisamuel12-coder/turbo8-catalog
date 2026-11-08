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
import cover_assets
import zlib
from pathlib import Path
import catalog_moderation as moderation
from editor_validation import (CONTRACT, LIMITS, compatibility_warnings, read_json,
                               script_files, validate_resources)

REPO = 'turbo8-coder/turbo8-catalog'
MAX_EXPANDED = LIMITS['expandedBytes']
MAX_ZIP = LIMITS['zipBytes']
MAX_FILES = LIMITS['files']
MAX_FILE = LIMITS['fileBytes']
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
    # ZIP resources are read as data, not extracted/executed. Editor script
    # labels may contain spaces or Unicode; those are not path traversal.
    if not isinstance(name, str) or len(name) > LIMITS['pathLength']:
        return False
    if any(ord(c) < 32 or ord(c) == 127 or c in '\\:*?"<>|' for c in name):
        return False
    return all(part.strip() and part not in ('.', '..') and not part.startswith('.')
               for part in name.split('/'))


def png_size(raw):
    return cover_assets.png_size(raw)


def validate(files, cart_id, actor=None, previous=None, check_js=True):
    """Never import, source, or execute any submitted file."""
    require(ID.fullmatch(cart_id), 'Invalid cartridge ID')
    require(0 < len(files) <= MAX_FILES and sum(map(len, files.values())) <= MAX_EXPANDED, 'Too many files or expanded bytes')
    require(all(len(raw) <= MAX_FILE for raw in files.values()), 'File exceeds editor submission limit')
    require(all(safe_path(p) for p in files), 'Unsafe path')
    require(len({p.casefold() for p in files}) == len(files), 'Case-insensitive path collision')
    require('submission.json' in files, 'Missing submission.json')
    meta = read_json(files['submission.json'])
    require(isinstance(meta, dict) and meta.get('schema') == 1, 'Unsupported submission schema')
    for retired in ('remix_of', 'code_license', 'assets_license', 'controls'):
        meta.pop(retired, None)  # Ignore retired fields in existing submissions.
    # Extra metadata may come from a newer client; security-sensitive fields are
    # still checked below. Do not let an optional new field block an old format.
    require(meta.get('id') == cart_id, 'ID does not match directory')
    author = meta.get('author_id')
    require(type(author) is int and author > 0 and cart_id.startswith(f'u{author}-'), 'Invalid author ID')
    if actor is not None:
        require(author == actor, 'Only the verified GitHub author may submit this cartridge')
    for key, limit in [('title', 120), ('summary', 2000), ('changes', 2000)]:
        value = meta.get(key, '')
        require(isinstance(value, str) and len(value) <= limit and '\x00' not in value and
                (key != 'title' or value.strip()), f'Missing or invalid {key}')
        meta[key] = value
    version(meta.get('version'))
    if previous:
        require(previous['author_id'] == author and previous['id'] == cart_id, 'Author and ID are immutable')
        require(version(meta['version']) > version(previous['version']), 'An update must increase the version')
    cartridge = {p[len('cartridge/'):]: v for p, v in files.items() if p.startswith('cartridge/')}
    require(len(cartridge) + 1 == len(files), 'Only submission.json and cartridge/ are allowed')
    require('index.json' in cartridge, 'Missing cartridge index')
    index = read_json(cartridge['index.json'])
    require(isinstance(index, dict), 'Invalid cartridge index')
    require(index.get('name') == meta['title'] and index.get('cartridgeVersion') == meta['version'], 'Cartridge title/version must match submission')
    display = CONTRACT['display']
    default = next(p for p in display['presets'] if p['id'] == display['default'])
    resolution = index.get('resolution', {'width': default['width'], 'height': default['height']})
    require(isinstance(resolution, dict), 'Invalid canvas')
    w, h = resolution.get('width'), resolution.get('height')
    require(all(type(n) in (int, float) and display['minDimension'] <= n <= display['maxDimension'] and int(n) == n
                for n in [w, h]), 'Invalid canvas dimensions')
    w, h = int(w), int(h)
    require(w * h <= display['maxPixels'] and max(w/h, h/w) <= display['maxAspect'], 'Canvas exceeds supported limits')
    cover = cartridge.get('cover.png', b'')
    cover_rules = CONTRACT['cover']
    require(len(cover) <= cover_rules['bytes'] and png_size(cover) == (cover_rules['width'], cover_rules['height']),
            'Cover does not match editor output dimensions or byte limit')
    scripts = script_files(index)
    allowed_files = set(scripts) | {'index.json', 'cover.png', 'sprites.png'}
    allowed_files.update(name + '.json' for name in CONTRACT['resource_json'])
    image_rules = CONTRACT['images']
    images = index.get('images', [])
    require(isinstance(images, list) and len(images) <= image_rules['maxImages'], 'Invalid image list')
    image_bytes = image_pixels = 0
    image_ids = set()
    for entry in images:
        require(isinstance(entry, dict) and isinstance(entry.get('id'), str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', entry['id']), 'Invalid image entry')
        require(entry['id'] not in image_ids, 'Duplicate image ID')
        image_ids.add(entry['id'])
        require(isinstance(entry.get('name', entry['id']), str) and len(entry.get('name', entry['id'])) <= 128,
                'Invalid image name')
        name = 'images/' + entry['id'] + '.png'
        require(entry.get('file') == name and name in cartridge, 'Missing embedded image')
        require(len(cartridge[name]) <= image_rules['maxBytesPerImage'], 'Embedded image too large')
        iw, ih = png_size(cartridge[name])
        require(1 <= iw <= image_rules['maxSide'] and 1 <= ih <= image_rules['maxSide'] and
                iw * ih <= image_rules['maxPixelsPerImage'], 'Embedded image dimensions too large')
        require(entry.get('width') == iw and entry.get('height') == ih, 'Embedded image dimensions do not match')
        image_bytes += len(cartridge[name])
        image_pixels += iw * ih
        require(image_bytes <= image_rules['maxTotalBytes'] and image_pixels <= image_rules['maxTotalPixels'],
                'Total embedded image budget exceeded')
        allowed_files.add(name)
    # Optional JSON extensions are data, bounded by the same submission budgets.
    # Preserve their bytes for newer clients; older editors already ignore them.
    unexpected = sorted(name for name in set(cartridge) - allowed_files if not name.endswith('.json'))
    require(not unexpected, 'Unexpected cartridge file: ' + ', '.join(unexpected))
    # The legacy ZIP reader resolves suffixes as well as exact names. An extra
    # nested index/maps/etc. must not shadow the root resource we validated.
    reserved = {name + '.json' for name in CONTRACT['resource_json']} | {'index.json'}
    require(not any('/' in name and name.rsplit('/', 1)[-1] in reserved for name in cartridge),
            'Nested JSON resource shadows a reserved editor filename')
    require(all(s in cartridge for s in scripts), 'Missing script')
    validate_resources(cartridge)
    if 'sprites.json' not in cartridge:
        require('sprites.png' in cartridge, 'Missing sprites')
        sw, sh = png_size(cartridge['sprites.png'])
        require(1 <= sw <= image_rules['maxSide'] and 1 <= sh <= image_rules['maxSide'] and
                sw * sh <= image_rules['maxPixelsPerImage'], 'Sprite sheet exceeds decoded image budget')
    for name, raw in cartridge.items():
        if name.endswith('.js'):
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


def blob_response_limit(size):
    # GitHub wraps base64 at 60 columns; each newline occupies two JSON bytes.
    # This transport allowance does not change decoded file/resource budgets.
    encoded = 4 * ((size + 2) // 3)
    return encoded + 2 * ((encoded + 59) // 60) + 65536


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
    directories = 0
    total = 0
    while pending:
        prefix, sha = pending.pop()
        directories += 1
        require(directories <= MAX_FILES * LIMITS['pathLength'] // 2, 'Too many cartridge directories')
        tree = api(f'/repos/{repository}/git/trees/{sha}')
        require(not tree.get('truncated') and len(tree['tree']) <= MAX_FILES, 'Oversized tree')
        for entry in tree['tree']:
            if metadata_only and (prefix or entry['path'] != 'submission.json'):
                continue
            name = prefix + entry['path']
            require(safe_path(name), 'Unsafe path')
            if entry['type'] == 'tree':
                require(name == 'cartridge' or name.startswith('cartridge/'), 'Unexpected subdirectory')
                pending.append((name + '/', entry['sha']))
                continue
            require(entry['type'] == 'blob' and entry['mode'] == '100644', 'Symlinks, executables and submodules are not allowed')
            size = entry.get('size', MAX_EXPANDED + 1)
            total += size
            require(total <= MAX_EXPANDED and size <= MAX_FILE and len(files) < MAX_FILES, 'File budget exceeded')
            blob = api(f'/repos/{repository}/git/blobs/{entry["sha"]}', blob_response_limit(size))
            require(blob.get('encoding') == 'base64', 'Unexpected blob encoding')
            data = base64.b64decode(blob['content'])
            require(len(data) == size, 'Blob size mismatch')
            files[name] = data
    return files, root_sha


def current_review_pr(event_pr, current):
    # Reruns retain the old webhook names after an owner/repository rename.
    # Match immutable repository IDs, then use fresh server-owned PR metadata.
    base = current['base']
    require(base['repo']['full_name'] == REPO and base['ref'] == 'main', 'Unexpected PR target')
    repo_id = base['repo'].get('id')
    require(type(repo_id) is int and repo_id > 0 and
            event_pr['base']['repo'].get('id') == repo_id and
            event_pr['base']['ref'] == 'main' and
            event_pr['number'] == current['number'], 'PR event repository identity changed')
    require(current['head']['sha'] == event_pr['head']['sha'], 'PR changed; wait for its newer check')
    return current


def check_pr(event_path, output):
    event = json.loads(Path(event_path).read_text())
    pr = event['pull_request']
    current = api(f'/repos/{REPO}/pulls/{pr["number"]}')
    pr = current_review_pr(pr, current)
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
    warnings = compatibility_warnings(files)
    output.mkdir(parents=True, exist_ok=True)
    (output / f'{cart_id}.zip').write_bytes(raw)
    (output / 'review.json').write_bytes(json_bytes({'id': cart_id, 'version': meta['version'], 'author_id': meta['author_id'], 'head_sha': pr['head']['sha'], 'submission_revision': revision, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'compatibility_warnings': warnings}))
    for warning in warnings:
        print('Compatibility warning: ' + warning)
    print('Validated one cartridge; candidate ZIP is available as a workflow artifact.')


def local_files(directory):
    files = {}
    for p in directory.rglob('*'):
        require(not p.is_symlink(), 'Symlinks are not allowed')
        if p.is_file():
            require(p.stat().st_size <= MAX_FILE, 'File too large')
            files[p.relative_to(directory).as_posix()] = p.read_bytes()
            require(len(files) <= MAX_FILES and sum(map(len, files.values())) <= MAX_EXPANDED, 'Cartridge exceeds file budget')
    return files


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True).strip()


def release_asset(tag, filename, raw, commit):
    """Existing version assets are immutable; retries verify rather than overwrite."""
    existing = None
    # The tag endpoint excludes drafts. Page the authenticated release listing
    # so retries also recover drafts older than the first 100 releases.
    for page in range(1, 1001):
        listed = json.loads(gh('api', f'repos/{REPO}/releases?per_page=100&page={page}'))
        require(isinstance(listed, list), 'Cannot determine existing Release state')
        existing = next((r for r in listed if r['tag_name'] == tag), None)
        if existing is not None or len(listed) < 100:
            break
    else:
        raise ValueError('Release listing exceeds safe paging limit; refusing to create a duplicate')
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / filename
        path.write_bytes(raw)
        if existing is None:
            # Creation returns the draft and its numeric ID directly. Never
            # immediately look it up through the public tag endpoint.
            existing = json.loads(gh('api', '--method', 'POST', f'repos/{REPO}/releases',
                                     '-f', f'tag_name={tag}', '-f', f'target_commitish={commit}',
                                     '-f', f'name={tag}', '-f', 'body=Reviewed Turbo8 community cartridge.',
                                     '-F', 'draft=true', '-f', 'make_latest=false'))
        require(isinstance(existing, dict) and type(existing.get('id')) is int and
                existing['id'] > 0 and existing.get('tag_name') == tag and
                isinstance(existing.get('assets'), list), 'Invalid Release response')
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
            gh('api', '--method', 'PATCH', f'repos/{REPO}/releases/{existing["id"]}',
               '-F', 'draft=false', '-f', 'make_latest=false')
    # Verify public delivery before exposing a catalog entry.
    public = f'https://github.com/{REPO}/releases/download/{tag}/{filename}'
    for attempt in range(4):
        url = public if attempt == 0 else f'{public}?verify={time.time_ns()}'
        request = urllib.request.Request(url)
        if attempt >= 2:
            # Read anonymously through GitHub's asset API when its web gateway is down.
            if not asset:
                fresh = json.loads(gh('api', f'repos/{REPO}/releases/{existing["id"]}'))
                asset = next(a for a in fresh['assets'] if a['name'] == filename)
            request = urllib.request.Request(
                f'https://api.github.com/repos/{REPO}/releases/assets/{int(asset["id"])}',
                headers={'Accept': 'application/octet-stream'})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                downloaded = response.read(MAX_ZIP + 1)
            break
        except urllib.error.HTTPError as error:
            if error.code not in (502, 503, 504) or attempt == 3:
                raise
            print(f'Retrying public verification of {filename} after HTTP {error.code}', flush=True)
            time.sleep(2 ** attempt)
    require(downloaded == raw, 'Public Release download verification failed')


def build(root, output, publish=False, unlisted=None):
    require(not output.exists(), 'Output directory must be new')
    if unlisted is None:
        unlisted = moderation.ledger(moderation.current_catalog()) if publish else {}
    moderation.ledger({'unlisted': unlisted})
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
        entries[directory.name] = {'id': directory.name, 'title': meta['title'], 'version': meta['version'], 'tag': tag, 'asset': asset, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'resolution': resolution, 'author_id': meta['author_id'], 'summary': meta['summary'], 'submission_revision': revision}
        (output / 'covers').mkdir(exist_ok=True)
        (output / 'covers' / (directory.name + '.png')).write_bytes(cover)
    # All curated and reviewed entries share one immutable thumbnail namespace.
    covers = cover_assets.generate(list(entries.values()), output)
    if publish:
        cover_assets.publish(covers, commit, gh)
        add_publication_times(entries.values())
    # Also improve discovery in older clients that render the server order.
    manifest['cartridges'] = sorted(moderation.visible(entries.values(), unlisted), key=lambda x: (-publication_time(x.get('updated_at')), x['title'].casefold(), x['id']))
    manifest['unlisted'] = unlisted
    manifest['source_commit'] = commit
    require(len(json_bytes(manifest)) <= moderation.MAX_MANIFEST, 'Catalog including visibility history exceeds 1 MiB')
    (output / 'catalog-v2.json').write_bytes(json_bytes(manifest))
    if publish:
        cover_assets.publish_catalog(json_bytes(manifest), gh)
    legacy = dict(manifest, cartridges=[x for x in manifest['cartridges'] if x['bytes'] <= 8 * 1024 * 1024])
    (output / 'catalog.json').write_bytes(json_bytes(legacy))
    print(f'Built {len(manifest["cartridges"])} visible entries; retained {len(unlisted)} unlisting records and all release assets.')


def publication_time(value):
    from datetime import datetime, timezone
    try:
        return int(datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp())
    except (ValueError, TypeError):
        return 0


def add_publication_times(entries):
    """Use immutable public asset creation dates, never the current build time."""
    releases = {}
    for entry in entries:
        tag = entry['tag']
        if tag not in releases:
            releases[tag] = json.loads(gh('api', f'repos/{REPO}/releases/tags/{tag}'))
        release = releases[tag]
        asset = next((a for a in release['assets'] if a['name'] == entry['asset']), None)
        require(asset is not None, 'Published catalog asset is missing: ' + entry['asset'])
        date = asset.get('created_at') or release.get('published_at')
        require(publication_time(date) > 0, 'Published asset has no valid timestamp')
        entry['updated_at'] = date


def verify_pages(expected):
    wanted = json.loads(expected.read_text())
    digest = hashlib.sha256(json_bytes(wanted)).hexdigest()
    for attempt in range(12):
        url = f'https://turbo8-coder.github.io/turbo8-catalog/catalog-v2.json?revision={wanted["source_commit"]}&manifest={digest}&attempt={attempt}'
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                actual = json.loads(response.read(1024 * 1024))
            if actual == wanted:
                cover_assets.verify(wanted['cartridges'], 'https://turbo8-coder.github.io/turbo8-catalog/')
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
    unlist = commands.add_parser('unlist')
    unlist.add_argument('--root', type=Path, default=Path('.'))
    unlist.add_argument('--output', type=Path, required=True)
    unlist.add_argument('--id', required=True)
    unlist.add_argument('--expected-sha', required=True)
    unlist.add_argument('--request-id', required=True)
    unlist.add_argument('--preview', action='store_true')
    unlist.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    if args.command == 'check-pr':
        check_pr(args.event, args.output)
    elif args.command == 'build':
        build(args.root.resolve(), args.output.resolve(), args.publish)
    elif args.command == 'unlist':
        actor, actor_id = moderation.require_admin(api, REPO)
        current = moderation.current_catalog()
        records = (moderation.plan_restore(current, args.id, args.expected_sha) if args.restore else
                   moderation.plan_unlist(current, args.id, args.expected_sha, args.request_id, actor, actor_id))
        if args.preview:
            print('Authorized preview succeeded. No catalog, Release or local files were changed.')
        else:
            build(args.root.resolve(), args.output.resolve(), True, records)
    else:
        verify_pages(args.expected)


if __name__ == '__main__':
    main()
