from pathlib import Path
import urllib.request, urllib.parse, json, subprocess, hashlib, re, sys, ssl
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
HEAD={'User-Agent':'Mozilla/5.0','Referer':'https://www.cninfo.com.cn/'}
def save(name,data):
    p=ROOT/name
    if p.exists():
        assert p.read_bytes()==data, f'refuse overwrite {p}'
    else:p.write_bytes(data)
    return {'path':str(p.relative_to(REPO)),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
def get(url,name,form=None):
    cached=ROOT/name
    if cached.exists():return cached.read_bytes(),dict(save(name,cached.read_bytes()),url=url,access_date='2026-10-29',cached=True)
    data=urllib.parse.urlencode(form).encode() if form else None
    req=urllib.request.Request(url,data=data,headers=HEAD)
    context=ssl.create_default_context()
    context.verify_flags &= ~ssl.VERIFY_X509_STRICT
    with urllib.request.urlopen(req,timeout=25,context=context) as r:raw=r.read()
    meta=save(name,raw);meta.update(url=url,access_date='2026-10-29');return raw,meta
if __name__=='__main__':
    meta=[]
    for commit,label in [('7786cd0','07-03事前'),('5370704','08-21事前')]:
        spec=f'{commit}:公司档案/生益科技（600183）/2026-07-03/生益科技（600183）.md'
        raw=subprocess.check_output(['git','show',spec],cwd=REPO)
        row=save(f'2026-10-29_历史报告快照_{label}.md',raw);row.update(git_object=spec,provenance='本地已有Git对象；本轮导出');meta.append(row)
    history=subprocess.check_output(['git','log','--diff-filter=A','--format=%H %aI %s','--','公司档案/生益科技（600183）/2026-09-21/经营估值模型.py'],cwd=REPO)
    meta.append(save('2026-10-29_模型首次入库记录.txt',history))
    before=(REPO/'公司档案/生益科技（600183）/2026-09-21/生益科技（600183）.md').read_bytes()
    if not (ROOT/'2026-10-29_本轮施工前主报告快照.md').exists():meta.append(save('2026-10-29_本轮施工前主报告快照.md',before))
    jobs=[('cninfo','https://www.cninfo.com.cn/new/hisAnnouncement/query','2026-10-29_复盘_生益电子巨潮查询.json',{'pageNum':1,'pageSize':30,'column':'sse','tabName':'fulltext','stock':'688183,nssc1000615','searchkey':'第三季度报告','seDate':'2026-10-29~2026-10-30','isHLtitle':'true'}),
          ('emc','https://www.emctw.com/en-global/investors_news/index','2026-10-29_复盘_台光公告索引.html',None),
          ('pdf','https://static.cninfo.com.cn/finalpage/2026-10-30/1225645469.PDF','2026-10-30_生益电子_2026年第三季度报告.pdf',None),
          ('pdf','https://static.cninfo.com.cn/finalpage/2026-08-15/1225474834.PDF','2026-08-15_生益电子_2026年半年度报告.pdf',None),
          ('html','https://www.emctw.com/en-global/investors_news/detail/2026102801/1','2026-10-28_台光电_三季度财务公告.html',None),
          ('html','https://www.emctw.com/en-global/investors_news/detail/2026102803/1','2026-10-28_台光电_扩产决议.html',None)]
    for label,url,name,form in jobs:
        try:
            raw,row=get(url,name,form);meta.append(row)
            if label=='cninfo':print(raw.decode()[:14000])
            elif label=='html':
                from bs4 import BeautifulSoup
                soup=BeautifulSoup(raw,'html.parser')
                for x in soup(['script','style']):x.decompose()
                txt=soup.get_text('\n',strip=True)
                save(name[:-5]+'.txt',txt.encode('utf-8'));print(txt[:16000])
            elif label=='pdf':
                sys.path.append(str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/Lib/site-packages'))
                from pypdf import PdfReader
                reader=PdfReader(ROOT/name)
                txt='\n\n'.join(f'=== PDF第{i+1}页 ===\n'+(pg.extract_text() or '') for i,pg in enumerate(reader.pages))
                save(name[:-4]+'.txt',txt.encode('utf-8'));print(name,len(reader.pages),'pages')
            else:
                s=raw.decode('utf-8',errors='replace')
                print('EMC candidates', re.findall(r'.{0,90}(?:20261028|3Q|3Quarter|third|Third).{0,220}',s))
        except Exception as e:print(label,type(e).__name__,str(e))
    n=1
    while (ROOT/f'2026-10-29_复盘采集清单{n:02}.json').exists():n+=1
    save(f'2026-10-29_复盘采集清单{n:02}.json',json.dumps(meta,ensure_ascii=False,indent=2).encode())
