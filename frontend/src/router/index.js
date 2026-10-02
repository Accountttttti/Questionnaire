import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import MainLayout from '../views/MainLayout.vue'
import HomeView from '../views/HomeView.vue'
import MineView from '../views/MineView.vue'
import ProfileView from '../views/ProfileView.vue'
import MessagesView from '../views/MessagesView.vue'
import EditorView from '../views/EditorView.vue'
import PublishSuccessView from '../views/PublishSuccessView.vue'
import FillIntroView from '../views/FillIntroView.vue'
import FillView from '../views/FillView.vue'

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
      ],
    },
    { path: '/editor/:id', component: EditorView },
    { path: '/publish/:id', component: PublishSuccessView },
    { path: '/fill/:id', component: FillIntroView },
    { path: '/fill/:id/answer', component: FillView },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.path.startsWith('/fill')) {
    return
  }
  if (to.path !== '/login' && !token) {
    return '/login'
  }
  if (to.path === '/login' && token) {
    return '/'
  }
})

export default router
