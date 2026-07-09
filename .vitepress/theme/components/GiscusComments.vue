<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useData, useRoute } from 'vitepress'

const route = useRoute()
const { isDark } = useData()
const container = ref<HTMLElement | null>(null)

const repo = import.meta.env.VITE_GISCUS_REPO || 'aierchoom/Posttime'
const repoId = import.meta.env.VITE_GISCUS_REPO_ID || ''
const category = import.meta.env.VITE_GISCUS_CATEGORY || 'General'
const categoryId = import.meta.env.VITE_GISCUS_CATEGORY_ID || ''
const enabled = computed(() => Boolean(repo && repoId && category && categoryId))
const showComments = computed(() => enabled.value && route.path !== '/')

function renderGiscus() {
  if (!showComments.value || !container.value) return
  container.value.innerHTML = ''

  const script = document.createElement('script')
  script.src = 'https://giscus.app/client.js'
  script.async = true
  script.crossOrigin = 'anonymous'
  script.setAttribute('data-repo', repo)
  script.setAttribute('data-repo-id', repoId)
  script.setAttribute('data-category', category)
  script.setAttribute('data-category-id', categoryId)
  script.setAttribute('data-mapping', 'pathname')
  script.setAttribute('data-strict', '0')
  script.setAttribute('data-reactions-enabled', '1')
  script.setAttribute('data-emit-metadata', '0')
  script.setAttribute('data-input-position', 'bottom')
  script.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  script.setAttribute('data-lang', 'zh-CN')
  script.setAttribute('data-loading', 'lazy')
  container.value.appendChild(script)
}

function updateTheme() {
  const iframe = document.querySelector<HTMLIFrameElement>('iframe.giscus-frame')
  iframe?.contentWindow?.postMessage(
    {
      giscus: {
        setConfig: {
          theme: isDark.value ? 'dark' : 'light'
        }
      }
    },
    'https://giscus.app'
  )
}

onMounted(renderGiscus)

watch(
  () => route.path,
  async () => {
    await nextTick()
    renderGiscus()
  }
)

watch(isDark, updateTheme)
</script>

<template>
  <section v-if="showComments" class="research-comments" aria-label="留言">
    <div ref="container" />
  </section>
</template>
