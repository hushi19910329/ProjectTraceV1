import { defineStore } from "pinia";

import { fetchCurrentUser, login } from "../api/auth";
import { useAppStore } from "./app";

const TOKEN_KEY = "projecttrace_token";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: window.localStorage.getItem(TOKEN_KEY) || "",
    currentUser: null,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
    allowedModuleKeys: (state) => state.currentUser?.module_permissions || [],
  },
  actions: {
    async login(payload) {
      const { data } = await login(payload);
      this.token = data.access_token;
      this.currentUser = data.user;
      window.localStorage.setItem(TOKEN_KEY, data.access_token);
      useAppStore().setMenus(data.menus);
      return data;
    },
    async loadCurrentUser() {
      if (!this.token) {
        return null;
      }
      const { data } = await fetchCurrentUser();
      this.currentUser = data.user;
      useAppStore().setMenus(data.menus);
      return data.user;
    },
    logout() {
      this.token = "";
      this.currentUser = null;
      window.localStorage.removeItem(TOKEN_KEY);
      useAppStore().clearMenus();
    },
  },
});
