#!/usr/bin/env python3
"""
新闻抓取脚本 v3 - 修复版
✅ 草榴可访问，其他中文来源改为返回清单供人工跟进
"""

import subprocess, json, re
from datetime import datetime

PROXY = "http://127.0.0.1:33210"

def curl_get(url, use_jina=False):
    target = f"https://r.jina.ai/{url}" if use_jina else url
    cmd = ['curl', '-sL', '--max-time', '20', '--proxy', PROXY, target]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True, timeout=25)
        if result.returncode == 0 and result.stdout:
            return result.stdout
    except Exception as e:
        print(f"  curl失败[{url}]: {e}")
    return ""

# ============================================================
# 中文来源（草榴可用）
# ============================================================

def fetch_caoliu_forum():
    """草榴社区最新帖（可访问）"""
    print("  [中文] 抓取草榴最新帖...")
    results = []
    fid_map = {
        "7": "网站资源",
        "2": "综合讨论",
        "9": "成人商业",
        "5": "技术讨论",
    }
    for fid, name in fid_map.items():
        url = f"https://t66y.com/thread0806.php?fid={fid}"
        content = curl_get(url, use_jina=True)
        if not content:
            print(f"    ⚠ {name} 无响应")
            continue
        titles = re.findall(r'##+ (.{5,80})', content)
        print(f"    ✓ {name}: {len(titles)}个标题")
        for title in titles[:8]:
            t = title.strip()
            # 过滤有价值帖子
            if any(kw in t for kw in [
                '网站','平台','推荐','分享','APP','直播','视频',
                '变现','运营','推广','新站','上线','福利','资源','成人'
            ]):
                results.append({'title': t, 'source': f'草榴-{name}', 'url': url, 'type': '论坛帖', 'lang': 'zh'})
    return results[:20]


def fetch_chinese_sources_list():
    """
    中文成人信息来源清单 — 代理不通时返回供人工跟进
    """
    print("  [中文] 中文信息来源清单（代理不通）...")
    return {
        "description": "以下中文成人平台无法通过代理自动访问，需人工访问获取最新动态：",
        "sources": [
            {"name": "91导航",      "url": "https://91navi.com",       "action": "查看新站收录/排行榜"},
            {"name": "夜色导航",    "url": "https://yese.tv",           "action": "查看新站收录/视频站排行"},
            {"name": "草榴论坛",    "url": "https://t66y.com/thread0806.php?fid=7", "action": "查看新站推荐帖"},
            {"name": "91论坛",      "url": "https://91porn.com/forum",  "action": "查看用户讨论/竞品口碑"},
            {"name": "好撸导航",    "url": "https://www.haoLu.info",    "action": "查看新站/APP推荐"},
            {"name": "撸撸吧",      "url": "https://llb.la",            "action": "查看直播/社交平台动态"},
            {"name": "TG中文成人频道", "action": "搜索关键词：成人平台/91/麻豆/福利姬/探花 获取频道列表"},
        ],
        "note": "建议：每日花5分钟手动浏览以上1-2个导航站，记录新竞品URL"
    }


# ============================================================
# 英文来源（保留）
# ============================================================

def fetch_xbiz_news():
    print("  [英文] 抓取XBIZ...")
    news = []
    for sec in ["https://www.xbiz.com/news"]:
        c = curl_get(sec, use_jina=True)
        if not c: continue
        links = re.findall(r'\[([^\]]{10,120})\]\((https://[^\)]+)\)', c)
        for title, link in links[:8]:
            news.append({'title': title.strip(), 'url': link, 'source': 'XBIZ', 'lang': 'en'})
        if news: break
    print(f"    XBIZ: {len(news)}条")
    return news

def fetch_avn_news():
    print("  [英文] 抓取AVN...")
    news = []
    c = curl_get("https://avn.com/business/articles/", use_jina=True)
    if c:
        links = re.findall(r'\[([^\]]{10,120})\]\((https://[^\)]+)\)', c)
        for title, link in links[:6]:
            news.append({'title': title.strip(), 'url': link, 'source': 'AVN', 'lang': 'en'})
    print(f"    AVN: {len(news)}条")
    return news

def fetch_onlyfans_blog():
    print("  [英文] 抓取OF Blog...")
    news = []
    c = curl_get("https://onlyfans.com/blog", use_jina=True)
    if c:
        links = re.findall(r'\[([^\]]{10,100})\]\((https://[^\)]+)\)', c)
        for title, link in links[:4]:
            news.append({'title': title.strip(), 'url': link, 'source': 'OnlyFans Blog', 'lang': 'en'})
    print(f"    OF Blog: {len(news)}条")
    return news


# ============================================================
# main
# ============================================================

def main():
    print("=== 成人行业新闻抓取 v3（中文修复版）===\n")
    today = datetime.now().strftime('%Y-%m-%d')

    cn_forum  = fetch_caoliu_forum()
    cn_list   = fetch_chinese_sources_list()
    en_xbiz   = fetch_xbiz_news()
    en_avn    = fetch_avn_news()
    en_of     = fetch_onlyfans_blog()

    all_news = {
        'date': today,
        'chinese_caoliu_posts': cn_forum,
        'chinese_sources_list': cn_list,
        'xbiz': en_xbiz,
        'avn': en_avn,
        'onlyfans_blog': en_of,
        'total': {
            'chinese': len(cn_forum),
            'english': len(en_xbiz) + len(en_avn) + len(en_of),
        }
    }

    output = '/tmp/news_data.json'
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 数据已保存: {output}")

    print(f"\n📰 抓取摘要：")
    print(f"  🇨🇳 草榴论坛帖：{len(cn_forum)} 条")
    print(f"  🇨🇳 中文来源清单：需人工访问（{len(cn_list['sources'])}个来源）")
    print(f"  🌐 XBIZ：         {len(en_xbiz)} 条")
    print(f"  🌐 AVN：          {len(en_avn)} 条")
    print(f"  🌐 OF Blog：      {len(en_of)} 条")

    return all_news

if __name__ == '__main__':
    main()
