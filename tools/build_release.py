"""Build a Retro Trans compatible release from local source and target ISOs.

Requires Python 3.12+ and an installed retro-trans-tools package, or its checkout
passed with --retro-trans-root. Game binaries and configuration remain local.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('target', type=Path)
    parser.add_argument('version')
    parser.add_argument('--platform', choices=('PSP', 'PS2'), default='PSP')
    parser.add_argument('--retro-trans-root', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--upgrade-source', nargs=2, action='append', default=[],
                        metavar=('VERSION', 'ISO'), help='Add a patch from an exact published English image.')
    parser.add_argument('--source-commit', help='Keep the original game-source commit when extending an existing release.')
    args = parser.parse_args()
    if not re.fullmatch(r'0\.\d+\.\d+', args.version):
        parser.error('Use a 0.x.y build version.')
    for version, _ in args.upgrade_source:
        if not re.fullmatch(r'0\.\d+\.\d+', version) or version == args.version:
            parser.error('Upgrade source versions must be distinct 0.x.y versions.')
    if args.retro_trans_root:
        sys.path.insert(0, str(args.retro_trans_root.resolve()))
    import retro_trans.release as release
    from retro_trans.release import build_release, validate_directory
    # PSP file relocation needs the full original source window. PS2 retains
    # original LBAs; use a sliding window instead of indexing its entire >2GB
    # image, which produces an unnecessarily large patch with the Windows engine.
    # Decoding and validation stay with Retro Trans.
    def encode_full_source(engine, source, modified, destination, cancel=None, progress=None):
        from retro_trans.core import check_cancel, PatchError
        check_cancel(cancel)
        if progress:
            progress('Creating xdelta patch', None)
        window = 1 << max(20, (source.stat().st_size - 1).bit_length())
        if args.platform == 'PS2':
            window = min(window, 512 * 1024 * 1024)
        import os
        env = os.environ.copy()
        env.pop('XDELTA', None)
        result = subprocess.run(
            [str(engine), '-e', '-D', '-A', '-B', str(window), '-s', str(source), str(modified), str(destination)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            env=env, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        check_cancel(cancel)
        if result.returncode:
            raise PatchError('Could not encode patch: ' + result.stderr[:4096].decode('utf8', errors='replace'))
    release.encode = encode_full_source
    commit = args.source_commit or subprocess.check_output(['git', '-c', 'safe.directory=' + str(ROOT), 'rev-parse', 'HEAD'], cwd=str(ROOT), text=True).strip()
    local = ROOT / 'work/build' / ('release_' + args.platform.lower() + '_' + args.version + ('_upgrades' if args.upgrade_source else ''))
    local.mkdir(parents=True, exist_ok=True)
    is_ps2 = args.platform == 'PS2'
    prefix = 'SRWMX-PS2-English' if is_ps2 else 'SRWMX-English'
    edition = 'SLPS-25345' if is_ps2 else 'ULJS-00041'
    config = {
        'game_id': 'srw-mx' if is_ps2 else 'srw-mx-portable',
        'game_name': 'Super Robot Taisen MX' if is_ps2 else 'Super Robot Taisen MX Portable',
        'platform': args.platform, 'version': args.version, 'source_commit': commit,
        'patches': [{
            'patch': '%s-v%s.xdelta' % (prefix, args.version),
            'edition': edition, 'language': 'en', 'source_version': 'original',
            'source_format': 'iso', 'target_format': 'iso',
            'source': str(args.source.resolve()), 'target': str(args.target.resolve())
        }]
    }
    for version, path in args.upgrade_source:
        config['patches'].append({
            'patch': '%s-v%s-to-v%s.xdelta' % (prefix, version, args.version),
            'edition': edition, 'language': 'en', 'source_version': version,
            'source_format': 'iso', 'target_format': 'iso',
            'source': str(Path(path).resolve()), 'target': str(args.target.resolve())
        })
    config_path = local / 'config.json'
    config_path.write_text(json.dumps(config, indent=2) + '\n', encoding='utf8')
    output = args.output or ROOT / 'work/output' / ('release-' + args.platform.lower() + '-v' + args.version)
    previous = [None]
    def progress(message, fraction=None):
        if message != previous[0]:
            print(message, flush=True)
            previous[0] = message
    build_release(config_path, output, progress=progress, cache=local / 'engine-cache')
    validate_directory(output)
    print('Verified release built:', output)


if __name__ == '__main__':
    main()
