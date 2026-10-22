import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SOURCES = {
    '2026-10-22_TTM_Q3业绩公告': 'https://investors.ttm.com/news-events/press-releases/detail/420/ttm-technologies-inc-reports-third-quarter-2026-results',
    '2026-10-22_TTM_财报目录': 'https://investors.ttm.com/financial-information/financial-results',
    '2026-10-22_TTM_SEC目录': 'https://investors.ttm.com/sec-filings/all-sec-filings',
    '2026-10-22_TTM_演示材料目录': 'https://investors.ttm.com/news-events/presentations',
    '2026-10-12_TTM_新增4亿美元扩产': 'https://investors.ttm.com/news-events/press-releases/detail/417/ttm-technologies-announces-400-million-in-planned',
    '2026-09-30_TTM_Epiq交割及融资': 'https://investors.ttm.com/news-events/press-releases/detail/416/ttm-technologies-inc-completes-acquisition-of-epiq',
    '2026-10-19_TTM_Ophir收购协议': 'https://investors.ttm.com/news-events/press-releases/detail/419/ttm-technologies-inc-agrees-to-acquire-mks-inc-s',
    '2026-08-05_TTM_Q2业绩公告': 'https://investors.ttm.com/news-events/press-releases/detail/410/ttm-technologies-inc-reports-second-quarter-2026-results',
    '2026-10-22_ATS_最新关键指标': 'https://ats.net/en/investors/key-figures/',
    '2026-05_ATS_2025至2026财年业绩': 'https://ats.net/en/ir-news/ats-closes-successful-financial-year-with-strong-fourth-quarter/',
    '2026-08_Mercury_FY2026业绩': 'https://ir.mrcy.com/index.php/news-releases/news-release-details/mercury-systems-reports-fourth-quarter-and-fiscal-2026-results',
}

def capture(item):
    name, url = item
    target = ROOT / (name + '.html')
    if target.exists():
        return {'name': name, 'status': 'existing', 'url': url}
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 Financial Research public filings'})
    with urllib.request.urlopen(req, timeout=45) as response:
        data = response.read()
        final_url = response.url
    target.write_bytes(data)
    soup = BeautifulSoup(data, 'html.parser')
    for tag in soup(['script', 'style']):
        tag.decompose()
    (ROOT / (name + '.txt')).write_text(soup.get_text('\n', strip=True), encoding='utf-8')
    tables = []
    for idx, table in enumerate(soup.find_all('table')):
        rows = ['\t'.join(cell.get_text(' ', strip=True) for cell in tr.find_all(['td', 'th'], recursive=False)) for tr in table.find_all('tr')]
        tables.append('TABLE ' + str(idx) + '\n' + '\n'.join(rows))
    (ROOT / (name + '_tables.txt')).write_text('\n\n'.join(tables), encoding='utf-8')
    links = [{'text': a.get_text(' ', strip=True), 'href': a.get('href')} for a in soup.find_all('a', href=True)]
    (ROOT / (name + '_links.json')).write_text(json.dumps(links, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'name': name, 'url': url, 'final_url': final_url, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'tables': len(tables), 'access_date': '2026-10-22'}

if __name__ == '__main__':
    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(capture, item): item for item in SOURCES.items()}
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
            except Exception as exc:
                result = {'name': futures[future][0], 'url': futures[future][1], 'error': str(exc)}
            records.append(result)
            print(json.dumps(result, ensure_ascii=False))
    (ROOT / '2026-10-22_download_manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
