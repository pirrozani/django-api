"""PreToolUse guard: block reading .env files and editing installed packages.

Reads the hook payload (JSON) from stdin. Exit 2 blocks the tool call and
shows the stderr message to Claude; exit 0 lets it through.
"""
import json
import os
import re
import sys

# `.env`, `.env.local`, `.env.production`, ... but not `.env.example`
ENV_FILE = re.compile(r'^\.env(\.(?!example$)[\w.-]+)?$')
ENV_IN_COMMAND = re.compile(r'(?<![\w.-])\.env(?:\.(?!example\b)[\w.-]+)?(?![\w.-])')
VENV_DIRS = {'.venv', 'venv'}
WRITE_IN_COMMAND = re.compile(r'sed\s+(-\w*\s+)*-i|perl\s+-\w*i|\btee\b|(?<![0-9&])>')


def block(reason):
    print(f'Blocked by .claude/hooks/guard.py: {reason}', file=sys.stderr)
    sys.exit(2)


def parts(path):
    return [p for p in re.split(r'[\\/]+', path) if p]


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    tool = payload.get('tool_name', '')
    data = payload.get('tool_input') or {}

    if tool == 'Bash':
        command = data.get('command', '')
        if ENV_IN_COMMAND.search(command):
            block('commands must not touch .env files (secrets). Use .env.example.')
        if 'site-packages' in command and WRITE_IN_COMMAND.search(command):
            block('never modify installed packages. Rebuild the environment with `uv sync` (issue #1).')
        return 0

    path = data.get('file_path') or data.get('path') or ''
    if path and ENV_FILE.match(os.path.basename(path)):
        block(f'{os.path.basename(path)} holds secrets and must not be read or edited. Use .env.example.')
    if tool in ('Edit', 'Write', 'NotebookEdit') and VENV_DIRS & set(parts(path)):
        block('never edit files inside .venv/ or venv/. Rebuild the environment with `uv sync` (issue #1).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
