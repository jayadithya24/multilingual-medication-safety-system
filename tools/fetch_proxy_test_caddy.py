"""Fetch a pinned official portable Caddy release; verify its published checksum."""
import hashlib
import io
import json
from pathlib import Path
import zipfile
import requests

VERSION = 'v2.11.7'
ROOT = Path(__file__).resolve().parents[1]


def main():
    response = requests.get(f'https://api.github.com/repos/caddyserver/caddy/releases/tags/{VERSION}', timeout=30)
    response.raise_for_status()
    release = response.json()
    asset = next(a for a in release['assets'] if a['name'].endswith('_windows_amd64.zip'))
    checksums = next(a for a in release['assets'] if a['name'].endswith('_checksums.txt'))
    payload = requests.get(asset['browser_download_url'], timeout=120)
    payload.raise_for_status()
    manifest = requests.get(checksums['browser_download_url'], timeout=30)
    manifest.raise_for_status()
    expected = next(line.split()[0] for line in manifest.text.splitlines()
                    if line.split()[-1].lstrip('*') == asset['name'])
    algorithm = {64: 'sha256', 128: 'sha512'}.get(len(expected))
    if not algorithm or hashlib.new(algorithm, payload.content).hexdigest() != expected:
        raise RuntimeError('Published checksum mismatch; nothing extracted or executed.')
    digest = asset.get('digest')
    if digest:
        kind, value = digest.split(':', 1)
        if hashlib.new(kind, payload.content).hexdigest() != value:
            raise RuntimeError('GitHub asset digest mismatch; nothing extracted or executed.')
    directory = ROOT / 'artifacts/proxy-test/bin'
    directory.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(payload.content)) as archive:
        # Extract this one known member, never arbitrary archive paths.
        binary = archive.read('caddy.exe')
    (directory / 'caddy.exe').write_bytes(binary)
    record = {'version': VERSION, 'asset': asset['name'], 'published_checksum_algorithm': algorithm,
              'checksum_verified': True, 'archive_sha256': hashlib.sha256(payload.content).hexdigest(),
              'binary_sha256': hashlib.sha256(binary).hexdigest(), 'source': release['html_url']}
    (directory / 'download.json').write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
