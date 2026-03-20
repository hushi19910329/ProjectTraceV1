import { defineStore } from "pinia";

export const useAppStore = defineStore("app", {
  state: () => ({
    appName: "ProjectTrace",
    menuTree: [],
  }),
  getters: {
    topMenus: (state) => state.menuTree,
  },
  actions: {
    setMenus(menus) {
      this.menuTree = menus;
    },
    clearMenus() {
      this.menuTree = [];
    },
  },
});
