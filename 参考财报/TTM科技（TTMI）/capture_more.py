import json
from capture_sources import capture, ROOT

SOURCES = {
    '2026-08-05_TTM_Q2业绩公告_411核正': 'https://investors.ttm.com/news-events/press-releases/detail/411/ttm-technologies-inc-reports-second-quarter-2026-results',
    '2026-02_TTM_FY2025业绩公告': 'https://investors.ttm.com/news-events/press-releases/detail/400/ttm-technologies-inc-reports-fourth-quarter-fiscal-year',
    '2026-02_TTM_FY2025年报10K': 'https://investors.ttm.com/sec-filings/all-sec-filings/content/0001193125-26-051976/ttmi-20251229.htm',
    '2026-08-05_TTM_Q2季报10Q': 'https://investors.ttm.com/sec-filings/all-sec-filings/content/0001193125-26-335107/ttmi-20260629.htm',
    '2026-09-30_TTM_Epiq融资8K': 'https://investors.ttm.com/sec-filings/all-sec-filings/content/0001193125-26-409136/d147406d8k.htm',
    '2026-10-22_TTM_三季报8K': 'https://investors.ttm.com/sec-filings/all-sec-filings/content/0001193125-26-428263/d282109d8k.htm',
    '2026-08-18_Mercury_FY2026业绩_无index': 'https://ir.mrcy.com/news-releases/news-release-details/mercury-systems-reports-fourth-quarter-and-fiscal-2026-results',
}
records = []
for item in SOURCES.items():
    try:
        result = capture(item)
    except Exception as exc:
        result = {'name': item[0], 'url': item[1], 'error': str(exc)}
    records.append(result)
    print(json.dumps(result, ensure_ascii=False), flush=True)
(ROOT / '2026-10-22_download_manifest_02.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
