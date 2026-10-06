import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import MainLayout from '../views/MainLayout.vue'
import HomeView from '../views/HomeView.vue'
import MineView from '../views/MineView.vue'
import ProfileView from '../views/ProfileView.vue'
import MessagesView from '../views/MessagesView.vue'
import AdminView from '../views/AdminView.vue'
import EditorView from '../views/EditorView.vue'
import PublishSuccessView from '../views/PublishSuccessView.vue'
import FillIntroView from '../views/FillIntroView.vue'
import FillView from '../views/FillView.vue'
import HunterView from '../views/HunterView.vue'
import HunterTrainingView from '../views/HunterTrainingView.vue'
import HunterTrainingSessionView from '../views/HunterTrainingSessionView.vue'
import { useUserStore } from '../stores/user.js'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView },
    {
      path: '/',
      component: MainLayout,
      children: [
        { path: '', component: HomeView },
        { path: 'mine', component: MineView },
        { path: 'profile', component: ProfileView },
        { path: 'messages', component: MessagesView },
        { path: 'admin', component: AdminView },
      ],
    },
    { path: '/editor/:id', component: EditorView },
    { path: '/publish/:id', component: PublishSuccessView },
    { path: '/fill/:id', component: FillIntroView },
    { path: '/fill/:id/answer', component: FillView },
    { path: '/hunter', component: HunterView },
    { path: '/hunter/training', component: HunterTrainingView },
    { path: '/hunter/training/session', component: HunterTrainingSessionView },
  ],
})

router.beforeEach((to) => {
  const user = useUserStore()
  if (to.path.startsWith('/fill')) {
    return
  }
  if (to.path !== '/login' && !user.token) {
    return '/login'
  }
  if (to.path === '/login' && user.token) {
    return '/'
  }
})

export default router
