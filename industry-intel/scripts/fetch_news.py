#!/usr/bin/env python3
"""
成人行业新闻抓取脚本
收集成人行业大事件、新玩法、竞品动态
"""

import subprocess
import json
import re
from datetime import datetime

# 行业关键词
INDUSTRY_KEYWORDS = [
    'onlyfans', 'fansly', 'sealed', 'pornhub', 'adult',
    'content creator', 'subscription', 'monetization',
    '成人内容', '变现', '付费', '订阅',
]

def fetch_avn_news():
    """抓取AVN新闻（英文成人行业媒体）"""
    # AVN.com RSS feed
    url = "https://avn.com/feed"
    
    try:
        result = subprocess.run(
            ['curl', '-sL', '--max-time', '15', url],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            # 简单解析RSS
            titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', result.stdout)
            links = re.findall(r'<link>(.*?)</link>', result.stdout)
            
            news = []
            for title, link in zip(titles[1:6], links[1:6]):  # 跳过第一个（通常是feed标题）
                news.append({
                    'title': title,
                    'link': link,
                    'source': 'AVN',
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
            return news
    except Exception as e:
        print(f"AVN获取失败: {e}")
    return []

def fetch_xbiz_news():
    """抓取XBIZ新闻"""
    url = "https://xbiz.com/feed"
    
    try:
        result = subprocess.run(
            ['curl', '-sL', '--max-time', '15', url],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', result.stdout)
            
            news = []
            for title in titles[1:6]:
                news.append({
                    'title': title,
                    'link': 'https://xbiz.com',
                    'source': 'XBIZ',
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
            return news
    except Exception as e:
        print(f"XBIZ获取失败: {e}")
    return []

def fetch_reddit_news():
    """从Reddit获取行业讨论"""
    # 使用公开API获取热门帖
    subs = ["AdultCreators", "OnlyFans裸奔", "China_irl"]
    all_news = []
    
    for sub in subs:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
            result = subprocess.run(
                ['curl', '-s', '-H', 'User-Agent: Mozilla/5.0', url],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                children = data.get('data', {}).get('children', [])
                
                for post in children[:5]:
                    title = post['data'].get('title', '')
                    score = post['data'].get('score', 0)
                    
                    # 检查是否与行业相关
                    title_lower = title.lower()
                    is_relevant = any(kw in title_lower for kw in INDUSTRY_KEYWORDS)
                    
                    if is_relevant or score > 100:
                        all_news.append({
                            'title': title,
                            'link': post['data'].get('url', ''),
                            'source': f'Reddit/{sub}',
                            'score': score,
                            'date': datetime.now().strftime('%Y-%m-%d')
                        })
        except Exception as e:
            print(f"Reddit/{sub} 获取失败: {e}")
    
    return all_news

def fetch_hacker_news():
    """获取Hacker News中的相关创业/科技新闻"""
    try:
        # 获取top stories
        result = subprocess.run(
            ['curl', '-s', 'https://hacker-news.firebaseio.com/v0/topstories.json'],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode != 0:
            return []
        
        story_ids = json.loads(result.stdout)[:30]
        news = []
        
        for sid in story_ids:
            story_result = subprocess.run(
                ['curl', '-s', f'https://hacker-news.firebaseio.com/v0/item/{sid}.json'],
                capture_output=True, text=True, timeout=5
            )
            if story_result.returncode == 0:
                story = json.loads(story_result.stdout)
                title = story.get('title', '')
                
                # 检查是否与内容变现/创业相关
                keywords = ['creator', 'subscription', 'content', 'platform', 
                           'startup', 'revenue', 'million', 'launch']
                
                title_lower = title.lower()
                if any(kw in title_lower for kw in keywords):
                    news.append({
                        'title': title,
                        'link': story.get('url', f'https://news.ycombinator.com/item?id={sid}'),
                        'source': 'HackerNews',
                        'score': story.get('score', 0),
                        'date': datetime.now().strftime('%Y-%m-%d')
                    })
        
        return news[:5]  # 只取前5条最相关的
    except Exception as e:
        print(f"HN获取失败: {e}")
    return []

def analyze_news(news_list):
    """分析新闻，分类整理"""
    categories = {
        'big_events': [],      # 大事件
        'new_patterns': [],   # 新玩法
        'competitors': [],     # 竞品动态
        'monetization': []    # 商业化
    }
    
    monetization_keywords = ['revenue', 'million', 'billion', 'paid', 'subscription', 'pay', 'monetize', '变现', '付费', '赚钱']
    pattern_keywords = ['new', 'launch', 'feature', 'update', 'release', '玩法', '新功能', '创新']
    competitor_keywords = ['platform', 'app', 'site', 'onlyfans', 'fansly', 'sealed', '平台', '网站']
    
    for news in news_list:
        title_lower = news['title'].lower()
        
        if any(kw in title_lower for kw in monetization_keywords):
            categories['monetization'].append(news)
        elif any(kw in title_lower for kw in pattern_keywords):
            categories['new_patterns'].append(news)
        elif any(kw in title_lower for kw in competitor_keywords):
            categories['competitors'].append(news)
        else:
            categories['big_events'].append(news)
    
    return categories

def format_report(news_list, categories):
    """格式化新闻报告"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    report = f"""# 📰 成人行业情报日报 - {today}

## 一、今日大事件

"""
    
    for news in categories['big_events'][:5]:
        report += f"### {news['title']}\n"
        report += f"- 来源: {news['source']}"
        if news.get('score'):
            report += f" | 热度: {news['score']}票"
        report += "\n"
        if 'reddit' not in news['link']:
            report += f"- 链接: {news['link']}\n"
        report += "\n"
    
    report += """
## 二、最新玩法

"""
    
    for news in categories['new_patterns'][:5]:
        report += f"### {news['title']}\n"
        report += f"- 来源: {news['source']}"
        if news.get('score'):
            report += f" | 热度: {news['score']}票"
        report += "\n\n"
    
    report += """
## 三、竞品动态

"""
    
    for news in categories['competitors'][:5]:
        report += f"### {news['title']}\n"
        report += f"- 来源: {news['source']}"
        if news.get('score'):
            report += f" | 热度: {news['score']}票"
        report += "\n\n"
    
    report += """
## 四、商业化新模式

"""
    
    for news in categories['monetization'][:5]:
        report += f"### {news['title']}\n"
        report += f"- 来源: {news['source']}"
        if news.get('score'):
            report += f" | 热度: {news['score']}票"
        report += "\n\n"
    
    report += f"""
---

_数据来源：AVN / XBIZ / Reddit / HackerNews_
_生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_
"""
    
    return report

def main():
    print("正在抓取行业新闻...\n")
    
    all_news = []
    
    # 获取各来源新闻
    print("抓取 AVN...")
    all_news.extend(fetch_avn_news())
    
    print("抓取 XBIZ...")
    all_news.extend(fetch_xbiz_news())
    
    print("抓取 Reddit...")
    all_news.extend(fetch_reddit_news())
    
    print("抓取 HackerNews...")
    all_news.extend(fetch_hacker_news())
    
    print(f"\n共获取 {len(all_news)} 条新闻")
    
    # 分类整理
    categories = analyze_news(all_news)
    
    # 生成报告
    report = format_report(all_news, categories)
    print("\n" + report)
    
    # 保存
    output_path = '/root/.openclaw/workspace/industry_news_report.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n报告已保存: {output_path}")

if __name__ == '__main__':
    main()

