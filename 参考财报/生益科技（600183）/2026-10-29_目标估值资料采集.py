from pathlib import Path
import urllib.request,ssl,json,hashlib
root=Path(__file__).resolve().parent
url='https://www.twse.com.tw/exchangeReport/BWIBBU_d?response=json&date=20261029&selectType=ALL'
p=root/'2026-10-29_TWSE本益比原始.json'
if not p.exists():
    ctx=ssl.create_default_context();ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req,timeout=25,context=ctx) as res:raw=res.read()
    data=json.loads(raw);assert data.get('stat')=='OK',data
    p.write_bytes(raw)
else:raw=p.read_bytes();data=json.loads(raw)
result={'url':url,'access_date':'2026-10-29','sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'fields':data.get('fields'),'rows':[r for r in data.get('data',[]) if r[0]=='2383']}
assert len(result['rows'])==1
target=root/'2026-10-29_目标估值资料采集清单.json'
if not target.exists():target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True))
