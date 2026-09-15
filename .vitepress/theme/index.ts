import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import ArchiveHome from './components/ArchiveHome.vue'
import GiscusComments from './components/GiscusComments.vue'
import BoeValuationCalculator from './components/BoeValuationCalculator.vue'
import './styles.css'

export default {
  extends: DefaultTheme,
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'doc-after': () => h(GiscusComments)
    })
  },
  enhanceApp({ app }) {
    app.component('ArchiveHome', ArchiveHome)
    app.component('BoeValuationCalculator', BoeValuationCalculator)
  }
}
