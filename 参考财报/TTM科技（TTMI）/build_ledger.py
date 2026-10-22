import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POOL = Path(__file__).resolve().parent
OUT = ROOT/'公司档案'/'TTM科技（TTMI）'/'2026-10-22'
meta = {
'S1': ('TTM Q3 2026 Results','TTM','2026-10-22','2026Q3/9M; Q3 ended 2026-09-28','2026-10-22_TTM_Q3业绩公告.html','https://investors.ttm.com/news-events/press-releases/detail/420/ttm-technologies-inc-reports-third-quarter-2026-results','Statements of Operations; Supplemental Data; Reconciliations; Business Outlook','本轮新抓取'),
'S2': ('TTM Q2 2026 Results','TTM','2026-08-05','2026Q2/H1; ended 2026-06-29','2026-08-05_TTM_Q2业绩公告_411核正.html','https://investors.ttm.com/news-events/press-releases/detail/411/ttm-technologies-inc-reports-second-quarter-2026-results','Statements of Operations; Supplemental Data; Reconciliations','本轮新抓取；detail411核正'),
'S3': ('TTM Q4 and FY2025 Results','TTM','2026-02-04','FY2024/FY2025','2026-02_TTM_FY2025业绩公告.html','https://investors.ttm.com/news-events/press-releases/detail/400/ttm-technologies-inc-reports-fourth-quarter-fiscal-year','Annual P&L; Selected Balance Sheet; FCF reconciliation','本轮新抓取'),
'S4': ('TTM FY2025 Form 10-K','TTM/SEC','2026-02-17','FY2025 ended 2025-12-29','2026-02_TTM_FY2025年报10K.html','https://investors.ttm.com/sec-filings/all-sec-filings/content/0001193125-26-051976/ttmi-20251229.htm','Item 1/1A; Revenue Recognition; Contract Balances','本轮新抓取'),
'S5': ('TTM Q2 2026 Form 10-Q','TTM/SEC','2026-08-05','2026Q2/H1','2026-08-05_TTM_Q2季报10Q.html','https://investors.ttm.com/sec-filings/all-sec-filings/content/0001193125-26-335107/ttmi-20260629.htm','Segment Information; MD&A; Income Taxes','本轮新抓取'),
'S6': ('Epiq acquisition close and incremental facilities','TTM/SEC','2026-09-30','2026-09-30 close; 2027/2028 expectations','2026-09-30_TTM_Epiq融资8K.html','https://investors.ttm.com/sec-filings/all-sec-filings/content/0001193125-26-409136/d147406d8k.htm','Items 1.01 and 8.01; companion closing release Terms of Transaction','本轮新抓取；亦见2026-09-30_TTM_Epiq交割及融资.html'),
'S7': ('Ophir Optics definitive agreement','TTM','2026-10-19','expected close 2027Q2','2026-10-19_TTM_Ophir收购协议.html','https://investors.ttm.com/news-events/press-releases/detail/419/ttm-technologies-inc-agrees-to-acquire-mks-inc-s','Transaction terms and financing; exclusion of Instruments/brand','本轮新抓取'),
'S8': ('Additional 400 million AI capacity plan','TTM','2026-10-12','2025-2029 original program; incremental plan announced 2026-10-12','2026-10-12_TTM_新增4亿美元扩产.html','https://investors.ttm.com/news-events/press-releases/detail/417/ttm-technologies-announces-400-million-in-planned','Investment plan; brownfield; China and Penang','本轮新抓取'),
'S9': ('沪电股份2026年半年度报告','沪电股份','2026-08-26','2026H1','../生益科技（600183）/2026-08-26_沪电股份_半年报.pdf','https://static.cninfo.com.cn/finalpage/2026-08-26/1225502252.PDF','PDF物理页13-16 MD&A与产品毛利；主要会计数据及现金流表','本地已有；本轮读取既有txt并整合入ledger'),
'S10': ('AT&S Key Figures FY2026/27 Q1','AT&S','2026-08-04','quarter ended 2026-06-30','2026-10-22_ATS_最新关键指标.html','https://ats.net/en/investors/key-figures/','Key Figures table; Q1 2026/27 vs Q1 2025/26','本轮新抓取；网页文件名是访问日'),
'S11': ('Mercury Q4 and FY2026 Results','Mercury Systems','2026-08-18','FY2026 ended 2026-07-03','2026-08-18_Mercury_财务表补充_web抓取.json','https://ir.mrcy.com/news-releases/news-release-details/mercury-systems-reports-fourth-quarter-and-fiscal-2026-results','Statements of Operations; Balance Sheet; FCF reconciliation; company description','本轮网页工具抓取；HTTP下载403；亦见FY2026业绩_web抓取.json'),
'S12': ('TTM Executing on Growth Strategy','TTM/SEC','2026-08-17','Epiq 2027E EBITDA transaction assumptions','2026-08-17_TTM_Epiq并购演示_web抓取.json','https://www.sec.gov/Archives/edgar/data/1116942/000119312526353148/d375900dex992.htm','Slide 5 and slide 7','本轮网页工具抓取；不是原始PDF'),
'S13': ('Reproducible financial calculations and scenario model','本研究','2026-10-22','historical disclosed periods and 2027 scenarios','2026-10-22_计算输入与情景.json','','financial_analysis.py; 财务计算结果.csv; scenario assumptions','本轮派生计算；非独立外部证据'),
'S14': ('AT&S closes FY2025/26','AT&S','2026-05-21','FY2025/26 ended 2026-03-31','2026-05_ATS_2025至2026财年业绩.html','https://ats.net/en/ir-news/ats-closes-successful-financial-year-with-strong-fourth-quarter/','New Kulim and Leoben plants; cash flow and debt','本轮新抓取'),
}
fields = 'source_id,topic,claim_or_metric,claim_type,source_tier,publisher_or_issuer,analyst_or_author,document_title,publication_date,data_period,currency_unit,source_path_or_url,page_or_section,access_date,confidence,verification_stage,counterparty_or_segment,business_layer,peer_role,normalization_note,valuation_method,target_price_or_range,rating,valuation_multiple_or_key_assumption,absolute_value,percentage_value,percentage_denominator,calculation_formula,notes_or_formula'.split(',')
rows=[]
def add(sid,topic,claim,period=None,unit='USD million except EPS USD/share',value='',pct='',denom='',formula='',kind='事实',segment='集团',layer='财务',role='',norm='',stage='已披露',confidence='高'):
    title,issuer,date,default_period,file,url,section,origin=meta[sid]
    path=(POOL/file).resolve()
    assert path.is_file(), path
    d=dict.fromkeys(fields,'')
    d.update(source_id=sid,topic=topic,claim_or_metric=claim,claim_type=kind,source_tier='Derived/Assumption' if sid=='S13' else 'Tier 1',publisher_or_issuer=issuer,document_title=title,publication_date=date,data_period=period or default_period,currency_unit=unit,source_path_or_url=str(path),page_or_section=section,access_date='2026-10-22',confidence=confidence,verification_stage=stage,counterparty_or_segment=segment,business_layer=layer,peer_role=role,normalization_note=norm,absolute_value=value,percentage_value=pct,percentage_denominator=denom,calculation_formula=formula,notes_or_formula=origin+'；原始URL：'+url)
    rows.append(d)

model=json.loads((POOL/'2026-10-22_计算输入与情景.json').read_text(encoding='utf-8'))
for period,data in model['data'].items():
    sid='S3' if period.startswith('FY') else ('S2' if period=='2026Q2' else 'S1')
    for metric,value in data.items():
        add(sid,'财务原始输入',metric,period=period,value=value,norm='原表千美元÷1000转百万美元；2025季度分部采用2026公告重述口径；分部利润未扣总部和调整项',segment='Commercial' if metric.startswith('commercial') else ('A&D' if metric.startswith('ad_') else '集团'))
for row in csv.DictReader((POOL/'2026-10-22_财务计算结果.csv').open(encoding='utf-8-sig')):
    add('S13','派生百分比及敏感性',row['metric'],unit=row['unit'],value=row['value'] if row['unit']!='%' else '',pct=row['value'] if row['unit']=='%' else '',denom=row['formula'].split('/')[1] if '/' in row['formula'] else '见公式',formula=row['formula'],kind='计算',norm='输入见同目录计算JSON及S1-S3；百分比与百分点不得混用',stage='已重算')
add('S1','终端应用','Q3 A&D34%/汽车7%/数据中心及网络41%/医疗工业仪器18%；后两者同比115%/97%；端市场与会计分部不同',unit='USD million; %',pct='34/7/41/18',denom='consolidated Q3 net sales 1203.855',formula='估算收入=集团收入×整数占比；同比采用公司原文，不从整数占比反推',layer='客户/应用')
add('S1','订单和交割后杠杆','book-to-bill 2.13；A&D backlog约2000；9月30日post-Epiq净杠杆2.8x，备考调整后LTM EBITDA分母',value='2.13; 2000; 2.8',unit='ratio; USD million; times',norm='不可把积压订单全部计入2027；9月28日账面净债务与9月30日备考不同',layer='订单/资本')
add('S1','公司指引','Q4收入1420-1440/EPS1.77-1.83；2026收入4470-4490/EPS4.97-5.03；2027收入6500-6750/EPS8.10-8.90；含STG/Epiq及融资，排除未交割',period='2026Q4E/2026E/2027E',kind='管理层预测',stage='公司初步指引',confidence='中')
add('S1','净利调整桥','84.803+24.090+9.224+9.848+6.103+4.738+0.753-0.516+18.732=157.775',value='84.803 -> 157.775',formula='GAAP NI+all disclosed reconciliation adjustments',norm='衍生工具损失含已实现及未实现；税务细节待Q3 10-Q',stage='已披露并重算')
add('S4','客户与地区','FY2025前五OEM44%；非美国运营约50%；约96%收入按进度确认；定制、无替代用途及收款权',unit='%',pct='44; ~50; 96',denom='FY2025 consolidated net sales',norm='不把运营地点当最终销售地区，不沿用为2026季度比例',layer='客户/地区/会计')
add('S4','直接竞争者','Commercial列有AT&S和WUS；A&D列有Mercury，支持按分部选择',unit='qualitative',segment='A&D/Commercial',layer='竞争',role='直接竞品')
add('S5','分部重述','2026Q1 RF&S并入A&D，变为两个可报告分部；采用最新公告比较列',unit='qualitative',layer='会计分部',norm='不直接用旧三分部年度数推导新两分部')
add('S6','Epiq融资及EPS','9月30日交割；价款约1100；Term A增量300、Term B增量800；此前票据票息6.750%；2027调整EPS摊薄/2028增厚',period='2026-09-30; 2027E/2028E',value='1100;300;800',pct='6.750',denom='senior notes principal',layer='并购/资本',stage='交割及融资已完成；收益为公司预测',norm='不把票据与增量贷款总额全部当收购价；使用部分款项')
add('S7','Ophir交易','650现金价款、10.3x 2027E EBITDA不含协同；预计2027Q2交割；不含Instruments或品牌',value='650; implied EBITDA 63.1068',formula='650/10.3',kind='披露交易及派生',layer='并购',stage='签约未交割',confidence='中',norm='不计入当前收入情景，不与含协同交易倍数直接比较')
add('S8','扩产计划','额外400，原2025-2029年1200计划；中国四厂和槟城；brownfield设备扩容',value='400;1200',pct='33.3333',denom='original investment commitment 1200',formula='400/1200*100',layer='产能',stage='计划，非已实现产出',norm='1600为多年计划，非2027单年Capex')
add('S9','沪电财务与利润','H1收入13689.427504、归母2923.361746、CFO1150.686191、Capex约3602、研发863.265913；集团毛利38.72%、PCB40.52%、数据通讯43.26%',unit='CNY million; %',value='13689.427504;2923.361746;1150.686191;~3602;863.265913',pct='38.7156;40.52;43.26',denom='对应集团/PCB/数据通讯收入；不可混用',segment='数据通讯PCB/集团',layer='竞争/产品',role='Commercial直接竞品',norm='人民币百万元；半年度不强行和TTM季度排名；FCF1150.686191-约3602=约-2451.314，购建长期资产口径')
add('S9','沪电技术节点','数据通讯11330.137462同比73.46%；32层以上收入+190.83%；1.6T批量、224Gbps小批、448Gbps及3.2T预研；泰国海外客户认证>90%',unit='CNY million; %; product milestones',value='11330.137462',pct='73.46;190.83;>90',denom='对应同期产品收入/泰国海外客户',segment='数据通讯PCB',layer='产品/客户/产能',role='Commercial直接竞品',norm='不把预研、打样当收入；泰国节点不等同国内最高规格')
add('S10','AT&S近同期财务','Q1收入548.7同比37.5%，EBITDA165/30.1%，EBIT73.4/13.4%，CFO39.9，净Capex支出34.8，ROCE12.0%',unit='EUR million; %',value='548.7;165;73.4;39.9;34.8',pct='37.5;30.1;13.4;12.0',denom='对应季度收入/公司披露ROCE定义',segment='集团',layer='竞争/资本',role='先进互连和资本密集度参照',norm='IFRS；净Capex负号转支出绝对值；简化剩余39.9-34.8=5.1，不冒充统一定义FCF')
add('S11','Mercury标准化财务','FY收入983.622，上年912.020，毛利281.165、经营利润0.280、净亏29.673、调整EBITDA150.192；CFO102.388，Capex34.301，FCF68.087，研发59.736',unit='USD million; %',value='983.622;912.020;281.165;0.280;-29.673;150.192;102.388;34.301;68.087;59.736',formula='FCF=102.388-34.301; FCF margin=68.087/983.622*100=6.92207%',segment='集团',layer='竞争/系统',role='A&D直接竞品',norm='FY ended July3与TTM季度错位；不以GAAP亏损为分母计算转换；研发费用归类不同')
add('S11','Mercury营运与平台','现金214.306、债务441.5、存货366.968；公司披露从硅到系统及RF任务处理平台',unit='USD million; qualitative',value='214.306;441.5;366.968',formula='net debt proxy=441.5-214.306=227.194',segment='集团',layer='营运/产品',role='A&D直接竞品')
add('S12','Epiq原交易倍数','17.4x expected 2027 adjusted EBITDA，含9百万run-rate协同；预计2028 Non-GAAP EPS增厚',period='2027E/2028E',value='17.4;9',unit='times; USD million',layer='并购',norm='这是含协同交易估值，不是TTM上市估值；不用于直接套倍数')
add('S14','AT&S产品与新厂','Kulim、Leoben新厂已有增长贡献；载板/先进互连资本密集度参照',unit='qualitative',segment='集团/新厂',layer='产品/产能',role='Commercial直接竞品',norm='不能用集团经营数据推出TTM载板份额')
for label,a in model['scenarios'].items():
    add('S13','2027分部情景 '+label,json.dumps(a,ensure_ascii=False),period='2027E',value=a['adj_eps'],unit='USD million; EPS USD/share; shares million',formula='AD=416.540*4*project_factor+Epiq+Europe; Commercial=787.882*4*volume_factor*mix; NI=(segment_profit-corporate-net_interest-other)*(1-tax); EPS=NI/shares',kind='假设/模型计算',stage='研究情景，不是公司披露量价或独立验证',confidence='中低',norm='忽略小额内部抵销；不含Ophir/ILFA/Merlin；STG期间及贡献待附注修正')

ledger=OUT/'TTM科技（TTMI）_evidence-ledger.csv'
with ledger.open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)

summary='中性观察、经营偏强：Q3收入同比+59.93%，Commercial贡献68.34%分部利润及83.48%增量；9M FCF率仅1.17%，Epiq交割后杠杆2.8倍，等待现金回报验证；暂不出价格估值。'
category=ROOT/'公司档案'/'README.md'
text=category.read_text(encoding='utf-8')
lines=text.splitlines()
row='| TTM科技（TTMI） | 2026-10-22 | [TTM科技（TTMI）.md](TTM科技（TTMI）/2026-10-22/TTM科技（TTMI）.md) | '+summary+' |'
lines=[line for line in lines if not line.startswith('| TTM科技（TTMI） |')]
header_end=next(i for i,line in enumerate(lines) if line.startswith('|---'))
lines.insert(header_end+1,row)
category.write_text('\n'.join(lines)+'\n',encoding='utf-8')
obj=ROOT/'公司档案'/'TTM科技（TTMI）'/'README.md'
text=obj.read_text(encoding='utf-8')
row='| 2026-10-22 | 初始覆盖 / 2026Q3财报研究 | '+summary+' | 最新Q3、2027初步指引、分部利润与同行、GAAP调整桥、交割前后债务及盈利压力测试 | Commercial连续两季利润率<18%；滚动半年FCF负且无客户资金支持；交割后杠杆持续>3倍 | [TTM科技（TTMI）.md](2026-10-22/TTM科技（TTMI）.md) | [TTM科技（TTMI）_evidence-ledger.csv](2026-10-22/TTM科技（TTMI）_evidence-ledger.csv) |'
obj.write_text('\n'.join(row if line.startswith('| 2026-10-22 |') else line for line in text.splitlines())+'\n',encoding='utf-8')
print(f'ledger rows={len(rows)}, source IDs={len(meta)}; both README indexes synchronized.')
