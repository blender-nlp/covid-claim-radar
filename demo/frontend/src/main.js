import Vue from 'vue'
import App from './App.vue'
import router from './router'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
import locale from 'element-ui/lib/locale/lang/en'

import vGallery from 'v-gallery'

import ArgonDashboard from './plugins/argon-dashboard'
Vue.use(ArgonDashboard)

Vue.use(vGallery)

Vue.use(ElementUI, { locale })
Vue.config.productionTip = false

new Vue({
  router,
  render: h => h(App)
}).$mount('#app')
