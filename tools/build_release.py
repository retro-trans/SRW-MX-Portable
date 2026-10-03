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
    parser.add_argument('--retro-trans-root', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r'0\.\d+\.\d+', args.version):
        parser.error('Use a 0.x.y build version.')
    if args.retro_trans_root:
        sys.path.insert(0, str(args.retro_trans_root.resolve()))
    import retro_trans.release as release
    from retro_trans.release import build_release, validate_directory
    # ISO file relocation can exceed xdelta's default source window. Let it
    # reference the full original image; otherwise unchanged large game files
    # become literal patch data. Decoding and validation stay with Retro Trans.
    def encode_full_source(engine, source, modified, destination, cancel=None, progress=None):
        from retro_trans.core import check_cancel, PatchError
        check_cancel(cancel)
        if progress:
            progress('Creating xdelta patch with full source window', None)
        window = 1 << max(20, (source.stat().st_size - 1).bit_length())
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
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=str(ROOT), text=True).strip()
    local = ROOT / 'work/build' / ('release_' + args.version)
    local.mkdir(parents=True, exist_ok=True)
    config = {
        'game_id': 'srw-mx-portable', 'game_name': 'Super Robot Taisen MX Portable',
        'platform': 'PSP', 'version': args.version, 'source_commit': commit,
        'patches': [{
            'patch': 'SRWMX-English-v%s.xdelta' % args.version,
            'edition': 'ULJS-00041', 'language': 'en', 'source_version': 'original',
            'source_format': 'iso', 'target_format': 'iso',
            'source': str(args.source.resolve()), 'target': str(args.target.resolve())
        }]
    }
    config_path = local / 'config.json'
    config_path.write_text(json.dumps(config, indent=2) + '\n', encoding='utf8')
    output = args.output or ROOT / 'work/output' / ('release-v' + args.version)
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
