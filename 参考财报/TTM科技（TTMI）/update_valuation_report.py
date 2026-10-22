import csv
import io
import json
import re
from pathlib import Path

POOL=Path(__file__).resolve().parent
ROOT=POOL.parents[1]
REPORT=ROOT/'公司档案/TTM科技（TTMI）/2026-10-22/TTM科技（TTMI）.md'
LEDGER=REPORT.with_name('TTM科技（TTMI）_evidence-ledger.csv')
original=REPORT.read_text(encoding='utf-8')
backup=POOL/'2026-10-22_估值补充前主报告快照.md'
if not backup.exists():
    backup.write_text(original,encoding='utf-8')
old_bytes=LEDGER.read_bytes()
ledger_backup=POOL/'2026-10-22_估值补充前台账快照.csv'
if not ledger_backup.exists():
    ledger_backup.write_bytes(old_bytes)
text=original
def section(title,body):
    global text
    start=text.index(title)
    end=text.find('\n## ',start+len(title))
    if end<0: end=len(text)
    text=text[:start]+body.rstrip()+'\n'+text[end:]
def paragraph(prefix,body):
    global text
    pattern=re.escape(prefix)+r'.*?(?=\n\n|\Z)'
    text,n=re.subn(pattern,lambda _:body,text,count=1,flags=re.S)
    assert n==1,prefix

text=text.replace('**报告类型：** 初始覆盖 / 2026Q3财报研究。','**报告类型：** 初始覆盖 / 2026Q3财报研究 / 估值补充（原地更新）。',1)
text=text.replace('**信息截止日期：** 2026-10-22，北京时间；纳入当日新发布的Q3业绩和2027初步指引。','**信息截止日期：** 2026-10-22，北京时间；财务截至当日Q3公告；估值股价固定为美东10:54（北京时间22:54）的75.19美元盘中快照，非收盘价。',1)
paragraph('**核心判断：**','**核心判断：** 以2026-10-22美东10:54的75.19美元盘中价判断，**尚未明显透支2027年调整后盈利，但已经依赖未来现金转化改善**。公司2027 EPS指引中值8.50对应8.85倍PE，自有分部Base EPS8.39对应8.96倍；按条件估值Base约92.26–117.42美元。维持**中性观察、等待现金回报验证**：盈利上存在折价，Bear与现金流风险仍足以推翻乐观判断。[S1、S13、S15、S19]')
paragraph('**市场可能误判 / 机构估值分歧：**','**市场可能误判 / 机构估值分歧：** 用滞后的40多倍GAAP PE评价新价格，会忽略当日下跌及最新业绩；反过来，直接用不足9倍2027调整PE也会忽略资本消耗。公开聚合的211美元目标价仍来自财报前评级，不能视为财报后更新估值。原文的应用/分部、交割前后口径区分继续有效。[S15、S16、S19]')
paragraph('**同行竞品定位：**','**同行竞品定位：** 本轮同交易日可得近时点价格配2027预测，TTM自有Base PE8.96倍，对照Sanmina约11.05倍、沪电约21.35倍、Mercury约44.78倍。后三者来自公开聚合预测，财年与业务纯度不同；Mercury处于低利润基数，不能套用44倍。TTM的资本消耗与并购杠杆要求折价，商业升级则支持在兑现后获得较普通EMS更高的倍数。[S17、S19]')
paragraph('**关键百分比变化：**','**关键百分比变化：** Q3收入同比+59.93%、Commercial分部利润率21.10%；现价对应2027指引PE约8.45–9.28倍，自有Base条件估值空间约+22.7%至+56.2%；但过去十二个月FCF仅47.422，按110百万稀释股数估算现金收益率0.57%。[S1、S13、S19]')

section('## 关键信息栏', '''## 关键信息栏

| 项目 | 内容 | 依据 / 截点 |
|---|---|---|
| 投资观点 | 中性观察；2027盈利估值未明显透支，现金回报仍需验证 | 75.19美元，2026-10-22美东10:54 / 北京22:54盘中快照 |
| 适合阶段 | 财报后估值与经营兑现跟踪 | 非收盘价，后续价格变化须重算 |
| 观察价格/估值区间 | 用Base 92.26–117.42美元作条件估值对照；当前75.19低于该区间 | 2027自有EPS8.387×11–14倍；非直接交易指令 |
| 提高关注触发条件 | 价格相对Base仍有余量，商业利润率和订单交付兑现、滚动FCF改善、净杠杆下降；最新评级模型与风险未恶化 | 基本面、价格与催化共同验证 |
| 分批观察条件 / 重点对象 | 跟踪商业利润率、项目时点、合同资产回款、资本开支与交割后杠杆 | 不给单点建仓价 |
| 目标估值区间 | Bear32.43–40.54；Base92.26–117.42；Bull153.44–186.32美元 | 自有分部模型EPS4.05/8.39/10.96；倍数为研究假设 |
| 上行空间 | Base约+22.7%至+56.2%；Bull约+104.1%至+147.8% | 相对75.19，不是概率加权预期收益 |
| 下行风险 | Bear约-56.9%至-46.1% | 收入兑现放缓、利润率回落并叠加估值压缩 |
| 持有周期假设 | 条件估值用于未来6–12个月观察；产能回报需1–3年验证 | 不是个人持仓安排 |
| 核心催化剂 | Q4兑现、2027原有业务增长与并购桥、现金转化和去杠杆 | 未来财报日期未核实 |
| 退出 / 降低关注条件 | Commercial连续两季利润率<18%、滚动半年FCF负且缺少客户支持、杠杆持续>3倍，或2027指引显著下修 | 研究阈值，不是契约违约线 |
| 风险等级 | 高 | Bear跌幅可超过Base下沿上行；低PE尚非低风险 |
''')
text=text.replace('| 最大缺口 | 并购后资产负债表、应用层利润/量价数据、机构与同截点估值 |','| 估值结论 | 75.19美元对应2027指引PE8.85倍；盈利未明显透支，但LTM FCF收益率仅约0.57% |\n| 最大缺口 | 机构原始模型、并购后资产负债表、应用利润/量价；已补公开盘中价格与近时点同行估值 |',1)

section('## 2. 机构估值与估值依据','''## 2. 机构估值与估值依据

### 2.1 来源覆盖：原始研报、公开聚合与公司指引分开

| 来源类型 | 覆盖状态 | 已取得内容 | 限制 |
|---|---|---|---|
| 国内券商 | 原文未取得 | 无直接可核验覆盖模型 | 不编目标价或倍数 |
| 外资 / 国际机构 | 原文未取得；公开转述已取得 | Stifel、Needham、Truist、B. Riley等财报前评级及目标价 | Tier 2，不冒充Tier 1A原始报告；未取得外资/国际机构可核验原始估值模型 |
| 终端一致预期 | 终端导出未取得；公开聚合已取得 | StockAnalysis标注S&P Global/TipRanks，TTMI预测最后更新10月20日 | 未取得终端一致预期导出数据；不是10月22日财报后实时共识 |
| 公司 / 交易所 / IR引用 | 公司指引已取得；机构估值未取得 | 2027收入6,500–6,750、调整EPS8.10–8.90 | 指引来自S1，非机构目标价 |

### 2.2 财报前机构观点，不直接当作财报后合理价值

| 机构 / 分析师 | 公开记录日期 | 评级与目标价，美元 | 方法、倍数与财年 | 现价机械空间 / 来源 |
|---|---|---|---|---|
| Stifel / Ruben Roy | 2026-10-20 | Buy，205 | 原始方法及预测财年未取得；媒体转述关注2027有机增长、FCF及去杠杆 | 约+172.6%；S16、S20 |
| B. Riley / Mike Crawford | 2026-10-16 | Buy，208 | 原始方法、倍数及财年未取得 | 约+176.6%；S16 |
| Truist / William Stein | 2026-10-13 | Buy，231 | 原始方法、倍数及财年未取得 | 约+207.2%；S16 |
| Needham / James Ricchiuti | 2026-09-21 | Buy，175，由220下调 | 原始方法、倍数及财年未取得 | 约+132.7%；S16 |
| 公开聚合5家 | 页面最后更新2026-10-20 | 平均211、中位208，范围175–236 | 不是本研究目标价 | 均值机械空间约+180.6%；S16 |

以上空间=(目标价/75.19−1)，不代表目标价可靠度或未来收益。四家记录均早于Q3财报，尚未证明已吸收本次电话会与价格变化。不能把175–236当作本报告Base。

### 2.3 为什么财报前目标价这么高，而现价看起来很低

公开旧预测为2026 EPS4.81、2027 EPS7.29、2027收入约5,850，最后更新10月20日；公司10月22日新指引中值为8.50和6,625。后者分别比这组旧预测高约16.6%/13.2%，但二者采样时点不同，不能称超过最新终端共识。[S1、S16]

若把211美元除以新指引中值8.50，隐含约24.82倍PE；175–236对应20.59–27.76倍。这只是反推，不是各机构真实估值方法。与当前8.85倍相比，差异首先来自市场愿意支付的倍数与现金兑现信心，不能仅靠EPS上修解释。[S19]
''')

peer_add='''
### 4.5 估值补充：同交易日近时点、同标注2027财年的比较

本表为10月22日可取得的同交易日快照，**非同一秒**。沪电为当日中国市场延时报价，美国样本为盘中；高波动期间存在时点误差。EPS来自公开聚合，不能与机构原文等同。

| 公司 / 用途 | 价格与时间 | 2027 EPS / 财年截止 | 自算2027 PE | 对TTM倍数的约束 |
|---|---|---|---:|---|
| TTM，集团 | USD75.19，美东10:54 | 公司8.10–8.90；自有Base8.387，2027年末 | 8.45–9.28；Base8.96 | 不能把集团全当AI纯业务 |
| 沪电，Commercial直接竞品 | CNY106.96，北京15:04延时 | CNY5.01，2027-12-31 | 21.35 | 数据通讯纯度、应用毛利与A股定价不同，不能整组套用 |
| Sanmina，制造平台估值参照 | USD155.64，美东10:31 | USD14.08，2027-09-30 | 11.05 | TTM年报亦列为A&D竞品；集团EMS/组装比重更高、利润结构不同，只用于倍数交叉检验 |
| Mercury，A&D系统竞品 | USD74.79，美东10:36 | USD1.67，2027-06-30 | 44.78 | 低盈利基数和恢复期使PE放大，不用44倍给TTM定价 |

来源：S4、S17、S19。TTM Base当前PE比Sanmina低约18.9%、比沪电低约58.0%；只是算术差额，不能直接等同可回归空间。TTM Base研究倍数11–14倍接近Sanmina至约27%溢价、仍低于沪电约34%–48%：产品升级和较快增长支持溢价，薄FCF、杠杆和并购整合限制上限。AT&S仍保留经营比较，未取得足够标准化2027EPS，不强填估值。
'''
marker='## 5. 近期经营事实与财务质量'
if '### 4.5 估值补充' not in text:
    text=text.replace(marker,peer_add+'\n'+marker,1)

call_add='''
### 5.3 电话会转录补充：对估值信心的影响

本轮新取得StockAnalysis刊载、标注Quartr来源的Q3电话会转录，按**Tier 2**使用，尚未取得IR授权文字稿。转录中分析师指出数据中心及网络收入较前次预期低约10%，管理层解释为客户项目时点，第三个项目预计Q4后段爬坡、Q1充分生产；它与整体收入创新高并不矛盾，但提示不能只看集团总数。[S18]

转录还称Q4利息约33.9、利息收入约3.0，2027 EPS指引股数108.1百万；原模型股数110和年净融资165继续作为审慎研究假设保留，不把转录中的新口径悄悄混入原分部模型。新增融资可能解释部分EPS兑现压力，但本文不把全部盘中跌幅归因于单一事件。[S18、S19]
'''
if '### 5.3 电话会转录补充' not in text:
    text=text.replace('## 6. 基本面与财务质量',call_add+'\n## 6. 基本面与财务质量',1)
text=text.replace('公司期望届时杠杆在1.5–2.0倍目标范围；缺少完整桥及交割前后口径说明','公司公告期望在1.5–2.0倍目标范围；新获第三方转录称交割时低于2倍，但仍缺可核验净债务及备考EBITDA桥',1)

start=text.index('### 9.2 敏感性与估值输入')
end=text.index('\n## 10. 投资风险',start)
text=text[:start]+'''### 9.2 当前价格到底对应多少倍盈利

**事实：** 采用75.19美元，2026-10-22美东10:54 / 北京22:54盘中报价，较前收102.15低26.39%；不是收盘价，也不保证交付时仍是该价格。Nasdaq/公司静态页面未返回可用数字，以已保存的公开价格快照为计算锚，不沿用约100美元旧报价。[S15]

| 盈利分母 | 数值与期间 | 现价对应PE | 口径 |
|---|---|---:|---|
| GAAP LTM | 净利268.523，最新季度稀释股数107.699作代理 | 30.16倍 | LTM利润=2025全年−2025年9M+2026年9M，不把不同期间EPS机械相加 |
| 调整后LTM | 净利419.557，股数代理同上 | 19.30倍 | 调整净利与GAAP不同 |
| 公司2026指引 | EPS4.97–5.03 | 14.95–15.13倍 | Non-GAAP |
| 公司2027初步指引 | EPS8.10–8.90，中值8.50 | 8.45–9.28倍，中值8.85倍 | 未含Ophir等未交割收购 |
| 自有2027分部Base | EPS8.387 | 8.96倍 | 承接9.1量价利、费用、融资假设 |
| 10月20日公开旧预测 | 2027 EPS7.29 | 10.31倍 | 不是本次财报后终端共识 |

来源：S1、S3、S13、S15、S16、S19。估值分母切换会造成30倍与9倍同时存在，两者并不互相矛盾。低前瞻PE依赖2027盈利跃升，不代表已实现利润便宜。

### 9.3 盈利兑现后的条件估值，而非无条件目标价

| 情景 | 原分部模型2027 EPS | 研究PE假设 | 条件价格，美元 | 相对75.19空间 | 对应条件 |
|---|---:|---:|---:|---:|---|
| Bear | 4.054 | 8–10倍 | 32.43–40.54 | -56.9%至-46.1% | 商业利润率18%、交付慢、融资负担高，现金信心折价 |
| Base | 8.387 | 11–14倍 | 92.26–117.42 | +22.7%至+56.2% | 商业利润率24%、A&D20%、现金转化和杠杆改善 |
| Bull | 10.960 | 14–17倍 | 153.44–186.32 | +104.1%至+147.8% | 商业交付/组合更强、利润率26%，现金及整合均兑现 |

价格=自有分部EPS×研究倍数；不是直接使用机构净利。倍数取舍与4.5竞品、资本效率及产品纯度相连：Base接近Sanmina制造平台估值并允许增长溢价，但显著低于沪电；Bull仍不采用Mercury的恢复期高倍数；Bear将EPS下修和倍数压缩叠加。区间是2027E盈利、未来6–12个月观察口径，非特定交易日的精确内在价值。[S17、S19]

这些倍数**有研究主观性**，不是TTM历史分位或机构原文结论。Base下沿的潜在上行小于Bear最大下行，不能据此把观点升级为高确定性积极关注。

### 9.4 反推：当前股价要求多少2027盈利与利润率

| 假设市场愿付PE | 支持75.19所需EPS | 比公司中值8.50低 | 固定Base其他变量后所需Commercial利润率 |
|---|---:|---:|---:|
| 10倍 | 7.519 | 11.5% | 21.31% |
| 11倍 | 6.835 | 19.6% | 19.19% |
| 12倍 | 6.266 | 26.3% | 17.43% |
| 14倍 | 5.371 | 36.8% | 14.66% |
| 15倍 | 5.013 | 41.0% | 13.55% |

EPS=75.19/PE；所需商业利润=[EPS×110/(1−22%)+总部145+净融资165+其他10−A&D利润410.220]；再除商业收入4,552.382。[S19]

**判断：** 约9倍前瞻PE没有要求比公司指引更高的EPS，当前价格更接近对指引兑现打折。12倍情景容许约26% EPS落差；但利润变差时市场倍数也可能降低，**不能把上表称为保本空间**。所需利润率反推仍假设Base收入兑现，若收入也下修，该缓冲会缩小。

### 9.5 现金流约束：为何9倍PE仍可能不便宜

LTM公司FCF=17.942−6.265+35.745=47.422。按原Base的110百万未来稀释股数估算权益价值75.19×110=8,270.9，LTM FCF收益率仅0.57%。这是含未来稀释的估值代理，**不是声称当前普通股总市值为8,270.9**；7月31日披露普通股数105.348864对应约7,921.2，但股数时点较旧，仅辅助核对。[S3、S5、S19]

| 用现价反推成熟阶段现金回报 | 所需年度FCF | 占Base调整净利922.577 |
|---|---:|---:|
| 4% FCF收益率 | 330.836 | 35.86% |
| 6% | 496.254 | 53.79% |
| 8% | 661.672 | 71.72% |
| 10% | 827.090 | 89.65% |

本表是静态收益要求敏感性，不是DCF、不是公司2027 FCF指引，也不要求2027必须达到成熟现金收益率。它揭示现价需要未来FCF从当前水平明显上台阶。[S19]

进一步检验Base价格区间：在6%成熟现金收益率假设下，11–14倍PE要求FCF/调整净利约66%–84%；若最终仅转化40%，以6%–8%现金收益率衡量的简化资本化值约41.94–55.91美元；若转化60%，约62.90–83.87；若80%，约83.87–111.83。公式=Base EPS×现金转化率/现金收益要求。未计增长、债务偿还、未来稀释与交易，不冒充完整内在价值模型。

SBC另做口径敏感性：将Q3 SBC24.090年化为96.360，按22%税率、110股数相当于每股0.683；从Base调整EPS扣除后为7.704，对应9.76倍。此为保守经济成本对照，不是GAAP预测；SBC与未来稀释存在联系，不能在正式估值中不加区分重复惩罚。[S19]

### 9.6 净债务和EV的口径裁决

简化交割后净债务=9月28日账面净债务代理767.525+9月30日增量贷款1,100≈1,867.525。该桥假设新增贷款与收购价款约相抵，排除费用、交割调整与其他期间变动，**不是公司报告的9月30日净债务**。用110股数估计EV约10,138.425。[S1、S6、S19]

若除以LTM调整EBITDA668.133，表面约15.17倍，但分子已含Epiq债务，分母尚未充分包含Epiq收益，口径错配，故不据此判断贵贱，也不套用公司2.8倍备考净杠杆反造精确债务。PE已经使用扣融资费用的权益盈利，不另减一遍净债务。Ophir若交割，现金支出和标的收益/价值应同时更新；本轮同口径排除，不能只加盈利或只减650现金。

**估值结论：** 对75.19美元这个明确快照，2027盈利未明显透支；Base条件估值有空间，但现金估值尚要求明显兑现。若未来FCF长期只转化约40%调整净利、Commercial收入/利润率不达标，或者杠杆不降，当前低PE可成为价值陷阱。
''' + text[end:]

text=text.replace('| 估值与稀释 | 远期盈利提前定价，SBC降低每股经济收益 | 未量化 / 高 | Bear EPS比Base低51.7%；股数+1%使EPS-0.99% | 取得同截点估值后检查回报要求 |','| 估值与稀释 | 指引落空与倍数压缩叠加，SBC降低每股经济收益 | 中 / 高 | 当前Base估值上行22.7%–56.2%，Bear下行46.1%–56.9% | 不能把12倍反推缓冲当保本；FCF长期仅40%转化需降低估值 |',1)
text=text.replace('4. 2027指引显著下调、Epiq增厚再延后或新收购吞噬运营改善：优先按Bear重估。','4. 2027指引显著下调、Epiq增厚再延后或新收购吞噬运营改善：优先按Bear重估。\n5. 若成熟阶段FCF长期仅约40%调整净利，缺少合理成长性补偿：原11–14倍Base估值不成立，不能因2027 PE不足9倍而忽略现金折价。',1)
text=text.replace('| 2027增长桥 | 收入6,500–6,750，EPS8.10–8.90 | 有机/组合/并购/税率/股数，避免合并增速充当有机增速 |','| 2027增长桥 | 收入6,500–6,750，EPS8.10–8.90 | 有机/组合/并购/税率/股数，避免合并增速充当有机增速 |\n| 估值与现金转化 | 75.19快照；Base92.26–117.42 | 价格变化即重算；跟踪FCF是否向6%–8%收益要求所需496–662上台阶，非公司年度指引 |',1)

update_row='| 2026-10-22 | 估值更新 / 风险复盘 | 新增75.19盘中报价、公开旧预测与机构目标价、近时点同行；改投资结论/信息栏/第2、4、5、9–11节；由暂不估值更新为盈利未明显透支、Base条件估值92.26–117.42 | S15–S20为本轮新抓取/新计算；S1–S14及原分部模型为本地已有，本轮复用；用户未附新文件；ledger追加、旧251行保留 | 两级索引原日期行同步，不新建版本 | 机构原始模型、实时终端导出、并购后完整资产负债表和项目FCF仍缺；报价非收盘 |'
pos=text.index('\n## 质量收敛记录')
if update_row not in text:
    text=text[:pos].rstrip()+'\n'+update_row+'\n'+text[pos:]

section('## 质量收敛记录','''## 质量收敛记录

| 项目 | 结论 | 处理 |
|---|---|---|
| 结构校验 | 估值更新后待最终运行 | check_report.py --require-update-log；旧76项原始数字核验仍适用，新估值计算另行校验 |
| 业务拆解与同行深度 | 人工自评：业务22/25、同行22/25、模型估值17/20、证据13/15、风险9/10、洞见4/5，总87/100 | 加入Sanmina倍数参照及竞争→模型→估值桥；公开价格/预测为Tier 2、原始机构模型缺失扣分；无硬失败 |
| 证据收敛 | 原财务与分部模型保留，新增行情、机构转述、同行和公式可追溯 | 固定75.19的明确时间；不混用约100美元旧价；不把10/20预测当财报后共识 |
| 证据来源口径 | 本轮新抓取S15–S18、S20；本轮计算S19；S1–S14和分部模型均为本地已有，本轮复用；用户未附新文件 | 只追加台账，旧来源ID不变；补充前主报告和台账快照保存在参考财报 |
| 口径裁决 | Non-GAAP/GAAP分开，财年错位明确；盘中非收盘；净债务桥为代理 | LTM EV/EBITDA因Epiq分子分母错配不作估值锚；PE不重复扣债务 |
| 逻辑一致性 | 盈利未明显透支、现金仍需兑现；中性观察、风险高一致 | Bear下行可大于Base下沿上行，未升级为高确定性积极关注 |
| README同步 | 分类与对象原2026-10-22行已更新 | 不新开日期目录、不新增对象版本行 |
| 未收敛缺口 | 已补价格和条件估值，原始机构模型、完整Q3附注/并购后资产负债表与项目FCF尚缺 | 估值区间为假设驱动；原始行情交叉核验未完成，采用可追溯公开快照并明示限制 |
''')

new_sources='''
| S15 | TTMI价格快照；StockAnalysis；2026-10-22美东10:54 | [价格页面](https://stockanalysis.com/stocks/ttmi/forecast/)；参考财报/TTM科技（TTMI）/2026-10-22_估值补充_初始行情与预测_web抓取.json及定稿来源_web抓取.json；75.19美元，前收102.15 | Tier 2；公开行情，盘中非收盘 |
| S16 | 机构目标价与公开预测；StockAnalysis，标注S&P Global/TipRanks；最后更新2026-10-20 | [预测页](https://stockanalysis.com/stocks/ttmi/forecast/)；同S15快照；2027 EPS7.29、收入5.85B，机构目标价均在Q3财报前 | Tier 2；不是机构原文或终端导出 |
| S17 | 沪电/Sanmina/Mercury价格与预测；StockAnalysis；2026-10-22访问 | [沪电](https://stockanalysis.com/quote/she/002463/forecast/)、[Sanmina](https://stockanalysis.com/stocks/sanm/forecast/)、[Mercury](https://stockanalysis.com/stocks/mrcy/forecast/)；参考财报/TTM科技（TTMI）/2026-10-22_估值补充_定稿来源_web抓取.json及同行_web抓取.json、同行预测与资本开支检索_web抓取.json；财年与报价时点见4.5 | Tier 2；公开聚合 |
| S18 | Q3电话会转录；StockAnalysis / Quartr；2026-10-22 | [转录](https://stockanalysis.com/stocks/ttmi/transcripts/725340-q3-2026/)；参考财报/TTM科技（TTMI）/2026-10-22_估值补充_Q3电话会_web抓取.json、电话会与同行期间_web抓取.json及定稿来源_web抓取.json；Q&A和财务指引 | Tier 2；未取得IR授权稿 |
| S19 | 估值计算；本研究；2026-10-22 | 参考财报/TTM科技（TTMI）/valuation_analysis.py及2026-10-22_估值补充_计算结果.json；继承S13分部模型，新增PE/反推/现金敏感性 | 派生计算/研究假设 |
| S20 | Stifel财报前观点转述；Investing.com；2026-10-20 | [报道](https://www.investing.com/news/analyst-ratings/stifel-reiterates-buy-on-ttm-technologies-stock-ahead-of-results-93CH-4959271)；参考财报/TTM科技（TTMI）/2026-10-22_估值补充_机构检索_web抓取.json；205美元、FCF与去杠杆条件 | Tier 2；非原始研报 |
'''
if '| S15 |' not in text:
    text=text.replace('\n**来源完整性：**', '\n'+new_sources+'\n**来源完整性：**',1)

# Append new evidence without modifying the original rows or source IDs.
rows=list(csv.DictReader(io.StringIO(old_bytes.decode('utf-8'))))
fields=list(rows[0])
existing={r['source_id'] for r in rows}
new=[]
def evidence(sid,topic,claim,file,url,period,unit='',value='',pct='',denominator='',formula='',normalization='',method='',target='',rating='',multiple='',kind='事实',publisher='StockAnalysis',date='2026-10-22',section_name='',confidence='中'):
    path=POOL/file
    assert path.exists(),path
    d=dict.fromkeys(fields,'')
    d.update(source_id=sid,topic=topic,claim_or_metric=claim,claim_type=kind,source_tier='Derived/Assumption' if sid=='S19' else 'Tier 2',publisher_or_issuer=publisher,document_title=topic,publication_date=date,data_period=period,currency_unit=unit,source_path_or_url=str(path),page_or_section=section_name or topic,access_date='2026-10-22',confidence=confidence,verification_stage='公开快照/原文模型未取得' if sid!='S19' else '派生计算/假设',normalization_note=normalization,valuation_method=method,target_price_or_range=target,rating=rating,valuation_multiple_or_key_assumption=multiple,absolute_value=value,percentage_value=pct,percentage_denominator=denominator,calculation_formula=formula,notes_or_formula=('本轮派生计算' if sid=='S19' else '本轮新抓取')+'；原始URL：'+url)
    new.append(d)

snapshot='2026-10-22_估值补充_定稿来源_web抓取.json'
evidence('S15','TTMI固定行情','75.19美元；前收102.15；报价美东10:54/北京22:54，盘中非收盘',snapshot,'https://stockanalysis.com/stocks/ttmi/forecast/','2026-10-22 10:54 EDT',unit='USD/share',value='75.19;102.15',pct='-26.39256',denominator='previous close 102.15',formula='(75.19/102.15-1)*100',normalization='无法从Nasdaq/IR静态页取得可用报价；公开可追溯快照，不称独立交叉验证')
evidence('S16','TTMI财报前公开预测','2026 EPS4.81、2027 EPS7.29、2027收入约5850；5家目标均值211、中位208、175-236',snapshot,'https://stockanalysis.com/stocks/ttmi/forecast/','2026E/2027E；页面最后更新2026-10-20',unit='USD/share; USD million',value='4.81;7.29;5850;211;208;175;236',normalization='标注SP Global/TipRanks；财报前旧预测，不是财报后终端共识',date='2026-10-20',kind='机构公开聚合')
for firm,date,target in [('Stifel','2026-10-20',205),('B.Riley','2026-10-16',208),('Truist','2026-10-13',231),('Needham','2026-09-21',175)]:
    evidence('S16','财报前机构评级 '+firm,firm+' Buy target '+str(target),snapshot,'https://stockanalysis.com/stocks/ttmi/forecast/','预测财年未取得；12个月目标',unit='USD/share',value=str(target),method='原始方法未取得',target=str(target),rating='Buy',date=date,normalization='第三方转述，原始倍数和模型未取得；不能冒充Tier1A')
for company,price,eps,period in [('WUS',106.96,5.01,'2027-12-31'),('SANM',155.64,14.08,'2027-09-30'),('MRCY',74.79,1.67,'2027-06-30')]:
    evidence('S17','同行估值 '+company,f'price {price}, FY2027 EPS {eps}',snapshot,'https://stockanalysis.com/','FY2027 ending '+period,unit='WUS CNY/share; others USD/share',value=f'{price};{eps};PE={price/eps}',formula=f'{price}/{eps}',method='2027E adjusted PE',normalization='同交易日近时点非同秒；SANM10:31EDT，MRCY10:36EDT，WUS15:04CST；财年/业务纯度不同；公开聚合非机构原文',multiple=f'{price/eps:.8f}x')
evidence('S18','Q3电话会转录新增口径','第三方转录：DCN较前次预期低约10%，管理层归因项目时点；Q4利息33.9/利息收入3；2027指引108.1百万股；Ophir交割净杠杆预计<2x',snapshot,'https://stockanalysis.com/stocks/ttmi/transcripts/725340-q3-2026/','2026Q3call / 2026Q4E / 2027E',unit='USD million; million shares; %; times',value='33.9;3.0;108.1',pct='~10',normalization='Quartr第三方转录，未取得IR授权稿；原110股数/165融资假设保留；不单因果解释当日跌幅',confidence='中',publisher='StockAnalysis/Quartr')
v=json.loads((POOL/'2026-10-22_估值补充_计算结果.json').read_text(encoding='utf-8'))
for key,value in v['ratios'].items():
    evidence('S19','估值计算 '+key,str(value),'2026-10-22_估值补充_计算结果.json','','LTM through 2026-09-28 / 2026E / 2027E',unit='USD million; USD/share; times; percent as named',value=str(value),formula='见valuation_analysis.py同名键公式',normalization='原始输入S1/S3/S5/S6/S13/S15/S16；110为未来稀释假设，非当前普通股总数；净债务桥为代理',publisher='本研究',kind='计算/假设')
for label,value in v['valuation'].items():
    evidence('S19','条件估值 '+label,json.dumps(value,ensure_ascii=False),'2026-10-22_估值补充_计算结果.json','','2027E',unit='USD/share; times; %',value=str(value['eps']),pct=str(value['return_pct']),denominator='price 75.19',formula='own segment EPS*research PE; (value/75.19-1)*100',method='2027E adjusted PE',target=str(value['price_range']),multiple=str(value['pe']),normalization='分部经营模型S13；倍数以SANM/WUS交叉检验并反映资本效率、业务纯度及并购风险，非机构原文',publisher='本研究',kind='估值假设')
evidence('S19','逆向盈利与利润率',json.dumps(v['reverse_PE'],ensure_ascii=False),'2026-10-22_估值补充_计算结果.json','','2027E',unit='EPS USD/share; %',formula='EPS=P/PE; Commercial margin=(EPS*110/.78+145+165+10-410.21984)/4552.382196',normalization='除商业利润率外固定Base变量；收入若也不达标则缓冲缩小；非保本',publisher='本研究',kind='敏感性')
evidence('S19','逆向现金转化及SBC',json.dumps({'cash':v['cash_yield'],'SBC':v['SBC_stress'],'cash_multiple':v['cash_supported_multiples']},ensure_ascii=False),'2026-10-22_估值补充_计算结果.json','','mature-state sensitivity; not company 2027 FCF forecast',unit='USD million; USD/share; %',formula='Required FCF=75.19*110*yield; price=BaseEPS*conversion/yield; SBC cost=24.09*4*.78/110',normalization='简单现金资本化敏感性，非DCF；SBC经济成本与稀释不得在正式估值无区分重复惩罚',publisher='本研究',kind='敏感性')
evidence('S20','Stifel观点转述','10/20维持Buy/205；关注2027有机增长、资本开支转FCF和回到1.5-1.7倍杠杆','2026-10-22_估值补充_机构检索_web抓取.json','https://www.investing.com/news/analyst-ratings/stifel-reiterates-buy-on-ttm-technologies-stock-ahead-of-results-93CH-4959271','财报前，模型财年未取得',unit='USD/share; times',value='205',method='原文方法未取得',target='205',rating='Buy',publisher='Investing.com转述Stifel',date='2026-10-20',normalization='Tier2报道，不当作原始研报或最新共识')
to_append=[r for r in new if r['source_id'] not in existing]
if to_append:
    with LEDGER.open('a',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writerows(to_append)
assert LEDGER.read_bytes().startswith(old_bytes),'Old ledger content changed'
text=text.replace('| 日期 | 类型 | 章节与结论变化 | 证据来源口径 | README | 未收敛缺口 |','| 日期 | 类型 | 新增信息 / 改动章节与结论变化 | 证据来源口径 | README | 未收敛缺口 |')
REPORT.write_text(text,encoding='utf-8')

summary='中性观察：75.19美元盘中快照对应2027公司指引PE8.85倍，尚未明显透支盈利；自有Base条件估值92.26–117.42美元，Bear32.43–40.54。LTM FCF收益率仅约0.57%，现金转化和去杠杆仍是前提。'
category=ROOT/'公司档案/README.md'
t=category.read_text(encoding='utf-8')
t='\n'.join('| TTM科技（TTMI） | 2026-10-22 | [TTM科技（TTMI）.md](TTM科技（TTMI）/2026-10-22/TTM科技（TTMI）.md) | '+summary+' |' if line.startswith('| TTM科技（TTMI） |') else line for line in t.splitlines())+'\n'
category.write_text(t,encoding='utf-8')
obj=REPORT.parent.parent/'README.md'
t=obj.read_text(encoding='utf-8')
t='\n'.join('| 2026-10-22 | 初始覆盖 / Q3财报及估值补充 | '+summary+' | 原分部模型保留；补盘中价格、旧共识/目标价、近时点同行、反推EPS/商业利润率与FCF敏感性 | 商业连续两季利润率<18%；FCF长期仅40%调整净利；杠杆持续>3倍或指引显著下修 | [TTM科技（TTMI）.md](2026-10-22/TTM科技（TTMI）.md) | [TTM科技（TTMI）_evidence-ledger.csv](2026-10-22/TTM科技（TTMI）_evidence-ledger.csv) |' if line.startswith('| 2026-10-22 |') else line for line in t.splitlines())+'\n'
obj.write_text(t,encoding='utf-8')
print(f'Updated same report and both README indexes; appended {len(to_append)} ledger rows; old bytes preserved.')
print(f'Ledger total rows={len(list(csv.DictReader(LEDGER.open(encoding="utf-8"))))}; source IDs=20')
