from pathlib import Path
import json, hashlib, urllib.request, concurrent.futures
from bs4 import BeautifulSoup
try:
    from pypdf import PdfReader
except ImportError:
    import sys
    sys.path.append(str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/Lib/site-packages'))
    from pypdf import PdfReader
ROOT=Path(__file__).resolve().parent
HEADERS={'User-Agent':'Mozilla/5.0','Referer':'https://finance.sina.com.cn/'}
def fetch(name,url):
    p=ROOT/name
    if p.exists():
        data=p.read_bytes()
    else:
        with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=35) as r:data=r.read()
        p.write_bytes(data)
    if name.endswith('.html'):
        soup=BeautifulSoup(data,'html.parser')
        for x in soup(['script','style']):x.decompose()
        p.with_suffix('.txt').write_text(soup.get_text('\n',strip=True),encoding='utf-8')
    if name.endswith('.pdf'):
        assert data.startswith(b'%PDF')
        reader=PdfReader(p)
        p.with_suffix('.txt').write_text('\n\n'.join(f'=== PDF第{i+1}页 ===\n'+(pg.extract_text() or '') for i,pg in enumerate(reader.pages)),encoding='utf-8')
    return dict(path=str(p),url=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),access_date='2026-10-29',source_date_note='三季报公告落款2026-10-30；10月29日晚已公开可取得')
jobs=[
('2026-10-30_生益科技_2026年第三季度报告.pdf','https://file.finance.sina.com.cn/211.154.219.97:9494/MRGG/CNSESH_STOCK/2026/2026-10/2026-10-30/12679933.PDF'),
('2026-10-30_生益科技_三季报.html','https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12679933&stockid=600183'),
('2026-10-30_生益科技_利润分配.html','https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12679928&stockid=600183'),
('2026-10-30_生益科技_业绩说明会公告.html','https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12679930&stockid=600183'),
('2026-10-29_生益电子_公告索引.html','https://money.finance.sina.com.cn/corp/go.php/vCB_AllBulletin/stockid/688183.phtml'),
('2026-10-29_腾讯行情.txt','https://qt.gtimg.cn/q=sh600183'),
('2026-10-29_新浪行情.txt','https://hq.sinajs.cn/list=sh600183'),
('2026-10-24_生益电子_生产经营公告.html','https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12657665&stockid=688183'),
('2026-10-17_生益电子_业绩预告.html','https://money.finance.sina.com.cn/corp/view/vCB_AllBulletinDetail.php?id=12646220&stockid=688183'),
('2026-10-17_生益科技_业绩预告.pdf','https://static.cninfo.com.cn/finalpage/2026-10-17/1225608514.PDF'),
]
if __name__=='__main__':
    out=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
        futs={pool.submit(fetch,*job):job for job in jobs}
        for fut in concurrent.futures.as_completed(futs):
            try:r=fut.result()
            except Exception as e:r={'job':futs[fut],'error':str(e)}
            out.append(r);print(json.dumps(r,ensure_ascii=False))
    (ROOT/'2026-10-29_下载清单.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
