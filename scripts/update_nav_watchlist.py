#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导航站 watchlist 更新器
- 读取 references/nav_watchlist.json
- 逐个站点做可达性检查
- 回写 last_verified / status / updated_at
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

PROXY = "http://127.0.0.1:33210"
WATCHLIST_PATH = Path("/root/.openclaw/skills/industry-intel/references/nav_watchlist.json")


def check_site(url):
    # 优先直接访问，失败再走 r.jina.ai
    cmds = [
        ['curl', '-sL', '--max-time', '12', '--proxy', PROXY, url],
        ['curl', '-sL', '--max-time', '12', '--proxy', PROXY, 'https://r.jina.ai/' + url],
    ]
    for cmd in cmds:
        try:
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=15)
            text = (r.stdout or "")[:800]
            if r.returncode == 0 and text:
                low = text.lower()
                if "404" in low and "not found" in low:
                    continue
                if "securitycompromiseerror" in low or "blocked" in low:
                    return "blocked"
                return "ok"
        except Exception:
            pass
    return "down"


def main():
    if not WATCHLIST_PATH.exists():
        raise SystemExit("watchlist 文件不存在: %s" % WATCHLIST_PATH)

    with WATCHLIST_PATH.open('r', encoding='utf-8') as f:
        data = json.load(f)

    now = datetime.now().isoformat(timespec='seconds')

    ok_cnt = 0
    blocked_cnt = 0
    down_cnt = 0

    for s in data.get('sources', []):
        if not s.get('enabled', True):
            continue
        status = check_site(s.get('url', ''))
        s['status'] = status
        s['last_verified'] = now
        if status == 'ok':
            ok_cnt += 1
        elif status == 'blocked':
            blocked_cnt += 1
        else:
            down_cnt += 1

    data['updated_at'] = now

    with WATCHLIST_PATH.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("watchlist updated:")
    print("  ok=%d blocked=%d down=%d" % (ok_cnt, blocked_cnt, down_cnt))
    print("  file=%s" % WATCHLIST_PATH)


if __name__ == '__main__':
    main()

