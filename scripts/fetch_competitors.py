#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""竞品黑马发现脚本 v10 - 精准过滤版"""
import json, re, subprocess, time
from datetime import datetime, date
from pathlib import Path

BASE_DIR  = Path("/root/.openclaw/skills/industry-intel/references")
WATCHLIST = BASE_DIR / "nav_watchlist.json"
HISTORY   = BASE_DIR / "domain_history.json"
PROXY = "http://127.0.0.1:33210"

# 精确黑名单（非成人大站，导航站自身）
SKIP_DOMAINS = {
    "pornhub.com","xvideos.com","xnxx.com","xhamster.com","redtube.com",
    "google.com","baidu.com","youtube.com","twitter.com","reddit.com",
    "wikipedia.org","duckduckgo.com","github.com","cloudflare.com",
    "linkedin.com","facebook.com","spotify.com","weibo.com","qq.com",
    "sina.com","163.com","zhihu.com","taobao.com","jd.com","bilibili.com",
    "douyin.com","iqiyi.com","youku.com","meituan.com","csdn.net",
    "jianshu.com","cnblogs.com","v2ex.com","chacuo.net","360.com",
    "alicdn.com","alipay.com","tencent.com","aliyun.com","mmstat.com",
    "femoon.top","quitarfondo.cc","bonaventura.shop","coronavirus.app",
}
# 导航站自身域名（不算竞品）
KNOWN_NAV = {
    "onefuli.cc","antdh.net","onedh.cc","anyedh.net","fuliapp.org",
    "huaxinba.com","sejie80.com","jiao.se","91navi.com","yese.tv",
    "t66y.com","llb.la","haoLu.info","bluedaohang.club","zkdh.net",
    "wwwnav.com","xnavxx.com","navsmap.com","navw.cn","ainavtool.com",
    "navxd.com","8nav.com","jqnav.top","rrnav.cc","navcrab.com",
    "navs.site","navtools.ai","navfolders.com","ceonav.com","lovnav.cn",
    "yadimnav.com","fuyenav.com","mznav.com","daohangxie.com","swnav.cn",
    "ininav.com","navtool.cn","lovenav.cn","acgdh.cc","navattic.com",
    "lovableapp.org","toolnav.ai","nav-ai.net","xcdaohang.cn","designnavs.com",
    "miaonav.top","xianbaodaohang.com","zjnav.cc","paidaohang.org",
    "lmnavd.top","ykdh.net","yoyonav.com","fuliblue.xyz","qwnav.top",
    "wunav.com","jzdh.cc","juzinav.com","guannav.com","ossnav.com",
    "100nav.com","sexgps.net","fuliba2023.net","hentaidh.net","mitaofuli.xyz",
    "fuliji.biz","ytdhfuli.com","fuliji.cc","daysnavi.com","daysnavi.info",
    "qingmifuli.xyz","yinhufuli.lol","fuliji666.vip","fuliji666.cc",
    "91fulifs.icu","onefuli.net","onefuli.vip","fulibavip.net","yinav.com",
    "fulijianghu.net","xxmdh.cc","heiliaofuliwsh.shop","thdh.cc",
    "136fuli.com","168fuli50.xyz","daohangh.shop","bananavideoai.com",
    "njuptnavi.top","fuliba2025.net","javmap.com","adultpornguide.com",
    "thepornguide.xxx","dkdh.net","18fuli.app","pornav.net","toppornguide.com",
    "thepornmap.com","fuliba123.com","theeroticguide.net","paidpornguide.com",
    "fulitu.cc","pornavalanche.com","prfuliji.top","xxxchinavideo24.com",
}

# 成人关键词（长词/子串匹配）
ADULT_KW_STRONG = {
    "porn","hentai","adult","nude","naked","nsfw","erotic","fetish",
    "lesbian","fansly","onlyfans","xvideo","xhamster","redtube","brazzers",
    "youporn","beeg","creampie","blowjob","cumshot","gangbang","handjob",
    "fuli","daohang","caoliu","jiequ","saohua","yingshi","zhibo","fuliji",
    "dongman","manhua","manga","anime","lolita","idol",
}
# 成人关键词（短词，匹配独立段/前缀/后缀）
ADULT_KW_SHORT = {
    "91","av","se","jm","dh","lu","bb","pp","mm","xo","18",
    "sex","xxx","vip","cam","tube","nav","live","video","club","porn",
}
# 补充子串词（含即保留）
ADULT_KW_SUBSTR = {
    "avfun","avmao","avsex","avhd","avone","avgo","avpro","avcat","avdh",
    "sedh","sedao","seav","semei","sehao","seboy","segirl","sewang","seapp",
    "18av","18sex","18app","18vip","18fuli","18dh",
    "riben","rizhi","dongman","donghua","riman","guoman",
    "caose","caopao","caobi","caoporn",
    "yingshi","yingyin","yingyuan","shipin","tupian",
    "hongdou","hongdoufan","luoli","gaoqing","miaopai","duanshipin",
    "slwx","slwxdh","jktv","jtv","sjtv","adultjk","jkav",
}

NAV_SIGNALS = NAV_SIGNALS = ["nav","navi","fuli","dh","daohang","map","guide"]

def curl_get(url, use_proxy=False, timeout=15, use_jina=False):
    target = f"https://r.jina.ai/{url}" if use_jina else url
    cmd = ["curl","-sL","--max-time",str(timeout),
           "-H","User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
           "-H","Accept-Language: zh-CN,zh;q=0.9"]
    if use_proxy: cmd += ["--proxy", PROXY]
    cmd.append(target)
    try:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           universal_newlines=True, timeout=timeout+5)
        if r.returncode==0 and r.stdout and len(r.stdout)>200:
            return r.stdout
    except: pass
    return ""

def is_adult_domain(domain):
    d = domain.lower()
    if d in SKIP_DOMAINS: return False
    if d in KNOWN_NAV: return False
    if len(d) < 5: return False
    name = d.split(".")[0]
    if re.match(r"^[a-z]{1,3}\d{4,}$", name): return False
    if d.endswith(".io") and not any(kw in d for kw in ADULT_KW_STRONG): return False
    if any(kw in d for kw in ADULT_KW_SUBSTR): return True
    if any(kw in d for kw in ADULT_KW_STRONG): return True
    parts = re.split(r"[\-\.]", d)
    if any(kw in parts for kw in ADULT_KW_SHORT): return True
    if d.endswith((".tv",".app",".cc")): return True
    adult_tlds = {".top",".xyz",".sbs",".vip",".fun",".live",".se",".club"}
    if any(d.endswith(t) for t in adult_tlds): return True
    return False


def extract_domains(html):
    raw = re.findall(r"https?://([a-zA-Z0-9][a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,6})", html)
    doms = set()
    for d in raw:
        d = d.lower().strip(".")
        root = ".".join(d.split(".")[-2:])
        if len(root)>=5 and is_adult_domain(root):
            doms.add(root)
    return doms

def looks_like_nav(d):
    return any(sig in d for sig in NAV_SIGNALS)

def load_json(path, default):
    if not path.exists(): return default
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def monthly_reset(data):
    m = date.today().strftime("%Y-%m")
    if data.get("last_monthly_reset") == m: return data
    demoted = []
    for s in data["sources"]:
        if s.get("monthly_hits",0)==0 and s.get("priority")=="low":
            s["enabled"]=False; s["status"]="demoted"; demoted.append(s["name"])
        s["monthly_hits"] = 0
    data["last_monthly_reset"] = m
    if demoted: print(f"  [月度重置] 降级 {len(demoted)} 个")
    return data

def update_nav_hit(data, nav_name):
    for s in data["sources"]:
        if s["name"]==nav_name:
            s["monthly_hits"] = s.get("monthly_hits",0)+1
            s["last_hit_date"] = date.today().isoformat()
            h = s["monthly_hits"]
            if h>=5: s["priority"]="high"
            elif h>=2: s["priority"]="medium"
            break

def mine_navs(domain, data):
    known = {s["url"].lower().rstrip("/") for s in data["sources"]}
    html = curl_get(f"https://{domain}", timeout=10)
    if not html: return 0
    found = 0
    for d in extract_domains(html):
        cand = f"https://{d}"
        if cand.lower().rstrip("/") in known or not looks_like_nav(d): continue
        data["sources"].append({"name":d,"url":cand,"category":"自动发现-待分类",
            "priority":"low","enabled":True,"status":"new","monthly_hits":0,
            "last_hit_date":"","notes":f"从竞品{domain}友链发现{date.today().isoformat()}"})
        known.add(cand.lower())
        print(f"    ✨ 新导航站: {d}"); found+=1
    return found

def fetch_nav_sources(sources):
    active = [s for s in sources if s.get("enabled") and s.get("status")!="demoted"]
    active.sort(key=lambda x: {"high":0,"medium":1,"low":2}.get(x.get("priority","low"),2))
    print(f"\n[导航站抓取] {len(active)} 个")
    nav_doms = {}
    for s in active:
        name,url = s["name"],s["url"]
        print(f"  -> {name}")
        html = curl_get(url,use_proxy=False,timeout=12)
        if not html: html = curl_get(url,use_proxy=True,timeout=12)
        if not html: print(f"    x 无响应"); s["status"]="error"; continue
        s["status"]="ok"
        doms = extract_domains(html)
        new = sum(1 for d in doms if d not in nav_doms)
        for d in doms:
            if d not in nav_doms: nav_doms[d]=name
        print(f"    OK {len(doms)} 成人域名，新增 {new}")
        time.sleep(0.5)
    return nav_doms

def fetch_caoliu():
    print(f"\n[草榴论坛]")
    caoliu={}
    for fid,name in [("7","网站资源"),("2","综合讨论"),("9","成人商业")]:
        url=f"https://t66y.com/thread0806.php?fid={fid}"
        html=curl_get(url,use_proxy=False,timeout=12)
        if not html: html=curl_get(url,use_proxy=False,timeout=12,use_jina=True)
        if not html: print(f"  x {name}"); continue
        doms=extract_domains(html)
        added=sum(1 for d in doms if d not in caoliu and "t66y" not in d)
        for d in doms:
            if d not in caoliu and "t66y" not in d: caoliu[d]=f"草榴-{name}"
        print(f"  OK {name}: {len(doms)} 域名，新增 {added}")
        time.sleep(0.5)
    return caoliu

def main():
    print("=== 竞品黑马发现 v10（精准过滤+中文倾斜）===")
    today = date.today().isoformat()
    wdata = load_json(WATCHLIST, {"sources":[]})
    hist  = load_json(HISTORY, {})
    wdata = monthly_reset(wdata)
    print(f"导航站: {len(wdata['sources'])} 个 | 历史库: {len(hist)} 条")

    nav_doms = fetch_nav_sources(wdata["sources"])
    caoliu   = fetch_caoliu()
    extra    = {d:src for d,src in caoliu.items() if d not in nav_doms}
    print(f"\n[汇总] 导航站: {len(nav_doms)} | 草榴新增: {len(extra)}")

    all_doms = set(nav_doms)|set(extra)
    results=[]; new_nav_total=0

    for domain in all_doms:
        nav_src = nav_doms.get(domain,"")
        kw_src  = extra.get(domain,"")
        rank    = 1 if nav_src else 5
        prev    = hist.get(domain)
        if prev is None: ct="new"
        elif prev.get("rank",99)-rank>=3: ct="rising"
        else: ct="seen"

        results.append({"domain":domain,"nav_source":nav_src,"keyword":kw_src,
                        "rank":rank,"change_type":ct,
                        "first_seen":prev.get("first_seen",today) if prev else today})
        if ct in ("new","rising"):
            if nav_src: update_nav_hit(wdata,nav_src)
            if ct=="new": new_nav_total+=mine_navs(domain,wdata)
        hist[domain]={"rank":rank,"last_seen":today,
                      "first_seen":prev.get("first_seen",today) if prev else today,
                      "nav_source":nav_src or (prev.get("nav_source","") if prev else ""),
                      "keyword":kw_src}

    results.sort(key=lambda x:{"new":0,"rising":1,"seen":2}[x["change_type"]])
    print(f"[自学习] 友链新导航站候选: {new_nav_total}")

    save_json(HISTORY, hist)
    wdata["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_json(WATCHLIST, wdata)

    new_s  = [x for x in results if x["change_type"]=="new"][:30]
    rising = [x for x in results if x["change_type"]=="rising"][:10]

    out={"date":today,"version":"v10",
         "nav_ok":[s["name"] for s in wdata["sources"] if s.get("status")=="ok"],
         "watchlist_size":len(wdata["sources"]),"history_size":len(hist),
         "summary":{"new":len(new_s),"rising":len(rising)},
         "new_competitors":new_s,"rising_competitors":rising}

    save_json(Path("/tmp/competitors_data.json"), out)
    print(f"\n=== 完成 === 新竞品:{len(new_s)} 排名上升:{len(rising)}")
    if new_s:
        print("新竞品（前8）：")
        for s in new_s[:8]:
            print(f"  {s['domain']:35s} | {s['nav_source'] or s['keyword']}")
    return out

if __name__=="__main__": main()
