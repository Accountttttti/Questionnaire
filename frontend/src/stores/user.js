import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    username: localStorage.getItem('username') || '',
    role: 'user',
    avatar: '',
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
    isAdmin: (s) => s.role === 'super' || s.role === 'admin',
    initial: (s) => (s.username || '?').charAt(0),
  },
  actions: {
    authHeaders() {
      return { Authorization: this.token || '' }
    },
    setAuth(token, username) {
      this.token = token
      this.username = username
      localStorage.setItem('token', token)
      localStorage.setItem('username', username)
    },
    async fetchMe() {
      try {
        const res = await fetch('/api/me', { headers: this.authHeaders() })
        const data = await res.json()
        if (res.ok) {
          this.username = data.username
          this.role = data.role || 'user'
          this.avatar = data.avatar || ''
          localStorage.setItem('username', data.username)
          return data
        }
        return null
      } catch (e) {
        return null
      }
    },
    logout() {
      this.token = ''
      this.username = ''
      this.role = 'user'
      this.avatar = ''
      localStorage.removeItem('token')
      localStorage.removeItem('username')
    },
  },
})
