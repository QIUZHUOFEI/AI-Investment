#!/usr/bin/env python3
"""
Pre-commit hook: 在 git commit 前，自动为所有修改过的 .md 文件补上/更新时间戳。

用法：
  1. 把这个脚本放到项目的 .git/hooks/pre-commit（或 scripts/ 目录下）
  2. 如果用 .git/hooks/ 方式，改名为 pre-commit 并 chmod +x
  3. 如果用 scripts/ 方式，在 .git/hooks/pre-commit 里调用它

时间戳格式：*最后更新：YYYY-MM-DD HH:MM（北京时间）*
"""

import os
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta

# 北京时间
BEIJING = timezone(timedelta(hours=8))
NOW = datetime.now(BEIJING)
TIMESTAMP = f"*最后更新：{NOW.strftime('%Y-%m-%d %H:%M')}（北京时间）*"

# 匹配已有时间戳（允许行尾或有后续内容）
TIMESTAMP_RE = re.compile(r'\*最后更新：\d{4}-\d{2}-\d{2} \d{2}:\d{2}（北京时间）\*')

# 只处理 docs/ 目录下的 .md 文件
INCLUDE_PATHS = ('docs/',)
# 项目根目录
PROJECT_ROOT = subprocess.check_output(
    ['git', 'rev-parse', '--show-toplevel'],
    text=True
).strip()


def get_staged_md_files() -> list[str]:
    """获取本次 commit 中 staged 的 .md 文件（相对于项目根目录）"""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'],
        capture_output=True, text=True
    )
    files = []
    for f in result.stdout.strip().split('\n'):
        f = f.strip()
        if not f:
            continue
        if not f.endswith('.md'):
            continue
        if not any(f.startswith(p) for p in INCLUDE_PATHS):
            continue
        files.append(f)
    return files


def ensure_timestamp(filepath: str) -> bool:
    """确保文件末尾有时间戳。返回 True 表示有改动。"""
    full_path = os.path.join(PROJECT_ROOT, filepath)
    if not os.path.exists(full_path):
        return False

    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 只查最后 5 行
    lines = content.split('\n')
    tail = '\n'.join(lines[-5:]) if len(lines) > 5 else content

    match = TIMESTAMP_RE.search(tail)
    if match:
        # 更新时间戳
        old_ts = match.group(0)
        if old_ts == TIMESTAMP:
            return False  # 时间没变，跳过
        new_content = content.replace(old_ts, TIMESTAMP, 1)
    else:
        # 追加时间戳（确保末尾有空行）
        content = content.rstrip('\n') + '\n\n' + TIMESTAMP + '\n'
        new_content = content

    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return True


def main():
    staged = get_staged_md_files()
    if not staged:
        return 0  # 没有需要处理的 .md 文件

    modified = []
    for f in staged:
        if ensure_timestamp(f):
            modified.append(f)

    if modified:
        # 重新 git add 修改过的文件
        subprocess.run(['git', 'add'] + modified, capture_output=True)
        print(f"⏰ 自动更新了 {len(modified)} 个文件的时间戳:")
        for f in modified:
            print(f"   • {f}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
