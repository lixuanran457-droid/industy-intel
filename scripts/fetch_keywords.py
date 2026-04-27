#!/usr/bin/env python3
"""
关键词热度抓取脚本 v4 - 修复版
✅ 修复固定score=5问题
✅ 使用草榴论坛频次作为中文热度真实来源
✅ Reddit 热词作为英文来源
✅ 中文词库频次加权打分，不同来源有不同权重
"""

import subprocess, json, re
from datetime import datetime
from collections import Counter

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

# 分类关键词
CONTENT_KW = [
    "探花","素人","国产","乱伦","自拍","真实","人妻","换妻",
    "麻豆","天美传媒","91制片厂","蜜桃影视","偷拍","露出",
    "福利姬","国产原创","外围","搭讪","调教","短视频",
]
BIZ_KW = [
    "成人内容变现","付费社群","成人直播","成人订阅",
    "成人SEO","私域变现","成人推广","成人APP",
    "情趣用品","成人电商","OnlyFans中文","裂变推广",
]

def fetch_caoliu_keywords():
    """
    从草榴论坛帖标题提取高频词
    草榴是目前唯一可自动访问的中文成人论坛
    帖子标题中词频 = 真实用户关注热度
    """
    print("  [中文] 草榴论坛关键词频次分析...")
    all_titles = []
    fid_map = {"7":"网站资源","2":"综合讨论","9":"成人商业","5":"技术讨论","15":"影音资源"}
    for fid, name in fid_map.items():
        url = f"https://t66y.com/thread0806.php?fid={fid}"
        content = curl_get(url, use_jina=True)
        if not content:
            continue
        titles = re.findall(r'##+ (.{5,80})', content)
        all_titles.extend(titles)
        print(f"    ✓ 草榴-{name}: {len(titles)}个标题")

    # 统计关键词出现频次
    freq = Counter()
    for title in all_titles:
        for kw in CONTENT_KW + BIZ_KW + ['新站','平台','APP','直播','视频','变现','运营','推广']:
            if kw in title:
                freq[kw] += 1

    results = []
    for kw, count in freq.most_common(20):
        # 草榴频次 x3 (高权重，真实数据)
        score = min(count * 3 + 5, 30)
        trend = '↑↑↑' if count >= 5 else '↑↑' if count >= 3 else '↑' if count >= 2 else '→'
        results.append({
            'keyword': kw,
            'raw_count': count,
            'score': score,
            'source': '草榴论坛',
            'trend': trend,
            'category': '内容词' if kw in CONTENT_KW else '业务词' if kw in BIZ_KW else '热词'
        })
    print(f"  [中文] 草榴热词: {len(results)}个（总标题{len(all_titles)}篇）")
    return results

def fetch_similarweb_ranking():
    """SimilarWeb 成人站流量排行"""
    print("  [英文] 抓取SimilarWeb成人排行...")
    results = []
    content = curl_get("https://www.similarweb.com/top-websites/adult/", use_jina=True)
    if content:
        entries = re.findall(r'\d+\.\s+([a-zA-Z0-9\.\-]+\.(?:com|net|org|io|tv))', content)
        for i, site in enumerate(entries[:20], 1):
            results.append({'rank': i, 'site': site, 'source': 'SimilarWeb'})
    print(f"    SimilarWeb排行: {len(results)}个")
    return results

def fetch_reddit_keywords():
    """Reddit 热帖关键词频次"""
    print("  [英文] 抓取Reddit关键词...")
    all_text = []
    for url in [
        "https://www.reddit.com/r/AdultCreators/hot/",
        "https://www.reddit.com/r/onlyfansadvice/hot/",
    ]:
        content = curl_get(url, use_jina=True)
        if content:
            titles = re.findall(r'##+ (.{10,150})', content)
            all_text.extend([t.lower() for t in titles[:20]])

    terms = [
        'onlyfans','fansly','fanvue','subscription','creator',
        'income','promote','traffic','ai content','exclusive',
        'earn','alternative','live stream','adult',
    ]
    freq = Counter()
    for text in all_text:
        for t in terms:
            if t in text:
                freq[t] += 1

    results = []
    for kw, count in freq.most_common(10):
        results.append({
            'keyword': kw,
            'raw_count': count,
            'score': min(count * 2, 10),
            'source': 'Reddit',
            'trend': '↑↑' if count >= 4 else '↑' if count >= 2 else '→',
            'category': '英文词'
        })
    print(f"    Reddit热词: {len(results)}个")
    return results

def build_report(caoliu_kw, reddit_kw, traffic):
    """
    整合关键词，生成最终榜单
    评分逻辑：
    - 草榴出现1次 → +3分（基础）+5（固定）
    - Reddit出现1次 → +2分
    - 固定追踪词未出现 → 基础分5（不再是固定的5，而是追踪基准）
    """
    today = datetime.now().strftime('%Y-%m-%d')
    keyword_map = {}

    def add(kw, score, source, trend, category=''):
        kw = kw.strip()
        if not kw or len(kw) < 2:
            return
        if kw in keyword_map:
            keyword_map[kw]['score'] += score
            keyword_map[kw]['sources'].append(source)
        else:
            keyword_map[kw] = {
                'score': score, 'sources': [source],
                'trend': trend, 'category': category
            }

    # 草榴词（最高权重）
    for item in caoliu_kw:
        add(item['keyword'], item['score'], '草榴论坛', item['trend'], item['category'])

    # Reddit词
    for item in reddit_kw:
        add(item['keyword'], item['score'], 'Reddit', item['trend'], '英文词')

    # 固定追踪词 - 确保入榜，但分数低于真实抓到的词
    for kw in CONTENT_KW:
        if kw not in keyword_map:
            add(kw, 5, '固定追踪', '→', '内容词')
    for kw in BIZ_KW:
        if kw not in keyword_map:
            add(kw, 4, '固定追踪', '→', '业务词')

    # 排序
    ranked = sorted(keyword_map.items(), key=lambda x: x[1]['score'], reverse=True)

    top20 = []
    for i, (kw, data) in enumerate(ranked[:20]):
        score = data['score']
        top20.append({
            'rank': i + 1,
            'keyword': kw,
            'score': score,
            'category': data.get('category', ''),
            'source': '+'.join(set(data['sources']))[:50],
            'trend': data['trend'],
            'opportunity': '高' if score >= 20 else '中' if score >= 10 else '低',
            'note': '真实数据' if '草榴论坛' in data['sources'] or 'Reddit' in data['sources'] else '固定追踪基准'
        })

    return {
        'date': today,
        'top_keywords': top20,
        'traffic_ranking': traffic[:10],
        'data_quality': {
            'caoliu_keywords': len(caoliu_kw),
            'reddit_keywords': len(reddit_kw),
            'has_real_data': len(caoliu_kw) > 0 or len(reddit_kw) > 0,
        }
    }

def main():
    print("=== 关键词热度抓取 v4（真实评分）===\n")

    caoliu_kw = fetch_caoliu_keywords()
    reddit_kw  = fetch_reddit_keywords()
    traffic    = fetch_similarweb_ranking()

    report = build_report(caoliu_kw, reddit_kw, traffic)

    output = '/tmp/keywords_data.json'
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 数据已保存: {output}")

    dq = report['data_quality']
    print(f"\n📊 数据质量：")
    print(f"  草榴关键词：{dq['caoliu_keywords']}个 {'✅真实' if dq['caoliu_keywords']>0 else '⚠️未抓到'}")
    print(f"  Reddit关键词：{dq['reddit_keywords']}个")
    print(f"  数据质量：{'✅ 有真实来源' if dq['has_real_data'] else '⚠️ 全部为固定追踪基准'}")

    print("\n🔍 关键词 TOP 10：")
    for item in report['top_keywords'][:10]:
        note = '📡' if item['note'] == '真实数据' else '📌'
        print(f"  {item['rank']}. {note} [{item['category']}] {item['keyword']} | 热度:{item['score']} | {item['trend']} | 商机:{item['opportunity']}")

    return report

if __name__ == '__main__':
    main()
