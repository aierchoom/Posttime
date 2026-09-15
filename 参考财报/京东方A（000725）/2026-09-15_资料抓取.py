import concurrent.futures, hashlib, json, sys
from pathlib import Path
import urllib.request, re, html
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parent
SOURCES={
 '2026-08-29_京东方_半年报.pdf':'https://file.finance.sina.com.cn/211.154.219.97:9494/MRGG/CNSESZ_STOCK/2026/2026-8/2026-08-29/12572072.PDF',
 '2026-09-11_京东方_IR043.pdf':'https://file.finance.sina.com.cn/211.154.219.97:9494/MRGG/CNSESZ_STOCK/2026/2026-9/2026-09-11/12595880.PDF',
 '2026-05-21_京东方_康宁合作备忘录.pdf':'https://static.cninfo.com.cn/finalpage/2026-05-21/1225321632.PDF',
 '2026-08-29_TCL_半年报.html':'https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12565266&stockid=000100',
 '2026-09-15_SKC_官网新闻.html':'https://www.skc.co.kr/m/eng/Conmmunication/newsroom/system.do?gubun=006002',
 '2026-09-10_三星电机_KPCA.html':'https://samsungsem.com/global/newsroom/news/view.do?id=10522',
 '2026-07-02_住友_玻璃芯合资.html':'https://www.sumitomo-chem.co.jp/english/news/detail/20260702e_2.html',
 '2026-07-24_Intel_蓝思合作.html':'https://newsroom.intel.com/new-technologies/intel-and-lens-technology-collaborate-to-enable-advanced-semiconductor-packaging-for-the-ai-era',
 '2026-09-15_金元证券研报页面.html':'https://data.eastmoney.com/report/info/AP202609021828915450.html'
}
def fetch(item):
 name,url=item
 p=ROOT/name
 try:
  if not p.exists():
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
   with urllib.request.urlopen(req,timeout=40) as r: p.write_bytes(r.read())
  data=p.read_bytes()
  if p.suffix=='.pdf':
   reader=PdfReader(p)
   content='\n\n'.join(f'=== PDF page {i+1} ===\n'+(page.extract_text() or '') for i,page in enumerate(reader.pages))
  else:
   encoding='gb18030' if b'charset=gb' in data.lower() or b'charset="gb' in data.lower() else 'utf-8'
   raw=data.decode(encoding,errors='replace')
   raw=re.sub(r'<(script|style)\b.*?</\1>','',raw,flags=re.S|re.I)
   content=html.unescape(re.sub(r'<[^>]+>','\n',raw))
   content='\n'.join(x.strip() for x in content.splitlines() if x.strip())
  txt=p.with_suffix('.txt')
  if not txt.exists(): txt.write_text(content,encoding='utf-8')
  return {'file':name,'url':url,'access_date':'2026-09-15','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'status':'ok'}
 except Exception as e: return {'file':name,'url':url,'status':'error','error':str(e)}
if __name__=='__main__':
 if len(sys.argv)>1: SOURCES=json.loads((ROOT/sys.argv[1]).read_text(encoding='utf-8'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool: result=list(pool.map(fetch,SOURCES.items()))
 manifest=ROOT/('2026-09-15_下载清单02.json' if len(sys.argv)>1 else '2026-09-15_下载清单.json')
 if not manifest.exists(): manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False,indent=2))
