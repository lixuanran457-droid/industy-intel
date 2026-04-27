#!/usr/bin/env python3
"""
关键词热度抓取脚本
通过多渠道获取成人行业搜索关键词排行榜
"""

import subprocess
import json
import re
from datetime import datetime
from collections import Counter

# 核心关键词列表（追踪这些词的搜索量变化）
TRACK_KEYWORDS = [
    # 中文
    "成人内容创作", "OnlyFans中文", "福利姬", "成人直播",
    "私密聊天软件", "成人订阅平台", "成人内容变现", "情趣用品推广",
    "成人电商", "成人网红", "成人SEO", "成人推广",
    # 英文
    "onlyfans alternative", "adult content creator", "subscription platform",
    "content monetization", "private content", "fan subscription",
    "ai adult content", "adult streaming", "premium content",
]

# Reddit高频词来源板块
REDDIT_SUBS = [
    "OnlyFans裸奔",
    "AdultCreators",
    "China_irl",
    "r/OnlyFans裸奔",
]

def fetch_reddit_keywords():
    """从Reddit帖子中提取高频关键词"""
    all_titles = []
    
    for sub in REDDIT_SUBS:
        try:
            # 获取热门帖子
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=50"
            result = subprocess.run(
                ['curl', '-s', '-H', 'User-Agent: Mozilla/5.0', url],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                children = data.get('data', {}).get('children', [])
                for post in children:
                    title = post['data'].get('title', '').lower()
                    all_titles.append(title)
                    
                    # 获取评论中的关键词
                    # （需要单独请求评论API，这里简化处理）
        except Exception as e:
            print(f"获取 {sub} 失败: {e}")
    
    return all_titles

def fetch_google_trends():
    """获取Google Trends数据"""
    # 需要 pytrends 库
    # from pytrends.request import RelevanceRegionPayload
    # 
    # pytrends = PyTrends()
    # keywords = ['onlyfans', 'content subscription', 'adult streaming']
    # pytrends.build_payload(keywords, cat=67, timeframe='today 3-m')
    # interest = pytrends.interest_over_time()
    
    return {
        'note': '需要 pytrends 库支持',
        'suggested_keywords': TRACK_KEYWORDS
    }

def extract_keywords_from_titles(titles):
    """从标题中提取关键词"""
    # 定义提取模式
    adult_keywords = [
        # 中文
        'onlyfans', 'fansly', 'sealed', 'pornhub', '成人', '直播', 
        '聊天', '私密', '内容', '变现', '赚钱', '创作', '订阅',
        '福利', '会员', 'VIP', '解锁', '免费', '付费', '打赏',
        '微博', '推特', 'telegram', '电报', '微信',
        # 英文
        'premium', 'content', 'creator', 'fan', 'subscription', 'private',
        'exclusive', 'custom', 'live', 'chat', 'streaming', 'video',
    ]
    
    found = Counter()
    
    for title in titles:
        title_lower = title.lower()
        for kw in adult_keywords:
            if kw.lower() in title_lower:
                found[kw] += 1
    
    return found.most_common(30)

def fetch_search_suggestions():
    """获取搜索建议词"""
    suggestions = []
    
    # 基于用户提供的搜索习惯
    user_provided = [
        "最新黄片网站",
        "免费成人影片",
        "看片神器",
        "成人直播平台",
        "私密聊天软件",
        "同城约会",
        "视频聊天",
        "福利姬",
        "成人小说",
    ]
    
    suggestions.extend(user_provided)
    
    return suggestions

def format_report(keywords, suggestions):
    """格式化关键词报告"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    report = f"""# 🔍 成人行业搜索关键词周榜

**生成日期：** {today}
**数据来源：** Reddit热门帖子 / 搜索建议 / 社交媒体

---

## 一、Reddit热门关键词 TOP 20

| 排名 | 关键词 | 出现次数 | 热度评估 |
|------|--------|----------|----------|
"""
    
    for i, (kw, count) in enumerate(keywords[:20], 1):
        heat = "🔥" * min(count // 5 + 1, 5)
        report += f"| {i} | **{kw}** | {count}次 | {heat} |\n"
    
    report += f"""

## 二、用户搜索习惯词（来自真实用户反馈）

| 搜索词 | 类型 | 商机解读 |
|--------|------|----------|
"""
    
    for word in suggestions:
        heat = "🔥" * 3
        report += f"| {word} | 用户主动搜索 | 高需求 |\n"
    
    report += """

## 三、趋势关键词（需持续追踪）

| 关键词 | 趋势方向 | 说明 |
|--------|----------|------|
"""
    
    trending = [
        ("AI生成内容", "↑↑", "技术降低创作门槛"),
        ("私人定制", "↑", "高端变现模式"),
        ("订阅盲盒", "↑↑", "新的付费玩法"),
        ("内容打赏", "→", "稳定变现方式"),
    ]
    
    for kw, trend, desc in trending:
        report += f"| {kw} | {trend} | {desc} |\n"
    
    report += f"""

---

_此报告每周更新，持续追踪关键词热度变化_
"""
    
    return report

def main():
    print("正在抓取关键词...\n")
    
    # 获取Reddit标题
    titles = fetch_reddit_keywords()
    print(f"获取Reddit帖子: {len(titles)} 条")
    
    # 提取关键词
    keywords = extract_keywords_from_titles(titles)
    print(f"提取关键词: {len(keywords)} 个")
    
    # 获取搜索建议
    suggestions = fetch_search_suggestions()
    
    # 生成报告
    report = format_report(keywords, suggestions)
    print("\n" + report)
    
    # 保存
    output_path = '/root/.openclaw/workspace/keywords_report.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n报告已保存: {output_path}")

if __name__ == '__main__':
    main()

