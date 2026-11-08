"""Small, shared regression cases checked by both Python and the real editor."""
import copy
import json


def cases(fixture):
    result = []

    def add(name, updates=None, accepted=True, index=None):
        files = fixture()
        for resource, value in (updates or {}).items():
            files['cartridge/' + resource + '.json'] = json.dumps(value).encode()
        if index:
            value = json.loads(files['cartridge/index.json'])
            value.update(index)
            files['cartridge/index.json'] = json.dumps(value).encode()
        result.append((name, files, accepted))
        return files

    add('legacy-no-format-label')
    add('writer-1.3', index={'version': '1.3'})
    add('writer-1.4', index={'version': '1.4'})
    add('future-label-compatible-shape', index={'version': '999.0', 'futureMetadata': {'note': 'preserve'}})
    add('optional-json-extension', {'futureAnimation': {'version': 1, 'tracks': []}})
    for name in ('world.render', '7-start', 'a' * 65, 'a' * 128, 'lib/game',
                 'farm and story', '美术资源', 'AUREOLE / FLIGHT', 'trailing.'):
        files = add('script-' + name[:30])
        files['cartridge/' + name + '.js'] = files.pop('cartridge/main.js')
        value = json.loads(files['cartridge/index.json']); value['scripts'] = [name + '.js']
        files['cartridge/index.json'] = json.dumps(value).encode()
    add('script-name-over-editor-limit', accepted=False, index={'scripts': ['a' * 129 + '.js']})
    files = result[-1][1]
    files['cartridge/' + 'a' * 129 + '.js'] = files.pop('cartridge/main.js')
    add('legacy-script-extension-omitted', index={'scripts': ['main']})
    files = add('script-larger-than-old-cloud-limit')
    files['cartridge/main.js'] += b' ' * (2 * 1024 * 1024)
    for value in (False, True):
        add('virtual-controls-' + str(value), {'virtualControls': value})
    add('virtual-controls-numeric-invalid', {'virtualControls': 0}, False)
    add('buttons-empty', {'virtualButtons': []})
    add('buttons-extended', {'virtualButtons': ['A', 'B', 'SELECT', 'START', 'X', 'Y', 'LB', 'RB', 'LT', 'RT']})
    add('buttons-duplicate', {'virtualButtons': ['A', 'A']}, False)
    add('buttons-direction-invalid', {'virtualButtons': ['LEFT']}, False)
    add('optional-resources-legacy-defaults', {'maps': None, 'sfx': {}, 'music': False, 'spriteMeta': [], 'flags': {}})
    valid_map = {'width': 1, 'height': 1, 'tilewidth': 8, 'tileheight': 8,
                 'orientation': 'orthogonal', 'layers': [{'type': 'tilelayer', 'data': [4096]}]}
    add('valid-map', {'maps': [valid_map]})
    for tile_id, accepted in [(0, True), (4097, True), (16384, True), (16385, False), (-1, False)]:
        m = copy.deepcopy(valid_map)
        m['layers'][0]['data'] = [tile_id]
        add(f'map-tile-id-{tile_id}', {'maps': [m]}, accepted)
    add('map-legacy-nine-layers', {'maps': [dict(valid_map, layers=valid_map['layers'] * 9)]})
    add('map-missing-layers', {'maps': [{'width': 0}]}, False)
    for name, change in [('tile-size', {'tilewidth': 16}), ('orientation', {'orientation': 'isometric'}),
                         ('width', {'width': 0}), ('fractional-width', {'width': 1.5})]:
        add('map-invalid-' + name, {'maps': [dict(valid_map, **change)]}, False)
    for name, change in [('length', {'data': []}),
                         ('fractional-id', {'data': [1.5]}), ('offset', {'x': 1})]:
        m = copy.deepcopy(valid_map); m['layers'][0].update(change)
        add('map-invalid-' + name, {'maps': [m]}, False)
    add('sfx-basic', {'sfx': [{'frequency': 440.0, 'duration': .2, 'extraMetadata': 'allowed'}]})
    add('sfx-invalid-type', {'sfx': [{'frequency': '440'}]}, False)
    sound = {'pico_notes': [{'pitch': 63, 'wave': 7, 'volume': 7, 'effect': 7}] * 32,
             'pico_speed': 255, 'pico_loop_start': 0, 'pico_loop_end': 32}
    add('pico-sfx', {'sfx': [sound]})
    add('pico-sfx-missing-note', {'sfx': [dict(sound, pico_notes=sound['pico_notes'][:-1])]}, False)
    add('pico-sfx-invalid-speed', {'sfx': [dict(sound, pico_speed=256)]}, False)
    step = {'notes': [None, 48, 60, None], 'volumes': [0, .5, 1, 0], 'types': ['sine'] * 4}
    song = {'steps': [step], 'pico_channels': [0, 1, 2, 255]}
    add('music-valid', {'music': [song]})
    add('music-empty', {'music': [{'steps': []}]}, False)
    add('music-speed-invalid', {'music': [dict(song, speed='fast')]}, False)
    add('music-channel-invalid', {'music': [dict(song, pico_channels=[0, 1, 2, 256])]}, False)
    add('music-step-invalid', {'music': [{'steps': [dict(step, notes=[None])]}]}, False)
    add('effects-empty-values-valid', {'postEffects': {'values': {}}})
    add('effects-legacy-valid', {'postEffects': {'version': 1, 'values': {'gameboy_glare': .1, 'dot_pitch': 2}}})
    add('effects-missing-values', {'postEffects': {}}, False)
    add('effects-out-of-range', {'postEffects': {'values': {'exposure': 4}}}, False)
    add('effects-unknown-key', {'postEffects': {'values': {'unknown_effect': 1}}}, False)
    add('effects-fractional-enum', {'postEffects': {'values': {'phosphor_mode': .5}}}, False)
    add('effects-numeric-bool', {'postEffects': {'values': {'bloom_on': 1}}}, False)
    add('sprite-metadata-valid', {'spriteMeta': {'0': {'name': 'hero', 'future': 1}}})
    add('sprite-metadata-invalid', {'spriteMeta': {'0': 'hero'}}, False)
    add('flags-fractional-legacy-valid', {'flags': [0, .5, 255]})
    add('flags-truncate-legacy-valid', {'flags': [0] * 4097})
    add('flags-out-of-range', {'flags': [256]}, False)
    add('flags-bool-invalid', {'flags': [True]}, False)
    add('sprite-short-valid', {'sprites': [[None, '#aAbBcC']]})
    for count, accepted in [(4097, True), (16384, True), (16385, False)]:
        add(f'sprite-count-{count}', {'sprites': [[]] * count}, accepted)
    add('sprite-too-long', {'sprites': [[None] * 65]}, False)
    add('palette-invalid', {'palette': ['not-a-color']}, False)
    for width, height, accepted in [(64, 64, True), (512, 384, True), (64, 192, True),
                                     (63, 64, False), (512, 512, False), (64, 193, False)]:
        add('canvas-%d-%d' % (width, height), accepted=accepted, index={'resolution': {'width': width, 'height': height}})
    return result
