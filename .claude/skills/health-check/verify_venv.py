"""Verify installed packages in a virtualenv against their RECORD sha256 hashes.

Usage (from the repo root, any Python 3 works since it only uses the stdlib):
    python .claude/skills/health-check/verify_venv.py [site-packages-dir]

Without an argument it checks `.venv` (uv), falling back to the legacy `venv`.
Exit code 0 when every installed file matches its published hash, 1 otherwise.
"""
import base64
import csv
import datetime
import glob
import hashlib
import os
import sys
from collections import Counter

ISSUE_URL = 'https://github.com/pirrozani/django-api/issues/1'


def find_site_packages():
    for env_dir in ('.venv', 'venv'):
        candidates = [os.path.join(env_dir, 'Lib', 'site-packages')]
        candidates += glob.glob(os.path.join(env_dir, 'lib', 'python3*', 'site-packages'))
        for path in candidates:
            if os.path.isdir(path):
                return path
    return None


def file_hash(path):
    with open(path, 'rb') as f:
        digest = hashlib.sha256(f.read()).digest()
    return 'sha256=' + base64.urlsafe_b64encode(digest).rstrip(b'=').decode()


def main():
    site_packages = sys.argv[1] if len(sys.argv) > 1 else find_site_packages()
    if not site_packages or not os.path.isdir(site_packages):
        print(f'No environment found (.venv or venv). Run `uv sync`. See {ISSUE_URL}')
        return 1
    print(f'Checking {site_packages}')

    per_package = Counter()
    per_day = Counter()
    problems = []
    for record in glob.glob(os.path.join(site_packages, '*.dist-info', 'RECORD')):
        package = os.path.basename(os.path.dirname(record)).replace('.dist-info', '')
        with open(record, encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) < 2 or not row[1].startswith('sha256='):
                    continue
                path = os.path.join(site_packages, row[0])
                if not os.path.exists(path):
                    problems.append(('MISSING', package, row[0]))
                    per_package[package] += 1
                elif file_hash(path) != row[1]:
                    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
                    problems.append(('MODIFIED', package, row[0]))
                    per_package[package] += 1
                    per_day[mtime.strftime('%Y-%m-%d %H:%M')] += 1

    if not problems:
        print('OK: all installed package files match their RECORD hashes')
        return 0

    print(f'FAIL: {len(problems)} package files differ from their RECORD hashes')
    for package, count in per_package.most_common():
        print(f'  {package}: {count}')
    if per_day:
        print('Modification times:', dict(per_day))
    print(f'Rebuild the environment with uv: {ISSUE_URL}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
