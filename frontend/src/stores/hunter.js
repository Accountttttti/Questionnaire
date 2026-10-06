import { defineStore } from 'pinia'

// 猎人彩蛋状态按账号隔离：localStorage key 带用户名前缀，避免同一浏览器下不同账号串用。
function lsKey(name) {
  const u = localStorage.getItem('username') || 'anon'
  return `hunter_${u}_${name}`
}

export const useHunterStore = defineStore('hunter', {
  state: () => ({
    solved: false,
    deleted: false,
    seq: '',
    trainingUnlocked: false,
    hunterClass: '',
    nenType: '',
  }),
  getters: {
    unlocked: (state) => state.solved,
    hasValidSeq: (state) => /^[1-5]{5}$/.test(state.seq),
  },
  actions: {
    load() {
      this.solved = !!localStorage.getItem(lsKey('solved'))
      this.deleted = !!localStorage.getItem(lsKey('deleted'))
      this.seq = localStorage.getItem(lsKey('seq')) || ''
      this.trainingUnlocked = !!localStorage.getItem(lsKey('training'))
      this.hunterClass = localStorage.getItem(lsKey('class')) || ''
      this.nenType = localStorage.getItem(lsKey('nen')) || ''
    },
    setSolved() {
      this.solved = true
      localStorage.setItem(lsKey('solved'), '1')
    },
    setSeq(seq) {
      this.seq = seq
      localStorage.setItem(lsKey('seq'), seq)
    },
    setDeleted() {
      this.deleted = true
      localStorage.setItem(lsKey('deleted'), '1')
      if (!this.solved) {
        this.seq = ''
        localStorage.removeItem(lsKey('seq'))
      }
    },
    unlockTraining(classification, nenType) {
      this.trainingUnlocked = true
      this.hunterClass = classification || ''
      this.nenType = nenType || ''
      localStorage.setItem(lsKey('training'), '1')
      localStorage.setItem(lsKey('class'), this.hunterClass)
      localStorage.setItem(lsKey('nen'), this.nenType)
    },
  },
})
