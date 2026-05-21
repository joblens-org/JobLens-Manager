import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import ServiceList from '../views/ServiceList.vue'
import ServiceDetail from '../views/ServiceDetail.vue'
import JobManager from '../views/JobManager.vue'
import ConfigManager from '../views/ConfigManager.vue'
import RoleManager from '../views/RoleManager.vue'
import ClusterManager from '../views/ClusterManager.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard,
    },
    {
      path: '/services',
      name: 'services',
      component: ServiceList,
    },
    {
      path: '/services/:id',
      name: 'service-detail',
      component: ServiceDetail,
      props: true,
    },
    {
      path: '/jobs',
      name: 'jobs',
      component: JobManager,
    },
    {
      path: '/configs',
      name: 'configs',
      component: ConfigManager,
    },
    {
      path: '/roles',
      name: 'roles',
      component: RoleManager,
    },
    {
      path: '/clusters',
      name: 'clusters',
      component: ClusterManager,
    },
  ],
})

export default router
