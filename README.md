# Posttime 研究档案

更新日期：2026-09-01

本仓库按“研究对象 → 日期版本”归档公司、产业链与事件研究。正式报告、证据台账和参考资料分开保存，网页列表由构建脚本扫描日期版本目录自动生成，不再在本文件重复维护容易过期的静态清单。

## 研究入口

- [公司档案](公司档案/README.md)
- [产业链研究](产业链研究/README.md)
- [事件研究](事件研究/)

## 目录结构

```text
公司档案/
  公司名称（代码）/
    README.md
    YYYY-MM-DD/
      公司名称（代码）.md
      公司名称（代码）_evidence-ledger.csv

产业链研究/
  主题/
    README.md
    YYYY-MM-DD/
      主题.md
      主题_evidence-ledger.csv

事件研究/
  事件名称/
    YYYY-MM-DD/
      事件名称.md
      事件名称_evidence-ledger.csv

参考财报/
  对象名称/
    公司公告、财报、同行材料、机构研报与公开来源摘录
```

## 列表规则

- 分类 README 只列每个对象的最新日期版本，并按日期倒序排列。
- 对象 README 保存历次版本、核心结论、关键变化和证伪条件。
- 网页构建只把与对象同名的 Markdown，以及使用空格后缀命名的正式更新 memo 识别为研报；`_计算说明.md` 等辅助文件不会进入研报列表。
- 日期版本目录内的报告链接必须指向真实文件，版本日期以目录名为准。

## 本地预览

```powershell
npm install
npm run docs:build
npm run docs:preview
```

`npm run docs:build` 会先更新 `.vitepress/theme/archive-data.json`，再执行 VitePress 构建。
