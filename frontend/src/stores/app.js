import { defineStore } from "pinia";

export const useAppStore = defineStore("app", {
  state: () => ({
    appName: "ProjectTrace",
    menuTree: [],
    sidebarCollapsed: false,
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
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed;
    },
    setSidebarCollapsed(value) {
      this.sidebarCollapsed = Boolean(value);
    },
  },
});
