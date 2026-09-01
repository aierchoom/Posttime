import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

const sections = [
  { key: 'companies', title: '公司档案', dir: '公司档案', accent: 'company' },
  { key: 'sectors', title: '产业链研究', dir: '产业链研究', accent: 'sector' },
  { key: 'events', title: '事件研究', dir: '事件研究', accent: 'event' }
]

function toPosix(filePath) {
  return filePath.split(path.sep).join('/')
}

function stripMd(filePath) {
  return filePath.replace(/\.md$/i, '')
}

function walk(dir) {
  if (!existsSync(dir)) return []
  const entries = readdirSync(dir, { withFileTypes: true })
  return entries.flatMap((entry) => {
    const fullPath = path.join(dir, entry.name)
    if (entry.isDirectory()) return walk(fullPath)
    return fullPath
  })
}

function readUtf8(filePath) {
  return readFileSync(filePath, 'utf8').replace(/^\uFEFF/, '')
}

function firstHeading(markdown, fallback) {
  const heading = markdown.match(/^#\s+(.+)$/m)
  return heading ? heading[1].trim() : fallback
}

function firstSummary(markdown) {
  const preferred = markdown.match(/^\*\*(?:核心判断|核心结论|核心观点)：\*\*\s*(.+)$/m)
  if (preferred) return preferred[1].replace(/\[[^\]]+\]/g, '').trim().slice(0, 160)

  const lines = markdown
    .replace(/```[\s\S]*?```/g, '')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)

  const candidate = lines.find((line) => {
    if (line.startsWith('#')) return false
    if (line.startsWith('|')) return false
    if (line.startsWith('>')) return false
    if (/^-\s+\*\*(?:报告类型|档案名称|信息截止日期|市场与货币|研究期限|投资期限|数据可靠性|报告日期版本)：/.test(line)) return false
    if (/^[-*_]{3,}$/.test(line)) return false
    return /[\u4e00-\u9fffA-Za-z0-9]/.test(line)
  })

  if (!candidate) return '已归档研报，保留版本、证据台账与后续复盘入口。'
  return candidate.replace(/^[-*]\s+/, '').replace(/\[[^\]]+\]/g, '').slice(0, 160)
}

function countLedgerRows(filePath) {
  if (!existsSync(filePath)) return 0
  const lines = readUtf8(filePath).split(/\r?\n/).filter((line) => line.trim())
  return Math.max(0, lines.length - 1)
}

function findLedger(reportPath) {
  const dir = path.dirname(reportPath)
  const base = path.basename(reportPath, '.md')
  const preferred = path.join(dir, `${base}_evidence-ledger.csv`)
  if (existsSync(preferred)) return preferred
  const ledgers = readdirSync(dir).filter((name) => /_evidence-ledger\.csv$/i.test(name))
  return ledgers.length ? path.join(dir, ledgers[0]) : ''
}

function reportDate(relativeParts, objectName) {
  const datePart = relativeParts.find((part) => /^\d{4}-\d{2}-\d{2}/.test(part))
  if (datePart) return datePart.slice(0, 10)
  const fromObject = objectName.match(/\d{4}-\d{2}-\d{2}/)
  return fromObject ? fromObject[0] : '未标注'
}

function dateRank(date) {
  return /^\d{4}-\d{2}-\d{2}$/.test(date) ? date : '0000-00-00'
}

function collectSection(section) {
  const sectionRoot = path.join(root, section.dir)
  const files = walk(sectionRoot)
    .filter((file) => /\.md$/i.test(file))
    .filter((file) => !/README\.md$/i.test(file))
    .filter((file) => !/_evidence-ledger\.md$/i.test(file))
    .filter((file) => {
      const rel = path.relative(sectionRoot, file)
      const parts = rel.split(path.sep)
      const objectName = parts[0] || ''
      const base = path.basename(file, '.md')
      return base === objectName || base.startsWith(`${objectName} `)
    })

  const reports = files.map((file) => {
    const rel = path.relative(root, file)
    const parts = rel.split(path.sep)
    const objectName = parts[1] || path.basename(file, '.md')
    const markdown = readUtf8(file)
    const ledger = findLedger(file)
    const date = reportDate(parts, objectName)
    const stat = statSync(file)

    return {
      title: firstHeading(markdown, path.basename(file, '.md')),
      object: objectName,
      date,
      summary: firstSummary(markdown),
      path: toPosix(rel),
      link: `/${stripMd(toPosix(rel))}`,
      evidencePath: ledger ? toPosix(path.relative(root, ledger)) : '',
      evidenceRows: ledger ? countLedgerRows(ledger) : 0,
      updatedAt: stat.mtime.toISOString()
    }
  })

  reports.sort((a, b) => dateRank(b.date).localeCompare(dateRank(a.date)) || a.object.localeCompare(b.object, 'zh-Hans-CN'))

  const objectMap = new Map()
  for (const report of reports) {
    if (!objectMap.has(report.object)) objectMap.set(report.object, [])
    objectMap.get(report.object).push(report)
  }

  const objects = Array.from(objectMap.entries()).map(([name, objectReports]) => {
    objectReports.sort((a, b) => dateRank(b.date).localeCompare(dateRank(a.date)))
    const readme = path.join(sectionRoot, name, 'README.md')
    return {
      name,
      latest: objectReports[0],
      reports: objectReports,
      readmePath: existsSync(readme) ? toPosix(path.relative(root, readme)) : ''
    }
  })

  objects.sort((a, b) => {
    const byDate = b.latest.date.localeCompare(a.latest.date)
    return byDate || a.name.localeCompare(b.name, 'zh-Hans-CN')
  })

  return {
    ...section,
    objects,
    reports,
    count: reports.length
  }
}

const categories = sections.map(collectSection)
const allReports = categories.flatMap((category) =>
  category.reports.map((report) => ({
    ...report,
    categoryKey: category.key,
    categoryTitle: category.title,
    accent: category.accent
  }))
)

allReports.sort((a, b) => dateRank(b.date).localeCompare(dateRank(a.date)) || b.updatedAt.localeCompare(a.updatedAt))

const archive = {
  generatedAt: allReports[0]?.updatedAt ?? '',
  totals: {
    reports: allReports.length,
    objects: categories.reduce((sum, category) => sum + category.objects.length, 0),
    evidenceRows: allReports.reduce((sum, report) => sum + report.evidenceRows, 0)
  },
  latestReports: allReports.slice(0, 8),
  categories
}

const outDir = path.join(root, '.vitepress', 'theme')
mkdirSync(outDir, { recursive: true })
writeFileSync(path.join(outDir, 'archive-data.json'), `${JSON.stringify(archive, null, 2)}\n`, 'utf8')

console.log(`Generated archive data: ${archive.totals.reports} reports across ${archive.totals.objects} objects.`)
