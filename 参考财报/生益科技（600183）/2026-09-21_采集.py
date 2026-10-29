from pathlib import Path
import json,urllib.request,re,html,hashlib,concurrent.futures,sys
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parent
SOURCES={
 '2026-08-26_生益科技_业绩说明会.html':'https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12548066&stockid=600183',
 '2026-09-19_生益电子_权益稀释.html':'https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12611725&stockid=688183',
 '2026-09-19_生益电子_发行结果.html':'https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12611724&stockid=688183',
 '2026-08-29_南亚新材_半年报.html':'https://vip.stock.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12568945&stockid=688519',
 '2026-08-31_华正新材_半年报.html':'https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12574649&stockid=603186',
 '2026-04-16_华正新材_2025年报.pdf':'https://static.cninfo.com.cn/finalpage/2026-04-16/1225107720.PDF',
 '2026-08-26_沪电股份_半年报.pdf':'https://static.cninfo.com.cn/finalpage/2026-08-26/1225502252.PDF',
 '2026-03-25_沪电股份_2025年报.html':'https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12014866&stockid=002463',
 '2026-07-29_台光电_中报公告.html':'https://www.emctw.com/en-global/investors_news/detail/2026072901/1',
 '2026-09-21_台光电_月收入索引.html':'https://www.emctw.com/en-global/monthly_revenue/index',
 '2026-09-21_建滔_公告索引.html':'https://www.kblaminates.com/en/list/192.html',
 '2026-09-21_生益科技_盈利预测.html':'https://basic.10jqka.com.cn/600183/worth.html',
 '2026-05-08_西南证券_生益科技.pdf':'https://pdf.dfcfw.com/pdf/H3_AP202605191822431344_1.pdf',
 '2026-09-21_生益科技_行情.html':'https://stock.aigupiao.com/code/sh600183',
 '2026-09-21_南亚新材_行情.html':'https://stock.aigupiao.com/code/sh688519',
 '2026-09-21_华正新材_行情.html':'https://stock.aigupiao.com/code/sh603186',
 '2026-09-21_沪电股份_行情.html':'https://stock.aigupiao.com/code/sz002463',
 '2026-09-21_生益电子_行情.html':'https://stock.aigupiao.com/code/sh688183'
}
def fetch(item):
 name,url=item;p=ROOT/name
 try:
  if not p.exists():
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
   with urllib.request.urlopen(req,timeout=35) as response:p.write_bytes(response.read())
  data=p.read_bytes()
  if p.suffix.lower()=='.pdf':
   pdf=PdfReader(p);content='\n\n'.join(f'=== PDF page {i+1} ===\n'+(page.extract_text() or '') for i,page in enumerate(pdf.pages))
  else:
   enc='gb18030' if re.search(br'charset\s*=\s*["\x27]?gb',data,re.I) else 'utf-8'
   raw=data.decode(enc,errors='replace');raw=re.sub(r'<(script|style)\b.*?</\1>','',raw,flags=re.S|re.I)
   content='\n'.join(x.strip() for x in html.unescape(re.sub('<[^>]+>','\n',raw)).splitlines() if x.strip())
  txt=p.with_suffix('.txt')
  if not txt.exists():txt.write_text(content,encoding='utf-8')
  return dict(file=name,url=url,access_date='2026-09-21',status='ok',bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
 except Exception as e:return dict(file=name,url=url,status='error',error=str(e))
if __name__=='__main__':
 label='01'
 if len(sys.argv)>1:
  SOURCES=json.loads((ROOT/sys.argv[1]).read_text(encoding='utf-8'));label=sys.argv[2]
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(fetch,SOURCES.items()))
 m=ROOT/f'2026-09-21_下载清单{label}.json'
 if not m.exists():m.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps([{'file':r['file'],'status':r['status'],'error':r.get('error')} for r in results],ensure_ascii=False))
