"""Classify every archive file by where its exact bytes can be found.

Usage: python3 -I provenance.py <archive manifest> <out.json>
"""
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

S = Path('/tmp/claude-0/-home-user-SIPs/43e7d837-e0f2-5826-bbf5-351964606ee5/scratchpad')
COORD = Path('/home/user/coord')


def manifest(p):
    out = {}
    for line in open(p, encoding='utf-8'):
        h, path = line.rstrip('\n').split('  ', 1)
        out[path] = h
    return out


def tree(root, tracked=None):
    root = Path(root)
    if tracked:
        paths = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'], capture_output=True,
                               check=True).stdout.decode().split('\0')
        files = [root / p for p in paths if p]
    else:
        files = [p for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts]
    out = {}
    for f in files:
        if f.is_file() and not f.is_symlink():
            out[f.relative_to(root).as_posix()] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


SOURCES = {
    'sila-chain/SIPs@de0fadf0': manifest(COORD / 'audit/claude-evidence/manifests/sila-chain-SIPs-de0fadf0.sha256'),
    'claude-batch1-local': manifest(COORD / 'audit/claude-evidence/manifests/sila-chain-SIPs-batch1-local.sha256'),
    'generator(upstream c4f6cf42)': tree(S / 'gen/out'),
    'generator(upstream deb8f0d, latest)': tree(S / 'gen/out-latest'),
    'raw upstream c4f6cf42': tree('/home/user/upstream/base', tracked=True),
    'raw upstream deb8f0d': tree('/home/user/upstream/latest', tracked=True),
    'sila-chain/SRCs@7c5ef3b': tree('/home/user/upstream/srcs-wt', tracked=True),
    'this branch (sila-network/SIPs)': tree(COORD, tracked=True),
}

archive = manifest(sys.argv[1])
by_hash = defaultdict(list)
for src, files in SOURCES.items():
    for path, h in files.items():
        by_hash[h].append((src, path))

rows = []
for path, h in sorted(archive.items()):
    same_path = [src for src, files in SOURCES.items() if files.get(path) == h]
    elsewhere = [(src, p) for src, p in by_hash.get(h, []) if p != path]
    if same_path:
        cls = 'identical at same path'
    elif elsewhere:
        cls = 'identical content at a different path'
    else:
        cls = 'unmatched (archive-specific bytes)'
    rows.append({'path': path, 'sha256': h, 'class': cls, 'same_path_sources': same_path,
                 'other_path_matches': elsewhere[:5]})

json.dump({'sources': {k: len(v) for k, v in SOURCES.items()}, 'rows': rows},
          open(sys.argv[2], 'w'), indent=1)

print('source sizes:', {k: len(v) for k, v in SOURCES.items()})
print('classes:', dict(Counter(r['class'] for r in rows)))
first = Counter()
for r in rows:
    if r['same_path_sources']:
        for src in r['same_path_sources']:
            first[src] += 1
print('same-path matches per source (a file can match several):')
for k, v in first.most_common():
    print(f'  {v:5}  {k}')
area = defaultdict(Counter)
for r in rows:
    top = r['path'].split('/')[0] if '/' in r['path'] else '(root)'
    area[top][r['class']] += 1
print('by area:')
for top, c in sorted(area.items(), key=lambda x: -sum(x[1].values())):
    print(f'  {top:12} {dict(c)}')
