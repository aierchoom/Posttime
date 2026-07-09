<script setup lang="ts">
import { computed } from 'vue'
import { withBase } from 'vitepress'
import archive from '../archive-data.json'

const latestReports = computed(() => archive.latestReports.slice(0, 6))

function categoryLink(category: { dir: string }) {
  return withBase(`/${category.dir}/`)
}

function reportLink(report: { link: string }) {
  return withBase(report.link)
}
</script>

<template>
  <main class="archive-shell">
    <section class="archive-masthead">
      <div>
        <p class="archive-kicker">Posttime Research Archive</p>
        <h1>研报档案</h1>
        <p class="archive-lead">
          公司档案、产业链研究和事件研究的版本化阅读台。每份主报告保留日期版本、证据台账和后续复盘入口。
        </p>
      </div>
      <dl class="archive-stats">
        <div>
          <dt>研报</dt>
          <dd>{{ archive.totals.reports }}</dd>
        </div>
        <div>
          <dt>对象</dt>
          <dd>{{ archive.totals.objects }}</dd>
        </div>
        <div>
          <dt>证据行</dt>
          <dd>{{ archive.totals.evidenceRows }}</dd>
        </div>
      </dl>
    </section>

    <section class="archive-panel">
      <div class="archive-section-head">
        <div>
          <p>Latest</p>
          <h2>最新版本</h2>
        </div>
      </div>

      <div class="archive-card-grid">
        <article v-for="report in latestReports" :key="report.path" class="archive-card" :class="`is-${report.accent}`">
          <div class="archive-card-topline">
            <span>{{ report.categoryTitle }}</span>
            <time>{{ report.date }}</time>
          </div>
          <h3>
            <a :href="reportLink(report)">{{ report.object }}</a>
          </h3>
          <p>{{ report.summary }}</p>
          <div class="archive-card-meta">
            <span>{{ report.evidenceRows }} 条证据</span>
            <a :href="reportLink(report)">阅读</a>
          </div>
        </article>
      </div>
    </section>

    <section class="archive-directory">
      <article v-for="category in archive.categories" :key="category.key" class="archive-list">
        <div class="archive-list-head">
          <div>
            <p>{{ category.count }} 篇</p>
            <h2>{{ category.title }}</h2>
          </div>
          <a :href="categoryLink(category)">进入</a>
        </div>
        <ol>
          <li v-for="object in category.objects" :key="object.name">
            <a :href="reportLink(object.latest)">
              <span>{{ object.name }}</span>
              <time>{{ object.latest.date }}</time>
            </a>
          </li>
        </ol>
      </article>
    </section>
  </main>
</template>
