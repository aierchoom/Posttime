<script setup lang="ts">
import { computed, ref } from 'vue'
import model from '../../../公司档案/京东方A（000725）/2026-09-15/情景模型.json'

const base = model.core.Base.fy2027
const margin = ref(14.7)
const pe = ref(20)
const result = computed(() => {
  const displayRevenue = base.segments['显示'][0]
  const gross = base.gross_profit - base.segments['显示'][1] + displayRevenue * margin.value / 100
  const pretax = gross - base.opex - base.finance + base.other_income + base.investment - base.impairment
  const tax = pretax * 0.25
  const parent = pretax - tax - base.minority
  const eps = parent / model.share_count_100million
  return { gross, pretax, tax, parent, eps, price: eps * pe.value, low: eps * 18, high: eps * 22 }
})
const bridge = computed(() => [
  ['合并毛利', result.value.gross],
  ['减：销管研及税金附加（11%）', -base.opex],
  ['减：财务费用', -base.finance],
  ['加：其他收益', base.other_income],
  ['加：投资收益', base.investment],
  ['减：减值', -base.impairment],
  ['税前利润', result.value.pretax],
  ['减：所得税（25%）', -result.value.tax],
  ['减：少数股东损益', -base.minority],
  ['归母净利润', result.value.parent]
])
const format = (value: number, digits = 4) => value.toLocaleString('zh-CN', {
  minimumFractionDigits: digits, maximumFractionDigits: digits
})
</script>

<template>
  <section class="boe-calculator" aria-label="京东方2027年Base估值计算器">
    <div class="boe-controls">
      <label for="boe-doc-margin">
        <span>显示毛利率（假设） <output>{{ margin.toFixed(1) }}%</output></span>
        <input id="boe-doc-margin" v-model.number="margin" type="range" min="10" max="20" step="0.1">
      </label>
      <label for="boe-doc-pe">
        <span>2027预测PE（假设） <output>{{ pe }} 倍</output></span>
        <input id="boe-doc-pe" v-model.number="pe" type="range" min="12" max="28" step="1">
      </label>
    </div>
    <div class="boe-results" aria-live="polite" aria-atomic="true">
      <div>
        <span>2027归母净利润</span>
        <strong data-boe-profit>{{ format(result.parent) }} 亿元</strong>
        <small>EPS {{ format(result.eps, 6) }} 元</small>
      </div>
      <div>
        <span>所选PE对应每股估值</span>
        <strong data-boe-price>{{ format(result.price) }} 元</strong>
        <small>18–22倍：{{ format(result.low) }}–{{ format(result.high) }} 元</small>
      </div>
    </div>
    <details open>
      <summary>查看计算过程（金额：亿元）</summary>
      <table>
        <thead><tr><th scope="col">步骤</th><th scope="col">金额</th></tr></thead>
        <tbody>
          <tr v-for="[label, value] in bridge" :key="String(label)">
            <th scope="row">{{ label }}</th><td>{{ format(Number(value)) }}</td>
          </tr>
        </tbody>
      </table>
    </details>
    <p class="boe-note">固定股本370.4433亿股，其余假设沿用主报告Base。玻璃正向利润未计入。同行TTM与2027预测PE口径不同，滑块不会自动采用同行均值。</p>
  </section>
</template>

<style scoped>
.boe-calculator { margin: 24px 0; padding: 20px; border: 1px solid var(--vp-c-divider); border-radius: 12px; background: var(--vp-c-bg); color: var(--vp-c-text-1); font-variant-numeric: tabular-nums; }
.boe-controls, .boe-results { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }
.boe-controls label { display: grid; gap: 8px; min-width: 0; }
.boe-controls label span { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
.boe-controls input { width: 100%; min-height: 36px; accent-color: var(--vp-c-brand-1); }
.boe-results { margin: 16px 0; }
.boe-results > div { display: grid; gap: 4px; padding: 16px; border-radius: 8px; background: var(--vp-c-bg-soft); }
.boe-results strong { font-size: 22px; line-height: 1.5; overflow-wrap: anywhere; }
.boe-results small, .boe-note { color: var(--vp-c-text-2); font-size: 13px; }
.boe-calculator summary { cursor: pointer; padding: 8px 0; }
.boe-calculator table { display: table; width: 100%; margin: 8px 0; font-size: 14px; }
.boe-calculator th, .boe-calculator td { padding: 8px; overflow-wrap: anywhere; }
.boe-calculator td, .boe-calculator thead th:last-child { text-align: right; white-space: nowrap; }
.boe-calculator tbody th { font-weight: 400; }
.boe-calculator .boe-note { margin: 12px 0 0; line-height: 1.7; }
@media (max-width: 540px) { .boe-controls, .boe-results { grid-template-columns: 1fr; gap: 12px; } .boe-calculator { padding: 12px; } }
</style>
