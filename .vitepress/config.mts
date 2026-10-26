import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { defineConfig } from 'vitepress'

const archive = JSON.parse(
  readFileSync(resolve(__dirname, 'theme/archive-data.json'), 'utf8')
) as ArchiveData

type Report = {
  title: string
  object: string
  date: string
  link: string
}

type ArchiveObject = {
  name: string
  latest: Report
  reports: Report[]
  readmePath: string
}

type ArchiveCategory = {
  title: string
  dir: string
  objects: ArchiveObject[]
}

type ArchiveData = {
  categories: ArchiveCategory[]
}

function markdownLink(filePath: string) {
  if (!filePath) return ''
  return `/${filePath.replace(/\.md$/i, '')}`
}

function categorySidebar(category: ArchiveCategory) {
  return {
    text: category.title,
    collapsed: false,
    items: category.objects.map((object) => ({
      text: object.name,
      link: markdownLink(object.readmePath) || object.latest.link,
      collapsed: true,
      items: object.reports.map((report) => ({
        text: `${report.date} ${report.title}`,
        link: report.link
      }))
    }))
  }
}

const sidebar = [
  {
    text: '总览',
    items: [{ text: '研报档案', link: '/' }]
  },
  {
    text: '论文研究',
    collapsed: false,
    items: [
      { text: '研究索引', link: '/论文研究/README' },
      { text: 'LLM训练与DeepSeek调研', link: '/论文研究/算力与LLM训练_DeepSeek案例/2026-10-25/调研报告' },
      { text: '论文方案', link: '/论文研究/算力与LLM训练_DeepSeek案例/2026-10-25/论文方案' },
      { text: 'Scaling law与算力预估', link: '/论文研究/算力与LLM训练_DeepSeek案例/2026-10-25/Scaling%20law与未来算力预估' },
      { text: 'ETF与主动基金布局', link: '/论文研究/算力与LLM训练_DeepSeek案例/2026-10-25/相关ETF与主动基金布局' }
    ]
  },
  ...archive.categories.map(categorySidebar)
]

export default defineConfig({
  title: 'Posttime 研报档案',
  description: '公司、产业链与事件研究的版本化 GitBook',
  lang: 'zh-CN',
  base: process.env.VITEPRESS_BASE ?? '/Posttime/',
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: true,
  srcExclude: [
    '.agents/**',
    '.obsidian/**',
    '.skill-edit-posttime/**',
    '参考财报/**',
    'node_modules/**'
  ],
  head: [
    ['meta', { name: 'theme-color', content: '#0f172a' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'Posttime 研报档案' }]
  ],
  markdown: {
    lineNumbers: false
  },
  themeConfig: {
    logo: { light: '/logo.svg', dark: '/logo.svg', alt: 'Posttime' },
    nav: [
      { text: '档案总览', link: '/' },
      { text: '公司档案', link: '/公司档案/README' },
      { text: '产业链研究', link: '/产业链研究/README' },
      { text: '论文研究', link: '/论文研究/README' },
      { text: '事件研究', link: '/事件研究/Meta出租AI算力（2026-07-02）/Meta出租AI算力（2026-07-02）' }
    ],
    sidebar,
    outline: {
      level: [2, 3],
      label: '本页目录'
    },
    search: {
      provider: 'local'
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/aierchoom/Posttime' }
    ],
    docFooter: {
      prev: '上一篇',
      next: '下一篇'
    },
    lastUpdated: {
      text: '最后更新',
      formatOptions: {
        dateStyle: 'medium',
        timeStyle: 'short'
      }
    },
    darkModeSwitchLabel: '切换深色模式',
    sidebarMenuLabel: '菜单',
    returnToTopLabel: '回到顶部',
    langMenuLabel: '语言'
  }
})
