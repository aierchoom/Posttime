from pathlib import Path
import json,runpy,concurrent.futures
ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT/'同行PE'
OUTPUT.mkdir(exist_ok=True)
ns=runpy.run_path(str(ROOT/'2026-09-15_资料抓取.py'))
sources={
 '2026-04-15_彩虹2025年报.pdf':'https://dataclouds.cninfo.com.cn/shgonggao/hsomarket/2026/20260415/1c1e02ed162d4ec0abd1b2a9ce8673dd.PDF',
 '2026-08-27_彩虹2026中报摘要.html':'https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12548500&stockid=600707',
 '2026-03-28_TCL2025年报.pdf':'https://static.cninfo.com.cn/finalpage/2026-03-28/1225045623.PDF',
 '2026-03-14_天马2025年报.pdf':'https://static.cninfo.com.cn/finalpage/2026-03-14/1225009341.PDF',
 '2026-04-29_维信诺2025年报摘要.html':'https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12253785&stockid=002387',
 '2026-08-28_维信诺2026中报.pdf':'https://disc.static.szse.cn/disc/disk03/finalpage/2026-08-28/467859c6-155c-4a66-874d-46836770a5d9.PDF',
 '2026-04-23_龙腾2025年报.html':'https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12148830&stockid=688055',
 '2026-08-26_龙腾2026中报.html':'https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12535828&stockid=688055',
 '2026-09-15_京东方行情.html':'https://stock.aigupiao.com/code/sz000725',
 '2026-09-15_TCL行情.html':'https://stock.aigupiao.com/code/sz000100',
 '2026-09-15_彩虹行情.html':'https://stock.aigupiao.com/code/sh600707',
 '2026-09-15_天马行情.html':'https://stock.aigupiao.com/code/sz000050',
 '2026-09-15_维信诺行情.html':'https://stock.aigupiao.com/code/sz002387',
 '2026-09-15_龙腾行情.html':'https://stock.aigupiao.com/code/sh688055'
}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
 results=list(pool.map(ns['fetch'], [('同行PE/'+name,url) for name,url in sources.items()]))
p=OUTPUT/'2026-09-15_下载清单.json'
if not p.exists():p.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{'file':r['file'],'status':r['status'],'error':r.get('error')} for r in results],ensure_ascii=False,indent=2))
